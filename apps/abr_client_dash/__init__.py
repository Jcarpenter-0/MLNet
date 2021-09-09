# Those code utilizes the dash changes made by the MIT Park and Pensieve Team

def MakeCustomDashClient(abrTargetIP:str, abrServerPort:int, finishedFilePath:str='./dash.all.min.js', dashClientCodePath:str='./dash.all.min.js'):
    """Load in the the dash code, and simply do a replacement for some code"""

    dashCodeFP = open(dashClientCodePath, 'r')
    dashLines = dashCodeFP.readlines()
    dashCodeFP.close()

    finishedDashLines = []

    for line in dashLines:
        line = line.replace('http://localhost:8333', 'http://{}:{}'.format(abrTargetIP, abrServerPort))
        finishedDashLines.append(line)

    finisheddashCodeFP = open(finishedFilePath, 'w')

    finisheddashCodeFP.writelines(finishedDashLines)

    finisheddashCodeFP.flush()
    finisheddashCodeFP.close()


def MakeCustomDashClientHTML(abrAlg:str, dashLib:str, finishedFilePath:str='', htmlPatternPath:str=''):
    """"""
    pass


