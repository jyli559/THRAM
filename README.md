THRAM Framework
=======================

Template-based Reconfigurable Architecture Modeling Framework, including:

1. CGRA-MG: CGRA modeling and generation based on Chisel. Design a flexible CGRA template, and generate architecture IR and Verilog. 

2. CGRA-Compiler: CGRA mapper, mapping DFGs to CGRA in batches. The mapping flow includes placement and routing, data synchronization, optimization, visualization, and configuration generation.

3. Bechmarks: DFGs in Json format derived from dot files.

4. CGRA-DSE: CGRA design space exploration based on Bayesian Optimization


## Getting Started


### Dependencies

##### JDK 8 or newer (for CGRA-MG)

##### SBT (for CGRA-MG)

##### CMake  (for CGRA-Compiler)

##### C++-11 (for CGRA-Compiler)



### CGRA-MG

#### Build and run

Using the script run.sh
```sh
cd cgra-mg
./run.sh
```

Or using sbt command:
```sh
cd cgra-mg
sbt "runMain mg.CGRAMG -td ./test_run_dir"
```


### CGRA-Compiler

#### Build

Using the script build.sh
```sh
cd cgra-compiler
./build.sh
```

#### Run

Using the script run.sh
```sh
./run.sh
```

Change the benchmark file path as you need.
The generated result files are in the same directory as the benchmark.

### CGRA-DSE
Using the script dse.py
```python
python3 dse.py
```
Automatic DSE flow including benchmark analyzing, modeling and compiling , change the benchmarks as you need. Or implement the process step by step.

