
import json

def readJson(strFileName):
    dictData = None
    with open(strFileName,'r') as file:
        dictData = json.load(file)
    return dictData