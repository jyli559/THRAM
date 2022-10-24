package dsa

import scala.collection.mutable.ArrayBuffer
import scala.io.Source

/** A class that helps users to automatically generate simulation codes for an architecture.
 * A result TXT can be interpreted in this class.
 * The result TXT indicate the mapping result of DFG IO nodes,
 * which consists of the name of these nodes, fire time and skew.
 */
class SimulationHelper() {

  var size = 0
  val opArray = new ArrayBuffer[String]()
  val fireTimeArray = new ArrayBuffer[Int]()
  val outPorts = new ArrayBuffer[Int]()
  val inputPorts = new ArrayBuffer[Int]()
  var inputnum = 0
  var outputnum = 0
  var outputCycle = 0

  /** A map between the index of a opNode with "output" opcode and the ID of output port.
   */
  var outputPortCycleMap = Map[Int, Int]()

  /** A map between the index of a opNode with "input" opcode and the ID of input port.
   */
  var inputPortCycleMap = Map[Int, Int]()

  /** Add the mapping result of a mapped DFG node.
   *
   * @param result a line in the result TXT indicating the mapping result of a mapped DFG IO node
   */
  def addResult(result: String): Unit = {
    val tempList = result.replaceAll(",","").split(" ").toList

    //Add the name of the DFG node ID into opArray.
    val op = tempList(0)
    opArray.append(op)

    val moduleNum = tempList(1)
    if (op.contains("output") || op.contains("input")) {
      if (op.contains("output")) {
        //Add the identification number of the mapped output ports into outPorts.
        outPorts.append(moduleNum.toInt)
        outputnum = outputnum + 1
      } else if (op.contains("input")) {
        //Add the identification number of the mapped input ports into inputPorts.
        inputPorts.append(moduleNum.toInt)
        inputnum = inputnum + 1
      }
    }
    println(tempList(1))
    //Add the fire time of the mapped IO node into fireTimeArray.
    val fireTime = tempList(2).toInt
    fireTimeArray.append(fireTime)
    if (op.contains("output")) {
      outputPortCycleMap += outPorts.last -> fireTime
    } else if (op.contains("input")) {
      inputPortCycleMap += inputPorts.last -> fireTime
    }

  }

  /** Reset values in this class.
   */
  def reset(): Unit = {
    size = 0
    opArray.clear()
    fireTimeArray.clear()
    outPorts.clear()
    outputPortCycleMap = Map[Int, Int]()
    inputPortCycleMap = Map[Int, Int]()
  }

  /** Initialize values in this class according to a result TXT.
   *
   * @param resultFilename the file name of the result TXT
   */
  def init(resultFilename: String): Unit = {
    reset()
    val resultArray = Source.fromFile(resultFilename).getLines().toArray
    val mesageArray = resultArray.tail
    mesageArray.map(r => addResult(r))
    size = opArray.size
    //Set the cycle we can obtain the last result.
    if(outputPortCycleMap.size>0) {
      outputCycle = outputPortCycleMap.map(t => t._2)
        .reduce((t1, t2) => Math.max(t1, t2))
    }else{
      outputCycle = 0
    }
  }

  /** Get the number of inputports
   */
  def getinputnum(): Int = {
    inputnum
  }

  /** Get the number of outputports
   */
  def getoutputnum(): Int = {
    outputnum
  }

  /** Get data arrays with corresponding address.
   *
   * @param dataSize      the data size of a data array
   * @param inDataArrays  the input data arrays for LSUs
   * @param outDataArrays the expected data arrays for LSUs
   * @param refDataArrays the expected data arrays for the output ports
   * @return the expected data arrays for the output ports with corresponding identification number)
   */
  def getDataWithAddr(dataSize: Int = 0, inDataArrays: Array[Array[Int]] = null,
                      outDataArrays: Array[Array[Int]] = null, refDataArrays: Array[Array[Int]] = null): Array[Any] = {
    val refDataAddr = new ArrayBuffer[Int]()
    var inDatas = Map[List[Int], Array[Int]]()
    var outDatas = Map[List[Int], Array[Int]]()
    var refDatas = Map[Int, Array[Int]]()
    var index = 0
    var p = 0
    var addrMap = Map[Int, Int]()
    var addr = 0
    
      for (i <- 0 until size) {
        val op = opArray(i)
        if (op.contains("output")) {
          refDataAddr.append(outPorts(p))
          p = p + 1
        }
      }

    for (i <- 0 until refDataAddr.size) {
      refDatas = refDatas ++ Map(refDataAddr(i) -> refDataArrays(i))
    }
    Array(refDatas)
  }

  /** Get the cycle we can obtain the result.
   *
   * @return the cycle we can obtain the result
   */
  def getOutputCycle(): Int = {
    outputCycle
  }
}
