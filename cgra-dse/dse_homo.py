from unicodedata import decimal
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
#set the number of judgement
num_obj=3
num_constr=0
allSample={}
'''def obj(params : pd.DataFrame) -> np.ndarray:

    with open('area.txt', 'r') as a:
        area=float(a.read().strip())
    with open('power.txt', 'r') as p:   
        power=float(p.read().strip())

    out={'F': array([[area, power]])}
    o = out['F'].reshape(1, num_obj)
    print(np.hstack([o]))
    return np.hstack([o])'''

def obj(params : pd.DataFrame) -> np.ndarray:

    with open('area.txt', 'r') as a:
        area=float(a.read().strip())
    with open('PEWaste.txt', 'r') as p:   
        power=float(p.read().strip())
    with open('bestLatency.txt', 'r') as l:   
        latency=float(l.read().strip())
    out={'F': array([[area, power,latency]])}
    o = out['F'].reshape(1, num_obj)
    #print((np.hstack([o])))
    return np.hstack([o])

def extract_pf(points : np.ndarray) -> np.ndarray:
    dom_matrix = Dominator().calc_domination_matrix(points,None)
    is_optimal = (dom_matrix >= 0).all(axis = 1)
    return points[is_optimal]  

def formResult(spec):
    with open('area.txt', 'r') as a:
        area=float(a.read().strip())
    with open('PEWaste.txt', 'r') as p:   
        power=float(p.read().strip())
    with open('bestLatency.txt', 'r') as l:   
        latency=float(l.read().strip())
    key=area+power+latency
    allSample[key]=spec
# {
#     "num_output_ib" : 3,
#     "num_rf_reg" : 1, %
#     "num_input_ob" : 6,
#     "num_row" : 4,
#     "operations" : [ "PASS", "ADD", "SUB", "MUL", "AND", "OR", "XOR", "SEL" ], %
#     "cfg_data_width" : 64, %
#     "cfg_addr_width" : 8,  %
#     "data_width" : 32,     %
#     "num_track" : 3,
#     "num_colum" : 4,
#     "cfg_blk_offset" : 2,    %
#     "connect_flexibility" : {
#       "num_otrack_per_opin" : 6,
#       "num_itrack_per_ipin" : 2,
#       "num_ipin_per_opin" : 9
#     },
#     "max_delay" : 4
# }

'''params = [
    {'name' : 'num_row', 'type' : 'int', 'lb' : 4, 'ub' : 10},
    {'name' : 'num_colum', 'type' : 'int', 'lb' : 4, 'ub' : 10},
    {'name' : 'num_track', 'type' : 'int', 'lb' : 1, 'ub' : 8},
    {'name' : 'max_delay', 'type' : 'int', 'lb' : 1, 'ub' : 8},
    {'name' : 'num_output_ib', 'type' : 'int', 'lb' : 1, 'ub' : 4},
    {'name' : 'num_input_ob', 'type' : 'int', 'lb' : 2, 'ub' : 8, 'step' : 2},
    {'name' : 'num_input_ib', 'type' : 'int', 'lb' : 1, 'ub' : 4},
    {'name' : 'num_output_ob', 'type' : 'int', 'lb' : 1, 'ub' : 4}, 
    {'name' : 'num_itrack_per_ipin', 'type' : 'int', 'lb' : 1, 'ub' : 5},
    {'name' : 'num_otrack_per_opin', 'type' : 'int', 'lb' : 1, 'ub' : 5},
    {'name' : 'num_ipin_per_opin', 'type' : 'int', 'lb' : 1, 'ub' : 2},
    {'name' : 'track_reged_mode', 'type' : 'int', 'lb' : 1, 'ub' : 2}, 
    {'name' : 'num_rf_reg', 'type' : 'int', 'lb' : 1, 'ub' : 1},
    {'name' : 'cfg_data_width', 'type' : 'int', 'lb' : 32, 'ub' : 32},
    {'name' : 'cfg_addr_width', 'type' : 'int', 'lb' : 8, 'ub' : 8},
    {'name' : 'data_width', 'type' : 'int', 'lb' : 32, 'ub' : 32},
    {'name' : 'cfg_blk_offset', 'type' : 'int', 'lb' : 2, 'ub' : 2}
]'''

'''params = [
    {'name' : 'num_row', 'type' : 'int', 'lb' : 4, 'ub' : 12},
    {'name' : 'num_colum', 'type' : 'int', 'lb' : 4, 'ub' : 12},
    {'name' : 'num_track', 'type' : 'int', 'lb' : 1, 'ub' : 2},
    {'name' : 'max_delay', 'type' : 'int', 'lb' : 1, 'ub' : 4},
    {'name' : 'num_output_ib', 'type' : 'int', 'lb' : 1, 'ub' : 2},
    {'name' : 'num_input_ob', 'type' : 'int', 'lb' : 2, 'ub' : 4},
    {'name' : 'num_input_ib', 'type' : 'int', 'lb' : 1, 'ub' : 2},
    {'name' : 'num_output_ob', 'type' : 'int', 'lb' : 1, 'ub' : 2}, 
    {'name' : 'num_itrack_per_ipin', 'type' : 'int', 'lb' : 2, 'ub' : 4},
    {'name' : 'num_otrack_per_opin', 'type' : 'int', 'lb' : 2, 'ub' : 4},
    {'name' : 'num_ipin_per_opin', 'type' : 'int', 'lb' : 4, 'ub' : 4},
    {'name' : 'track_reged_mode', 'type' : 'int', 'lb' : 1, 'ub' : 1}, 
    {'name' : 'num_rf_reg', 'type' : 'int', 'lb' : 1, 'ub' : 1},
    {'name' : 'cfg_data_width', 'type' : 'int', 'lb' : 32, 'ub' : 32},
    {'name' : 'cfg_addr_width', 'type' : 'int', 'lb' : 12, 'ub' : 12},
    {'name' : 'data_width', 'type' : 'int', 'lb' : 32, 'ub' : 32},
    {'name' : 'cfg_blk_offset', 'type' : 'int', 'lb' : 2, 'ub' : 2}
]'''

params = [
    {'name' : 'num_row', 'type' : 'int', 'lb' : 4, 'ub' : 4},
    {'name' : 'num_colum', 'type' : 'int', 'lb' : 4, 'ub' : 4},
    {'name' : 'num_track', 'type' : 'int', 'lb' : 1, 'ub' : 6},
    {'name' : 'max_delay', 'type' : 'int', 'lb' : 1, 'ub' : 7},
    {'name' : 'num_output_ib', 'type' : 'int', 'lb' : 1, 'ub' : 2},
    {'name' : 'num_input_ob', 'type' : 'int', 'lb' : 1, 'ub' : 2},
    {'name' : 'num_input_ib', 'type' : 'int', 'lb' : 1, 'ub' : 2},
    {'name' : 'num_output_ob', 'type' : 'int', 'lb' : 1, 'ub' : 2}, 
    {'name' : 'num_itrack_per_ipin', 'type' : 'int', 'lb' : 2, 'ub' : 8},
    {'name' : 'num_otrack_per_opin', 'type' : 'int', 'lb' : 2, 'ub' : 8},
    {'name' : 'num_ipin_per_opin', 'type' : 'int', 'lb' : 2, 'ub' : 8},
    {'name' : 'cfg_addr_width', 'type' : 'int', 'lb' : 12, 'ub' : 12},
    {'name' : 'cfg_blk_offset', 'type' : 'int', 'lb' : 2, 'ub' : 2}
    #{'name' : 'diag_iopin_connect', 'type' : 'bool'}
]
#need to dump which is fixed
op = { #"operations" : [ "PASS", "ADD", "SUB", "MUL", "AND", "OR", "XOR" ],
        "operations" : [ "PASS", "ADD", "SUB", "MUL", "AND", "OR", "XOR","SHL","LSHR","ASHR","EQ","NE","LT","LE" ],
        "track_reged_mode":1,
        "num_rf_reg":1,
        "data_width":32,
        "cfg_data_width":32,
        "diag_iopin_connect":True
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
    subprocess.run('cd ../cgra-compiler && ./run.sh', shell=True)
    detect2=subprocess.run('cp ../cgra-compiler/PEWaste.txt .',shell=True).returncode
    detect3=subprocess.run('rm ../cgra-compiler/PEWaste.txt',shell=True).returncode
    detect4=subprocess.run('cp ../cgra-compiler/bestLatency.txt .',shell=True).returncode
    detect5=subprocess.run('rm ../cgra-compiler/bestLatency.txt',shell=True).returncode
    if (detect2==1 or detect3==1 or detect4==1 or detect5==1 ): raise TypeError
def run_cgra_ppa():
    subprocess.run('cd ../cgra-mg/SYNTHESIS && python3 scripts/run_synthesis.py', shell=True)
def run_cgra_analyze():
    subprocess.run('cd ../cgra-compiler && ./rundfg.sh >> /dev/null', shell=True)
    subprocess.run('cp ../cgra-compiler/dfgoptype.txt .',shell=True)
    subprocess.run('rm ../cgra-compiler/dfgoptype.txt',shell=True)

space = DesignSpace().parse(params)


conf = {}
conf['num_hiddens'] = 64
conf['num_layers'] = 2
conf['output_noise'] = False
conf['rand_prior'] = True
conf['verbose'] = False
conf['l1'] = 3e-3
conf['lr'] = 3e-2
conf['num_epochs'] = 100
opt = GeneralBO(space, num_obj, num_constr, model_conf = conf)
j=0

print('  <<<<<design space exploration begin>>>>>')


    
for i in range(5):
    rec = opt.suggest(n_suggestions=1)
    sample = rec.to_dict('records')[0]
    spec = formatSpec(sample)
    spec.update(**op)
    print(type(spec))
    # dump to the right place
    with open('cgra_spec.json', 'w') as f:
        json.dump(spec, f, indent=4)
        print(f)

    subprocess.run('cat cgra_spec.json',shell=True)
    subprocess.run('cp cgra_spec.json ../cgra-mg/src/main/resources', shell=True)
        
    try:
    #run CGRA modeling and generation and dump CGRA.v to cgra-mg to run ppa
        run_cgra_mg()
    except TypeError:
        print("MG ERROR")
        continue

    try:
    # run CGRA mapping 
        run_cgra_compiler()
    except TypeError:
        print("MAPPING ERROR")
        continue
    # run CGRA PPA using DC
    #run_cgra_ppa()
    # power.txt and area.txt should be extracted here as a result
    opt.observe(rec, obj(rec))
    formResult(spec)
    #print(allSample)
    j=j+1
    print('%d iterations\n ' % j )

#PF result
feasible_y = extract_pf(opt.y)
resultKey=feasible_y[:,0]+feasible_y[:,1]+feasible_y[:,2]

if(resultKey.size!=0):
    for i in range(resultKey.size):
        print('\n <<<<<design space exploration finished>>>>>')
        print(allSample[resultKey[i].astype(np.float)])
        print(feasible_y[i,0],feasible_y[i,1],feasible_y[i,2])
else:
    print("no valid arch reached")

print(feasible_y[:,0],feasible_y[:,1],feasible_y[:,2])
print('iterations are:%d ' % j )
end_time=time.time()
print('\n Total Time = '+str(end_time-start_time)+'\n')

'''draw
feasible_y = extract_pf(opt.y)
rand_y     = extract_pf(obj(space.sample(opt.y.shape[0])))
plt.plot(feasible_y[:,0], feasible_y[:,1], 'x', color = 'r', label = 'BO')
plt.plot(rand_y[:,0], rand_y[:,1], 'x', color = 'b', label = 'Rand')
plt.title('Number of Pareto optimal points from BO: ' )
plt.legend()
'''

