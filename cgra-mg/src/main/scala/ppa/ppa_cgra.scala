package ppa

import chisel3._
import chisel3.util._
import common.MacroVar.{NORTHEAST, NORTHWEST, SOUTHEAST, SOUTHWEST}
import dsa.template.{GibParam, GpeParam}
import scala.collection.mutable
import scala.collection.mutable.{ArrayBuffer, ListBuffer}

import java.io._

object ppa_cgra {
  def CGRA_area(attrs: mutable.Map[String, Any])  {
    // CGRA parameters
    val param = dsa.template.CgraParam(attrs)
    import param._

    var area : Double = 0
    var total_area : Double = 0

    for (k <- 0 until 2) { // top and buttom row
      for (i <- 0 until cols) {
        area = area + ppa.ppa_iob.getiobarea(1, numOutIB)
      }
    }
    total_area += area
    println("IB total area : " + area)

    area = 0
    for (k <- 0 until 2) { // top and buttom row
      for (i <- 0 until cols) {
        area = area + ppa.ppa_iob.getiobarea(numInOB, 1)
      }
    }
    total_area += area
    println("OB total area : " + area)

    area = 0
    for (i <- 0 until rows) {
      for (j <- 0 until cols) {
        val gpe_type = gpe_posmap((i, j))
        val gpe_param = gpe_typemap(gpe_type)
        area = area + ppa.ppa_gpe.getgpearea(gpe_param.operations, gpe_param.num_input_per_operand, gpe_param.max_delay)
      }
    }
    total_area += area
    println("GPE total area : " + area)

    area = 0
    for (i <- 0 to rows) {
      for (j <- 0 to cols) {
        val gib_type = gib_posmap(i, j)
        val gib_param = gib_typemap(gib_type)
        val track_reged = gibsParam(i)(j).track_reged // track_reged is not used to classify type
        area = area + ppa.ppa_gib.getgibarea(numTrack, gib_param.diag_iopin_connect, gib_param.num_iopin_list, gib_param.connect_flexibility, track_reged, gib_param.track_directions)
//        println("numTrack" + numTrack)
//        println("gib_param.diag_iopin_connect" + gib_param.diag_iopin_connect)
//        println("gib_param.num_iopin_list" + gib_param.num_iopin_list)
//        println("gib_param.connect_flexibility" +  gib_param.connect_flexibility)
//        println("gib_param.track_reged" +  gib_param.track_reged)
//        println("gib_param.track_directions" +  gib_param.track_directions)
//        println()
//        println("area is :" + area)
      }
    }
    total_area += area
    println("GIB total area :" + area)
    println("CGRA total area :" + total_area)
    total_area

    val writer = new PrintWriter(new File("area.txt"))
    writer.write(total_area.toString)
    writer.close()
  }
}