import json

# todo: make a dataclass for Config instead of using a dictionary

def createConfig() -> None: # if the config file doesn't exist this function needs to create it
    blankConfig = {
        "gameDirectory": None,
        "targetIpAddress": None
    }
    with open("./config.json", "x") as configFile:
        configFile.write(json.dumps(blankConfig))

def getConfig():
    """return type is any because for some reason json.loads also has a return type of any (ugh)"""
    with open("./config.json","r") as configFile:
        return json.loads(configFile.read())
    
def writeConfig(config: dict) -> None:
    with open("./config.json","w") as configFile:
        configFile.write(json.dumps(config))