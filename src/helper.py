def removeCommasFromNumber(number: str) -> int:
    NUMBERS = ["1","2","3","4","5","6","7","8","9","0","-"]
    newString: str = ""
    for i in number:
        if i not in NUMBERS:
            continue
        else:
            newString += i
    return int(newString)