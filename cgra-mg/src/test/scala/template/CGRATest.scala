package dsa

import scala.io.Source
import java.io._
import java.math.BigInteger
import scala.math.BigInt
import chisel3._
import chisel3.util._
import chisel3.assert

import scala.collection.mutable
import scala.collection.mutable.{ArrayBuffer, ListBuffer}
//import chisel3.iotesters.{ChiselFlatSpec, Driver, PeekPokeTester}
import chiseltest._
import org.scalatest._
import org.scalatest.flatspec.AnyFlatSpec
import spec.CGRASpec

//The main object of Architecture simulation
class TestSim extends FlatSpec with ChiselScalatestTester{
  
  //select which benchmark to be simulated
  val IOFilename = "../benchmarks/test/ewf/mapped_dfgio.txt"
//  val IOFilename = "../benchmarks/test2/conv3/mapped_dfgio.txt"

  val simulationHelper = new SimulationHelper()
  simulationHelper.init(IOFilename)
  val outputCycle = simulationHelper.getOutputCycle()
  val inputnum = simulationHelper.getinputnum()
  val outputnum = simulationHelper.getoutputnum()
  println("outputCycle: " + outputCycle)
  println("inputnum: " + inputnum)
  println("outputnum: " + outputnum)

  //set the size of data for simulation 
  val dataSize = 50

  var inData = Array.ofDim[Int](inputnum,dataSize)
  var outPortRefArrays = Array.ofDim[Int](outputnum,dataSize)
  var results = new Array[Int](outputnum)
  var inport = new ArrayBuffer[Int]()
  var inmap = Map[Int, Array[Int]]()

  for(j <- 0 until inputnum) {
//    inData(j) = (0 until dataSize).toArray
    inData(j) = (0 until dataSize).map(i => scala.util.Random.nextInt()).toArray
    inport.append(simulationHelper.inputPorts(j))
    inmap = inmap ++ Map(inport(j) -> inData(j))
  }

//TODO: simulation of architecture with LSU
  var refArray = Array[Int]()
  var ref = 0

  // the II of mapped DFG, II = 1 for static configuration
  val testII = 1

  // This part is specified for every benchmark
  for (i <- 0 until dataSize) {
//    results(0) = 4 * inData(0)(i) + 10
//    results(1) = inData(0)(i) + 4
    results(0) = (inData(0)(i) + inData(1)(i) + inData(2)(i) + inData(3)(i)) * 2
    results(1) = 0
    results(2) = inData(0)(i) + inData(1)(i)
    results(3) = (inData(0)(i) + inData(1)(i)) * 2
    results(4) = inData(2)(i) + inData(3)(i)
    // resultB = data + 4
    outPortRefArrays(0)(i) = results(0)
    outPortRefArrays(1)(i) = results(1)
    outPortRefArrays(2)(i) = results(2)
    outPortRefArrays(3)(i) = results(3)
    outPortRefArrays(4)(i) = results(4)     // resultB = data + 4
  }

  val outDataRefArrays = Array(refArray)
  val dataWithAddr = simulationHelper.getDataWithAddr(inDataArrays = inData, outDataArrays = outDataRefArrays, refDataArrays = outPortRefArrays)
  val outPortRefs = dataWithAddr(0).asInstanceOf[Map[Int, Array[Int]]]
  
  val appTestHelper = new AppTestHelper(testII)
  appTestHelper.setOutPortRefs(outPortRefs)
  appTestHelper.setOutputCycle(outputCycle)

  //Pass the input data to tester
  appTestHelper.setInputPortData(inmap)
  appTestHelper.setPortCycle(simulationHelper)
  
  //set the scale of simulated architecture
  val jsonFile = "src/main/resources/cgra_spec.json"
  CGRASpec.loadSpec(jsonFile)

  ////////chiseltest
  behavior of "CGRA"
  it should "work harder" in {
    test(new CGRA(CGRASpec.attrs, false)) {
      c => new BMTester(c, "../benchmarks/test/ewf/config.bit", appTestHelper)

    }
  }



}
////////////////////////////////////////////////////////////////////////////////////////////////////////
/** A class which passes the parameters for apptester.
 *
 * @param testII     the targeted II
 */
class AppTestHelper(testII: Int) {

  /** A map between the targeted output port and the expected data array.
   */
  var outPortRefs = Map[Int, Array[Int]]()

  /** A map between the targeted input port and the input data array.
   */
  var inputPortData = Map[Int, Array[Int]]()

  /** The cycle we can obtain the result.
   */
  var outputCycle = 1

  /** A map between the targeted output port and the expected outputcycle.
   */
  var outputPortCycleMap = Map[Int, Int]()

  /** A map between the targeted input port and the inputcycle.
   */
  var inputPortCycleMap = Map[Int, Int]()

//get parameters from simulate main function

  def setPortCycle(simulationHelper: SimulationHelper): Unit = {
    outputPortCycleMap = simulationHelper.outputPortCycleMap
    inputPortCycleMap = simulationHelper.inputPortCycleMap
    outputCycle = simulationHelper.outputCycle
  }

  def setOutputCycle(arg: Int): Unit = {
    outputCycle = arg
  }

  /** Set the map between the targeted output port and the expected data array.
   */
  def setOutPortRefs(arg: Map[Int, Array[Int]]): Unit = {
    outPortRefs = arg
  }

  /** Set the map between the targeted input port and the input data array.
   */
  def setInputPortData(arg: Map[Int, Array[Int]]): Unit = {
    inputPortData = arg
  }

//pass parameters to Apptester  

  /** Get the targeted II.
   */
  def getTestII(): Int = {
    testII
  }

  /** Get the cycle we can obtain the result.
   */
  def getOutputCycle(): Int = {
    outputCycle
  }

  /** Get the map between the targeted output port and the expected data array.
   */
  def getOutPortRefs(): Map[Int, Array[Int]] = {
    outPortRefs
  }

  /** Get the map between the targeted input port and the input data array.
   */
  def getInputPortData(): Map[Int, Array[Int]] = {
    inputPortData
  }
}

/** A base class of testers for benchmarks.
 * It help users to test the architecture and benchmark in the specific format of Chisel testers using the Verilator backend.
 *
 * @param c             the top design
 * @param appTestHelper the class which passes the parameters for apptester
 */
class ApplicationTester(c: CGRA, appTestHelper: AppTestHelper) extends AnyFlatSpec with ChiselScalatestTester {
  /** Translate a signed Int as unsigned BigInt.
   * @param signedInt the signed Int
   * @return the unsigned BigInt
   */
   // behavior of "c"
  def asUnsignedInt(signedInt: Int): BigInt = (BigInt(signedInt >>> 1) << 1) + (signedInt & 1)

  /** Verifies data in output ports during the activating process.
   *
   * @param testII the targeted II
   */
  def checkPortOuts(testII: Int): Unit = {
    val refs = appTestHelper.getOutPortRefs()
    val throughput = 1
    if (throughput > 1) {
      c.clock.step((throughput - 1) * testII)
    }
    for (ref <- refs) {
      for (i <- ref._2) {
        c.io.out(ref._1).expect(asUnsignedInt(i).U)
        println(asUnsignedInt(i).toString + " " + c.io.out(ref._1).peek().toString())
        c.clock.step(testII * throughput)
      }
    }
  }

  /** Verifies data in output ports during the activating process when transferring data through the input ports.
   *
   * @param testII the targeted II
   */
  def checkPortOutsWithInput(testII: Int): Unit = {
    val refs = appTestHelper.getOutPortRefs()
    val outputCycle = appTestHelper.getOutputCycle()
    val inputDataMap = appTestHelper.getInputPortData()
    val outputPortCycleMap = appTestHelper.outputPortCycleMap
    val inputPortCycleMap = appTestHelper.inputPortCycleMap
    val dataSize = refs.toArray.last._2.size

    val T = (dataSize + outputCycle / testII) * testII
    for (t <- 0 until T) {
      for (port <- inputDataMap.keys) {
        val data = inputDataMap(port)
        val cycle = inputPortCycleMap(port)
        if (t >= cycle && t < cycle + dataSize * testII) {
          if (cycle % testII == t % testII) {
            c.io.in(port).poke(asUnsignedInt(data((t - cycle)/testII)).U)
            println("cycle: " + t + "; " + "inportID: " + port.toString + " inData: " + data((t-cycle)/testII).toString)
          }
        }
      }
      for (port <- refs.keys) {
        val data = refs(port)
        val cycle = outputPortCycleMap(port)
        if (t >= cycle && t < cycle + dataSize * testII) {
          if (cycle % testII == t % testII) {
            c.io.out(port).expect(asUnsignedInt(data((t - cycle)/testII)).U)
            println("cycle: " + t + "; outportID: " + port)
            println(asUnsignedInt(data((t - cycle)/testII)).toString + " " + c.io.out(port).peek().toString())
          }
        }
      }
      c.clock.step(1)
    }
  }

}

class BMTester(c: CGRA, cfgFilename: String, appTestHelper: AppTestHelper) extends ApplicationTester(c, appTestHelper) {
  val rows = c.param.rows
  val cols = c.param.cols
  // read config bit file
  Source.fromFile(cfgFilename).getLines().foreach{
    line => {
      val items = line.split(" ")
      val addr = Integer.parseInt(items(0), 16);        // config bus address
      val data = BigInt(new BigInteger(items(1), 16));  // config bus data
      c.io.cfg_en.poke(1.B)
      c.io.cfg_addr.poke(addr.U)
      c.io.cfg_data.poke(data.U)
      c.clock.step(1)
    }
  }
  c.io.cfg_en.poke(0.B)
  // delay for config done
  c.clock.step(c.cfgRegNum + 10)
  // enable computation
  for( i <- 0 until cols){
    c.io.en(i).poke(1.B)
  }
  // input test data
  val testII = appTestHelper.getTestII()
  checkPortOutsWithInput(testII)
  
}
