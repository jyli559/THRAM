import time
from numpy import *
from hebo.design_space.design_space import DesignSpace
from hebo.optimizers.hebo import HEBO
from cgraflow.archSpec import *
from cgraflow.runCGRA import *
from result import *

def thram(maxIt:int):
    start_time = time.time()
    allSample = {}
    params = paramspace()
    space = DesignSpace().parse(params)
    opt = HEBO(space)
    hete = cgra_analyze()
        
    keyAndSignleValue = []

    for i in range(maxIt):
        rec = opt.suggest(n_suggestions=1)
        sample = rec.to_dict('records')[0]
        spec = formatSpec(sample)
        spec.update(**otherArchPara())
        cgraspec = genSpec(spec, hete)
        dumpArchSpec(cgraspec)
            
        successMg = cgra_mg()
        if(not successMg):
            opt.observe(rec, obj(rec))
            keyAndSignleValue = formStore(spec, allSample, i, keyAndSignleValue, opt)
            continue

        successMapping = cgra_compiler()
        if(not successMapping):
            opt.observe(rec, obj(rec))
            keyAndSignleValue = formStore(spec, allSample, i, keyAndSignleValue, opt)
            continue

        opt.observe(rec, obj(rec))
        keyAndSignleValue = formStore(spec, allSample, i, keyAndSignleValue, opt)
        
        print('After %d iterations, best obj is %.2f' % (i, opt.y.min()))
        keyAndSignleValue.append(formResult(spec, allSample))

    getBestPara(opt, allSample, keyAndSignleValue)

    end_time = time.time()
    print('\n Total Time = '+str(end_time-start_time)+'\n')
