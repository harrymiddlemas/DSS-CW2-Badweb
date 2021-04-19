from random import randint

def generateSessionToken():
    return randint(0,10)

print(generateSessionToken())