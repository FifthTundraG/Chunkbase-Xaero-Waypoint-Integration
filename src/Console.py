from ast import literal_eval
from dataclasses import dataclass, field
import logging
from multiprocessing import Value
from typing import Tuple

from CoordinateConverter import CoordinateConverter
from XaeroWaypoints import XaeroWaypoints
from XaeroWaypoints import XaeroWaypointColors
from helper import removeCommasFromNumber

def parseCoordinatesFromStringCoordinates(stringCoordinates: str) -> Tuple[int, int, int]: # ex: X: -6,652 Z: -5,420
    splitList = stringCoordinates.split(" ") # will split into ["X:","<x-coordinate>","Z:","<y-coordinate>"] OR ["X:","<x-coordinate>","Y:","<y-coordinate>","Z:","<y-coordinate>"]
    if len(splitList) == 4: # is an X Z pair (no Y coord)
        return (removeCommasFromNumber(splitList[1]), 63, removeCommasFromNumber(splitList[3]))
    elif len(splitList) == 6: # is an X Y Z pair (yes Y coord)
        return (removeCommasFromNumber(splitList[1]), removeCommasFromNumber(splitList[3]), removeCommasFromNumber(splitList[5]))
    else:
        logging.critical("The provided value for the \"add\" command was recognized as string coordinates, but appears to be malformed. Double-check the provided coordinates to make sure they are correct. This is a fatal error, and program execution will now end.")
        exit()

def parseCoordinatesFromTeleportCommand(teleportCommand: str) -> Tuple[int, int, int]: # ex: /tp 7540 ~ -11516
    splitList = teleportCommand.split(" ")
    if splitList[2] == "~": # so no Z value is provided
        splitList[2] = "63"
    return (int(splitList[1]), int(splitList[2]), int(splitList[3]))

@dataclass
class Command:
    """CFLAGS is a reserved keyword for saying "the following flags are valid"\n
    CVALUE is a reserved keyword for saying "this command can take a value after the flags"\n
    CHELP is for giving help instructions for the command"""
    CHELP: str
    CVALUE: bool
    CFLAGS: dict[str, bool] = field(default_factory=dict)

@dataclass
class UserFlag:
    flag: str
    flagIndex: int
    value: str | None = None
    valueIndex: int | None = None
@dataclass
class UserCommand:
    corecommand: str
    flags: list[UserFlag]
    value: str

class Console:
    def __init__(self) -> None:
        self.commandRegistry: dict[str, Command] = {}

        self.currentInput: UserCommand

    def handleInput(self, userInput: str) -> UserCommand | bool:
        """Takes a user input as a string and will return a `UserCommand` if it is parsed sucessfully. If it is not, it will return False"""
        userInputComponents: list[str] = userInput.split(" ")

        # handle flags
        # userFlags will be a a dict with info about the flag, more specifically,
        # the flag itself, the indice of the flag in the components, the value of the flag, and the indice of the value of the flag in the components
        userFlags: list[UserFlag] = []
        for i, v in enumerate(userInputComponents):
            if v[0] == "-" and v[1] == "-": # so the start of the component is "--" (aka a flag)
                flagValue = None
                flagValueIndex = None
                try: # this is in a try/catch block because if a flag doesn't exist, this will error out because it can't find it in CFLAGS, but the check for if it exists is in checkCommandValidity, once userCommand["flags"] is already defined. Instead of re-writing most of the stuff here to work even it it doesn't exist, putting it in a try/catch and just ignoring the error is best, since an error with an actual error message will show up after this line, anyway
                    if self.commandRegistry[userInputComponents[0]].CFLAGS[v] != False:
                        flagValue = userInputComponents[i+1]
                        flagValueIndex = i+1
                except Exception:
                    pass
                userFlags.append(UserFlag(v, i, flagValue, flagValueIndex))

        # handle obtaining the userValue
        if len(userFlags) == 0: # if there are no flags
            userValue = userInputComponents[1:]
        elif userFlags[-1].value is None: # if it's a no-value flag
            userValue = userInputComponents[userFlags[-1].flagIndex+1:] # from the indice of the final flag to the end
        else: # if its a value flag
            userValue = userInputComponents[userFlags[-1].valueIndex+1:] # from the indice of the final flag to the end
        
        # create the command dict
        userCommand: UserCommand = UserCommand(userInputComponents[0], userFlags, " ".join(userValue))
        print(userCommand)
        
        # check for validity
        if self.checkCommandValidity(userCommand):
            self.currentInput = userCommand
            return userCommand
        else:
            logging.error("User command failed validity check.")
            return False #! do something
    
    def checkCommandValidity(self, userCommand: UserCommand):
        if userCommand.corecommand not in self.commandRegistry:
            logging.error("Invalid command.")
            return False
        for i in userCommand.flags:
            if i.flag not in self.commandRegistry[userCommand.corecommand].CFLAGS:
                logging.error(f"Invalid flag \"{i.flag}\" for command \"{userCommand.corecommand}\"")
                return False #! since this is a for loop, saying continue here will end THIS for loop, not the while running: for loop. big issue but fix later
        if self.commandRegistry[userCommand.corecommand].CVALUE == True and userCommand.value == "":
            logging.error(f"Command \"{userCommand.corecommand}\" requires an input.")
            return False
        return True

    def registerCommand(self, name: str, command: Command):
        self.commandRegistry[name] = command
        logging.debug("Sucessfully registered \"name\" command.")

    #* in the future this will ofc be more sophisticated, ideally i wouldn't have a chain of if statements and the xaeroWaypoints param is currently a temporary workaround
    def runCommand(self, userCommand: UserCommand, xaeroWaypoints: XaeroWaypoints) -> bool:
        """Handles where commands go to run.\n
        Returns a boolean based on whether or not the operation was successful, True is it was and False if it wasn't\n
        xaeroWaypoints param is temporary until I can figure out a better way to go about it."""
        if userCommand.corecommand == "add":
            if userCommand.value[0] == "X":
                waypointCoordinates: Tuple[int, int, int] = parseCoordinatesFromStringCoordinates(userCommand.value)
            elif userCommand.value[0] == "/":
                waypointCoordinates: Tuple[int, int, int] = parseCoordinatesFromTeleportCommand(userCommand.value)
            elif userCommand.value[0] == "(" and userCommand.value[-1] == ")": # a tuple (if the user made it correctly)
                try:
                    waypointCoordinates: Tuple[int, int, int] = literal_eval(userCommand.value)
                except (ValueError, SyntaxError) as e:
                    logging.error("An error occured when evaluating the tuple coordinates:", e)

                if len(waypointCoordinates) != 3:
                    logging.error("Waypoint coordinates passed as a tuple must contain X, Y, and Z values (length of 3).")
                    return False
            else:
                logging.error(f"Failed to parse string \"{userCommand.value}\"")
                return False
            
            # these are default values that are changed if certain values are present in the flags below
            waypointName: str = "new waypoint"
            waypointInitials: str | None = None
            waypointColor: str = str(XaeroWaypointColors.GREEN.value) #! this is returning the name of the enum member by default and i have no idea why, for some reason i have to specify to use .value or it will return "XaeroWaypointColors.GREEN"
            waypointDimension: str = XaeroWaypoints.OVERWORLD
            
            for i in userCommand.flags:
                if i.flag == "--innether":
                    waypointCoordinates = CoordinateConverter.overworldToNether(waypointCoordinates)
                    waypointDimension = XaeroWaypoints.NETHER
                    logging.info(f"Coordinates converted from Overworld to Nether coordinates.")
                if i.flag == "--inoverworld":
                    waypointCoordinates = CoordinateConverter.netherToOverworld(waypointCoordinates)
                    waypointDimension = XaeroWaypoints.OVERWORLD
                    logging.info(f"Coordinates converted from Nether to Overworld coordinates.")

                if i.flag == "--dimension":
                    if i.value == "overworld":
                        waypointDimension = XaeroWaypoints.OVERWORLD
                    elif i.value == "nether":
                        waypointDimension = XaeroWaypoints.NETHER
                    elif i.value == "the_end":
                        waypointDimension = XaeroWaypoints.THE_END
                    else:
                        logging.error("Invalid --dimension flag value: "+str(i.value))
                        return False
                if i.flag == "--name":
                    waypointName = str(i.value)
                if i.flag == "--initial":
                    # todo: add a limit on the number of chars this can be, idk what xaero uses but i know that there is one
                    waypointInitials = i.value
                if i.flag == "--color":
                    waypointColor = str(i.value)

            if waypointInitials is None: # it's value wasn't defined in a flag
                waypointInitials = waypointName[0].upper()
                
            xaeroWaypoints.addWaypoint({
                "name": waypointName,
                "initials": waypointInitials,
                "x": waypointCoordinates[0],
                "y": waypointCoordinates[1], # make this work
                "z": waypointCoordinates[2],
                "color": waypointColor,
                "disabled": "false",
                "type": 0,
                "set": "gui.xaero_default",
                "rotate_on_tp": "false",
                "tp_yaw": 0,
                "visibility_type": "0", # TODO: add boolean flag for local/global
                "destination": "false"
            }, waypointDimension)
            logging.info(f"Created waypoint \"{waypointName}\" at {str(waypointCoordinates)}!") # todo: make this output ACTUAL coords (this doesn't account for rounding)
        elif userCommand.corecommand == "help":
            if userCommand.value != "": # a value is provided
                # check if the input is a valid command
                if userCommand.corecommand not in self.commandRegistry:
                    logging.error(f"The \"{userCommand.corecommand}\" command does not exist.")
                    return False
                # check if the command even has help documented:
                # if "CHELP" not in self.commandRegistry[userCommand.value]:
                #     logging.error(f"The \"{userCommand.corecommand}\" command does not have documented help.")
                #     return False
                print(self.commandRegistry[userCommand.corecommand].CHELP)
            else: # no value is provided
                print("List of commands:")
                for i in self.commandRegistry:
                    print("- "+i)
                print("Type \"help <command>\" for additional information about the command.")
        elif userCommand.corecommand == "exit":
            exit()
        return True
        