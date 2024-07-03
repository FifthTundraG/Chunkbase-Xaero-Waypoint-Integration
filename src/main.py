# Chunkbase Nether Coordinator
# Parses the coordinates from a string of overworld coordinates from Chunkbase and spits back nether coordinates

import logging
import json
from typing import Tuple
import os

from CoordinateConverter import CoordinateConverter
from helper import removeCommasFromNumber, isValidIPv4Address
from XaeroWaypoints import XaeroWaypoints, XaeroWaypointColors

# CFLAGS is a reserved keyword for saying "the following flags are valid"
# CVALUE is a reserved keyword for saying "this command can take a value after the flags"
# CHELP is for giving help instructions for the command
COMMANDS = {
    "add": {
        "CHELP": """Usage: add <flags> [coordinates]
        Description

        Required Arguments: 
        coordinates - The X, (Y), and Z of the waypoint. Can be copy/pasted in this format (what you see when clicking on an object): "X: -6,652 Z: -5,420", or this format (what the copy button gives you): /tp -1392 ~ -1264. If a Y-value is not provided it is set to 63.
        Flags: 
        --dimension [value]: What dimension to put the waypoint in. Allowed values are: "overworld", "nether", "the_end". "overworld" is the default value.
        --innether: Whether to translate Overworld coordinates to Nether coordinates and put the waypoint in the Nether. Y-level is set to 128 for Nether Roof travel.
        --inoverworld: Whether to translate Nether coordinates to Overworld coordinates and put the waypoint in the Overworld. Y-level is set to 63 since that's the Ocean level.""",
        "CFLAGS": { #* format is the flag then whether it has an input afterwards as it's default value, so for --dimension since it takes a value it's value is the default value "overworld", but since --innether doesn't take a value it is False
            "--dimension": XaeroWaypoints.OVERWORLD,
            "--innether": False, # says "these coordinates are from the overworld, but make the waypoint in the nether (divided by 8). All waypoint's Y levels will be set to 128 for nether roof travel purposes."
            "--inoverworld": False, # says "these coordinates are from the nether, but make the waypoint in the overworld (multiplied by 8)"
        },
        "CVALUE": True
    },
    "help": {
        "CHELP": """I seriously doubt you require additional assistance with the help command.""",
        "CVALUE": False
    },
    "exit": {
        "CHELP": """Exits the program.""",
        "CVALUE": False
    }
}

def parseCoordinatesFromStringCoordinates(stringCoordinates: str) -> Tuple[int, int, int]: # ex: X: -6,652 Z: -5,420
    splitList = stringCoordinates.split(" ") # will split into ["X:","<x-coordinate>","Z:","<y-coordinate>"] OR ["X:","<x-coordinate>","Y:","<y-coordinate>","Z:","<y-coordinate>"]
    if len(splitList) == 4: # is an X Z pair (no Y coord)
        return (removeCommasFromNumber(splitList[1]), 63, removeCommasFromNumber(splitList[3]))
    elif len(splitList) == 6: # is an X Y Z pair (yes Y coord)
        return (removeCommasFromNumber(splitList[1]), removeCommasFromNumber(splitList[3]), removeCommasFromNumber(splitList[5]))

def parseCoordinatesFromTeleportCommand(teleportCommand: str) -> Tuple[int, int]:
    pass

def createConfig(): # if the config file doesn't exist this function needs to create it
    blankConfig = {
        "gameDirectory": None,
        "targetIpAddress": None
    }
    with open("./config.json", "x") as configFile:
        configFile.write(json.dumps(blankConfig))

def getConfig():
    with open("./config.json","r") as configFile:
        return json.loads(configFile.read())
def writeConfig(config: dict) -> None:
    with open("./config.json","w") as configFile:
        configFile.write(json.dumps(config))

def main() -> None:
    logging.basicConfig(format='[%(levelname)s] %(message)s',level=logging.INFO)

    logging.warning("Currently, this tool only supports multiplayer servers. Singleplayer worlds will be added in the future.") # todo: you know what

    if "config.json" not in os.listdir("."):
        logging.info("A config.json file was not found at the project root. Creating a new one...")
        createConfig()
    
    config = getConfig()
    if config["gameDirectory"] == None: # it's at it's default value of null
        logging.warning("No game instance directory was set! Please type the path to your \".minecraft\" directory below:")
        minecraftDir = input("> ").replace("/","\\")
        config["gameDirectory"] = minecraftDir
        writeConfig(config)
        logging.info(f"Set gameDirectory to {minecraftDir}!")
    # check if the directory provided is actually a valid .minecraft folder
    # we do this by looking for the "logs" directory because it will always be present in every instance of the game as long as it's ever been launched.
    # we also put it in a try/except for a FileNotFoundError to check if the dir even exists
    try:
        if "logs" not in os.listdir(config["gameDirectory"]):
            logging.error(f"The provided .minecraft directory ({config["gameDirectory"]}) does not appear to be valid.")
            exit()
    except FileNotFoundError:
        logging.error(f"The provided .minecraft directory ({config["gameDirectory"]}) does not exist.")
        exit()
    # todo: check for trailing slash in gameDirectory and if there is one remove it

    # check that both minimap and world map are installed by looking in .minecraft/config for their config files
    # technically it's not flawless because the configs won't be generated if the game hasn't started up with the mod installed before,
    # but the chances of that happening are less than zero. also the reason we don't look for the .jar file is because, unlike the config
    # file, it could be renamed
    configDirectoryContents = os.listdir(f"{config["gameDirectory"]}\\config")
    if "xaerominimap.txt" not in configDirectoryContents:
        logging.warning("Xaero's Minimap was not detected in this instance. You have a very high chance of receiving errors following this message.")
    if "xaeroworldmap.txt" not in configDirectoryContents:
        logging.warning("Xaero's World Map was not detected in this instance. You have a very high chance of receiving errors following this message.")

    if config["targetIpAddress"] == None:
        logging.warning("No target IP address was set! Please type the IP address of the server you want to add the waypoints to below:")
        targetIP = input("> ")
        if not isValidIPv4Address(targetIP):
            logging.error("The provided target IP address is not valid.")
            exit()
        config["targetIpAddress"] = targetIP
        writeConfig(config)
        logging.info(f"Set targetIpAddress to {targetIP}!")

    logging.info(f"Using \"{config["gameDirectory"]}\" as gameDirectory.")
    logging.info(f"Using \"{config["targetIpAddress"]}\" as targetIpAddress.")

    xaeroWaypoints: XaeroWaypoints = XaeroWaypoints(f"{config["gameDirectory"]}\\XaeroWaypoints\\Multiplayer_{config["targetIpAddress"]}")

    running = True
    print("Chunkbase-Xaero Waypoint Integration Script. Type \"help\" for instructions.")
    while running:
        userInput: str = input("> ")
        if userInput == "" or userInput is None:
            logging.error("An input is required to continue.")
            continue

        userInputComponents: list[str] = userInput.split(" ")

        # handle flags
        # userFlags will be a a dict with info about the flag, more specifically,
        # the flag itself, the indice of the flag in the components, the value of the flag, and the indice of the value of the flag in the components
        userFlags: list[dict[str, str | int]] = []
        for i, v in enumerate(userInputComponents):
            if v[0] == "-" and v[1] == "-": # so the start of the component is "--" (aka a flag)
                flagValue = None
                flagValueIndex = None
                if COMMANDS[userInputComponents[0]]["CFLAGS"][v] != False:
                    flagValue = userInputComponents[i+1]
                    flagValueIndex = i+1
                userFlags.append({
                    "flag": v,
                    "flagIndex": i,
                    "value": flagValue,
                    "valueIndex": flagValueIndex
                })

        # handle obtaining the userValue
        if len(userFlags) == 0: # if there are no flags
            userValue = userInputComponents[1:]
        elif userFlags[-1]["value"] is None: # if it's a no-value flag
            userValue = userInputComponents[userFlags[-1]["flagIndex"]+1:] # from the indice of the final flag to the end
        else: # if its a value flag
            userValue = userInputComponents[userFlags[-1]["valueIndex"]+1:] # from the indice of the final flag to the end
        
        # create the command dict
        userCommand = {
            "corecommand": userInputComponents[0],
            "flags": userFlags,
            "value": " ".join(userValue)
        }
        print(userCommand)

        if userCommand["corecommand"] not in COMMANDS:
            logging.error("Invalid command.")
            continue
        for i in userCommand["flags"]:
            if i["flag"] not in COMMANDS[userCommand["corecommand"]]["CFLAGS"]:
                logging.error(f"Invalid flag \"{i["flag"]}\" for command \"{userCommand["corecommand"]}\"")
                continue
        if COMMANDS[userCommand["corecommand"]]["CVALUE"] == True and userCommand["value"] == "":
            logging.error(f"Command \"{userCommand["corecommand"]}\" requires an input.")
            continue
        
        if userCommand["corecommand"] == "add":
            if userCommand["value"][0] == "X": # todo: ternary?
                waypointCoordinates: Tuple[int, int, int] = parseCoordinatesFromStringCoordinates(userCommand["value"])
            elif userCommand["value"][0] == "/":
                waypointCoordinates: Tuple[int, int, int] = parseCoordinatesFromTeleportCommand(userCommand["value"])
            else:
                logging.error(f"Failed to parse string \"{userCommand["value"]}\"")
                continue

            waypointDimension: str = XaeroWaypoints.OVERWORLD
            
            for i in userCommand["flags"]:
                if i["flag"] == "--innether":
                    waypointCoordinates = CoordinateConverter.overworldToNether(waypointCoordinates)
                    waypointDimension = XaeroWaypoints.NETHER
                    logging.info(f"Coordinates converted from Overworld to Nether coordinates.")
                if i["flag"] == "--inoverworld":
                    waypointCoordinates = CoordinateConverter.netherToOverworld(waypointCoordinates)
                    waypointDimension = XaeroWaypoints.OVERWORLD
                    logging.info(f"Coordinates converted from Nether to Overworld coordinates.")

                if i["flag"] == "--dimension":
                    if i["value"] == "overworld":
                        waypointDimension = XaeroWaypoints.OVERWORLD
                    elif i["value"] == "nether":
                        waypointDimension = XaeroWaypoints.NETHER
                    elif i["value"] == "the_end":
                        waypointDimension = XaeroWaypoints.THE_END
                    else:
                        logging.error("Invalid --dimension flag value: "+i["value"])
                        continue
                
            xaeroWaypoints.addWaypoint({
                "name": "new waypoint",
                "initials": "N",
                "x": waypointCoordinates[0],
                "y": waypointCoordinates[1], # make this work
                "z": waypointCoordinates[2],
                "color": XaeroWaypointColors.GREEN,
                "disabled": "false",
                "type": 0,
                "set": "gui.xaero_default",
                "rotate_on_tp": "false",
                "tp_yaw": 0,
                "visibility_type": "1",
                "destination": "false"
            }, waypointDimension)
            logging.info("Created waypoint at "+str(waypointCoordinates)+"!") # todo: make this output ACTUAL coords (this doesn't account for rounding)
        elif userCommand["corecommand"] == "help":
            if userCommand["value"] != "": # a value is provided
                # check if the input is a valid command
                if userCommand["value"] not in COMMANDS:
                    logging.error(f"The \"{userCommand["corecommand"]}\" command does not exist.")
                    continue
                # check if the command even has help documented:
                if "CHELP" not in COMMANDS[userCommand["value"]]:
                    logging.error(f"The \"{userCommand["value"]}\" command does not have documented help.")
                    continue
                print(COMMANDS[userCommand["value"]]["CHELP"])
            else: # no value is provided
                print("List of commands:")
                for i in COMMANDS:
                    print("- "+i)
                print("Type \"help <command>\" for additional information about the command.")
        elif userCommand["corecommand"] == "exit":
            running = False

if __name__ == "__main__":
    main()