package dsa

import chisel3._
import chisel3.util._
import scala.collection.mutable
import scala.collection.mutable.{ListBuffer, ArrayBuffer}
import scala.math.{pow}
import op._
import ir._


/** GPE: Generic Processing Element
 * 
 * @param attrs     module attributes
 */ 
class GPE(attrs: mutable.Map[String, Any]) extends Module with IR {
  val width = attrs("data_width").asInstanceOf[Int]
  // cfgParams
  val cfgDataWidth = attrs("cfg_data_width").asInstanceOf[Int]
  val cfgAddrWidth = attrs("cfg_addr_width").asInstanceOf[Int]
  val cfgBlkIndex  = attrs("cfg_blk_index").asInstanceOf[Int]     // configuration index of this block, cfg_addr[width-1 : offset]
  val cfgBlkOffset = attrs("cfg_blk_offset").asInstanceOf[Int]   // configuration offset bit of blocks
  // number of registers in Regfile
  val numRegRF = attrs("num_rf_reg").asInstanceOf[Int]
  // supported operations
  val opsStr = attrs("operations").asInstanceOf[ListBuffer[String]]
  val ops = opsStr.map(OPC.withName(_))
  val aluOperandNum = ops.map(OpInfo.getOperandNum(_)).max
  // val aluCfgWidth = log2Ceil(OPC.numOPC) // ALU Config width
  val numInPerOperand = attrs("num_input_per_operand").asInstanceOf[ListBuffer[Int]]
  // max delay cycles of the DelayPipe
  val maxDelay = attrs("max_delay").asInstanceOf[Int]
  apply("data_width", width)
  apply("num_operands", aluOperandNum)
  apply("num_input", numInPerOperand.sum)
  apply("num_output", 1)
  apply("cfg_blk_index", cfgBlkIndex)
  apply("num_rf_reg", numRegRF)
  apply("operations", opsStr)
  apply("max_delay", maxDelay)

  val io = IO(new Bundle {
    val cfg_en = Input(Bool())
    val cfg_addr = Input(UInt(cfgAddrWidth.W))
    val cfg_data = Input(UInt(cfgDataWidth.W))
    val en = Input(Bool())
    val in = Input(Vec(numInPerOperand.sum, UInt(width.W)))   
    val out = Output(Vec(1, UInt(width.W)))
  })

  val alu = Module(new ALU(width, ops))
  val rf = Module(new RF(width, numRegRF, 1, 2))
  val delay_pipe = Module(new SharedDelayPipe(width, maxDelay, aluOperandNum))
//  val delay_pipes = Array.fill(aluOperandNum){ Module(new DelayPipe(width, maxDelay)).io }
  val const = Wire(UInt(width.W))
  val imuxs = numInPerOperand.map{ num => Module(new Muxn(width, num+2)).io } // input + const + rf_out


  // ======= sub_module attribute ========//
  // 1 : Constant
  // 2-n : sub-modules 
  val sm_id: Map[String, Int] = Map(
    "Const" -> 1,
    "ALU" -> 2,
    "RF" -> 3,
    "DelayPipe" -> 4,
    "Muxn" -> 5
  )

  val sub_modules = sm_id.map{case (name, id) => Map(
    "id" -> id, 
    "type" -> name
  )}
  apply("sub_modules", sub_modules)

  // ======= sub_module instance attribute ========//
  // 0 : this module
  // 1 : Constant
  // 2-n : sub-modules 
  val smi_id: Map[String, List[Int]] = Map(
    "This" -> List(0),
    "Const" -> List(1),
    "ALU" -> List(2),
    "RF" -> List(3),
    "DelayPipe" -> List(4), // (4 until aluOperandNum+4).toList,
    "Muxn" -> (5 until aluOperandNum+5).toList // (aluOperandNum+4 until 2*aluOperandNum+4).toList
  )
  val instances = smi_id.map{case (name, ids) =>
    ids.map{id => Map(
      "id" -> id, 
      "type" -> name,
      "module_id" -> {if(name == "This") 0 else sm_id(name)}
    )}
  }.flatten
  apply("instances", instances)

  // ======= connections attribute ========//
  // apply("connection_format", ("src_id", "src_type", "src_out_idx", "dst_id", "dst_type", "dst_in_idx"))
  // This:src_out_idx is the input index
  // This:dst_in_idx is the output index
  val connections = ListBuffer(
    (smi_id("ALU")(0), "ALU", 0, smi_id("RF")(0), "RF", 0), 
    (smi_id("RF")(0), "RF", 0, smi_id("This")(0), "This", 0)
  )
  delay_pipe.io.en := io.en
  rf.io.en := io.en
  rf.io.in(0) := alu.io.out
  io.out(0) := rf.io.out(0)

  var offset = 0
  for(i <- 0 until aluOperandNum){
    val num = numInPerOperand(i)
    imuxs(i).in.zipWithIndex.foreach{ case (in, j) =>
      if(j < num) {
        in := io.in(offset+j)
        connections.append((smi_id("This")(0), "This", offset+j, smi_id("Muxn")(i), "Muxn", j))
      } else if(j == num) {
        in := const
        connections.append((smi_id("Const")(0), "Const", 0, smi_id("Muxn")(i), "Muxn", j))
      } else {
        in := rf.io.out(1)
        connections.append((smi_id("RF")(0), "RF", 1, smi_id("Muxn")(i), "Muxn", j))
      }
    }
    delay_pipe.io.in(i) := imuxs(i).out
    alu.io.in(i) := delay_pipe.io.out(i)
    connections.append((smi_id("Muxn")(i), "Muxn", 0, smi_id("DelayPipe")(0), "DelayPipe", i))
    connections.append((smi_id("DelayPipe")(0), "DelayPipe", i, smi_id("ALU")(0), "ALU", i))
    //    delay_pipes(i).en := io.en
    //    delay_pipes(i).in := imuxs(i).out
    //    alu.io.in(i) := delay_pipes(i).out
    offset += num
  }

  // apply("connections", connections)
  apply("connections", connections.zipWithIndex.map{case (c, i) => i -> c}.toMap)

  // ======= configuration attribute ========//
  // configuration memory
  val constCfgWidth = width // constant
  val aluCfgWidth = alu.io.config.getWidth // ALU Config width
  val rfCfgWidth = rf.io.config.getWidth  // RF
  //  val delayCfgWidthEach = delay_pipes(0).config.getWidth // DelayPipe Config width
  //  val delayCfgWidth = aluOperandNum * delayCfgWidthEach
  val delayCfgWidth = delay_pipe.io.config.getWidth
  val imuxCfgWidthList = imuxs.map{ mux => mux.config.getWidth } // input Muxes
  val imuxCfgWidth = imuxCfgWidthList.sum
  val sumCfgWidth = constCfgWidth + aluCfgWidth + rfCfgWidth + delayCfgWidth + imuxCfgWidth

  val cfg = Module(new ConfigMem(sumCfgWidth, 1, cfgDataWidth))
  cfg.io.cfg_en := io.cfg_en && (cfgBlkIndex.U === io.cfg_addr(cfgAddrWidth-1, cfgBlkOffset))
  cfg.io.cfg_addr := io.cfg_addr(cfgBlkOffset-1, 0)
  cfg.io.cfg_data := io.cfg_data
  assert(cfg.cfgAddrWidth <= cfgBlkOffset)
  assert(cfgBlkIndex < (1 << (cfgAddrWidth-cfgBlkOffset)))

  val configuration = mutable.Map( // id : type, high, low
    smi_id("This")(0) -> ("This", sumCfgWidth-1, 0),
    smi_id("Const")(0) -> ("Const", constCfgWidth-1, 0)
  )

  val cfgOut = Wire(UInt(sumCfgWidth.W))
  cfgOut := cfg.io.out(0)
  const := cfgOut(constCfgWidth-1, 0)
  offset = constCfgWidth
  if(aluCfgWidth != 0){
    alu.io.config := cfgOut(offset+aluCfgWidth-1, offset)
    configuration += smi_id("ALU")(0) -> ("ALU", offset+aluCfgWidth-1, offset)
  } else {
    alu.io.config := DontCare
  }
  offset += aluCfgWidth

  if(rfCfgWidth != 0){
    rf.io.config := cfgOut(offset+rfCfgWidth-1, offset)
    configuration += smi_id("RF")(0) -> ("RF", offset+rfCfgWidth-1, offset)
  } else{
    rf.io.config := DontCare
  }
  offset += rfCfgWidth
  //  for(i <- 0 until aluOperandNum){
  //    if(delayCfgWidthEach != 0){
  //      delay_pipes(i).config := cfgOut(offset+delayCfgWidthEach-1, offset)
  //    } else {
  //      delay_pipes(i).config := DontCare
  //    }
  //    offset += delayCfgWidthEach
  //  }
  if(delayCfgWidth != 0){
    delay_pipe.io.config := cfgOut(offset+delayCfgWidth-1, offset)
    configuration += smi_id("DelayPipe")(0) -> ("DelayPipe", offset+delayCfgWidth-1, offset)
  } else{
    delay_pipe.io.config := DontCare
  }
  offset += delayCfgWidth

  for(i <- 0 until aluOperandNum){
    if(imuxCfgWidthList(i) != 0){
      imuxs(i).config := cfgOut(offset+imuxCfgWidthList(i)-1, offset)
      configuration += smi_id("Muxn")(i) -> ("Muxn", offset+imuxCfgWidthList(i)-1, offset)
    } else {
      imuxs(i).config := DontCare
    }
    offset += imuxCfgWidthList(i)
  }

  apply("configuration", configuration)

  // val outFilename = "test_run_dir/my_cgra_test.json"
  // printIR(outFilename)
}






// object petest extends App {
////   Map(num_rf_reg -> 1, operations -> ListBuffer(ADD), cfg_data_width -> 32, cfg_addr_width -> 12, y -> 1, data_width -> 32, num_input_per_operand -> ListBuffer(4, 4), x -> 3, cfg_blk_offset -> 2, max_delay -> 4, cfg_blk_index -> 10)
//
//   val attrs: mutable.Map[String, Any] = mutable.Map(
//     "data_width" -> 32,
//     "cfg_data_width" -> 32,
//     "cfg_addr_width" -> 12,
//     "cfg_blk_index" -> 1,
//     "cfg_blk_offset" -> 4,
//     "num_rf_reg" -> 1,
//     "operations" -> ListBuffer("ADD"),
//     "num_input_per_operand" -> ListBuffer(4, 4),
//     "max_delay" -> 4
//   )
//
//   (new chisel3.stage.ChiselStage).emitVerilog(new GPE(attrs),args)
//   ppa.ppa_gpe.getgpearea(ListBuffer("ADD"),ListBuffer(4, 4),4)
// }