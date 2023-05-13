import subprocess
import json

def run_cgra_mg():
    detect1 = subprocess.run('cd ../cgra-mg && ./run.sh', shell=True).returncode
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
    print('  <<<<< design space exploration begin >>>>>')
    subprocess.run('cd analyzeDFG && ./rundfg.sh ', shell=True)
    subprocess.run('cp analyzeDFG/dfgoptype.txt .',shell=True)
    subprocess.run('rm analyzeDFG/dfgoptype.txt',shell=True)

def cgra_mg():
    try:
        run_cgra_mg()
        return True
    except TypeError:
        print("MG ERROR")
        with open('area.txt', 'w') as a:
            a.write("1000000")
        with open('PEWaste.txt', 'w') as p:   
            p.write("1")
        with open('bestLatency.txt', 'w') as l:   
            l.write("20")
        with open('mappingFailureRate.txt', 'w') as m:   
            m.write("1")
        return False

def cgra_compiler():
    try:
        run_cgra_compiler()
        return True
    except TypeError:
        print("MAPPING ERROR")
        with open('PEWaste.txt', 'w') as p:   
            p.write("1")
        with open('bestLatency.txt', 'w') as l:   
            l.write("20")
        with open('mappingFailureRate.txt', 'w') as m:   
            m.write("1")
        return False

def dumpArchSpec(spec:dict):
    with open('cgra_spec_hete.json', 'w') as f:
        json.dump(spec, f, indent=4)
    subprocess.run('cp cgra_spec_hete.json ../cgra-mg/src/main/resources', shell=True)

def cgra_analyze():
    run_cgra_analyze()
    result = []
    with open('dfgoptype.txt','r') as f:
        for line in f:
            result.append(list(line.strip('\n').split(',')))    
    return result
