import pandas as pd
import numpy  as np
from hebo.optimizers.hebo import HEBO

def obj(params : pd.DataFrame) -> np.ndarray:

    with open('area.txt', 'r') as a:
        area = float(a.read().strip())
    with open('PEWaste.txt', 'r') as p:   
        pew = float(p.read().strip())
    with open('bestLatency.txt', 'r') as l:   
        latency = float(l.read().strip())
    with open('mappingFailureRate.txt', 'r') as m:   
        mappingFailureRate = float(m.read().strip())
    x = 1
    y = 1
    z = 1
    k = 0.4*1000000
    comprehensive = x*area+y*pew+z*latency+k*mappingFailureRate

    return np.array(comprehensive).reshape(-1, 1)
    

def formResult(spec : dict, allSample : dict):
    with open('area.txt', 'r') as a:
        area = float(a.read().strip())
    with open('PEWaste.txt', 'r') as p:   
        pew = float(p.read().strip())
    with open('bestLatency.txt', 'r') as l:   
        latency = float(l.read().strip())
    with open('mappingFailureRate.txt', 'r') as m:   
        mappingFailureRate = float(m.read().strip())
    x = 1
    y = 1
    z = 1
    k = 0.4*1000000
    key = x*area+y*pew+z*latency+k*mappingFailureRate
    allSample[key] = spec
    restoreResult = [key]
    result = [area,pew,latency,mappingFailureRate]
    return (restoreResult,result)

def formStore(spec : dict, allSample : dict, iter : int, keyAndSignleValue : list, opt : HEBO):
    restoreResult = formResult(spec, allSample)[0]
    if(iter == 0):
        keyAndSignleValue.append(formResult(spec, allSample))
    elif(restoreResult[0] < opt.y.min()):
        keyAndSignleValue.append(formResult(spec, allSample))
    return keyAndSignleValue

def getBestPara(opt : HEBO, allSample : dict, keyAndSignleValue : list):
    resultKey = opt.y.min()
    if(resultKey.size!=0):
        print(allSample[resultKey.astype(np.float)])
        for j in range(len(keyAndSignleValue)):
            if(keyAndSignleValue[j][0]==resultKey):
                print(keyAndSignleValue[j][1])
            else:
                continue
    else:
        print("no valid arch reached")
    print('\n <<<<< design space exploration finished >>>>>')