def loadPatternFile(patternPath:str) -> list:
    """Loads a csv file in for use by pattern module"""
    patternFP = open(patternPath, 'r')
    patternPieces = patternFP.readlines()

    patternPieces[0] = patternPieces[0].replace('\n', '')

    patternFields = patternPieces[0].split(',')

    pattern = []

    for line in patternPieces[1:]:
        patternDict = dict()

        line = line.replace('\n', '')

        linePieces = line.split(',')

        for idx, piece in enumerate(linePieces):
            patternDict[patternFields[idx]] = piece

        pattern.append(patternDict)

    patternFP.close()

    return pattern