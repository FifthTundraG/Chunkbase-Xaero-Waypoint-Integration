# Chunkbase Nether Coordinator
# Parses the coordinates from a string of overworld coordinates from Chunkbase and spits back nether coordinates

import logging
import json
from typing import Tuple
import os
from ast import literal_eval # used for if a tuple is passed into the "add" command making that string into a tuple

import config
from Console import Command, Console
from CoordinateConverter import CoordinateConverter
from helper import removeCommasFromNumber, isValidIPv4Address
from XaeroWaypoints import XaeroWaypoints, XaeroWaypointColors

# CFLAGS is a reserved keyword for saying "the following flags are valid"
# CVALUE is a reserved keyword for saying "this command can take a value after the flags"
# CHELP is for giving help instructions for the command
COMMANDS = {
    "add": Command(
        CHELP="""Usage: add <flags> [coordinates]

Description
    Required Arguments: 
        coordinates: The X, (Y), and Z of the waypoint. Can be copy/pasted in this format (what you see when clicking on an object): "X: -6,652 Z: -5,420" or what the copy button gives you: "/tp -1392 ~ -1264". You can also pass a Tuple that contains the coordinates, ex. (432, 77, -98). If a Y-value is not provided it is set to 63.
    Flags: 
        --dimension [value]: What dimension to put the waypoint in. Allowed values are: "overworld", "nether", "the_end". Default value: "overworld"
        --name [value]: The name of the waypoint. Cannot have spaces. Default value: "new waypont"
        --initial [value]: The initial to show for the waypoint. Cannot exceed # characters. Default value: waypointName[0].upper() (the first char of waypointName uppercased)
        --color [value]: The color of the waypoint. Should be an integer from 0-15. Use the constants in the class XaeroWaypointColors to see the colors these numbers translate to. Default value: XaeroWaypointColors.GREEN
        --innether: Whether to translate Overworld coordinates to Nether coordinates and put the waypoint in the Nether. Y-level is set to 128 for Nether Roof travel.
        --inoverworld: Whether to translate Nether coordinates to Overworld coordinates and put the waypoint in the Overworld. Y-level is set to 63 since that's the Ocean level.""",
        CFLAGS={ #* format is the flag then whether it has an input afterwards, so for --dimension since it takes a value it's value is True, but since --innether doesn't take a value it is False
            "--dimension": True,
            "--name": True,
            "--initial": True,
            "--color": True,
            "--innether": False, # says "these coordinates are from the overworld, but make the waypoint in the nether (divided by 8). All waypoint's Y levels will be set to 128 for nether roof travel purposes."
            "--inoverworld": False # says "these coordinates are from the nether, but make the waypoint in the overworld (multiplied by 8)"
        },
        CVALUE=True
    ),
    "help": Command(
        CHELP="""I seriously doubt you require additional assistance with the help command.""",
        CVALUE=False
    ),
    "exit": Command(
        CHELP="""Exits the program.""",
        CVALUE=False
    )
}

#* this isn't in main() because when it's execution is started again (if gameDirectory config is malformed) we don't want this message printing write
# we don't use logging.warning() because basicConfig hasn't run yet (it's in main)
print("[WARNING] Currently, this tool only supports multiplayer servers. Singleplayer worlds will be added in the future.") # todo: you know what

def main() -> None:
    logging.basicConfig(format='[%(levelname)s] %(message)s',level=logging.INFO)

    if "config.json" not in os.listdir("."):
        logging.info("A config.json file was not found at the project root. Creating a new one...")
        config.createConfig()
    
    if config.getConfig()["gameDirectory"] == None: # it's at it's default value of null
        logging.warning("No game instance directory was set! Please type the path to your \".minecraft\" directory below:")
        minecraftDir = input("> ").replace("/","\\")
        newConfig = config.getConfig()
        newConfig["gameDirectory"] = minecraftDir
        config.writeConfig(newConfig)
        logging.info(f"Set gameDirectory to {minecraftDir}!")
    # check if the directory provided is actually a valid .minecraft folder
    # we do this by looking for the "logs" directory because it will always be present in every instance of the game as long as it's ever been launched.
    # we also put it in a try/except for a FileNotFoundError to check if the dir even exists
    try:
        if "logs" not in os.listdir(config.getConfig()["gameDirectory"]):
            logging.error(f"The provided .minecraft directory ({config.getConfig()["gameDirectory"]}) does not appear to be valid. Resetting config value...")
            newConfig = config.getConfig()
            newConfig["gameDirectory"] = None #* set the config value to None and write it to file, then restart execution of main() so that the program detects it's None and will ask for a dir to use.
            config.writeConfig(newConfig)
            main()
    except FileNotFoundError:
        logging.error(f"The provided .minecraft directory ({config.getConfig()["gameDirectory"]}) does not exist. Resetting config value...")
        newConfig = config.getConfig()
        newConfig["gameDirectory"] = None # see above comment
        config.writeConfig(newConfig)
        main()
    # todo: check for trailing slash in gameDirectory and if there is one remove it

    # check that both minimap and world map are installed by looking in .minecraft/config for their config files
    # technically it's not flawless because the configs won't be generated if the game hasn't started up with the mod installed before,
    # but the chances of that happening are less than zero. also the reason we don't look for the .jar file is because, unlike the config
    # file, it could be renamed
    #* this is put here because it requires config.gameDirectory to be assigned a value and it might as well be before we do anything with IP addresses since we don't need IP addresses for this check
    configDirectoryContents = os.listdir(f"{config.getConfig()["gameDirectory"]}\\config")
    if "xaerominimap.txt" not in configDirectoryContents:
        logging.warning("Xaero's Minimap was not detected in this instance. You have a very high chance of receiving errors following this message.")
    if "xaeroworldmap.txt" not in configDirectoryContents:
        logging.warning("Xaero's World Map was not detected in this instance. You have a very high chance of receiving errors following this message.")

    if config.getConfig()["targetIpAddress"] == None:
        logging.warning("No target IP address was set! Please type the IP address of the server you want to add the waypoints to below:")
        targetIP = input("> ")
        newConfig = config.getConfig()
        newConfig["targetIpAddress"] = targetIP
        config.writeConfig(newConfig)
        logging.info(f"Set targetIpAddress to {targetIP}!")
    
    if not isValidIPv4Address(config.getConfig()["targetIpAddress"]):
        logging.error(f"The provided target IP address ({config.getConfig()["targetIpAddress"]}) is not valid. Resetting config value...")
        newConfig = config.getConfig()
        newConfig["targetIpAddress"] = None #* set the config value to None and write it to file, then restart execution of main() so that the program detects it's None and will ask for a dir to use.
        config.writeConfig(newConfig)
        main()

    logging.info(f"Using \"{config.getConfig()["gameDirectory"]}\" as gameDirectory.")
    logging.info(f"Using \"{config.getConfig()["targetIpAddress"]}\" as targetIpAddress.")

    console: Console = Console()
    for i in COMMANDS:
        console.registerCommand(i, COMMANDS[i])
    xaeroWaypoints: XaeroWaypoints = XaeroWaypoints(f"{config.getConfig()["gameDirectory"]}\\XaeroWaypoints\\Multiplayer_{config.getConfig()["targetIpAddress"]}")

    running = True
    print("Chunkbase-Xaero Waypoint Integration Script. Type \"help\" for instructions.")
    while running:
        userInput: str = input("> ")
        if userInput == "" or userInput is None:
            logging.error("An input is required to continue.")
            continue
        
        userCommand = console.handleInput(userInput)
        if userCommand is False:
            logging.error("Failed to handle user input.")
            continue

        console.runCommand(userCommand, xaeroWaypoints)

if __name__ == "__main__":
    main()