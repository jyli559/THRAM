
#include "llvm_cdfg.h"


LLVMCDFG::~LLVMCDFG()
{
    for(auto& elem : _nodes){
        delete elem.second;
    }
    for(auto& elem : _edges){
        delete elem.second;
    }
}


LLVMCDFGNode* LLVMCDFG::node(int id)
{
    if(_nodes.count(id)){
        return _nodes[id];
    }
    return NULL;
}

LLVMCDFGNode* LLVMCDFG::node(Instruction *ins)
{
    if(_insNodeMap.count(ins)){
        return _insNodeMap[ins];
    }
    return NULL;
}


void LLVMCDFG::addNode(LLVMCDFGNode *node)
{
    int id = node->id();
    if(_nodes.count(id)){
        return;
    }
    _nodes[id] = node;
    if(auto ins = node->instruction()){
        _insNodeMap[ins] = node;
    }
}

// create node according to instruction and add node
LLVMCDFGNode* LLVMCDFG::addNode(Instruction *ins)
{
    if(_insNodeMap.count(ins)){
        return _insNodeMap[ins];
    }
    // create new node
    LLVMCDFGNode *node = new LLVMCDFGNode(ins, this);
    int id = 0;
    if(!_nodes.empty()){
        id = _nodes.rbegin()->first + 1;
    }
    node->setId(id);
    node->setBB(ins->getParent());
    _nodes[id] = node;
    _insNodeMap[ins] = node;
    return node;
}

// create node according to the custom instruction and add node
LLVMCDFGNode* LLVMCDFG::addNode(std::string customIns, BasicBlock *BB)
{
    LLVMCDFGNode *node = new LLVMCDFGNode(this);
    node->setCustomInstruction(customIns);
    int id = 0;
    if(!_nodes.empty()){
        id = _nodes.rbegin()->first + 1;
    }
    node->setId(id);
    node->setBB(BB);
    _nodes[id] = node;    
    return node;
}


void LLVMCDFG::delNode(LLVMCDFGNode *node)
{
    int id = node->id();
    _nodes.erase(id);
    if(auto ins = node->instruction()){
        _insNodeMap.erase(ins);
    }
    auto inputEdges = node->inputEdges();
    for(int eid : inputEdges){
        delEdge(eid);
    }
    auto outputEdges = node->outputEdges();
    for(int eid : outputEdges){
        delEdge(eid);
    }
    delete node;
}


void LLVMCDFG::delNode(Instruction *ins)
{
    if(!_insNodeMap.count(ins)){
        return;
    }
    auto node = _insNodeMap[ins];
    _nodes.erase(node->id());
    _insNodeMap.erase(ins);
    auto inputEdges = node->inputEdges();
    for(int eid : inputEdges){
        delEdge(eid);
    }
    auto outputEdges = node->outputEdges();
    for(int eid : outputEdges){
        delEdge(eid);
    }
    delete node;
}


LLVMCDFGEdge* LLVMCDFG::edge(int id)
{
    if(_edges.count(id)){
        return _edges[id];
    }
    return NULL;
}


LLVMCDFGEdge* LLVMCDFG::edge(LLVMCDFGNode *src, LLVMCDFGNode *dst)
{
    for(auto eid : src->outputEdges()){
        assert(_edges.count(eid));
        auto outEdge = _edges[eid];
        if(outEdge->dst() == dst){
            return outEdge;
        }
    }
    return NULL;
}


void LLVMCDFG::addEdge(LLVMCDFGEdge *edge)
{
    int id = edge->id();
    if(!_edges.count(id)){
        _edges[id] = edge;
        edge->src()->addOutputEdge(id);
        edge->dst()->addInputEdge(id);
    }
}


LLVMCDFGEdge* LLVMCDFG::addEdge(LLVMCDFGNode *src, LLVMCDFGNode *dst, EdgeType type)
{
    int eid = 0;
    if(!_edges.empty()){
        eid = _edges.rbegin()->first + 1;
    }
    LLVMCDFGEdge *edge = new LLVMCDFGEdge(eid, type, src, dst);
    _edges[eid] = edge;
    src->addOutputEdge(eid);
    dst->addInputEdge(eid);
    return edge;
}



void LLVMCDFG::delEdge(LLVMCDFGEdge *edge)
{
    int id = edge->id();
    if(_edges.count(id)){
        _edges.erase(id);
    }
    edge->src()->delOutputEdge(id);
    edge->dst()->delInputEdge(id);
    delete edge;    
}


void LLVMCDFG::delEdge(int id)
{
    if(!_edges.count(id)){
       return;
    }
    auto edge = _edges[id];
    edge->src()->delOutputEdge(id);
    edge->dst()->delInputEdge(id);
    _edges.erase(id);
    delete edge;    
}


// get GEP node info 
std::string LLVMCDFG::GEPInfo(LLVMCDFGNode* node)
{
    assert(_GEPInfoMap.count(node));
    return _GEPInfoMap[node];
}


void LLVMCDFG::setGEPInfo(LLVMCDFGNode* node, std::string name)
{
    _GEPInfoMap[node] = name;
}


// get Input/Output node info 
std::string LLVMCDFG::IOInfo(LLVMCDFGNode* node)
{
    assert(_IOInfoMap.count(node));
    return _IOInfoMap[node];
}


void LLVMCDFG::setIOInfo(LLVMCDFGNode* node, std::string name)
{
    _IOInfoMap[node] = name;
}


// initialize CDFG according to loopBBs
void LLVMCDFG::initialize()
{
    // Create CDFG nodes
    for(auto BB : _loopBBs){
        for(auto &I : *BB){
            addNode(&I);
        }
    }
    // create connections
    for(auto BB : _loopBBs){
        for(auto &I : *BB){
            Instruction *ins = &I;
            LLVMCDFGNode *node = this->node(ins);            
            // find out-of-loop connections or constant operands for non-phi nodes
            if(!dyn_cast<PHINode>(ins)){
                int idx = 0;
                for(Use &pred : ins->operands()){
                    // add input nodes
                    LLVMCDFGNode *inputNode = NULL;
                    if(ConstantInt *CI = dyn_cast<ConstantInt>(pred)){
                        if(dyn_cast<GetElementPtrInst>(ins)){ // GEP Constant will be handled in the handleGEPNodes
                            idx++;
                            continue;
                        }
                        inputNode = addNode("CONST", node->BB());
                        inputNode->setConstVal(CI->getSExtValue());
                    }else if(Instruction *predIns = dyn_cast<Instruction>(pred)){
                        if(!_loopBBs.count(predIns->getParent())){ // out of loop BB
                            inputNode = getInputNode(predIns, BB);
                        }
                    }else if(Argument *arg = dyn_cast<Argument>(pred)){
                        if(!pred->getType()->isPointerTy()){
                            inputNode = getInputNode(arg, BB);
                        }
                    }
                    EdgeType type = EDGE_TYPE_DATA;
                    if(pred->getType()->getPrimitiveSizeInBits() == 1){ //  single-bit operand
                        type = EDGE_TYPE_CTRL;
                    }    
                    if(inputNode){
                        // reorder the operand of SELECT and STORE node
                        if(auto SI = dyn_cast<SelectInst>(ins)){
                            if(dyn_cast<Value>(pred) == SI->getCondition()){
                                idx = 2;
                            }else if(dyn_cast<Value>(pred) == SI->getTrueValue()){
                                idx = 0;
                            }else if(dyn_cast<Value>(pred) == SI->getFalseValue()){
                                idx = 1;
                            }else{
                                assert(false);
                            }
                        }else if(auto SI = dyn_cast<StoreInst>(ins)){
                            if(dyn_cast<Value>(pred) == SI->getValueOperand()){
                                idx = 1;
                            }else{
                                idx = 0;
                            }
                        }
                        node->addInputNode(inputNode, idx);
                        inputNode->addOutputNode(node);
                        addEdge(inputNode, node, type);
                    }
                    idx++;
                }
            }
            for(User *succ : ins->users()){                
                if(Instruction *succIns = dyn_cast<Instruction>(succ)){
                    LLVMCDFGNode *succNode = NULL;
                    bool isBackEdge = false;
                    if(!_loopBBs.count(succIns->getParent())){ // out of loop BB
                        succNode = getOutputNode(succIns, BB);
                    }else if(dyn_cast<PHINode>(succIns)){
                        continue; // not connected here, instead in handlePHINodes
                    }else{
                        succNode = this->node(succIns);
                        // // only if the successor is PHINode, the back edge can exist.
                        // // the following condition should never be true
                        // if(BB != succIns->getParent()){ // not in the same BB
                        //     std::pair<const BasicBlock*, const BasicBlock*> bbp(BB, succIns->getParent());
                        //     if(std::find(_backEdgeBBPs.begin(), _backEdgeBBPs.end(), bbp) != _backEdgeBBPs.end()){
                        //         isBackEdge = true;
                        //     }
                        // }
                    }
                    // get the input index
                    int idx = -1;
                    // reorder the operand of SELECT and STORE node
                    if(auto SI = dyn_cast<SelectInst>(succIns)){
                        if(ins == dyn_cast<Instruction>(SI->getCondition())){
                            idx = 2;
                        }else if(ins == dyn_cast<Instruction>(SI->getTrueValue())){
                            idx = 0;
                        }else if(ins == dyn_cast<Instruction>(SI->getFalseValue())){
                            idx = 1;
                        }else{
                            assert(false);
                        }
                    }else if(auto SI = dyn_cast<StoreInst>(succIns)){
                        if(ins == dyn_cast<Instruction>(SI->getValueOperand())){
                            idx = 1;
                        }else{
                            idx = 0;
                        }
                    }else{
                        for(int i = 0; i < succIns->getNumOperands(); i++){
                            if(ins == dyn_cast<Instruction>(succIns->getOperand(i))){
                                idx = i;
                                break;
                            }
                        }
                    }   
                    EdgeType type = EDGE_TYPE_DATA;
                    if(ins->getType()->getPrimitiveSizeInBits() == 1){ //  single-bit operand
                        type = EDGE_TYPE_CTRL;
                    }                 
                    node->addOutputNode(succNode, isBackEdge);
                    succNode->addInputNode(node, idx, isBackEdge);
                    addEdge(node, succNode, type);
                }
            }
        }
    }  
}



// add edge between two nodes that have memory dependence (loop-carried)
void LLVMCDFG::addMemDepEdges()
{
    std::vector<LLVMCDFGNode *> LSNodes; // load/store nodes
    // find the load/store nodes
    for(auto &elem : _nodes){
        auto node = elem.second;
        Instruction *ins = node->instruction();
        if(ins == NULL){
            continue;
        }
        if(LoadInst *LI = dyn_cast<LoadInst>(ins)){
            if(LI->isSimple()){
                LSNodes.push_back(node);
            }
        }else if(StoreInst *SI = dyn_cast<StoreInst>(ins)){
            if(SI->isSimple()){
                LSNodes.push_back(node);
            }
        }
    }
    // analyze dependence between every two LSNodes
    int N = LSNodes.size();
    for(int i = 0; i < N; i++){
        LLVMCDFGNode *srcNode = LSNodes[i];
        Instruction *srcIns = srcNode->instruction();
        for(int j = i + 1; j < N; j++){
            LLVMCDFGNode *dstNode = LSNodes[j];
            Instruction *dstIns = dstNode->instruction();
            if(auto D = DI->depends(srcIns, dstIns, true)){
                outs() << "Found memory dependence between " << LSNodes[i]->getName() 
                       << "(src) and " << LSNodes[j]->getName() << "(dst)\n";
                if(D->isLoopIndependent()){
                    outs() << "Loop independent(skipped)\n";
                    continue;
                }
                outs() << "Loop carried dependence\n";
                DepType type = NON_DEP; // dependence type
                if(D->isFlow()){ // RAW, read after write
                    type = FLOW_DEP;
                    outs() << "FLOW_DEP, ";
                }else if(D->isAnti()){ // WAR, write after read
                    type = ANTI_DEP;
                    outs() << "ANTI_DEP, ";
                }else if(D->isOutput()){ // WAW
                    type = OUTPUT_DEP;
                    outs() << "OUTPUT_DEP, ";
                }else if(D->isInput()){ // RAR
                    type = INPUT_DEP;
                    outs() << "INPUT_DEP, ";
                }               
                int loopIterDist; // loop-carried iteration distance, e.g. a[i+1] = a[i] : 1
                bool isLoopDistConst = 0;
                int nestedLevels = D->getLevels(); // nested loop levels, [1, nestedLevels], 1 is the outer-most loop
                assert(nestedLevels > 0);
                // target at the inner-most loop
                const SCEV *dist = D->getDistance(nestedLevels);
                const SCEVConstant *distConst = dyn_cast_or_null<SCEVConstant>(dist);
                bool reverse = false;
                if(distConst){
                    loopIterDist = distConst->getAPInt().getSExtValue();
                    outs() << "const distance: " << loopIterDist << "\n";
                    isLoopDistConst = true;
                    if(loopIterDist < 0){
                        reverse = true;
                        loopIterDist = -loopIterDist;
                        if(type == FLOW_DEP){
                            type = ANTI_DEP;
                        }else if(type == ANTI_DEP){
                            type = FLOW_DEP;
                        }
                    }                   
                }else{ /// if no subscript in the source or destination mention the induction variable associated with the loop at this level.
                    isLoopDistConst = false;   
                    outs() << "non-const distance\n";                               
                }                
                // add mem dep edges
                DependInfo dep;
                dep.type = type;
                dep.isConstDist = isLoopDistConst;
                dep.distance = loopIterDist;
                if(reverse){
                    dstNode->addDstDep(srcNode, dep);
                    srcNode->addSrcDep(dstNode, dep);
                    addEdge(dstNode, srcNode, EDGE_TYPE_MEM);
                }else{
                    srcNode->addDstDep(dstNode, dep);
                    dstNode->addSrcDep(srcNode, dep);
                    addEdge(srcNode, dstNode, EDGE_TYPE_MEM);
                }                
            }
        }
    }
}


// root nodes : no output nodes
std::vector<LLVMCDFGNode *> LLVMCDFG::getRoots()
{
	std::vector<LLVMCDFGNode *> rootNodes;
    for(auto &elem : _nodes){
        if(elem.second->outputNodes().size() == 0){
            rootNodes.push_back(elem.second);
        }
    }
	return rootNodes;
}

// leaf nodes : no input nodes
std::vector<LLVMCDFGNode *> LLVMCDFG::getLeafs()
{
	std::vector<LLVMCDFGNode *> leafNodes;
    for(auto &elem : _nodes){
        if(elem.second->inputNodes().size() == 0){
            leafNodes.push_back(elem.second);
        }
    }
	return leafNodes;
}

// leaf nodes in a BB : no input nodes in this BB or is INPUT/PHI
std::vector<LLVMCDFGNode *> LLVMCDFG::getLeafs(BasicBlock *BB)
{
	std::vector<LLVMCDFGNode *> leafNodes;
    for(auto &elem : _nodes){
        auto node = elem.second;
        if(node->BB() != BB || node->customInstruction() == "INPUT"){
            continue;
        }
        if(node->instruction() && dyn_cast<PHINode>(node->instruction())){
            continue;
        }
        bool flag = true;
        for(auto &inNode : node->inputNodes()){
            if(inNode->BB() == BB && inNode->customInstruction() != "INPUT"){
                if(inNode->instruction() == NULL || !dyn_cast<PHINode>(inNode->instruction())){
                    flag = false;
                    break;
                }
            }
        }
        if(flag){
            leafNodes.push_back(node);
        }
    }
	return leafNodes;
}


// insert Control NOT node behind the condition node of the Branch node
// record the true and false condition nodes of each BB in _condNodesOfBBMap
void LLVMCDFG::insertCtrlNotNodes()
{
    outs() << "insertCtrlNotNodes STARTED!\n";
    for(auto BB : _loopBBs){       
        BranchInst* BRI = cast<BranchInst>(BB->getTerminator());
        if(!BRI->isConditional()){
            continue;
        }
        Instruction *condIns = dyn_cast<Instruction>(BRI->getCondition()); // conditional predecessor
        LLVMCDFGNode *node = this->node(condIns);  
        outs() << "insert CTRLNOT node behind " << node->getName() << ", ";
        // create CTRLNOT node
        LLVMCDFGNode* notNode = addNode("CTRLNOT", node->BB());
		outs() << "newNOTNode = " << notNode->getName() << "\n";  
        _condNodesOfBBMap[BB] = std::make_pair(node, notNode);
        std::set<LLVMCDFGNode*> falseOutNodes;                
        for(auto outNode : node->outputNodes()){
            if(node->getOutputCondVal(outNode) == FALSE_COND){
                falseOutNodes.insert(outNode);
            }
        }
        for(auto outNode : falseOutNodes){
            bool isBackEdge = node->isOutputBackEdge(outNode); //  should be false
            // delete old connections
            node->delOutputNode(outNode);
            int idx = outNode->delInputNode(node);
            // add new connections           
            notNode->addOutputNode(outNode, isBackEdge, TRUE_COND);
            outNode->addInputNode(notNode, idx, isBackEdge, TRUE_COND);
            addEdge(notNode, outNode, EDGE_TYPE_CTRL);            
        }
        // delete old edges
        auto outEdges = node->outputEdges();
        for(auto eid : outEdges){
            auto outEdge = edge(eid);
            auto dstNode = outEdge->dst();
            if(falseOutNodes.count(dstNode)){
                delEdge(outEdge);
            }
        }
        node->addOutputNode(notNode, false, FALSE_COND);
        notNode->addInputNode(node, 0, false, FALSE_COND);
        addEdge(node, notNode, EDGE_TYPE_CTRL);
    }
    outs() << "insertCtrlNotNodes ENDED!\n";
}



// return a map of basicblocks to their direct control dependent CDFG node (only one) with the respective control value
// based on Dominator tree
std::map<BasicBlock*, std::pair<LLVMCDFGNode*, CondVal>> LLVMCDFG::getDirectCtrlDepNodeOfBB() 
{
    std::map<BasicBlock*, std::pair<LLVMCDFGNode*, CondVal>> res;
    LLVMCDFGNode *ctrlNode;
    // find control nodes for loop header
    BasicBlock *header = _loop->getHeader(); 
    // control node for header from preheader and backedge (each with only one due to loop-simplify)
    BasicBlock *preheader;
    BasicBlock *backEdgeBB;
    bool flag = _loop->getIncomingAndBackEdge(preheader, backEdgeBB);
    assert(flag);
    LLVMCDFGNode *headerCtrlNode = addNode("CTRLOR", header); 
    LLVMCDFGNode *ctrlNode1 = getLoopStartNode(preheader);            
    LLVMCDFGNode *ctrlNode2;
    BranchInst *BRI = dyn_cast<BranchInst>(backEdgeBB->getTerminator());
    assert(BRI->isConditional());
    for (int i = 0; i < BRI->getNumSuccessors(); ++i) {
		if(header == BRI->getSuccessor(i)){ 
            if(i == 0){ // true condition
                ctrlNode2 = _condNodesOfBBMap[backEdgeBB].first;
            }else{ // false condition
                ctrlNode2 = _condNodesOfBBMap[backEdgeBB].second;
            }
            break;
		}
	}
    headerCtrlNode->addInputNode(ctrlNode1, 0, false);
    headerCtrlNode->addInputNode(ctrlNode2, 1, true);
    ctrlNode1->addOutputNode(headerCtrlNode, false);
    ctrlNode2->addOutputNode(headerCtrlNode, true);
    addEdge(ctrlNode1, headerCtrlNode, EDGE_TYPE_CTRL);
    addEdge(ctrlNode2, headerCtrlNode, EDGE_TYPE_CTRL);
    res[header] = std::make_pair(headerCtrlNode, UNCOND);
    outs() << "Direct control node of " << header->getName() << " is " << headerCtrlNode->getName() << ", 0\n";
    // find control nodes for other loop BB except header
	for(BasicBlock *BB : _loop->getBlocks()){
        if(BB == header){
            continue;
        }else{ // find conditional dominator
            bool success = false;
            BasicBlock *curBB = BB;
            while(!success){
                BasicBlock *idomBB = DT->getNode(curBB)->getIDom()->getBlock(); // immediate dominator BB
                Instruction *BR = idomBB->getTerminator();
                BranchInst *BRI = dyn_cast<BranchInst>(BR);
                CondVal cv;
                int numPaths = 0; // number of conditional path from idomBB to BB
                if(BRI->isConditional()){
                    for (int i = 0; i < BRI->getNumSuccessors(); ++i) {
                        BasicBlock *succBB = BRI->getSuccessor(i);
		        		if(_succBBsMap[succBB].count(BB)){ // idomBB -> succBB -> BB (succBB may be BB)
                            cv = (i==0)? TRUE_COND : FALSE_COND;
                            numPaths++;
		        		}
		        	}
                }
                if(numPaths == 1){ // found one conditional path
                    success = true;
                    ctrlNode = (cv == TRUE_COND)? _condNodesOfBBMap[idomBB].first : _condNodesOfBBMap[idomBB].second;
                    res[BB] = std::make_pair(ctrlNode, cv);
                }else if(idomBB == header){
                    success = true;
                    res[BB] = std::make_pair(headerCtrlNode, UNCOND);
                }else{
                    curBB = idomBB;
                }
            }
            outs() << "Direct control node of " << curBB->getName() << " is " << res[BB].first->getName() << ", " << res[BB].second << "\n";
        }       
    }
    return res;
}


// get control dependent nodes for the BB by DFS
void LLVMCDFG::getCtrlNodesDFS(BasicBlock *currBB, std::map<BasicBlock*, std::pair<LLVMCDFGNode*, CondVal>> &directCtrlNodeMap, 
        std::map<BasicBlock*, bool> &visited)
{
    std::pair<LLVMCDFGNode*, CondVal> directCtrlNodeCV = directCtrlNodeMap[currBB];
    LLVMCDFGNode *directCtrlNode = directCtrlNodeCV.first; 
    CondVal cv = directCtrlNodeCV.second;
    BasicBlock *ctrlBB = directCtrlNode->BB();
    BranchInst *currBRI = dyn_cast<BranchInst>(currBB->getTerminator());
    _ctrlNodesOfBBMap[currBB].directCtrlNode = directCtrlNode;
    if(currBB == _loop->getHeader()){
        visited[currBB] = true;            
        _ctrlNodesOfBBMap[currBB].ctrlNode = directCtrlNode;                
    }else{
        if(visited.count(ctrlBB) && visited[ctrlBB]){ // _ctrlNodesOfBBMap[ctrlBB] already got
            visited[currBB] = true;
        }else{
            getCtrlNodesDFS(ctrlBB, directCtrlNodeMap, visited);
        }
        if(cv == UNCOND){
            _ctrlNodesOfBBMap[currBB].ctrlNode = _ctrlNodesOfBBMap[ctrlBB].ctrlNode;
        }else if(cv == TRUE_COND){
            _ctrlNodesOfBBMap[currBB].ctrlNode = _ctrlNodesOfBBMap[ctrlBB].trueCtrlingNode;
        }else{
            _ctrlNodesOfBBMap[currBB].ctrlNode = _ctrlNodesOfBBMap[ctrlBB].falseCtrlingNode;
        }
    }
    if(currBRI->isConditional()){
        LLVMCDFGNode *ctrlNode = _ctrlNodesOfBBMap[currBB].ctrlNode;
        // set trueCtrlingNode
        LLVMCDFGNode *trueAndNode = addNode("CTRLAND", currBB);
        LLVMCDFGNode *trueNode = _condNodesOfBBMap[currBB].first;
        trueAndNode->addInputNode(ctrlNode, 0);
        trueAndNode->addInputNode(trueNode, 1);
        ctrlNode->addOutputNode(trueAndNode);
        trueNode->addOutputNode(trueAndNode);
        addEdge(ctrlNode, trueAndNode, EDGE_TYPE_CTRL);
        addEdge(trueNode, trueAndNode, EDGE_TYPE_CTRL);
        _ctrlNodesOfBBMap[currBB].trueCtrlingNode = trueAndNode;
        // set falseCtrlingNode
        LLVMCDFGNode *falseAndNode = addNode("CTRLAND", currBB);
        LLVMCDFGNode *falseNode = _condNodesOfBBMap[currBB].second;
        falseAndNode->addInputNode(ctrlNode, 0);
        falseAndNode->addInputNode(falseNode, 1);
        ctrlNode->addOutputNode(falseAndNode);
        falseNode->addOutputNode(falseAndNode);
        addEdge(ctrlNode, falseAndNode, EDGE_TYPE_CTRL);
        addEdge(falseNode, falseAndNode, EDGE_TYPE_CTRL);
        _ctrlNodesOfBBMap[currBB].falseCtrlingNode = falseAndNode;
    }        
}


// get control dependent nodes of each BB: _ctrlNodesOfBBMap
void LLVMCDFG::getCtrlNodesOfBBMap() 
{
    // get real control dependent CDFG node (only one) with the respective control value
    std::map<BasicBlock*, std::pair<LLVMCDFGNode*, CondVal>> directCtrlNodeMap = getDirectCtrlDepNodeOfBB();
    std::map<BasicBlock*, bool> visited;
    for(auto &elem : directCtrlNodeMap){
        BasicBlock *currBB = elem.first;
        if(visited.count(currBB) && visited[currBB]){ // _ctrlNodesOfBBMap[ctrlBB] already got
            continue;
        }
        getCtrlNodesDFS(currBB, directCtrlNodeMap, visited);        
    }
}

// // return a map of basicblocks to their real control dependent (recursive) predecessors with the respective control value
// std::map<BasicBlock*, std::set<std::pair<BasicBlock*, CondVal>>> LLVMCDFG::getCtrlDepPredBBs() {
// 	std::map<BasicBlock*,std::set<std::pair<BasicBlock*,CondVal>>> res;
//     // BFS to find all the recursive predecessors except the out-of-loop and back-edge ones for each BB
// 	for(BasicBlock* BB : _loopBBs){
// 		std::queue<BasicBlock*> q;
// 		q.push(BB);
// 		std::map<BasicBlock*,std::set<CondVal>> visited;
// 		while(!q.empty()){
// 			BasicBlock* curr = q.front(); q.pop();
// 			for (auto it = pred_begin(curr); it != pred_end(curr); ++it){
// 				BasicBlock* predecessor = *it;
// 				if(_loopBBs.find(predecessor) == _loopBBs.end()){
// 					continue; // no need to care for out of loop BBs.
// 				}
// 				std::pair<const BasicBlock*,const BasicBlock*> bbPair = std::make_pair(predecessor, curr);
// 				if(std::find(_backEdgeBBPs.begin(), _backEdgeBBPs.end(), bbPair) != _backEdgeBBPs.end()){
// 					continue; // no need to traverse backedges;
// 				}
// 				CondVal cv;
// 				assert(predecessor->getTerminator());
// 				BranchInst* BRI = cast<BranchInst>(predecessor->getTerminator());
//                 // get control value
// 				if(!BRI->isConditional()){
// 					cv = UNCOND;
// 				}else{
// 					for (int i = 0; i < BRI->getNumSuccessors(); ++i) {
// 						if(BRI->getSuccessor(i) == curr){
// 							if(i==0){
// 								cv = TRUE_COND;
// 							}else if(i==1){
// 								cv = FALSE_COND;
// 							}else{
// 								assert(false);
// 							}
// 						}
// 					}
// 				}
// 				visited[predecessor].insert(cv);
// 				q.push(predecessor);
// 			}
// 		}

// 		outs() << "BasicBlock : " << BB->getName() << " :: CtrlDependentBBs = ";
// 		for(std::pair<BasicBlock*,std::set<CondVal>> pair : visited){
// 			BasicBlock* bb = pair.first;
// 			std::set<CondVal> brOuts = pair.second;
// 			outs() << bb->getName();
// 			if(brOuts.count(TRUE_COND)){
// 				res[BB].insert(std::make_pair(bb, TRUE_COND)); // TRUE control dependent predecessor BB
// 				outs() << "(TRUE),";
// 			}
// 			if(brOuts.count(FALSE_COND)){
// 				res[BB].insert(std::make_pair(bb, FALSE_COND)); // FALSE control dependent predecessor BB
// 				outs() << "(FALSE),";
// 			}
// 		}
// 		outs() << "\n";
// 	} // res[BB] = set<preBB, TRUE/FALSE_COND>

//     // remove extra <preBB, TRUE/FALSE_COND>
// 	std::map<BasicBlock*, std::set<std::pair<BasicBlock*, CondVal>>> refinedRes;
// 	for(auto &pair : res){
// 		std::set<std::pair<BasicBlock*,CondVal>> tobeRemoved;
// 		BasicBlock* currBB = pair.first;
// 		outs() << "BasicBlock : " << currBB->getName() << " :: RefinedCtrlDependentBBs = ";
// 		for(auto &bbVal : pair.second){
// 			BasicBlock* depBB = bbVal.first;
// 			for(auto &p2 : res[depBB]){
// 				tobeRemoved.insert(p2);
// 			}
// 		}
//         // if currBB and depBB have the same <preBB, TRUE/FALSE_COND>, remove from res[BB]
// 		for(auto &bbVal : pair.second){
// 			if(tobeRemoved.find(bbVal) == tobeRemoved.end()){
// 				outs() << bbVal.first->getName();
// 				outs() << ((bbVal.second == TRUE_COND)? "(TRUE)," : "(FALSE),");
// 				refinedRes[currBB].insert(bbVal);
// 			}
// 		}
// 		outs() << "\n";
// 	}

//     // remove preBB with both TRUE_COND and FALSE_COND from refinedRes
// 	std::map<BasicBlock*,std::set<std::pair<BasicBlock*,CondVal>>> finalRes;
//     for(auto &pair : refinedRes){
// 		BasicBlock* currBB = pair.first;
// 		outs() << "BasicBlock : " << currBB->getName() << " :: FinalCtrlDependentBBs = ";
// 		std::set<std::pair<BasicBlock*, CondVal>> bbValPairs = pair.second; // auto-sorted, first prority : BasicBlock*, second : CondVal
//         assert(bbValPairs.size() > 0);
//         bool changed = true;
//         while(changed){
//             changed = false;
//             for(auto it = bbValPairs.begin(), ie = --bbValPairs.end(); it != ie;){
//                 auto bb1 = it->first;
//                 auto old_it = it;
//                 auto next_it = ++it;
//                 if(bb1 == next_it->first){
//                     bbValPairs.erase(old_it, ++next_it); // remove TRUE_COND and FALSE_COND preBBs
//                     if(finalRes.count(bb1)){ // already got the final control dependent BBs
//                         for(auto bbp : finalRes[bb1]){
//                             bbValPairs.insert(bbp);
//                         }
//                     }else if(refinedRes.count(bb1)){ // add control dependent BBs from refinedRes[bb1]
//                         for(auto bbp : refinedRes[bb1]){
//                             bbValPairs.insert(bbp);
//                         }
//                     }
//                     changed = (bbValPairs.size() > 0); // if still have element, continue
//                     break;
//                 }
//             }
//         }
//         if(bbValPairs.size() > 0){
//             finalRes[currBB] = bbValPairs;
//             for(auto &bbVal: bbValPairs){
// 			    outs() << bbVal.first->getName();
// 			    outs() << ((bbVal.second == TRUE_COND)? "(TRUE)," : "(FALSE),");
// 		    }
//         }
//         outs() << "\n";
//     }
// 	return finalRes;
// }


// get the controlled nodes (conditional execution) in a BB, including StoreInst, OUTPUT
std::vector<LLVMCDFGNode*> LLVMCDFG::getCtrledNodesInBB(BasicBlock *BB)
{
    std::vector<LLVMCDFGNode*> res;
    for(auto &elem : _nodes){
        auto node = elem.second;
        if(node->BB() != BB){
            continue;
        }
        if(Instruction *ins = node->instruction()){
            if(dyn_cast<StoreInst>(ins)){
                res.push_back(node);
            }
        }else if(node->customInstruction() == "OUTPUT"){
            res.push_back(node);
        }
    }
    return res;
}


// Connect control dependent node pairs among BBs
void LLVMCDFG::connectCtrlDepBBs(){
    // get control dependent nodes of each BB: _ctrlNodesOfBBMap
    getCtrlNodesOfBBMap();
    for(auto &elem : _ctrlNodesOfBBMap){
        BasicBlock* currBB = elem.first;
        LLVMCDFGNode* ctrlNode = elem.second.ctrlNode; 
        outs() << currBB->getName() << " :: " << "directCtrlNode:" << elem.second.directCtrlNode->getName()
               << ", ctrlNode: " << ctrlNode->getName();
        if(elem.second.trueCtrlingNode){
            outs() << ", trueCtrlingNode: " << elem.second.trueCtrlingNode->getName()
                   << ", falseCtrlingNode: " << elem.second.falseCtrlingNode->getName();
        }
        outs() << "\n";      
        // get the controlled nodes (conditional execution) in this BB
        std::vector<LLVMCDFGNode*> ctrledNodes = getCtrledNodesInBB(currBB);
		outs() << "ConnectBB :: From " << ctrlNode->getName() << "(srcBB = " << ctrlNode->BB()->getName() << ")" << ", To ";
		for(LLVMCDFGNode* ctrledNode : ctrledNodes){
			outs() << ctrledNode->getName() << ", ";
            ctrlNode->addOutputNode(ctrledNode);
            ctrledNode->addInputNode(ctrlNode, -1); // donot care the index
            addEdge(ctrlNode, ctrledNode, EDGE_TYPE_CTRL);
		}
		outs() << "(destBB = " << currBB->getName() << ")\n";

    }
    // // get real control dependent (recursive) predecessors with the respective control value
	// std::map<BasicBlock*, std::set<std::pair<BasicBlock*, CondVal>>> CtrlDepPredBBs = getCtrlDepPredBBs();
	// for(auto &elem : CtrlDepPredBBs){
	// 	BasicBlock* currBB = elem.first;
	// 	std::vector<LLVMCDFGNode*> ctrlDepNodes = getCtrlDepNodes(currBB);

	// 	for(auto &ctrlDepPredBB : elem.second){
	// 		BasicBlock* preBB = ctrlDepPredBB.first;
	// 		CondVal cond = ctrlDepPredBB.second;
	// 		BranchInst* BRI = cast<BranchInst>(preBB->getTerminator());
	// 		bool isConditional = BRI->isConditional();
	// 		assert(isConditional);
	// 		LLVMCDFGNode* BRNode = node(BRI); 
    //         assert(BRNode);
	// 		assert(BRNode->inputNodes().size() == 1);
    //         auto preBRNode = BRNode->inputNodes()[0];
    //         bool isBackEdge = false;
    //         // // preBB->currBB is not backedge since it is avoided in getCtrlDepNodes
    //         // std::pair<const BasicBlock*, const BasicBlock*> bbp = std::make_pair(preBB, currBB);
    //         // if(std::find(_backEdgeBBPs.begin(), _backEdgeBBPs.end(), bbp) != _backEdgeBBPs.end()){
    //         //     isBackEdge = true;
    //         // }
	// 		outs() << "ConnectBB :: From " << preBRNode->getName() << "(srcBB = " << preBB->getName() << ")" << ", To ";
	// 		for(LLVMCDFGNode* succNode : ctrlDepNodes){
	// 			outs() << succNode->getName() << ", ";
    //             preBRNode->addOutputNode(succNode, isBackEdge, cond);
    //             succNode->addInputNode(preBRNode, -1, isBackEdge, cond); // donot care the index
    //             addEdge(preBRNode, succNode, EDGE_TYPE_CTRL);
	// 		}
	// 		outs() << "(destBB = " << currBB->getName() << ")\n";
	// 	}
	// }
}



// transfer the multiple control predecessors (input nodes) into a inverted OR tree 
// with the root connected to a node and leaves connected to control predecessors
void LLVMCDFG::createCtrlOrTree() 
{
	outs() << "createCtrlOrTree STARTED!\n";
    std::map<LLVMCDFGNode*, std::set<LLVMCDFGNode*>> condParentsMap; // conditional parents Map
	for(auto &elem : _nodes){
        LLVMCDFGNode* node = elem.second;		
		for(LLVMCDFGNode* par : node->inputNodes()){
            auto cond = node->getInputCondVal(par);
			if( cond != UNCOND){
                condParentsMap[node].insert(par);
				// condParents.insert(par);
			}
		}
    }
    for(auto &elem : condParentsMap){
        LLVMCDFGNode* node = elem.first;
        auto &condParents = elem.second; // conditional parents
        // create CTRLOR tree
		if(condParents.size() > 1){
			std::queue<LLVMCDFGNode*> q;
			for(auto pp : condParents){
				q.push(pp);
			}
			while(!q.empty()){
				auto pp1 = q.front(); q.pop();
				if(!q.empty()){
					auto pp2 = q.front(); q.pop();
					outs() << "Connecting pp1 = " << pp1->getName() << ", ";
					outs() << "pp2 = " << pp2->getName() << ", ";                   
                    // add CTRLOR node
                    LLVMCDFGNode* orNode = addNode("CTRLOR", node->BB());
					outs() << "newORNode = " << orNode->getName() << "\n";                    
					bool isPP1BackEdge = node->isInputBackEdge(pp1);
					bool isPP2BackEdge = node->isInputBackEdge(pp2);
                    assert(node->getInputCondVal(pp1) == TRUE_COND); // the FALSE_COND should be transformed to TRUE_COND before calling this function
                    assert(node->getInputCondVal(pp2) == TRUE_COND);
                    // delete old connections
                    pp1->delOutputNode(node);
                    node->delInputNode(pp1);
                    pp2->delOutputNode(node);
                    node->delInputNode(pp2);     
                    delEdge(edge(pp1, node));     
                    delEdge(edge(pp2, node));  
                    // add new connections
                    pp1->addOutputNode(orNode, isPP1BackEdge, TRUE_COND);
                    orNode->addInputNode(pp1, 0, isPP1BackEdge, TRUE_COND);
                    pp2->addOutputNode(orNode, isPP2BackEdge, TRUE_COND);
                    orNode->addInputNode(pp2, 1, isPP2BackEdge, TRUE_COND);
                    orNode->addOutputNode(node, false, TRUE_COND);
                    node->addInputNode(orNode, -1, false, TRUE_COND);
                    addEdge(pp1, orNode, EDGE_TYPE_CTRL);
                    addEdge(pp2, orNode, EDGE_TYPE_CTRL);
                    addEdge(orNode, node, EDGE_TYPE_CTRL);   
                            
					q.push(orNode);
				}else{
					outs() << "Alone node = " << pp1->getName() << "\n";
				}
			}
		}
	}
	outs() << "createCtrlOrTree ENDED!\n";
}


// get loop start node. If not exist, create one.
LLVMCDFGNode* LLVMCDFG::getLoopStartNode(BasicBlock *BB)
{
    if(_loopStartNodeMap.count(BB)){
        return _loopStartNodeMap[BB];
    }
    // create new node and add node
    LLVMCDFGNode *node = addNode("LOOPSTART", BB);
    // int cnt = _loopStartNodeMap.size();
    _loopStartNodeMap[BB] = node;
    // node->setConstVal(cnt);
    return node;
}


// get loop exit node. If not exist, create one.
LLVMCDFGNode* LLVMCDFG::getLoopExitNode(BasicBlock *BB)
{
    if(_loopExitNodeMap.count(BB)){
        return _loopExitNodeMap[BB];
    }
    // create new node and add node
    LLVMCDFGNode *node = addNode("LOOPEXIT", BB);
    // int cnt = _loopExitNodeMap.size();
    _loopExitNodeMap[BB] = node;
    // node->setConstVal(cnt);
    return node;
}

// get input node. If not exist, create one.
LLVMCDFGNode* LLVMCDFG::getInputNode(Value *ins, BasicBlock *BB)
{
    if(_ioNodeMap.count(ins)){
        return _ioNodeMap[ins];
    }
    // create new node and add node
    LLVMCDFGNode *node = addNode("INPUT", BB);
    _ioNodeMap[ins] = node;
    // _ioNodeMapReverse[node] = ins;
    setIOInfo(node, ins->getName());
    return node;
}


// get out loop store node. If not exist, create one.
LLVMCDFGNode* LLVMCDFG::getOutputNode(Value *ins, BasicBlock *BB)
{
    if(_ioNodeMap.count(ins)){
        return _ioNodeMap[ins];
    }
    // create new node and add node
    LLVMCDFGNode *node = addNode("OUTPUT", BB);
    _ioNodeMap[ins] = node;
    // _ioNodeMapReverse[node] = ins;
    setIOInfo(node, ins->getName());
    return node;
}



// transfer PHI nodes to SELECT nodes
void LLVMCDFG::handlePHINodes() 
{
	std::vector<LLVMCDFGNode*> phiNodes;
	for(auto &elem : _nodes){
        auto &node = elem.second;
		if(node->instruction() && dyn_cast<PHINode>(node->instruction())){
			phiNodes.push_back(node);
		}
	}
    
	for(LLVMCDFGNode* node : phiNodes){
		PHINode* PHI = dyn_cast<PHINode>(node->instruction());
        outs() << "PHI :: "; PHI->dump();
		assert(node->inputNodes().empty());
        std::vector<std::pair<LLVMCDFGNode*, LLVMCDFGNode*>> phiParents; // <value-node, control-node>>
		for (int i = 0; i < PHI->getNumIncomingValues(); ++i) {
			BasicBlock* bb = PHI->getIncomingBlock(i);
			Value* V = PHI->getIncomingValue(i);
			outs() << "IncomingValue :: "; V->dump();
			LLVMCDFGNode* previousCtrlNode = NULL;
			if(_loopBBs.find(bb) == _loopBBs.end()){ // predecessor not in loopBBs					
				std::pair<BasicBlock*,BasicBlock*> bbPair = std::make_pair(bb, node->BB());
				assert(_loopentryBBs.find(bbPair) != _loopentryBBs.end()); // should be loop entry
                LLVMCDFGNode *startNode = getLoopStartNode(bb);
				previousCtrlNode = startNode;
			}else{ // within the loopBBs
				BranchInst* BRI = cast<BranchInst>(bb->getTerminator());
				LLVMCDFGNode* BRNode = this->node(BRI);
				if(!BRI->isConditional()){
                    previousCtrlNode = _ctrlNodesOfBBMap[bb].directCtrlNode;
				}else{
                    LLVMCDFGNode *ctrlNode = BRNode->inputNodes()[0];
                    if(BRI->getSuccessor(0) == node->BB()){ // true condition
                        previousCtrlNode = _condNodesOfBBMap[bb].first;
                    }else{ // false condition
                        assert(BRI->getSuccessor(1) == node->BB());
                        previousCtrlNode = _condNodesOfBBMap[bb].second;
                    }
				}
			}
			assert(previousCtrlNode != NULL);
            outs() << "previousCTRLNode : " << previousCtrlNode->getName() << "\n";
            // get operand value
            LLVMCDFGNode* phiParent = NULL;
            
            if(ConstantInt* CI = dyn_cast<ConstantInt>(V)){
				int constant = CI->getSExtValue();
                phiParent = addNode("CONST", bb);
                phiParent->setConstVal(constant);
			}else if(ConstantFP* FP = dyn_cast<ConstantFP>(V)){
				int constant = (int)FP->getValueAPF().convertToFloat();
                phiParent = addNode("CONST", bb);
                phiParent->setConstVal(constant);
			}else if(UndefValue *UND = dyn_cast<UndefValue>(V)){
                phiParent = addNode("CONST", bb);
                phiParent->setConstVal(0);
			}else if(Argument *ARG = dyn_cast<Argument>(V)){
                phiParent = addNode("CONST", bb);
                phiParent->setConstVal(0);
			}else{				
				if(Instruction* ins = dyn_cast<Instruction>(V)){
					phiParent = this->node(ins);
				}
				if(phiParent == NULL){ //not found
                    phiParent = getInputNode(V, bb);
				}
            }
            phiParents.push_back(std::make_pair(phiParent, previousCtrlNode));
        }
        for(int i = 0; i + 1 < phiParents.size(); i += 2){
            // connect two parents to a SELECT node
            // operand 0 : true data; 1 : false data; 2 : condition (conditional node of parent 1)
            auto &pp1 = phiParents[i];
            auto &pp2 = phiParents[i+1];
            // create a SELECT node
            LLVMCDFGNode *selNode = addNode("SELECT", node->BB());
            outs() << "new SELECT node = " << selNode->getName() << "\n";
            bool isBackEdge1 = false;
            std::pair<const BasicBlock*, const BasicBlock*> bbp1 = std::make_pair(pp1.first->BB(), node->BB());
            if(std::find(_backEdgeBBPs.begin(), _backEdgeBBPs.end(), bbp1) != _backEdgeBBPs.end()){
                isBackEdge1 = true;
            }
            bool isBackEdge2 = false;
            std::pair<const BasicBlock*, const BasicBlock*> bbp2 = std::make_pair(pp2.first->BB(), node->BB());
            if(std::find(_backEdgeBBPs.begin(), _backEdgeBBPs.end(), bbp2) != _backEdgeBBPs.end()){
                isBackEdge2 = true;
            }
            selNode->addInputNode(pp1.first, 0, isBackEdge1); // true data
            selNode->addInputNode(pp2.first, 1, isBackEdge2); // false data
            selNode->addInputNode(pp1.second, 2); // condition
            pp1.first->addOutputNode(selNode, isBackEdge1); 
            pp2.first->addOutputNode(selNode, isBackEdge2);
            pp1.second->addOutputNode(selNode);
            addEdge(pp1.first, selNode, EDGE_TYPE_DATA);
            addEdge(pp2.first, selNode, EDGE_TYPE_DATA);
            addEdge(pp1.second, selNode, EDGE_TYPE_CTRL);
            if(i+2 == phiParents.size()){ // last pair, don not crete new conditional node
                // add new parent to vector
                phiParents.push_back(std::make_pair(selNode, (LLVMCDFGNode *)NULL));
            }else{
                // create new conditional node: CTRLOR (cond1 | cond2)
                LLVMCDFGNode *newCondNode = addNode("CTRLOR", node->BB());
                outs() << "new CTRLOR node = " << newCondNode->getName() << "\n";
                newCondNode->addInputNode(pp1.second, 0);
                newCondNode->addInputNode(pp2.second, 1);
                pp1.second->addOutputNode(newCondNode);
                pp2.second->addOutputNode(newCondNode);
                addEdge(pp1.second, newCondNode, EDGE_TYPE_CTRL);
                addEdge(pp2.second, newCondNode, EDGE_TYPE_CTRL);
                // add new parent to vector
                phiParents.push_back(std::make_pair(selNode, newCondNode));
            }
        }
        // connect last node to the successor nodes of the phi node
        LLVMCDFGNode *lastNode = phiParents.rbegin()->first;
        for(auto succ : node->outputNodes()){
            int idx = succ->delInputNode(node);
            lastNode->addOutputNode(succ);
            succ->addInputNode(lastNode, idx);
            addEdge(lastNode, succ, EDGE_TYPE_DATA);
        }
        outs() << "remove PHI node = " << node->getName() << "\n";
        delNode(node);
    }
}


// add mask AND node behind the Shl node with bytewidth less than MAX_DATA_BYTES
void LLVMCDFG::addMaskAndNodes()
{
    std::vector<LLVMCDFGNode*> shlNodes;
    for(auto &elem : _nodes){
        auto node = elem.second;
        auto ins = node->instruction();
        if(ins && ins->getOpcode() == Instruction::Shl){
            shlNodes.push_back(node);
        }
    }
    for(auto node : shlNodes){
        auto ins = node->instruction();
        BasicBlock *BB = node->BB();
        int bytes = ins->getType()->getIntegerBitWidth() / 8;
        if(bytes < MAX_DATA_BYTES){
            LLVMCDFGNode *andNode = addNode("AND", BB);
            DataType maskVal = (1 << (8 * bytes)) - 1;
            LLVMCDFGNode *constNode = addNode("CONST", BB);
            constNode->setConstVal(maskVal);
            andNode->addInputNode(node, 0);
            andNode->addInputNode(constNode, 1);            
            constNode->addOutputNode(andNode);
            auto outNodes = node->outputNodes();
            for(auto outNode : outNodes){
                node->delOutputNode(outNode);
                int idx = outNode->delInputNode(node);
                delEdge(edge(node, outNode));
                andNode->addOutputNode(outNode);
                outNode->addInputNode(andNode, idx);
                addEdge(andNode, outNode, EDGE_TYPE_DATA);
            }
        }        
    }
}


// get the offset of each element in the struct
std::map<int, int> LLVMCDFG::getStructElemOffsetMap(StructType *ST)
{
    std::map<int, int> elemOffsetMap;
    int offset = 0;
    int idx = 0;
    for(Type *type : ST->elements()){
        elemOffsetMap[idx] = offset;
        offset += DL->getTypeAllocSize(type);
        idx++;
    }
    return elemOffsetMap;
}


// transfer GetElementPtr(GEP) node to MUL/ADD/Const tree
void LLVMCDFG::handleGEPNodes()
{
    std::vector<LLVMCDFGNode*> GEPNodes;
    for(auto &elem : _nodes){
        auto node = elem.second;
        auto ins = node->instruction();
        if(ins && dyn_cast<GetElementPtrInst>(ins)){
            GEPNodes.push_back(node);            
        }
    }
    for(auto node : GEPNodes){
        auto ins = node->instruction();
        GetElementPtrInst *GEP = dyn_cast<GetElementPtrInst>(ins);
        setGEPInfo(node, GEP->getPointerOperand()->getName());
        Type *currType = GEP->getSourceElementType();
        std::vector<std::pair<Value*, int>> varOperandSizes; // <non-constant-operand, element-size>
        int offset = 0;
        int NumOperands = ins->getNumOperands();
        if(NumOperands == 1){ // only one pointer, no index, so GEP should be a Const node
            // base address, should be provided by the scheduler that allocate the address space for the memory
            outs() << "GEP has only one pointer: constant base address\n";
        }else{ // have indexes, get the operand
            for(int i = 1; i < NumOperands; i++){
                outs() << "Operand " << i << ": ";
                Value *V = ins->getOperand(i);
                V->dump();
                outs() << "currType: ";
                currType->dump();
                // check if this operand is constant
                bool isConst = false;
                int constVal;
                // Instruction *I;
                if(ConstantInt *constIns = dyn_cast<ConstantInt>(V)){
                    isConst = true;
                    constVal = constIns->getSExtValue();
                    outs() << "Const: " << constVal << ", ";
                }else{
                    // I = dyn_cast<Instruction>(V);
                    outs() << "Variable, ";
                }
                // get the type and elemnt size of this operand
                int elemSize = 0;
                if(i == 1){ // source element index
                    elemSize = DL->getTypeAllocSize(currType);
                    if(isConst){
                        offset += constVal * elemSize;
                    }                   
                }else if(StructType *ST = dyn_cast<StructType>(currType)){
                    std::map<int, int> elemOffsetMap = getStructElemOffsetMap(ST);
                    assert(isConst); // the operand should be constant
                    offset += elemOffsetMap[constVal];
                    currType = ST->getElementType(constVal);
                    outs() << "StructType, ";
                }else if(ArrayType *AT = dyn_cast<ArrayType>(currType)){                    
                    currType = AT->getElementType();
                    elemSize = DL->getTypeAllocSize(currType);
                    outs() << "ArrayType, ";
                    if(isConst){
                        offset += constVal * elemSize;
                    }
                }else{
                    outs() << "Other type\n";
                    assert(false);
                }
                outs() << "\n";
                if(!isConst){
                    varOperandSizes.push_back(std::make_pair(V, elemSize));
                }
            }
        }
        // construct MUL/ADD/Const tree
        std::vector<LLVMCDFGNode*> newNodes;
        // create MUL nodes
        for(auto &elem : varOperandSizes){
            Instruction *ins = dyn_cast<Instruction>(elem.first);
            LLVMCDFGNode *preNode = this->node(ins); // predecessor node
            if(preNode == NULL){ // out of loop node
                preNode = _ioNodeMap[elem.first];
                outs() << "Out of loop ";
            }
            // elem.first->dump();
            outs() << "preNode: " << preNode->getName() << "\n";
            // delete old connection
            preNode->delOutputNode(node);
            node->delInputNode(preNode);
            delEdge(edge(preNode, node));
            // create new nodes and edges
            auto mulNode = addNode("MUL", node->BB());
            auto constNode = addNode("CONST", node->BB());
            constNode->setConstVal(elem.second);
            preNode->addOutputNode(mulNode);
            mulNode->addInputNode(preNode, 0);
            constNode->addOutputNode(mulNode);
            mulNode->addInputNode(constNode, 1);
            addEdge(preNode, mulNode, EDGE_TYPE_DATA);
            addEdge(constNode, mulNode, EDGE_TYPE_DATA);
            newNodes.push_back(mulNode);
        }
        // create ADD nodes
        for(int i = 0; i + 1 < newNodes.size(); i += 2){
            auto n1 = newNodes[i];
            auto n2 = newNodes[i+1];
            auto newNode = addNode("ADD", node->BB());
            n1->addOutputNode(newNode);
            n2->addOutputNode(newNode);
            newNode->addInputNode(n1, 0);
            newNode->addInputNode(n2, 1);
            addEdge(n1, newNode, EDGE_TYPE_DATA);
            addEdge(n2, newNode, EDGE_TYPE_DATA);
            newNodes.push_back(newNode);
        }
        // connect the last node to GEP node and set constant
        outs() << "Total offset: " << offset << "\n";
        node->setConstVal(offset);
        if(!newNodes.empty()){
            auto lastNewNode = *(newNodes.rbegin());
            lastNewNode->addOutputNode(node);
            node->addInputNode(lastNewNode, 0);
            addEdge(lastNewNode, node, EDGE_TYPE_DATA);
        }
        // the flollowing solution will delete GEP node
        // // connect last offset constant
        // LLVMCDFGNode *gepConstNode = addNode("GEPCONST", node->BB());
        // gepConstNode->setConstVal(offset);
        // outs() << "Total offset: " << offset << "\n";
        // LLVMCDFGNode *finalNode;
        // if(newNodes.empty()){
        //     finalNode = gepConstNode;
        // }else{
        //     auto finalNode = addNode("ADD", node->BB());
        //     auto lastNewNode = *(newNodes.rbegin());
        //     lastNewNode->addOutputNode(finalNode);
        //     gepConstNode->addOutputNode(finalNode);
        //     finalNode->addInputNode(lastNewNode);
        //     finalNode->addInputNode(gepConstNode);
        //     addEdge(lastNewNode, finalNode, EDGE_TYPE_DATA);
        //     addEdge(gepConstNode, finalNode, EDGE_TYPE_DATA);
        // }
        // // connect final node to the successors of GEP node
        // for(auto outNode : node->outputNodes()){
        //     finalNode->addOutputNode(outNode);
        //     outNode->addInputNode(finalNode);
        //     addEdge(finalNode, outNode, EDGE_TYPE_DATA);
        // }
        // delNode(node);
    }
}


// add loop exit nodes
void LLVMCDFG::addLoopExitNodes()
{
    for(auto &elem : _loopexitBBs){
        BasicBlock *srcBB = elem.first;
        BasicBlock *dstBB = elem.second;        
        LLVMCDFGNode *ctrlNode;
        bool isTrueCond;
        BranchInst *BRI = cast<BranchInst>(srcBB->getTerminator());
        assert(BRI->isConditional());
        // BRI must be conditional, otherwise, 
        // the srcBB will have no edge into the loop and wil not included in the loop
        // if(BRI->isConditional()){
        ctrlNode = node(dyn_cast<Instruction>(BRI->getCondition()));
        // check true/false condition
        for(int i = 0; i < BRI->getNumSuccessors(); i++){
            if(dstBB == BRI->getSuccessor(i)){
                isTrueCond = (i == 0);
                break;
            }
        }
        // }else{ // find the control node in the dominating BB
        //     BasicBlock *domBB = DT->getNode(srcBB)->getIDom()->getBlock();
        //     BranchInst *domBRI = cast<BranchInst>(domBB->getTerminator());
        //     assert(domBRI->isConditional());
        //     ctrlNode = node(dyn_cast<Instruction>(domBRI->getCondition()));
        //     // check true/false condition
        //     for(int i = 0; i < domBRI->getNumSuccessors(); i++){
        //         if(DT->dominates(domBRI->getSuccessor(i), srcBB)){
        //             isTrueCond = (i == 0);
        //             break;
        //         }
        //     }
        // }        
        // create LOOPEXIT node and connect ctrlNode to it
        auto exitNode = getLoopExitNode(srcBB);
        if(!isTrueCond){
            // find the CTRLNOT node
            for(auto outNode : ctrlNode->outputNodes()){
                if(outNode->customInstruction() == "CTRLNOT"){
                    ctrlNode = outNode;
                    break;
                }
            }
        }
        outs() << "Control node: " << ctrlNode->getName();
        outs() << ", exit node: " << exitNode->getName() << "\n";
        exitNode->addInputNode(ctrlNode, 0);
        ctrlNode->addOutputNode(exitNode);
        addEdge(ctrlNode, exitNode, EDGE_TYPE_CTRL);
    }
}


// remove redundant nodes, e.g. Branch
void LLVMCDFG::removeRedundantNodes()
{
    // remove redundant nodes iteratively until no node to be remove
    bool removed = true;
    while(removed){
        std::vector<LLVMCDFGNode*> rmNodes;
        for(auto &elem : _nodes){
            auto node = elem.second;
            Instruction *ins = node->instruction();
            std::string customIns = node->customInstruction();
            if(node->inputNodes().empty()){ // no input node
                if(customIns != "CONST" && customIns != "LOOPSTART" && customIns != "INPUT"){
                    rmNodes.push_back(node);
                }
            }else if(node->outputNodes().empty()){ // no output node
                if(!(ins && dyn_cast<StoreInst>(ins)) && customIns != "LOOPEXIT" && customIns != "OUTPUT"){
                    rmNodes.push_back(node);
                }
            }
        }
        removed = !rmNodes.empty();
        outs() << "remove node: ";
        for(auto node : rmNodes){
            outs() << node->getName() << ", ";
            delNode(node);            
        }
        outs() << "\n";
    }
}


// assign final node name
void LLVMCDFG::assignFinalNodeName()
{
    for(auto &elem : _nodes){
        auto node = elem.second;
        Instruction *ins = node->instruction();
        std::string customIns = node->customInstruction();
        if(ins){
            switch (ins->getOpcode()){
            case Instruction::Add:
                node->setFinalInstruction("ADD");
                break;
            case Instruction::FAdd:
                node->setFinalInstruction("FADD");
                break;
            case Instruction::Sub:
                node->setFinalInstruction("SUB");
                break;
            case Instruction::FSub:
                node->setFinalInstruction("FSUB");
                break;
            case Instruction::Mul:
                node->setFinalInstruction("MUL");
                break;
            case Instruction::FMul:
                node->setFinalInstruction("FMUL");
                break;
            case Instruction::UDiv:
            case Instruction::SDiv:
            case Instruction::FDiv:
                errs() << "Do not support Div Instructions\n";
                assert(false);
                break;
            case Instruction::URem:
            case Instruction::SRem:
            case Instruction::FRem:
                errs() << "Do not support Rem Instructions\n";
                assert(false);
                break;
            case Instruction::Shl:
                node->setFinalInstruction("SHL");
                break;
            case Instruction::LShr:
                node->setFinalInstruction("LSHR");
                break;
            case Instruction::AShr:
                node->setFinalInstruction("ASHR");
                break;
            case Instruction::And:
                node->setFinalInstruction("AND");
                break;
            case Instruction::Or:
                node->setFinalInstruction("OR");
                break;
            case Instruction::Xor:
                node->setFinalInstruction("XOR");
                break;
            case Instruction::Load:
                node->setFinalInstruction("LOAD");
                break;
            case Instruction::Store:
                node->setFinalInstruction("STORE");
                break;
            case Instruction::GetElementPtr:
                if(node->inputNodes().empty()){
                    node->setFinalInstruction("CONST");
                }else{
                    node->setFinalInstruction("ADD");
                }                
                break;
            case Instruction::Trunc:{
                TruncInst *TI = dyn_cast<TruncInst>(ins);
                auto bitWidth = TI->getDestTy()->getIntegerBitWidth();
                DataType mask = (DataType)(1 << bitWidth) - 1;
                node->setConstVal(mask);
                node->setFinalInstruction("AND");             
                break;    
            }        
            case Instruction::SExt:{
                SExtInst *SI = dyn_cast<SExtInst>(ins);
                auto srcBitWidth = SI->getSrcTy()->getIntegerBitWidth();
                auto dstBitWidth = SI->getDestTy()->getIntegerBitWidth();
                DataType constVal = (DataType)((dstBitWidth << 8) | srcBitWidth);
                node->setConstVal(constVal);
                node->setFinalInstruction("SEXT");         
                break;       
            }    
            case Instruction::ZExt:{
                node->setConstVal(0);
                node->setFinalInstruction("OR");         
                break;
            }
            case Instruction::ICmp:{
                CmpInst *CI = dyn_cast<CmpInst>(ins);
                switch(CI->getPredicate()){
                case CmpInst::ICMP_EQ:
                    node->setFinalInstruction("EQ");
                    break;
                case CmpInst::ICMP_NE:
                    node->setFinalInstruction("NE");
                    break;
                case CmpInst::ICMP_SGE:
                    node->setFinalInstruction("SGE");
                    break;
                case CmpInst::ICMP_UGE:
                    node->setFinalInstruction("UGE");
                    break;
                case CmpInst::ICMP_SGT:
                    node->setFinalInstruction("SGT");
                    break;
                case CmpInst::ICMP_UGT:
                    node->setFinalInstruction("UGT");
                    break;
                case CmpInst::ICMP_SLE:
                    node->setFinalInstruction("SLE");
                    break;
                case CmpInst::ICMP_ULE:
                    node->setFinalInstruction("ULE");
                    break;
                case CmpInst::ICMP_SLT:
                    node->setFinalInstruction("SLT");
                    break;
                case CmpInst::ICMP_ULT:
                    node->setFinalInstruction("ULT");
                    break;
                default:
                    assert(false);
                    break;
                }
                break;
            }
            case Instruction::Select:
                node->setFinalInstruction("SELECT");
                break;
            default:
                assert(false);
                break;
            }
        }else{
            node->setFinalInstruction(customIns);
        }
    }
}



// print DOT file of CDFG
void LLVMCDFG::printDOT(std::string fileName) {
	std::ofstream ofs;
	ofs.open(fileName.c_str());
    ofs << "Digraph G {\n";
    // nodes
	assert(_nodes.size() != 0);
    for(auto &elem : _nodes){
        auto node = elem.second;
        auto name = node->getName();
        ofs << name << "[label = \"" << name;
        if(node->hasConst()){
            ofs << ", Const=" << node->constVal();
        }
        ofs << "\", shape = box, color = black];\n";
    }
	// edges
    for(auto &elem : _edges){
        auto edge = elem.second;
        auto srcName = edge->src()->getName();
        auto dstName = edge->dst()->getName();
        ofs << srcName << " -> " << dstName;
        auto type = edge->type();
        if(type == EDGE_TYPE_CTRL){
            ofs << "[color = red";
        }else if(type == EDGE_TYPE_MEM){
            ofs << "[color = blue";
        }else{
            ofs << "[color = black";
        }
        bool isBackEdge = edge->src()->isOutputBackEdge(edge->dst());
        if(isBackEdge){
            ofs << ", style = dashed";
        }else{
            ofs << ", style = bold";
        }
        int opIdx = edge->dst()->getInputIdx(edge->src());
        ofs << ", label = \"Op=" << opIdx;
        if(type == EDGE_TYPE_MEM){
            ofs << ", DepDist = " << edge->dst()->getSrcDep(edge->src()).distance;
        }
        ofs << "\"];\n";
    }
	ofs << "}\n";
	ofs.close();
}


// generate CDFG
void LLVMCDFG::generateCDFG()
{
    outs() << "########################################################\n";
    outs() << "Generate CDFG Started\n";
    // initialized CDFG
    printDOT(_name + "_init.dot");
    // add edge between two nodes that have memory dependence (loop-carried)
    outs() << ">>>>>> add edge between two nodes that have memory dependence (loop-carried)\n";
    addMemDepEdges();
    printDOT(_name + "_after_addMemDepEdges.dot");
    // insert Control NOT node behind the node with FALSE_COND control output edge
    outs() << ">>>>>> Insert CTRLNOT node behind the node with FALSE_COND control output edge\n";
    insertCtrlNotNodes();
    printDOT(_name + "_after_insertCtrlNotNodes.dot");
    // Connect control dependent node pairs among BBs
    outs() << ">>>>>> Connect control dependent node pairs among BBs\n";
    connectCtrlDepBBs();
    printDOT(_name + "_after_connectCtrlDepBBs.dot");
    // transfer the multiple control predecessors (input nodes) into a inverted OR tree 
    // with the root connected to a node and leaves connected to control predecessors
    outs() << ">>>>>> Transfer multiple control predecessors (input nodes) into a inverted OR tree\n";
    createCtrlOrTree();
    printDOT(_name + "_after_createCtrlOrTree.dot");
    // transfer GetElementPtr(GEP) node to MUL/ADD/Const tree
    outs() << ">>>>>> Transfer GEP node to MUL/ADD/Const tree\n";
    handleGEPNodes();
    printDOT(_name + "_after_handleGEPNodes.dot");
    // Transfer PHINode to SELECT nodes
    outs() << ">>>>>> Transfer PHINode to SELECT nodes\n";
    handlePHINodes(); 
    printDOT(_name + "_after_handlePHINodes.dot");
    // add mask AND node behind the Shl node with bytewidth less than MAX_DATA_BYTE
    outs() << ">>>>>> Add mask AND node behind the Shl node with bytewidth less than MAX_DATA_BYTE\n";
    addMaskAndNodes();
    printDOT(_name + "_after_addMaskAndNodes.dot");
    // add loop exit nodes
    outs() << ">>>>>> Add loop exit nodes\n";
    addLoopExitNodes();
    printDOT(_name + "_after_addLoopExitNodes.dot");
    // remove redundant nodes, e.g. Branch
    outs() << ">>>>>> Remove redundant nodes\n";
    removeRedundantNodes();
    printDOT(_name + "_after_removeRedundantNodes.dot");
    // assign final node name
    outs() << ">>>>>> Assign final node name\n";
    assignFinalNodeName();
    printDOT(_name + "_after_assignFinalNodeName.dot");
    outs() << "Generate CDFG Ended\n";
    outs() << "########################################################\n";
}


