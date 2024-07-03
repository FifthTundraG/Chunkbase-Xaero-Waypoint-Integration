from typing import Tuple
import os
import logging

class XaeroWaypointColors:
    BLACK: int = 0
    DARK_BLUE: int = 1
    DARK_GREEN: int = 2
    DARK_AQUA: int = 3
    DARK_RED: int = 4
    DARK_PURPLE: int = 5
    GOLD: int = 6
    GRAY: int = 7
    DARK_GRAY: int = 8
    BLUE: int = 9
    GREEN: int = 10
    AQUA: int = 11
    RED: int = 12
    LIGHT_PURPLE: int = 13
    YELLOW: int = 14
    WHITE: int = 15

#* example PyPoint (the way we store xaero waypoints)
#! BOOLEANS MUST BE STRINGS!!!
# booleans are not handled correctly when converted to strings (they must be converted to be used in str.join() when converting to xaero)
# they're stored with an uppercase T (True) when they need to be stored with a lowercase t (true)
# there's no effect on anything notable when the boolean is a string so pls use a string and no bool
examplePyPoints = [
    {
        "name": "Skeleton Spawner",
        "initials": "S",
        "x": -48,
        "y": 66,
        "z": -9,
        "color": XaeroWaypointColors.WHITE,
        "disabled": "false",
        "type": 0,
        "set": "gui.xaero_default",
        "rotate_on_tp": "false",
        "tp_yaw": 0,
        "visibility_type": "1",
        "destination": "false"
    }
]

WAYPOINT_FORMAT_MESSAGE: str = """#
#waypoint:name:initials:x:y:z:color:disabled:type:set:rotate_on_tp:tp_yaw:visibility_type:destination
#\n""" # this message is at the top of every waypoint file, and when converting from PyPoints to xaero waypoints we will lose the comment. i like to keep it there because it helps me remember the format for them, so this is that same message so we can place it at the top of the waypoint file

class XaeroWaypoints:
    OVERWORLD: str = "dim%0"
    NETHER: str = "dim%-1"
    THE_END: str = "dim%1"

    def __init__(self, waypointDirectory: str) -> None:
        self.waypointDirectory = waypointDirectory

        waypointDirFiles = os.listdir(f"{waypointDirectory}\\dim%0") # for this we just use overworld because that one's the easiest. we might be able to use worldmap for this but who knows
        print("Type the identifier associtated with which map you would like to use:")
        for i in enumerate(waypointDirFiles):
            print(f"({i[0]}) {i[1]}")
        mapSelection = int(input("Map ID: "))
        self.currentMap = waypointDirFiles[mapSelection]

        self.waypointsOverworld = self.parseXaeroWaypointFile(f"{waypointDirectory}\\{XaeroWaypoints.OVERWORLD}\\{self.currentMap}")
        self.waypointsNether = self.parseXaeroWaypointFile(f"{waypointDirectory}\\{XaeroWaypoints.NETHER}\\{self.currentMap}")
        self.waypointsTheEnd = self.parseXaeroWaypointFile(f"{waypointDirectory}\\{XaeroWaypoints.THE_END}\\{self.currentMap}")

        self.writeXaeroWaypointFile(self.waypointsOverworld, XaeroWaypoints.OVERWORLD)

    # this is run when we read from the waypoint file to convert the xaero waypoints to PyPoints
    def parseXaeroWaypointFile(self, file: str) -> list[dict] | None:
        newPyPoints: list[dict[str, str | Tuple[int, int, int] | int | bool]] = []
        try:
            with open(file, "r") as waypointFile:
                waypointsData: list[str] = waypointFile.read().split("\n")[3:-1]
        except FileNotFoundError:
            logging.warning(f"Unable to find file \"{file}\". It's possible no waypoints have been created in that dimension.")
            return None
        for i in waypointsData:
            newPyPoints.append(self.convertXaeroToPyPoint(i))
        return newPyPoints
    
    def convertXaeroToPyPoint(self, xaeroFormat: str) -> dict[str, str | Tuple[int, int, int] | int | bool]:
        newPyPoint: dict[str, str | Tuple[int, int, int] | int | bool] = {}

        waypointData: list = xaeroFormat.split(":")
        newPyPoint = {
            "name": waypointData[1],
            "initials": waypointData[2],
            "x": waypointData[3],
            "y": waypointData[4],
            "z": waypointData[5],
            "color": waypointData[6],
            "disabled": waypointData[7],
            "type": waypointData[8],
            "set": waypointData[9],
            "rotate_on_tp": waypointData[10],
            "tp_yaw": waypointData[11],
            "visibility_type": waypointData[12],
            "destination": waypointData[13]
        }
        return newPyPoint
    def convertPyPointToXaero(self, pyPoint: dict[str, str | Tuple[int, int, int] | int | bool]) -> str:
        waypointStart: str = "waypoint:"
        # xaero doesn't like decimals so round them out here
        pyPoint["x"] = str(round(int(pyPoint["x"]))) # type gymnastics!
        pyPoint["y"] = str(round(int(pyPoint["y"])))
        pyPoint["z"] = str(round(int(pyPoint["z"])))
        # str.join() only takes strings so this just set's every value in pyPoint to a string #! ISSUE! doesn't account for stuff like False -> false in json.loads() 'cause they're all strings
        for i, v in enumerate(pyPoint):
            pyPoint[v] = str(pyPoint[v])
        waypointCSV = ":".join(list(pyPoint.values()))
        return waypointStart+waypointCSV
    
    def writeXaeroWaypointFile(self, pyPoints: list[dict[str, str | Tuple[int, int, int] | int | bool]], dimension: str):
        with open(f"{self.waypointDirectory}\\{dimension}\\{self.currentMap}", "w") as waypointFile:
        # with open(f"C:\\Users\\fifth\\AppData\\Roaming\\.minecraft\\launcher_log.txt", "w") as waypointFile:
            waypointFile.write(f"{WAYPOINT_FORMAT_MESSAGE}")
            for i in pyPoints:
                waypointFile.write(self.convertPyPointToXaero(i)+"\n")

    def addWaypoint(self, pyPoint: dict[str, str | Tuple[int, int, int] | int | bool], dimension: str) -> None:
        if dimension == XaeroWaypoints.OVERWORLD:
            self.waypointsOverworld.append(pyPoint)
            self.writeXaeroWaypointFile(self.waypointsOverworld, XaeroWaypoints.OVERWORLD)
        elif dimension == XaeroWaypoints.NETHER:
            self.waypointsNether.append(pyPoint)
            self.writeXaeroWaypointFile(self.waypointsNether, XaeroWaypoints.NETHER)
        elif dimension == XaeroWaypoints.THE_END:
            self.waypointsTheEnd.append(pyPoint)
            self.writeXaeroWaypointFile(self.waypointsTheEnd, XaeroWaypoints.THE_END)
        else:
            logging.error("Invalid dimension parameter for XaeroWaypoints.addWaypoint()")
            return
        

    # def setWaypointDirectory(self, waypointDirectory: str) -> None: # todo: maps?
    #     self.waypointFile = open(waypointDirectory, "w") 