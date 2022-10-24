#ifndef __LLVM_CDFG_H__
#define __LLVM_CDFG_H__


#include "llvm/Analysis/ScalarEvolution.h"
#include "llvm/Analysis/ScalarEvolutionExpander.h"
#include "llvm/Analysis/ScalarEvolutionExpressions.h"
#include "llvm/Analysis/DependenceAnalysis.h"
#include "llvm/IR/DataLayout.h"
#include "llvm/Transforms/Utils/BasicBlockUtils.h"
#include <queue>
#include <iostream>
#include <fstream>

#include "llvm_cdfg_node.h"
#include "llvm_cdfg_edge.h"

using namespace llvm;

// control dependent nodes of a BB
struct CtrlDeps
{
    LLVMCDFGNode *directCtrlNode = NULL;   // direct control node, not cascading
    LLVMCDFGNode *ctrlNode = NULL;         // control node of this BB (recursively)
    LLVMCDFGNode *trueCtrlingNode = NULL;  // control node of this BB AND true condition node in this BB
    LLVMCDFGNode *falseCtrlingNode = NULL; // control node of this BB AND true condition node in this BB
};


class LLVMCDFG
{
private:
    std::string _name;
    std::map<int, LLVMCDFGNode*> _nodes; // <node-id, node>
    std::map<int, LLVMCDFGEdge*> _edges; // <edge-id, edge>
    std::map<Instruction*, LLVMCDFGNode*> _insNodeMap; // <instruction, node>
    // function annotation: size attribute
    std::map<std::string, int> _sizeAttrMap;
    // basic block pairs that there is a back edge in between, <srcBB, dstBB>
    SmallVector<std::pair<const BasicBlock *, const BasicBlock *>, 1> _backEdgeBBPs;    
    // the recursively successive basic blocks except the back-edge BBs    
    std::map<const BasicBlock *, std::set<const BasicBlock *>> _succBBsMap;
    Loop* _loop = NULL;
	std::set<BasicBlock*> _loopBBs;
	std::set<std::pair<BasicBlock*,BasicBlock*>> _loopentryBBs;
	std::set<std::pair<BasicBlock*,BasicBlock*>> _loopexitBBs;
    // Out of loop control and data node
    // control node : LOOPSTART, LOOPEXIT
    // data node : INPUT, OUTPUT
    std::map<BasicBlock*, LLVMCDFGNode*> _loopStartNodeMap;
    std::map<BasicBlock*, LLVMCDFGNode*> _loopExitNodeMap;
    std::map<Value*, LLVMCDFGNode*> _ioNodeMap;
	// std::map<LLVMCDFGNode*, Value*> _ioNodeMapReverse;
    // GEP node info map including pointer name
    // GEP base address should be provided by the sceduler
    std::map<LLVMCDFGNode*, std::string> _GEPInfoMap;
    // Input/output node info map, inlcudidng variable name
    std::map<LLVMCDFGNode*, std::string> _IOInfoMap;
    // true and false branch condition node of each BB, <true-node, false-node>
    std::map<BasicBlock*, std::pair<LLVMCDFGNode*, LLVMCDFGNode*>> _condNodesOfBBMap;
    // control dependent nodes of each BB
    std::map<BasicBlock*, CtrlDeps> _ctrlNodesOfBBMap;
public:
    DominatorTree *DT;
    DependenceInfo *DI;
    const DataLayout *DL;

    LLVMCDFG(std::string name) : _name(name){}
    ~LLVMCDFG();

	void setName(std::string str){_name = str;}
	std::string name(){return _name;}

	const std::map<int, LLVMCDFGNode*>& nodes(){ return _nodes; }
    LLVMCDFGNode* node(int id);
    LLVMCDFGNode* node(Instruction *ins);
    void addNode(LLVMCDFGNode *node);
    LLVMCDFGNode* addNode(Instruction *ins); // create node according to instruction and add node
    LLVMCDFGNode* addNode(std::string customIns, BasicBlock *BB); // create node according to the custom instruction and add node
    // delete node and corresponding edges
    void delNode(LLVMCDFGNode *node);
    void delNode(Instruction *ins); 

	const std::map<int, LLVMCDFGEdge*>& edges(){ return _edges; }
    LLVMCDFGEdge* edge(int id);
    LLVMCDFGEdge* edge(LLVMCDFGNode *src, LLVMCDFGNode *dst);
    // add edge and corresponding src->outEdge and dst->inEdge
	void addEdge(LLVMCDFGEdge *edge);
    LLVMCDFGEdge* addEdge(LLVMCDFGNode *src, LLVMCDFGNode *dst, EdgeType type);
    // delete edge and corresponding src->outEdge and dst->inEdge
    void delEdge(LLVMCDFGEdge *edge);
    void delEdge(int eid);

    // Loop info
    void setLoop(Loop* loop){ _loop = loop;}
	Loop* loop(){return _loop;}
	void setLoopBBs(std::set<BasicBlock*> BBs){_loopBBs = BBs;}
	void setLoopBBs(std::set<BasicBlock*> BBs, std::set<std::pair<BasicBlock*,BasicBlock*>> entryBBs, std::set<std::pair<BasicBlock*,BasicBlock*>> exitBBs){
        _loopBBs = BBs; 
        _loopentryBBs = entryBBs; 
        _loopexitBBs = exitBBs;
    }
	const std::set<BasicBlock*>& loopBBs(){return _loopBBs;}

    // Basic block relation
    void setSuccBBMap(std::map<const BasicBlock*,std::set<const BasicBlock*>> succBBsMap){_succBBsMap = succBBsMap;}
	const std::map<const BasicBlock*,std::set<const BasicBlock*>>& succBBMap(){return _succBBsMap;}

    const SmallVector<std::pair<const BasicBlock *, const BasicBlock *>, 1>& backEdgeBBPs(){ return _backEdgeBBPs; } 
    void setBackEdgeBBPs(SmallVector<std::pair<const BasicBlock *, const BasicBlock *>, 1> backEdgeBBPs){ _backEdgeBBPs = backEdgeBBPs; }
	
    // GEP node info map including pointer name
    const std::map<LLVMCDFGNode*, std::string>& GEPInfoMap(){ return _GEPInfoMap; }
    std::string GEPInfo(LLVMCDFGNode* node);
    void setGEPInfo(LLVMCDFGNode* node, std::string name);

    // Input/output node info map, inlcudidng variable name
    const std::map<LLVMCDFGNode*, std::string>& IOInfoMap(){ return _IOInfoMap; }
    std::string IOInfo(LLVMCDFGNode* node);
    void setIOInfo(LLVMCDFGNode* node, std::string name);


    // initialize CDFG according to loopBBs
    void initialize();

    // add edge between two nodes that have memory dependence (loop-carried)
    void addMemDepEdges();

    // insert Control NOT node behind the condition node of the Branch node
    // record the true and false condition nodes of each BB in _condNodesOfBBMap
    void insertCtrlNotNodes();

    // root: output node, no children
	std::vector<LLVMCDFGNode*> getRoots();
    // leaf: node with no parents
    std::vector<LLVMCDFGNode*> getLeafs();
	std::vector<LLVMCDFGNode*> getLeafs(BasicBlock* BB);

    // return a map of basicblocks to their direct control dependent CDFG node (only one) with the respective control value
    // based on Dominator tree
    std::map<BasicBlock*, std::pair<LLVMCDFGNode*, CondVal>> getDirectCtrlDepNodeOfBB();
    // get control dependent nodes for the BB by DFS
    void getCtrlNodesDFS(BasicBlock *BB, std::map<BasicBlock*, std::pair<LLVMCDFGNode*, CondVal>> &directCtrlNodeMap, 
                         std::map<BasicBlock*, bool> &visited);
    // get control dependent nodes of each BB: _ctrlNodesOfBBMap
    void getCtrlNodesOfBBMap();
    // get the controlled nodes (conditional execution) in a BB, including StoreInst, OUTPUT
    std::vector<LLVMCDFGNode*> getCtrledNodesInBB(BasicBlock *BB);

    // // get a map of basicblocks to their control dependent (recursive) predecessors with the respective control value
    // std::map<BasicBlock*, std::set<std::pair<BasicBlock*, CondVal>>> getCtrlDepPredBBs();
    // get the control dependent nodes in a BB, including unconditional BranchInst, StoreInst, OutLoopSTORE
    // only TRUE_COND, STORE can be performed
    // std::vector<LLVMCDFGNode*> getCtrlDepNodes(BasicBlock *BB);
    // Connect control dependent node pairs among BBs
    // Conditional Branch predecessor -> control dependent nodes
	void connectCtrlDepBBs();

    

    // transfer the multiple control predecessors (input nodes) into a inverted OR tree 
    // with the root connected to a node and leaves connected to control predecessors
    void createCtrlOrTree();

    // get loop start node. If not exist, create one.
    LLVMCDFGNode* getLoopStartNode(BasicBlock *BB);
    // get loop exit node. If not exist, create one.
    LLVMCDFGNode* getLoopExitNode(BasicBlock *BB);
    // get input node. If not exist, create one.
    LLVMCDFGNode* getInputNode(Value *ins, BasicBlock *BB);
    // get output node. If not exist, create one.
    LLVMCDFGNode* getOutputNode(Value *ins, BasicBlock *BB);

	// Transfer PHI nodes to SELECT nodes
	void handlePHINodes();

    // add mask AND node behind the Shl node with bytewidth less than MAX_DATA_BYTE
    void addMaskAndNodes();

    // get the offset of each element in the struct
    std::map<int, int> getStructElemOffsetMap(StructType *ST);

    // transfer GetElementPtr(GEP) node to MUL/ADD/Const tree
    void handleGEPNodes();

    // add loop exit nodes
    void addLoopExitNodes();

    // remove redundant nodes, e.g. Branch
    void removeRedundantNodes();

    // assign final node name
    void assignFinalNodeName();

	// print DOT file of CDFG
    void printDOT(std::string fileName);

    // generate CDFG
    void generateCDFG();
	
			
};




#endif