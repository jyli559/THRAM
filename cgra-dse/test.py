import pandas as pd
import numpy  as np
from hebo.design_space.design_space import DesignSpace
from hebo.optimizers.hebo import HEBO
import json
import subprocess


def obj(params : pd.DataFrame) -> np.ndarray:

    with open('area.txt', 'r') as a:
        area=float(a.read().strip())
    with open('power.txt', 'r') as p:   
        power=float(p.read().strip())
    print([area,power])
    return [area,power]
    
    #return ((params.values - 0.37)**2).sum(axis = 1).reshape(-1, 1)

# {
#     "num_output_ib" : 3,
#     "num_rf_reg" : 1,
#     "num_input_ob" : 6,
#     "num_row" : 4,
#     "operations" : [ "PASS", "ADD", "SUB", "MUL", "AND", "OR", "XOR", "SEL" ],
#     "cfg_data_width" : 64,
#     "cfg_addr_width" : 8,
#     "data_width" : 32,
#     "num_track" : 3,
#     "num_colum" : 4,
#     "cfg_blk_offset" : 2,
#     "connect_flexibility" : {
#       "num_otrack_per_opin" : 6,
#       "num_itrack_per_ipin" : 2,
#       "num_ipin_per_opin" : 9
#     },
#     "max_delay" : 4
# }

params = [
    {'name' : 'num_row', 'type' : 'int', 'lb' : 4, 'ub' : 32},
    {'name' : 'num_colum', 'type' : 'int', 'lb' : 4, 'ub' : 32},
    {'name' : 'num_track', 'type' : 'int', 'lb' : 1, 'ub' : 8},
    {'name' : 'max_delay', 'type' : 'int', 'lb' : 1, 'ub' : 8},
    {'name' : 'num_output_ib', 'type' : 'int', 'lb' : 1, 'ub' : 8},
    {'name' : 'num_input_ob', 'type' : 'int', 'lb' : 2, 'ub' : 16, 'step' : 2},
    {'name' : 'num_itrack_per_ipin', 'type' : 'int', 'lb' : 1, 'ub' : 20},
    {'name' : 'num_otrack_per_opin', 'type' : 'int', 'lb' : 1, 'ub' : 20},
    {'name' : 'num_ipin_per_opin', 'type' : 'int', 'lb' : 1, 'ub' : 20}
]

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
    subprocess.run('cd ../cgra-mg && ./run.sh', shell=True)

def run_cgra_compiler():
    subprocess.run('cd ../cgra-compiler && ./run.sh', shell=True)

def run_cgra_ppa():
    subprocess.run('cd ../cgra-mg/SYSTHESIS && python3 scripts/run_systhesis', shell=True)

space = DesignSpace().parse(params)
opt   = HEBO(space)
for i in range(5):
    # get samples in design space
    rec = opt.suggest(n_suggestions = 1)
    sample = rec.to_dict('records')[0]
    # get CGRA Specification Json file
    spec = formatSpec(sample)
    # print(json.dumps(spec, indent=4))
    with open('cgra_spec.json', 'w') as f:
        json.dump(spec, f, indent=4)
    # run CGRA modeling and generation
    run_cgra_mg()
    # run CGRA mapping
    run_cgra_compiler()
    # run CGRA PPA
    # run_cgra_ppa()

    opt.observe(rec, obj(rec))
    #print('After %d iterations, best obj is %.2f' % (i, opt.y.min()))
    print('After %d iterations, best obj is %.2fand%.2f' % (i, opt.y.min(),opt.x.min()))

    
