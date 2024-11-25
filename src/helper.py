import re
import platform

def removeCommasFromNumber(number: str) -> int:
    NUMBERS = ["1","2","3","4","5","6","7","8","9","0","-"]
    newString: str = ""
    for i in number:
        if i not in NUMBERS:
            continue
        else:
            newString += i
    return int(newString)

def isValidIPv4Address(addr: str):
    if re.search("^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\\.(?!$)|$)){4}$", addr) or addr == "localhost" or addr == "0":
        return True
    else:
        return False

def parsePath(path: str):
    """Since different operating systems use different slashes for file paths (windows), this function parses anything that doesn't match the OS slash and replaces it."""
    if platform.system() == "Windows":
        return path.replace("/","\\")
    else:
        return path.replace("\\","/")