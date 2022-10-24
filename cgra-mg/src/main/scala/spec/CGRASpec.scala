 package spec
 // Architecture Specification

 import scala.collection.mutable
 import scala.collection.mutable.ListBuffer
 import common.MacroVar.{NORTHEAST, NORTHWEST, SOUTHEAST, SOUTHWEST}
 import dsa.template.{GibParam, GpeParam}
 import ir._

 // GPE Spec to support heterogeneous GPEs
 class GpeSpec(num_rf_reg_ : Int = 1, max_delay_ :Int = 4,
               operations_ : ListBuffer[String] = ListBuffer( "PASS", "ADD", "SUB", "MUL", "AND", "OR", "XOR"),
               fromdir_ : List[Int] =  List(NORTHWEST, NORTHEAST, SOUTHWEST, SOUTHEAST),
               todir_ : List[Int] = List(NORTHWEST, NORTHEAST, SOUTHWEST, SOUTHEAST)){
   var num_rf_reg =  num_rf_reg_  // number of registers in Regfile
   var max_delay = max_delay_     // max delay cycles of the DelayPipe
   var operations = operations_   // supported operations
   var from_dir = fromdir_        // which directions the GPE inputs are from
   var to_dir = todir_            // which directions the GPE outputs are to
 }

 object GpeSpec {
   def apply(num_rf_reg_ : Int = 1, max_delay_ :Int = 4,
             operations_ :ListBuffer[String] = ListBuffer( "ADD"),
             fromdir_ : List[Int] =  List(NORTHWEST,NORTHEAST, SOUTHWEST, SOUTHEAST),
             todir_ : List[Int] =  List(NORTHWEST, NORTHEAST, SOUTHWEST, SOUTHEAST)) = {
     new GpeSpec(num_rf_reg_, max_delay_, operations_, fromdir_, todir_)
   }
//   def apply(attr : mutable.Map[String, Any]) = {
//     val num_rf_reg_ = attr("num_rf_reg").asInstanceOf[Int]
//     val max_delay_ = attr("max_delay").asInstanceOf[Int]
//     val operations_ = attr("operations").asInstanceOf[List[String]].to[ListBuffer]
//     val fromdir_ = attr("from_dir").asInstanceOf[List[Int]]
//     val todir_ = attr("to_dir").asInstanceOf[List[Int]]
//     new GpeSpec(num_rf_reg_, max_delay_, operations_, fromdir_, todir_)
//   }
 }


 // GIB Spec to support heterogeneous GIBs
 class GibSpec(diagIOPinConnect : Boolean = true , fclist_ : List[Int] = List(2, 4, 4)){
   var diag_iopin_connect = diagIOPinConnect // if support diagonal connections between OPins and IPins
   var fclist = fclist_ // num_itrack_per_ipin, num_otrack_per_opin, num_ipin_per_opin
   // "num_itrack_per_ipin" : ipin-itrack connection flexibility, connected track number
   // "num_otrack_per_opin" : opin-otrack connection flexibility, connected track number
   // "num_ipin_per_opin"   : opin-ipin  connection flexibility, connected ipin number
 }

 object GibSpec {
   def apply(diagIOPinConnect : Boolean = true , fclist_ : List[Int] = List(2, 4, 4)) = {
     new GibSpec(diagIOPinConnect, fclist_)
   }
//   def apply(attr : mutable.Map[String, Any]) = {
//     val diagIOPinConnect = attr("diag_iopin_connect").asInstanceOf[Boolean]
//     val fclist_ = attr("fclist").asInstanceOf[List[Int]]
//     new GibSpec(diagIOPinConnect, fclist_)
//   }
 }

 // CGRA Specification
 object CGRASpec{
   val connect_flexibility = mutable.Map(
     "num_itrack_per_ipin" -> 2, // ipin number = 2
     "num_otrack_per_opin" -> 4, // opin number = 1
     "num_ipin_per_opin"   -> 4
   )

   val attrs: mutable.Map[String, Any] = mutable.Map(
     "num_row" -> 4,
     "num_colum" -> 4,
     "data_width" -> 32,
     "cfg_data_width" -> 32,
     "cfg_addr_width" -> 12,
     "cfg_blk_offset" -> 2,
     "num_rf_reg" -> 1,
     "operations" -> ListBuffer("PASS", "ADD", "SUB", "MUL", "AND", "OR", "XOR"),
     "max_delay" -> 4,
     "gpe_in_from_dir" -> List(NORTHWEST, NORTHEAST, SOUTHWEST, SOUTHEAST),
     "gpe_out_to_dir" -> List(NORTHWEST, NORTHEAST, SOUTHWEST, SOUTHEAST),
     "num_track" ->1,
     "track_reged_mode" -> 1,
     "connect_flexibility" -> connect_flexibility,
     "diag_iopin_connect" -> true,
     "num_output_ib" -> 1,
     "num_input_ob" -> 2,
     "num_input_ib" -> 1,
     "num_output_ob" -> 1
   )
   //     attrs += ("gpes" -> gpes_spec)
   //     attrs += ("gibs" -> gibs_spec)
   // set default values from attr
   // the attributes in attrs are used as default values
   def setDefaultGpesSpec(): Unit = {
     val gpes_spec = ListBuffer[ListBuffer[GpeSpec]]()
     for(i <- 0 until attrs("num_row").asInstanceOf[Int]){
       gpes_spec.append(new ListBuffer[GpeSpec])
       for( j <- 0 until attrs("num_colum").asInstanceOf[Int]){
         val num_rf_reg = attrs("num_rf_reg").asInstanceOf[Int]
         val max_delay = attrs("max_delay").asInstanceOf[Int]
         val operations = attrs("operations").asInstanceOf[ListBuffer[String]]
         val fromdir = attrs("gpe_in_from_dir").asInstanceOf[List[Int]]
         val todir= attrs("gpe_out_to_dir").asInstanceOf[List[Int]]
         gpes_spec(i).append(GpeSpec(num_rf_reg, max_delay, operations, fromdir, todir))
       }
     }
     attrs("gpes") = gpes_spec
   }

   def setDefaultGibsSpec(): Unit = {
     val gibs_spec = ListBuffer[ListBuffer[GibSpec]]()
     for(i <- 0 to attrs("num_row").asInstanceOf[Int]){
       gibs_spec.append(new ListBuffer[GibSpec])
       for( j <- 0 to attrs("num_colum").asInstanceOf[Int]){
         val diag_iopin_connect = attrs("diag_iopin_connect").asInstanceOf[Boolean]
         val conf = attrs("connect_flexibility").asInstanceOf[mutable.Map[String, Int]]
         val fclist = List(conf("num_itrack_per_ipin"), conf("num_otrack_per_opin"), conf("num_ipin_per_opin"))
         gibs_spec(i).append(GibSpec(diag_iopin_connect, fclist))
       }
     }
     attrs("gibs") = gibs_spec
   }

   setDefaultGpesSpec()
   setDefaultGibsSpec()


   def loadSpec(jsonFile : String): Unit ={
     val jsonMap = IRHandler.loadIR(jsonFile)
     var gpes_spec_update = false
     var gibs_spec_update = false
     for(kv <- jsonMap){
       if(attrs.contains(kv._1)) {
         if (kv._1 == "operations") {
           attrs(kv._1) = kv._2.asInstanceOf[List[String]].to[ListBuffer]
         } else if (kv._1 == "connect_flexibility") {
           attrs(kv._1) = mutable.Map() ++ kv._2.asInstanceOf[Map[String, Int]]
         } else if (kv._1 == "gpe_in_from_dir") {
           attrs(kv._1) = kv._2.asInstanceOf[List[Int]]
         } else if (kv._1 == "gpe_out_to_dir") {
           attrs(kv._1) = kv._2.asInstanceOf[List[Int]]
         } else if (kv._1 == "gpes") {
           gpes_spec_update = true
           val gpe_2d = kv._2.asInstanceOf[List[List[Any]]]
           val gpes_spec = ListBuffer[ListBuffer[GpeSpec]]()
           for (i <- gpe_2d.indices) {
             gpes_spec.append(new ListBuffer[GpeSpec])
             val gpe_1d = gpe_2d(i)
             for (j <- gpe_1d.indices) {
               val gpemap = gpe_1d(j).asInstanceOf[Map[String, Any]]
               val num_rf_reg = gpemap("num_rf_reg").asInstanceOf[Int]
               val max_delay = gpemap("max_delay").asInstanceOf[Int]
               val operations = gpemap("operations").asInstanceOf[List[String]].to[ListBuffer]
               val fromdir = gpemap("from_dir").asInstanceOf[List[Int]]
               val todir = gpemap("to_dir").asInstanceOf[List[Int]]
               gpes_spec(i).append(GpeSpec(num_rf_reg, max_delay, operations, fromdir, todir))
             }
           }
           attrs("gpes") = gpes_spec
         } else if (kv._1 == "gibs") {
           gibs_spec_update = true
           val gib_2d = kv._2.asInstanceOf[List[List[Any]]]
           val gibs_spec = ListBuffer[ListBuffer[GibSpec]]()
           for (i <- gib_2d.indices) {
             gibs_spec.append(new ListBuffer[GibSpec])
             val gib_1d = gib_2d(i)
             for (j <- gib_1d.indices) {
               val gibmap = gib_1d(j).asInstanceOf[Map[String, Any]]
               val diag_iopin_connect = gibmap("diag_iopin_connect").asInstanceOf[Boolean]
               val fclist = gibmap("fclist").asInstanceOf[List[Int]]
               gibs_spec(i).append(GibSpec(diag_iopin_connect, fclist))
             }
           }
           attrs("gibs") = gibs_spec
         } else {
           attrs(kv._1) = kv._2
         }
       }
     }
     if(gpes_spec_update == false){ // set default values
       setDefaultGpesSpec()
     }
     if(gibs_spec_update == false){ // set default values
       setDefaultGibsSpec()
     }
   }

   def dumpSpec(jsonFile : String): Unit={
     IRHandler.dumpIR(attrs, jsonFile)
   }

 }
// object testjson extends  App{
//   IRHandler.dumpIR( attrs , "test.json")
// }



