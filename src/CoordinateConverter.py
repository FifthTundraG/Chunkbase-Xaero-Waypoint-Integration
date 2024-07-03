from typing import Tuple

class CoordinateConverter:
    def overworldToNether(overworldCoordinates: Tuple[int, int, int]) -> Tuple[int, int, int]:
        return (overworldCoordinates[0]/8, 128, overworldCoordinates[1]/8)

    def netherToOverworld(netherCoordinates: Tuple[int, int, int]) -> Tuple[int, int, int]:
        return (netherCoordinates[0]*8, netherCoordinates[1]*8)