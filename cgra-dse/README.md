# DSE flow

## benchmark selection
Modify the run.sh and rundfg.sh in cgra-compiler/ to run your own benchmark


## choose arch description
Modify the CGRAMG.scala in cgra-mg/src/main/scala/mg  to choose arc description(homo or hete or other)


## set parameter of design space and DSE style
Modify your own dse parameters and dse style in the python script 


## run dse
```sh
python3 dse_hete.py
```