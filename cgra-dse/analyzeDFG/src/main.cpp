#include <iostream>
#include <set>
#include <cstdlib>
#include <ctime>
#include <regex>
#include <sstream>
#include <getopt.h>
#include "op/operations.h"
//#include "ir/adg_ir.h"
#include "ir/dfg_ir.h"
#include "spdlog/spdlog.h"
#include "spdlog/cfg/argv.h"
#include <vector>
#include <fstream>
#include <stdexcept>

// split string using regex
std::vector<std::string> split(const std::string& str, const std::string& delim){
    std::regex re{ delim };
    return std::vector<std::string>{
        std::sregex_token_iterator(str.begin(), str.end(), re, -1),
        std::sregex_token_iterator()
    };
}

// remove the prefix path  
std::string fileNameRemovePath(const std::string& filename) {
  size_t lastindex = filename.find_last_of(".");
  std::string res = filename.substr(0, lastindex);

  lastindex = filename.find_last_of("\\/");
  if (lastindex != std::string::npos) {
    res = res.substr(lastindex + 1);
  }
  return res;
}

// get the file directory
std::string fileDir(const std::string& filename) {
  size_t lastindex = filename.find_last_of("\\/");
  if (lastindex == std::string::npos) {
    return std::string("./");
  }
  return filename.substr(0, lastindex);
}

int main(int argc, char* argv[]) {
    // spdlog load log level from argv
    // ./examlpe SPDLOG_LEVEL=info, mylogger=trace
    spdlog::cfg::load_argv_levels(argc, argv);

    static struct option long_options[] = {
        // {"verbose",        no_argument,       nullptr, 'v',},
        {"dump-config",     required_argument, nullptr, 'c',},  // true/false
        {"dump-mapped-viz", required_argument, nullptr, 'm',},  // true/false
        {"obj-opt",         required_argument, nullptr, 'o',},  // true/false
        {"timeout-ms",      required_argument, nullptr, 't',},
        {"max-iters",       required_argument, nullptr, 'i',},
        {"op-file",         required_argument, nullptr, 'p',},
        //{"adg-file",        required_argument, nullptr, 'a',},
        {"dfg-files",       required_argument, nullptr, 'd',},  // can input multiple files, separated by " " or ","
        {0, 0, 0, 0,}
    };
    static char* const short_options = (char *)"c:m:o:t:i:p:a:d:";

    std::string op_fn;  // "resources/ops/operations.json";  // operations file name
    std::string adg_fn; // "resources/adgs/my_cgra_test.json"; // ADG filename
    std::vector<std::string> dfg_fns; // "resources/dfgs/conv3.dot"; // DFG filenames
    int timeout_ms = 3600000;
    int max_iters = 2000;
    bool dumpConfig = true;
    bool dumpMappedViz = true;
    bool objOpt = true;
    std::string resultDir = "";

    int opt;
    while ((opt = getopt_long(argc, argv, short_options, long_options, nullptr)) != -1) {
        switch (opt) {
        //   case 'v': verbose = true; break;
            case 'c': std::istringstream(optarg) >> std::boolalpha >> dumpConfig; break;
            case 'm': std::istringstream(optarg) >> std::boolalpha >> dumpMappedViz; break;
            case 'o': std::istringstream(optarg) >> std::boolalpha >> objOpt; break;
            case 't': timeout_ms = atoi(optarg); break;
            case 'i': max_iters = atoi(optarg); break;
            case 'p': op_fn = optarg; break;
            //case 'a': adg_fn = optarg; break;
            case 'd': dfg_fns = split(optarg, "[\\s,?]+"); break;            
            case '?': std::cout << "Unknown option: " << optopt << std::endl; exit(1);
        }
    }
    if(op_fn.empty()){
        std::cout << "Please input operation file!" << std::endl; 
        exit(1);
    }
    // if(adg_fn.empty()){
    //     std::cout << "Please input ADG file!" << std::endl; 
    //     exit(1);
    // }
    if(dfg_fns.empty()){
        std::cout << "Please input at least one DFG file!" << std::endl; 
        exit(1);
    }

    unsigned seed = time(0); // random seed using current time
    srand(seed);  // set random generator seed 
    std::cout << "Parse Operations: " << op_fn << std::endl;
    Operations::Instance(op_fn);
    // Operations::print();
    
    std::vector<float>storePEusage;
    std::vector<int>bestLatency;
    std::vector<float> storeOptypeAdd;
    std::vector<float> storeOptypeMul;
    std::vector<float> storeOptypeCom;
    std::vector<float> storeOptypeLog;
    std::vector<int> storeDFGNodes;
    
    int numDfg = dfg_fns.size();
    for(auto& dfg_fn : dfg_fns){
        std::cout << "Parse DFG: " << dfg_fn << std::endl;
        DFGIR dfg_ir(dfg_fn);
        OpTypeCount result = dfg_ir.getNumType();
        int total = result.numaddsub+result.numlogic+result.nummul+result.numcomp;
	    std::cout << "Operation Count:\n";
	    std::cout << "ADDandSUB: " << result.numaddsub << ", " << result.numaddsub*100/total << "%\n";
        std::cout << "MUL: " << result.nummul << ", " << result.nummul*100/total << "%\n";
        std::cout << "LOGIC: " << result.numlogic << ", " << result.numlogic*100/total << "%\n";
        std::cout << "COMP:" << result.numcomp << ", " << result.numcomp*100/total << "%\n";
        storeOptypeAdd.push_back(result.numaddsub);
        storeOptypeMul.push_back(result.nummul);
        storeOptypeLog.push_back(result.numlogic);
        storeOptypeCom.push_back(result.numcomp);
        DFG* dfg = dfg_ir.getDFG();
        int numNodes = dfg->nodes().size();
        storeDFGNodes.push_back(numNodes);
        // dfg->print();
        
    }
    
    
    std::cout << "\nSucceed to analyze all the DFGs, number:  " << numDfg << std::endl;
    float avgAdd = std::accumulate(storeOptypeAdd.begin(), storeOptypeAdd.end(), 0.0);
    float avgMul = std::accumulate(storeOptypeMul.begin(), storeOptypeMul.end(), 0.0);
    float avgCom = std::accumulate(storeOptypeCom.begin(), storeOptypeCom.end(), 0.0); 
    float avgLog = std::accumulate(storeOptypeLog.begin(), storeOptypeLog.end(), 0.0);
    float allNumDFGNodes = std::accumulate(storeDFGNodes.begin(), storeDFGNodes.end(), 0);
    float maxDFGNodes = *max_element(storeDFGNodes.begin(),storeDFGNodes.end());
    
    avgAdd = avgAdd/allNumDFGNodes;
    avgMul = avgMul/allNumDFGNodes;
    avgLog = avgLog/allNumDFGNodes;
    avgCom = avgCom/allNumDFGNodes;

    std::ofstream fout("dfgoptype.txt");
    fout << avgAdd << "\n" << avgMul << "\n" << avgLog << "\n" << avgCom;
    fout.close();
    std::ofstream fout1("maxDFGNodes.txt");
    fout1 << maxDFGNodes;
    fout1.close();
    
    std::cout << "avgADDandSUB: " << avgAdd << "\n" <<  "avgMUL: " << avgMul << "\n" ;
    std::cout << "avgLogic: " << avgLog << "\n" << "avgCom: " << avgCom << "\n";
    std::cout << "=============================================\n";
    
    
    return 0;
}
