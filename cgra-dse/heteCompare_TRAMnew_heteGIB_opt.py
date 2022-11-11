from pickle import TRUE
from re import T
import pandas as pd
import numpy  as np
import json
import subprocess
import scipy as sp
import torch
import matplotlib.pyplot as plt
import time
from tkinter.messagebox import RETRY
from unicodedata import decimal
from xml.sax import make_parser
from click import option
from numpy import *
from hebo.design_space.design_space import DesignSpace
from hebo.optimizers.hebo import HEBO
from pymoo.factory import get_problem
from pymoo.util.plotting import plot
from pymoo.util.dominator import Dominator
from hebo.optimizers.general import GeneralBO


start_time = time.time()

allSample = {}

def obj(params : pd.DataFrame) -> np.ndarray:

    with open('area.txt', 'r') as a:
        area = float(a.read().strip())
    with open('PEWaste.txt', 'r') as p:   
        pew = float(p.read().strip())
    with open('bestLatency.txt', 'r') as l:   
        latency = float(l.read().strip())
    with open('mappingFailureRate.txt', 'r') as m:   
        mappingFailureRate = float(m.read().strip())
    
    # x=0.1
    # y=0.4*1000000
    # z=0.1*10000
    # k=0.4*1000000
    x = 1
    y = 0
    z = 0
    k = 0.4*10000000
    comprehensive = x*area+y*pew+z*latency+k*mappingFailureRate

    return np.array(comprehensive).reshape(-1, 1)
 

def formResult(spec):
    with open('area.txt', 'r') as a:
        area = float(a.read().strip())
    with open('PEWaste.txt', 'r') as p:   
        pew = float(p.read().strip())
    with open('bestLatency.txt', 'r') as l:   
        latency = float(l.read().strip())
    with open('mappingFailureRate.txt', 'r') as m:   
        mappingFailureRate = float(m.read().strip())

    # x=0.1
    # y=0.4*1000000
    # z=0.1*10000
    # k=0.4*1000000
    x = 1
    y = 0
    z = 0
    k = 0.4*1000000
    key = x*area+y*pew+z*latency+k*mappingFailureRate
    allSample[key] = spec
    restoreResult = [key]
    result = [area,pew,latency,mappingFailureRate]
    return (restoreResult,result)


# params = [
#     {'name' : 'num_row',               'type' : 'int', 'lb' : 4, 'ub' : 16},
#     {'name' : 'num_colum',             'type' : 'int', 'lb' : 4, 'ub' : 16},
#     {'name' : 'num_track',             'type' : 'int', 'lb' : 1, 'ub' : 6},
#     {'name' : 'max_delay',             'type' : 'int', 'lb' : 1, 'ub' : 7}, 
#     {'name' : 'num_output_ib',         'type' : 'int', 'lb' : 1, 'ub' : 2},
#     {'name' : 'num_input_ob',          'type' : 'int', 'lb' : 2, 'ub' : 2},
#     {'name' : 'num_input_ib',          'type' : 'int', 'lb' : 1, 'ub' : 2},
#     {'name' : 'num_output_ob',         'type' : 'int', 'lb' : 1, 'ub' : 2}, 
#     {'name' : 'num_itrack_per_ipin',   'type' : 'int', 'lb' : 2, 'ub' : 8},
#     {'name' : 'num_otrack_per_opin',   'type' : 'int', 'lb' : 2, 'ub' : 8},
#     {'name' : 'num_ipin_per_opin',     'type' : 'int', 'lb' : 2, 'ub' : 6},
#     {'name' : 'num_itrack_per_ipin_l', 'type' : 'int', 'lb' : 2, 'ub' : 4},
#     {'name' : 'num_otrack_per_opin_l', 'type' : 'int', 'lb' : 2, 'ub' : 4},
#     {'name' : 'num_ipin_per_opin_l',   'type' : 'int', 'lb' : 2, 'ub' : 4},
#     {'name' : 'cfg_addr_width',        'type' : 'int', 'lb' : 12, 'ub' : 12},
#     {'name' : 'cfg_blk_offset',        'type' : 'int', 'lb' : 2, 'ub' : 2}
#     #{'name' : 'diag_iopin_connect_l',  'type' : 'bool'}
# ]

params = [
    {'name' : 'num_row',               'type' : 'int', 'lb' : 4, 'ub' : 4},
    {'name' : 'num_colum',             'type' : 'int', 'lb' : 11, 'ub' : 11},
    {'name' : 'num_track',             'type' : 'int', 'lb' : 2, 'ub' : 2},
    {'name' : 'max_delay',             'type' : 'int', 'lb' : 4, 'ub' : 4}, 
    {'name' : 'num_output_ib',         'type' : 'int', 'lb' : 2, 'ub' : 2},
    {'name' : 'num_input_ob',          'type' : 'int', 'lb' : 2, 'ub' : 2},
    {'name' : 'num_input_ib',          'type' : 'int', 'lb' : 2, 'ub' : 2},
    {'name' : 'num_output_ob',         'type' : 'int', 'lb' : 1, 'ub' : 1}, 
    {'name' : 'num_itrack_per_ipin',   'type' : 'int', 'lb' : 4, 'ub' : 4},
    {'name' : 'num_otrack_per_opin',   'type' : 'int', 'lb' : 4, 'ub' : 4},
    {'name' : 'num_ipin_per_opin',     'type' : 'int', 'lb' : 4, 'ub' : 4},
    {'name' : 'num_itrack_per_ipin_l', 'type' : 'int', 'lb' : 2, 'ub' : 2},
    {'name' : 'num_otrack_per_opin_l', 'type' : 'int', 'lb' : 2, 'ub' : 2},
    {'name' : 'num_ipin_per_opin_l',   'type' : 'int', 'lb' : 2, 'ub' : 2},
    {'name' : 'cfg_addr_width',        'type' : 'int', 'lb' : 12, 'ub' : 12},
    {'name' : 'cfg_blk_offset',        'type' : 'int', 'lb' : 2, 'ub' : 2},
    {'name' : 'diag_iopin_connect_l',  'type' : 'bool'}
]

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
    gib = []
    for i in range(row+1):
        gib.append([])
        if(i==0 or i==row):
            for j in range(col+1):
                gib[i].append({"diag_iopin_connect" : diag_iopin_connect_l,"fclist" : fclist_l})
        else:
            for j in range(col+1):
                if(j==0 or j==col):
                    gib[i].append({"diag_iopin_connect" : diag_iopin_connect_l,"fclist" : fclist_l})
                else:
                    gib[i].append({"diag_iopin_connect" : diag_iopin_connect_h,"fclist" : fclist_h})
    return gib


def addGPE(row,col,add,mul,logic,comp,maxDelay):
    gpe = []
    a = int(row*col*add)
    m = int(row*col*mul)
    l = int(row*col*logic)
    c = int(row*col*comp)
    print("ADD need:",a," ","MUL need:",m," ","LOGIC need:",l," ","COMP need:",c)
    atemp = 0
    mtemp = 0
    ltemp = 0
    ctemp = 0
    watch = [[0]*col for i in range(row)]
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
                    atemp = atemp+1
                else:
                    gpe[i].append( {
                    "num_rf_reg" : 1,
                    "operations" : [ "PASS", "MUL"],
                    "from_dir" : [ 4, 5, 7, 6 ],
                    "to_dir" : [ 4, 5, 7, 6 ],
                    "max_delay" : maxDelay
                    })
                    mtemp = mtemp+1
                    watch[i][j] = 1
            else:
                if((j+1)%2!=0):
                    gpe[i].append( {
                    "num_rf_reg" : 1,
                    "operations" : [ "PASS", "MUL"],
                    "from_dir" : [ 4, 5, 7, 6 ],
                    "to_dir" : [ 4, 5, 7, 6 ],
                    "max_delay" : maxDelay
                    })
                    mtemp = mtemp+1
                    watch[i][j] = 1
                else:
                    gpe[i].append( {
                    "num_rf_reg" : 1,
                    "operations" : [ "PASS", "ADD","SUB"],
                    "from_dir" : [ 4, 5, 7, 6 ],
                    "to_dir" : [ 4, 5, 7, 6 ],
                    "max_delay" : maxDelay
                    })
                    atemp = atemp+1
    
    # for i in range (row-1):
    #     if(mtemp >= m):
    #         for j in range(col-1):
    #             if(gpe[i+1][j+1]["operations"]==[ "PASS","MUL"]):
    #                 gpe[i+1][j+1]["operations"]=[ "PASS", "ADD","SUB","MUL"]
    #                 atemp = atemp+1
    #                 watch[i+1][j+1]=2
    #                 if(atemp >= a):
    #                     break
    #         else:
    #             continue
    #         break
    #     else:
    #         for j in range(col-1):
    #             if(gpe[i+1][j+1]["operations"]==[ "PASS","ADD","SUB"]):
    #                 gpe[i+1][j+1]["operations"]=[ "PASS", "ADD","SUB","MUL"]
    #                 mtemp = mtemp+1
    #                 watch[i+1][j+1]=2
    #                 if(mtemp >= m-2):
    #                     break
    #         else:
    #             continue
    #         break

    m1 = int(row/2)
    m2 = int(row/2) + 1
    while(True):
        if(mtemp >= m):
            for j in range(col-1):
                if(gpe[m1][j+1]["operations"]==[ "PASS","MUL"]):
                    gpe[m1][j+1]["operations"] = [ "PASS", "ADD","SUB","MUL"]
                    atemp = atemp+1
                    watch[m1][j+1] = 2
                    if(atemp >= a):
                        break
                    else:
                        m1 = m1 - 1

                if(gpe[m2][j+1]["operations"]==[ "PASS","MUL"]):
                    gpe[m1][j+1]["operations"] = [ "PASS", "ADD","SUB","MUL"]
                    atemp = atemp+1
                    watch[m2][j+1] = 2
                    if(atemp >= a):
                        break
                    else:
                        m2 = m2 + 1
            else:
                continue
            break

        else:
            for j in range(col-1):
                if(gpe[m1][j+1]["operations"]==[ "PASS","ADD","SUB"]):
                    gpe[m1][j+1]["operations"] = [ "PASS", "ADD","SUB","MUL"]
                    mtemp = mtemp+1
                    watch[m1][j+1] = 2
                    if(mtemp >= m-2):
                        break
                    else:
                        m1 = m1 - 1

                if(gpe[m2][j+1]["operations"]==[ "PASS","ADD","SUB"]):
                    gpe[m2][j+1]["operations"] = [ "PASS", "ADD","SUB","MUL"]
                    mtemp = mtemp+1
                    watch[m2][j+1] = 2
                    if(mtemp >= m-2):
                        break
                    else:
                        m2 = m2 + 1
            else:
                continue
            break



    if(l != 0 or c != 0):
        i1 = 1
        i2 = row - 2
        while(True):
            for j in range (col-1):
                if((j+1)%2 == 0 ):
                    gpe[i1][j+1]["operations"] = gpe[i1][j+1]["operations"] + ["AND", "OR", "XOR","SHL","LSHR","ASHR"]
                    ltemp = ltemp + 1
                    if(ltemp>=l and ctemp<c):
                        gpe[i1][j+1]["operations"] = gpe[i1][j+1]["operations"] + ["EQ","NE","LT","LE"]
                        ctemp = ctemp + 1
                    elif(ltemp>=l and ctemp>=c):
                        break
                else:
                    gpe[i1][j+1]["operations"] = gpe[i1][j+1]["operations"] + ["EQ","NE","LT","LE"]
                    ctemp = ctemp + 1
                    if(ctemp>=c and ltemp<l):
                        gpe[i1][j+1]["operations"] = gpe[i1][j+1]["operations"] + ["AND", "OR", "XOR","SHL","LSHR","ASHR"]
                        ltemp = ltemp + 1
                    elif(ltemp>=l and ctemp>=c):
                        break
                i1 = i1 + 1

                if((j+1)%2 == 0 ):
                    gpe[i2][j+1]["operations"] = gpe[i2][j+1]["operations"] + ["AND", "OR", "XOR","SHL","LSHR","ASHR"]
                    ltemp = ltemp + 1
                    if(ltemp>=l and ctemp<c):
                        gpe[i2][j+1]["operations"] = gpe[i2][j+1]["operations"] + ["EQ","NE","LT","LE"]
                        ctemp = ctemp + 1
                    elif(ltemp>=l and ctemp>=c):
                        break
                else:
                    gpe[i2][j+1]["operations"] = gpe[i2][j+1]["operations"] + ["EQ","NE","LT","LE"]
                    ctemp = ctemp + 1
                    if(ctemp>=c and ltemp<l):
                        gpe[i2][j+1]["operations"] = gpe[i2][j+1]["operations"] + ["AND", "OR", "XOR","SHL","LSHR","ASHR"]
                        ltemp = ltemp + 1
                    elif(ltemp>=l and ctemp>=c):
                        break
                i2 = i2 - 1
            else:
                continue
            break


    print("ADD placed:",atemp," ","MUL placed:",mtemp," ","LOGIC placed:",ltemp," ","COMP placed:",ctemp)
    print(watch)
    return gpe

def run_cgra_mg():
    detect1 = subprocess.run('cd ../cgra-mg && ./run.sh', shell=True).returncode
    #subprocess.run('cp ../cgra-mg/test_run_dir/CGRA.v ../cgra-mg/SYNTHESIS/arch/RTL', shell=True)
    subprocess.run('cp ../cgra-mg/area.txt .',shell=True)
    if detect1==1 : raise TypeError
def run_cgra_compiler():
    detect1 = subprocess.run('cd ../cgra-compiler && ./run.sh', shell=True)
    detect2 = subprocess.run('cp ../cgra-compiler/PEWaste.txt .',shell=True).returncode
    detect3 = subprocess.run('rm ../cgra-compiler/PEWaste.txt',shell=True).returncode
    detect4 = subprocess.run('cp ../cgra-compiler/bestLatency.txt .',shell=True).returncode
    detect5 = subprocess.run('rm ../cgra-compiler/bestLatency.txt',shell=True).returncode
    detect6 = subprocess.run('cp ../cgra-compiler/mappingFailureRate.txt .',shell=True).returncode
    detect7 = subprocess.run('rm ../cgra-compiler/mappingFailureRate.txt',shell=True).returncode
    if (detect1==1 or detect2==1 or detect3==1 or detect4==1 or detect5==1 or detect6==1 or detect7==1): raise TypeError
def run_cgra_ppa():
    subprocess.run('cd ../cgra-mg/SYNTHESIS && python3 scripts/run_synthesis.py', shell=True)
def run_cgra_analyze():
    subprocess.run('cd analyzeDFG && ./rundfg.sh ', shell=True)
    subprocess.run('cp analyzeDFG/dfgoptype.txt .',shell=True)
    subprocess.run('rm analyzeDFG/dfgoptype.txt',shell=True)

space = DesignSpace().parse(params)

opt   = HEBO(space)

print('  <<<<< design space exploration begin >>>>>')
# to analyze DFG
run_cgra_analyze()
#get op hete
result = []
with open('dfgoptype.txt','r') as f:
    for line in f:
        result.append(list(line.strip('\n').split(',')))    
    
add   = float(result[0][0])
mul   = float(result[1][0])
logic = float(result[2][0])
comp  = float(result[3][0])
    
y = []
keyAndSignleValue = []

it = 1
for i in range(it):
    rec = opt.suggest(n_suggestions=1)
    sample = rec.to_dict('records')[0]
    spec = formatSpec(sample)
    spec.update(**op)

    track = spec['num_track']
    num_itrack_per_ipin_h = spec["connect_flexibility"]["num_itrack_per_ipin"] if (spec["connect_flexibility"]["num_itrack_per_ipin"] <= 2*track) else 2*track
    num_otrack_per_opin_h = spec["connect_flexibility"]["num_otrack_per_opin"] if (spec["connect_flexibility"]["num_otrack_per_opin"] <= 2*track) else 2*track
    fclist_h = []
    fclist_h.append(num_itrack_per_ipin_h)
    fclist_h.append(num_otrack_per_opin_h)
    fclist_h.append(spec["connect_flexibility"]["num_ipin_per_opin"])

    num_itrack_per_ipin_l = spec["num_itrack_per_ipin_l"] if (spec["num_itrack_per_ipin_l"] <= 2*track) else 2*track
    num_otrack_per_opin_l = spec["num_otrack_per_opin_l"] if (spec["num_otrack_per_opin_l"] <= 2*track) else 2*track
    fclist_l = []
    fclist_l.append(num_itrack_per_ipin_l)
    fclist_l.append(num_otrack_per_opin_l)
    fclist_l.append(spec["num_ipin_per_opin_l"])

    #op hete peocess
    row = spec["num_row"]
    col = spec["num_colum"]
    maxDelay = spec["max_delay"]
    diag_iopin_connect_h = spec["diag_iopin_connect"]
    diag_iopin_connect_l = spec["diag_iopin_connect_l"]
    GIB = {"gibs":addGIB(row,col,diag_iopin_connect_h,diag_iopin_connect_l,fclist_h,fclist_l)}
    spec.update(**GIB)
    GPE = {"gpes":addGPE(row,col,add,mul,logic,comp,maxDelay)}
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
        elif(restoreResult[0] < opt.y.min()):
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
        # with open('area.txt', 'w') as a: #only for area exploration 1000000
        #     a.write("1000000")
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
        elif(restoreResult[0] < opt.y.min()):
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
    # run_cgra_ppa()
    # pew.txt and area.txt should be extracted here as a result
    opt.observe(rec, obj(rec))

    restoreResult = formResult(spec)[0]
    
    if(i==0):
        y.append(restoreResult[0])
        keyAndSignleValue.append(formResult(spec))
    elif(restoreResult[0] < opt.y.min()):
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
resultKey = opt.y.min()
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

# double security
print('\n <<<<< start optimizing >>>>>')
beforeOpt = allSample[resultKey.astype(np.float)]
optResult = keyAndSignleValue[0][1]
try:
    while(True):
        if(beforeOpt['num_track']!=1):
            beforeOpt['num_track'] = beforeOpt['num_track'] - 1

            with open('cgra_spec_hete.json', 'w') as f:
                json.dump(beforeOpt, f, indent=4)

            subprocess.run('cp cgra_spec_hete.json ../cgra-mg/src/main/resources', shell=True)
                
            run_cgra_mg()
            
            run_cgra_compiler()

            with open('area.txt', 'r') as a:
                area = float(a.read().strip())
            with open('PEWaste.txt', 'r') as p:   
                pew = float(p.read().strip())
            with open('bestLatency.txt', 'r') as l:   
                latency = float(l.read().strip())
            with open('mappingFailureRate.txt', 'r') as m:   
                mappingFailureRate = float(m.read().strip())

            optResult = [area,pew,latency,mappingFailureRate]
        else:
            break

except TypeError:
    print('\nThe optimal architecture is below : ')
    beforeOpt['num_track'] = beforeOpt['num_track'] + 1
    print(beforeOpt)
    print(optResult)

print('\nThe optimal architecture is below : ')
print(beforeOpt)
print(optResult)

print('\n <<<<< design space exploration finished >>>>>')
end_time = time.time()
print('\n Total Time = '+str(end_time-start_time)+'\n')


x = range(1,it+1)
x = [str(y) for y in x]
plt.plot(x, y, color='orangered', marker='o', linestyle='-', label='compo')
plt.legend()  
plt.xlabel("iterations")  
plt.ylabel("evaluation")  
plt.show()

with open('data.txt', 'w') as d:   
    for i in range(it):
        d.write(str(y[i])+'\n')

