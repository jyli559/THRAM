from tkinter.messagebox import RETRY
from unicodedata import decimal
from xml.sax import make_parser
from click import option
import pandas as pd
import numpy  as np
from numpy import *
from hebo.design_space.design_space import DesignSpace
from hebo.optimizers.hebo import HEBO
import json
import subprocess
import scipy as sp
import torch
from pymoo.factory import get_problem
from pymoo.util.plotting import plot
from pymoo.util.dominator import Dominator
import matplotlib.pyplot as plt
from hebo.optimizers.general import GeneralBO
import time

start_time = time.time()

allSample={}

def obj(params : pd.DataFrame) -> np.ndarray:

    with open('area.txt', 'r') as a:
        area=float(a.read().strip())
    with open('PEWaste.txt', 'r') as p:   
        pew=float(p.read().strip())
    with open('bestLatency.txt', 'r') as l:   
        latency=float(l.read().strip())
    with open('mappingFailureRate.txt', 'r') as m:   
        mappingFailureRate=float(m.read().strip())
    
    x=0.1
    y=0.4*1000000
    z=0.1*10000
    k=0.4*1000000
    comprehensive=x*area+y*pew+z*latency+k*mappingFailureRate

    return np.array(comprehensive).reshape(-1, 1)
 

def formResult(spec):
    with open('area.txt', 'r') as a:
        area=float(a.read().strip())
    with open('PEWaste.txt', 'r') as p:   
        pew=float(p.read().strip())
    with open('bestLatency.txt', 'r') as l:   
        latency=float(l.read().strip())
    with open('mappingFailureRate.txt', 'r') as m:   
        mappingFailureRate=float(m.read().strip())

    x=0.1
    y=0.4*1000000
    z=0.1*10000
    k=0.4*1000000
    key=x*area+y*pew+z*latency+k*mappingFailureRate
    allSample[key]=spec
    restoreResult=[key]
    result=[area,pew,latency,mappingFailureRate]
    return (restoreResult,result)


params = [
    {'name' : 'num_row', 'type' : 'int', 'lb' : 4, 'ub' : 4},
    {'name' : 'num_colum', 'type' : 'int', 'lb' : 11, 'ub' : 11},
    {'name' : 'num_track', 'type' : 'int', 'lb' : 2, 'ub' : 2},
    {'name' : 'max_delay', 'type' : 'int', 'lb' : 4, 'ub' : 4}, 
    {'name' : 'num_output_ib', 'type' : 'int', 'lb' : 2, 'ub' : 2},
    {'name' : 'num_input_ob', 'type' : 'int', 'lb' : 2, 'ub' : 2},
    {'name' : 'num_input_ib', 'type' : 'int', 'lb' : 2, 'ub' : 2},
    {'name' : 'num_output_ob', 'type' : 'int', 'lb' : 1, 'ub' : 1}, 
    {'name' : 'num_itrack_per_ipin', 'type' : 'int', 'lb' : 2, 'ub' : 2},
    {'name' : 'num_otrack_per_opin', 'type' : 'int', 'lb' : 4, 'ub' : 4},
    {'name' : 'num_ipin_per_opin', 'type' : 'int', 'lb' : 4, 'ub' : 4},
    {'name' : 'cfg_addr_width', 'type' : 'int', 'lb' : 12, 'ub' : 12},
    {'name' : 'cfg_blk_offset', 'type' : 'int', 'lb' : 2, 'ub' : 2}
    #{'name' : 'diag_iopin_connect','type' : 'bool'}
]


#need to dump which is fixed
op = { "operations" : [ "PASS", "ADD", "SUB", "MUL", "AND", "OR", "XOR","SHL","LSHR","ASHR","EQ","NE","LT","LE" ],
        "track_reged_mode":1,
        "num_rf_reg":1,
        "data_width":32,
        "cfg_data_width":32,
    "gpe_in_from_dir" : [ 4, 5, 7, 6 ],
    "gpe_out_to_dir" : [ 4, 5, 7, 6 ],
    "diag_iopin_connect" : True
    }


def formatSpec(sample : dict) -> dict:
    connect_flexibility = {
        'num_otrack_per_opin' : sample['num_otrack_per_opin'],
        'num_itrack_per_ipin' : sample['num_itrack_per_ipin'],
        'num_ipin_per_opin' : sample['num_ipin_per_opin']
    }
    del sample['num_otrack_per_opin']
    del sample['num_itrack_per_ipin']
    del sample['num_ipin_per_opin']
    sample['connect_flexibility'] = connect_flexibility
    return sample

def run_cgra_mg():
    detect1=subprocess.run('cd ../cgra-mg && ./run.sh', shell=True).returncode
    #subprocess.run('cp ../cgra-mg/test_run_dir/CGRA.v ../cgra-mg/SYNTHESIS/arch/RTL', shell=True)
    subprocess.run('cp ../cgra-mg/area.txt .',shell=True)
    if detect1==1 : raise TypeError
def run_cgra_compiler():
    detect1=subprocess.run('cd ../cgra-compiler && ./run.sh', shell=True)
    detect2=subprocess.run('cp ../cgra-compiler/PEWaste.txt .',shell=True).returncode
    detect3=subprocess.run('rm ../cgra-compiler/PEWaste.txt',shell=True).returncode
    detect4=subprocess.run('cp ../cgra-compiler/bestLatency.txt .',shell=True).returncode
    detect5=subprocess.run('rm ../cgra-compiler/bestLatency.txt',shell=True).returncode
    detect6=subprocess.run('cp ../cgra-compiler/mappingFailureRate.txt .',shell=True).returncode
    detect7=subprocess.run('rm ../cgra-compiler/mappingFailureRate.txt',shell=True).returncode
    if (detect1==1 or detect2==1 or detect3==1 or detect4==1 or detect5==1 or detect6==1 or detect7==1): raise TypeError
def run_cgra_ppa():
    subprocess.run('cd ../cgra-mg/SYNTHESIS && python3 scripts/run_synthesis.py', shell=True)
def run_cgra_analyze():
    subprocess.run('cd analyzeDFG && ./rundfg.sh ', shell=True)
    subprocess.run('cp analyzeDFG/dfgoptype.txt .',shell=True)
    subprocess.run('rm analyzeDFG/dfgoptype.txt',shell=True)

space = DesignSpace().parse(params)

opt   = HEBO(space)

print('  <<<<<design space exploration begin>>>>>')

result=[]

    
y=[]
keyAndSignleValue=[]

it=1
for i in range(it):
    rec = opt.suggest(n_suggestions=1)
    sample = rec.to_dict('records')[0]
    spec = formatSpec(sample)
    spec.update(**op)
    
    #print(spec)
    # dump to the right place
    with open('cgra_spec.json', 'w') as f:
        json.dump(spec, f, indent=4)
        #print(f)

    #subprocess.run('cat cgra_spec_hete.json',shell=True)
    subprocess.run('cp cgra_spec.json ../cgra-mg/src/main/resources', shell=True)
        
    try:
    #run CGRA modeling and generation and dump CGRA.v to cgra-mg to run ppa
        run_cgra_mg()
    except TypeError:
        print("MG ERROR")
        #Parameter penalty
        with open('area.txt', 'w') as a:
            a.write("1000000")
        with open('PEWaste.txt', 'w') as p:   
            p.write("1")
        with open('bestLatency.txt', 'w') as l:   
            l.write("20")
        with open('mappingFailureRate.txt', 'w') as m:   
            m.write("1")
    
        opt.observe(rec, obj(rec))

        restoreResult = formResult(spec)[0]
        
        if(i==0):
            y.append(restoreResult[0])
            keyAndSignleValue.append(formResult(spec))
        elif(restoreResult[0]< opt.y.min()):
            y.append(restoreResult[0])
            keyAndSignleValue.append(formResult(spec))
        else:
            y.append( opt.y.min() )
        

        print('%d iterations\n ' % (i+1) )
        continue

    try:
    # run CGRA mapping 
        run_cgra_compiler()
    except TypeError:
        print("MAPPING ERROR")
        #Parameter penalty
        with open('PEWaste.txt', 'w') as p:   
            p.write("1")
        with open('bestLatency.txt', 'w') as l:   
            l.write("20")
        with open('mappingFailureRate.txt', 'w') as m:   
            m.write("1")

        opt.observe(rec, obj(rec))

        restoreResult = formResult(spec)[0]
        
        if(i==0):
            y.append(restoreResult[0])
            keyAndSignleValue.append(formResult(spec))
        elif(restoreResult[0]< opt.y.min()):
            y.append(restoreResult[0])
            keyAndSignleValue.append(formResult(spec))
        else:
            y.append( opt.y.min() )
        
      
        # if(restoreResult[0]<=opt.y.min()):
        #     y.append(restoreResult[0])
        #     keyAndSignleValue.append(formResult(spec))
        

        print('%d iterations\n ' % (i+1) )
        continue
    
    # run CGRA PPA using DC
    #run_cgra_ppa()
    # pew.txt and area.txt should be extracted here as a result
    opt.observe(rec, obj(rec))

    restoreResult = formResult(spec)[0]
    
    if(i==0):
        y.append(restoreResult[0])
        keyAndSignleValue.append(formResult(spec))
    elif(restoreResult[0]< opt.y.min()):
        y.append(restoreResult[0])
        keyAndSignleValue.append(formResult(spec))
    else:
        y.append( opt.y.min() )
    
    #print(allSample)
    #print('%d iterations\n ' % (i+1) )
    print('After %d iterations, best obj is %.2f' % (i, opt.y.min()))
    keyAndSignleValue.append(formResult(spec))


#PF result
#feasible_y = extract_pf(opt.y)
resultKey=opt.y.min()
#print(resultKey)
if(resultKey.size!=0):
    print(allSample[resultKey.astype(np.float)])
    #print(feasible_y[i,0])
    for j in range(len(keyAndSignleValue)):
        if(keyAndSignleValue[j][0]==resultKey):
            print(keyAndSignleValue[j][1])
        else:
            continue
else:
    print("no valid arch reached")


print('\n <<<<<design space exploration finished>>>>>')
end_time=time.time()
print('\n Total Time = '+str(end_time-start_time)+'\n')


x=range(1,it+1)
x=[str(y) for y in x]
plt.plot(x, y, color='orangered', marker='o', linestyle='-', label='compo')
plt.legend()  
plt.xlabel("iterations")  
plt.ylabel("evaluation")  
plt.show()

with open('data.txt', 'w') as d:   
    for i in range(it):
        d.write(str(y[i])+'\n')

