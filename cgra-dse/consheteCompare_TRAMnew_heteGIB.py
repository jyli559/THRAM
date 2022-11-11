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
num_obj=1
num_constr=6

 
def obj(params : pd.DataFrame) -> np.ndarray:

    with open('area.txt', 'r') as a:
        area=float(a.read().strip())
    with open('PEWaste.txt', 'r') as p:   
        pew=float(p.read().strip())
    with open('bestLatency.txt', 'r') as l:   
        latency=float(l.read().strip())
    with open('mappingFailureRate.txt', 'r') as m:   
        mappingFailureRate=float(m.read().strip())
    with open('maxDFGNodes.txt', 'r') as d:   
        maxDFGNodes=float(d.read().strip())
    with open('maxcfgBits.txt', 'r') as b:   
        maxcfgBits=float(b.read().strip())
    
    x=0.1
    y=0.4*1000000
    z=0.1*10000
    k=0.4*1000000
    comprehensive=x*area+y*pew+z*latency+k*mappingFailureRate
    cons1 = maxDFGNodes - params.iloc[0,0] + params.iloc[0,1] #dfgnodes
    cons2 = params.iloc[0,8] - 2*params.iloc[0,2]              #itip
    cons3 = params.iloc[0,9] - 2*params.iloc[0,2]              #otop
    cons4 = params.iloc[0,11] - params.iloc[0,2]               #itip_l
    cons5 = params.iloc[0,12] - params.iloc[0,2]               #otop_l
    cons6 = maxcfgBits - 32 * 2**params.iloc[0,15]             #cfg constrain
    
    out={'F': np.array([[comprehensive]])}
    o = out['F'].reshape(1, num_obj)
    out={'G': np.array([[cons1, cons2, cons3, cons4, cons5,cons6]])}
    c = out['G'].reshape(1, num_constr)
    # print(params)
    # print(params.iloc[0,1])
    #print((np.hstack([o])))
    return np.hstack([o,c])

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

def extract_pf(points : np.ndarray) -> np.ndarray:
        dom_matrix = Dominator().calc_domination_matrix(points,None)
        is_optimal = (dom_matrix >= 0).all(axis = 1)
        return points[is_optimal]    

params = [
    {'name' : 'num_row', 'type' : 'int', 'lb' : 4, 'ub' : 16},
    {'name' : 'num_colum', 'type' : 'int', 'lb' : 4, 'ub' : 16},
    {'name' : 'num_track', 'type' : 'int', 'lb' : 1, 'ub' : 6},
    {'name' : 'max_delay', 'type' : 'int', 'lb' : 1, 'ub' : 7}, 
    {'name' : 'num_output_ib', 'type' : 'int', 'lb' : 1, 'ub' : 2},
    {'name' : 'num_input_ob', 'type' : 'int', 'lb' : 2, 'ub' : 2},
    {'name' : 'num_input_ib', 'type' : 'int', 'lb' : 1, 'ub' : 2},
    {'name' : 'num_output_ob', 'type' : 'int', 'lb' : 1, 'ub' : 2}, 
    {'name' : 'num_itrack_per_ipin', 'type' : 'int', 'lb' : 4, 'ub' : 8, 'step':2},
    {'name' : 'num_otrack_per_opin', 'type' : 'int', 'lb' : 4, 'ub' : 8, 'step':2},
    {'name' : 'num_ipin_per_opin', 'type' : 'int', 'lb' : 4, 'ub' : 8, 'step':2},
    {'name' : 'num_itrack_per_ipin_l', 'type' : 'int', 'lb' : 2, 'ub' : 6, 'step':2},
    {'name' : 'num_otrack_per_opin_l', 'type' : 'int', 'lb' : 2, 'ub' : 6, 'step':2},
    {'name' : 'num_ipin_per_opin_l', 'type' : 'int', 'lb' : 2, 'ub' : 4, 'step':2},
    {'name' : 'cfg_addr_width', 'type' : 'int', 'lb' : 12, 'ub' : 12},
    {'name' : 'cfg_blk_offset', 'type' : 'int', 'lb' : 1, 'ub' : 2}
]
# params = [
#     {'name' : 'num_row', 'type' : 'int', 'lb' : 4, 'ub' : 4},
#     {'name' : 'num_colum', 'type' : 'int', 'lb' : 4, 'ub' : 4},
#     {'name' : 'num_track', 'type' : 'int', 'lb' : 1, 'ub' : 1},
#     {'name' : 'max_delay', 'type' : 'int', 'lb' : 1, 'ub' : 1}, 
#     {'name' : 'num_output_ib', 'type' : 'int', 'lb' : 1, 'ub' : 1},
#     {'name' : 'num_input_ob', 'type' : 'int', 'lb' : 2, 'ub' : 2},
#     {'name' : 'num_input_ib', 'type' : 'int', 'lb' : 1, 'ub' : 1},
#     {'name' : 'num_output_ob', 'type' : 'int', 'lb' : 1, 'ub' : 1}, 
#     {'name' : 'num_itrack_per_ipin', 'type' : 'int', 'lb' : 4, 'ub' : 4,'step':2},
#     {'name' : 'num_otrack_per_opin', 'type' : 'int', 'lb' : 4, 'ub' : 4,'step':2},
#     {'name' : 'num_ipin_per_opin', 'type' : 'int', 'lb' : 4, 'ub' : 4,'step':2},
#     {'name' : 'num_itrack_per_ipin_l', 'type' : 'int', 'lb' : 2, 'ub' : 2,'step':2},
#     {'name' : 'num_otrack_per_opin_l', 'type' : 'int', 'lb' : 2, 'ub' : 2,'step':2},
#     {'name' : 'num_ipin_per_opin_l', 'type' : 'int', 'lb' : 2, 'ub' : 2},
#     {'name' : 'cfg_addr_width', 'type' : 'int', 'lb' : 12, 'ub' : 12},
#     {'name' : 'cfg_blk_offset', 'type' : 'int', 'lb' : 2, 'ub' : 2}
# ]
#need to dump which is fixed
op = { "operations" : [ "PASS", "ADD", "SUB", "MUL", "AND", "OR", "XOR","SHL","LSHR","ASHR","EQ","NE","LT","LE" ],
        "track_reged_mode":1,
        "num_rf_reg":1,
        "data_width":32,
        "cfg_data_width":32,
    "gpe_in_from_dir" : [ 4, 5, 7, 6 ],
    "gpe_out_to_dir" : [ 4, 5, 7, 6 ],
    "diag_iopin_connect" : True,
    "diag_iopin_connect_l" : False
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

def addGIB(row,col,diag_iopin_connect_h,diag_iopin_connect_l,fclist_h,fclist_l):
    gib=[]
    for i in range(row+1):
        gib.append([])
        if(i==0):
            for j in range(col+1):
                gib[i].append({"diag_iopin_connect" : diag_iopin_connect_l,"fclist" : fclist_l})
        else:
            for j in range(col+1):
                if(j==1 or j==col-1):
                    gib[i].append({"diag_iopin_connect" : diag_iopin_connect_h,"fclist" : fclist_h})
                else:
                    gib[i].append({"diag_iopin_connect" : diag_iopin_connect_l,"fclist" : fclist_l})
    return gib


def addGPE(row,col,add,mul,logic,comp,maxDelay):
    gpe=[]
    a=int(row*col*add)
    m=int(row*col*mul)
    l=int(row*col*logic)
    c=int(row*col*comp)
    print("ADD need:",a," ","MUL need:",m," ","LOGIC need:",l," ","COMP need:",c)
    atemp=0
    mtemp=0
    ltemp=0
    ctemp=0
    watch=[[0]*col for i in range(row)]
    #put around PE
    for i in range(row):
        gpe.append([])
        for j in range(col):
            if((i+1)%2==0):
                if((j+1)%2!=0):
                    gpe[i].append( {
                    "num_rf_reg" : 1,
                    "operations" : [ "PASS", "ADD", "SUB"],
                    "from_dir" : [ 4, 5, 7, 6 ],
                    "to_dir" : [ 4, 5, 7, 6 ],
                    "max_delay" : maxDelay
                    })
                    atemp=atemp+1
                else:
                    gpe[i].append( {
                    "num_rf_reg" : 1,
                    "operations" : [ "PASS", "MUL"],
                    "from_dir" : [ 4, 5, 7, 6 ],
                    "to_dir" : [ 4, 5, 7, 6 ],
                    "max_delay" : maxDelay
                    })
                    mtemp=mtemp+1
                    watch[i][j]=1
            else:
                if((j+1)%2!=0):
                    gpe[i].append( {
                    "num_rf_reg" : 1,
                    "operations" : [ "PASS", "MUL"],
                    "from_dir" : [ 4, 5, 7, 6 ],
                    "to_dir" : [ 4, 5, 7, 6 ],
                    "max_delay" : maxDelay
                    })
                    mtemp=mtemp+1
                    watch[i][j]=1
                else:
                    gpe[i].append( {
                    "num_rf_reg" : 1,
                    "operations" : [ "PASS", "ADD","SUB"],
                    "from_dir" : [ 4, 5, 7, 6 ],
                    "to_dir" : [ 4, 5, 7, 6 ],
                    "max_delay" : maxDelay
                    })
                    atemp=atemp+1
    
    for i in range (row-1):
        if(mtemp>=m):
            for j in range(col-1):
                if(gpe[i+1][j+1]["operations"]==[ "PASS","MUL"]):
                    gpe[i+1][j+1]["operations"]=[ "PASS", "ADD","SUB","MUL"]
                    atemp=atemp+1
                    watch[i+1][j+1]=2
                    if(atemp>=a):
                        break
            else:
                continue
            break
        else:
            for j in range(col-1):
                if(gpe[i+1][j+1]["operations"]==[ "PASS","ADD","SUB"]):
                    gpe[i+1][j+1]["operations"]=[ "PASS", "ADD","SUB","MUL"]
                    mtemp=mtemp+1
                    watch[i+1][j+1]=2
                    if(mtemp>=m-2):
                        break
            else:
                continue
            break

    print("ADD placed:",atemp," ","MUL placed:",mtemp," ","LOGIC placed:",ltemp," ","COMP placed:",ctemp)
    print(watch)
    return gpe

def run_cgra_mg():
    detect1=subprocess.run('cd ../cgra-mg && ./run.sh', shell=True).returncode
    #subprocess.run('cp ../cgra-mg/test_run_dir/CGRA.v ../cgra-mg/SYNTHESIS/arch/RTL', shell=True)
    subprocess.run('cp ../cgra-mg/area.txt .',shell=True)
    subprocess.run('rm ../cgra-mg/area.txt',shell=True) 
    subprocess.run('cp ../cgra-mg/maxcfgBits.txt .',shell=True)
    subprocess.run('rm ../cgra-mg/maxcfgBits.txt',shell=True) 
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
    subprocess.run('cp analyzeDFG/maxDFGNodes.txt .',shell=True)
    subprocess.run('rm analyzeDFG/maxDFGNodes.txt',shell=True) 

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

print('  <<<<<design space exploration begin>>>>>')
# to analyze DFG
run_cgra_analyze()
#get op hete
result=[]
with open('dfgoptype.txt','r') as f:
    for line in f:
        result.append(list(line.strip('\n').split(',')))    
    
add=float(result[0][0])
mul=float(result[1][0])
logic=float(result[2][0])
comp=float(result[3][0])
    
y=[]
keyAndSignleValue=[]

it=80
for i in range(it):
    rec = opt.suggest(n_suggestions=1)
    sample = rec.to_dict('records')[0]
    spec = formatSpec(sample)
    spec.update(**op)
    fclist_h=[]
    fclist_h.append(spec["connect_flexibility"]["num_itrack_per_ipin"])
    fclist_h.append(spec["connect_flexibility"]["num_otrack_per_opin"])
    fclist_h.append(spec["connect_flexibility"]["num_ipin_per_opin"])
    fclist_l=[]
    fclist_l.append(spec["num_itrack_per_ipin_l"])
    fclist_l.append(spec["num_otrack_per_opin_l"])
    fclist_l.append(spec["num_ipin_per_opin_l"])
    #op hete peocess
    row=spec["num_row"]
    col=spec["num_colum"]
    maxDelay=spec["max_delay"]
    diag_iopin_connect_h=spec["diag_iopin_connect"]
    diag_iopin_connect_l=spec["diag_iopin_connect_l"]
    GIB={"gibs":addGIB(row,col,diag_iopin_connect_h,diag_iopin_connect_l,fclist_h,fclist_l)}
    spec.update(**GIB)
    GPE={"gpes":addGPE(row,col,add,mul,logic,comp,maxDelay)}
    spec.update(**GPE)
    #print(spec)
    # dump to the right place
    with open('cgra_spec_hete.json', 'w') as f:
        json.dump(spec, f, indent=4)
        #print(f)

    #subprocess.run('cat cgra_spec_hete.json',shell=True)
    subprocess.run('cp cgra_spec_hete.json ../cgra-mg/src/main/resources', shell=True)
        
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
        elif(restoreResult[0]< opt.y[:,0].min()):
            y.append(restoreResult[0])
            keyAndSignleValue.append(formResult(spec))
        else:
            y.append( opt.y[:,0].min() )
        

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
        elif(restoreResult[0]< opt.y[:,0].min()):
            y.append(restoreResult[0])
            keyAndSignleValue.append(formResult(spec))
        else:
            y.append( opt.y[:,0].min() )
        
      
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
    elif(restoreResult[0]< opt.y[:,0].min()):
        y.append(restoreResult[0])
        keyAndSignleValue.append(formResult(spec))
    else:
        y.append( opt.y[:,0].min() )
    
    #print(allSample)
    #print('%d iterations\n ' % (i+1) )
    print('After %d iterations, best obj is %.2f' % (i, opt.y[:,0].min()))
    keyAndSignleValue.append(formResult(spec))


#PF result
#feasible_y = extract_pf(opt.y)
#resultKey=opt.y.min()
#print(resultKey)
# if(resultKey.size!=0):
#     print(allSample[resultKey.astype(np.float)])
#     #print(feasible_y[i,0])
#     for j in range(len(keyAndSignleValue)):
#         if(keyAndSignleValue[j][0]==resultKey):
#             print(keyAndSignleValue[j][1])
#         else:
#             continue
# else:
#     print("no valid arch reached")
feasible_y = extract_pf(opt.y)
resultKey=feasible_y[:,0].min()

if(resultKey.size!=0):
    print(allSample[resultKey.astype(np.float)])
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

