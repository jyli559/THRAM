package ppa

object area_par {
  //  val area_mux32_map :Map[Int,Int] = Map(
  //    1 ->0,
  //    2 ->115,
  //    3->143,
  //    4->215,
  //    5->277,
  //    6->316,
  //    7->386,
  //    8->421,
  //    9->509,
  //    10->572,
  //    11->607,
  //    12->690,
  //    13->740,
  //    14->776,
  //    15->834
  //
  //  )
  val area_mux32_map :Map[Int,Int] = Map(
    1 ->0,
    2 ->115,
    3->147,
    4->221,
    5->284,
    6->324,
    7->396,
    8->443,
    9->522,
    10->587,
    11->623,
    12->707,
    13->760,
    14->796,
    15->866

  )

  //  val area_delay32_map : Map[Int, Int] = Map(
  //    1 ->867,
  //    2-> 1322,
  //    3->1700,
  //    4 -> 2157,
  //    5 ->  2555,
  //    6 ->2926,
  //    7 ->  3315
  //
  //  )
//Map[num,[maxDelay,area]] num: number of operations
  val area_delay32_map : Map[Int, Map[Int,Int]] = Map(
    1 -> Map(
      1 -> 916,
      2-> 1426,
      3-> 1830,
      4 -> 2314,
      5 ->  2771,
      6 -> 3157,
      7 ->  3654
    ),
    2 -> Map(
      1 -> 1891,
      2 -> 2388,
      3 -> 3056,
      4 -> 3665,
      5 -> 4105,
      6 -> 4649,
      7 -> 5171
    ),
//    1 ->878,
//    2-> 1332,
//    3->1736,
//    4 -> 2192,
//    5 ->  2592,
//    6 ->2979,
//    7 ->  3396

  )

  //  val area_alu32_map : Map[String, Int] = Map(
  //    "PASS" -> 60,
  //    "ADD" -> 402,
  //    "SUB" -> 340,
  //    "MUL" -> 3895,
  //    "AND" -> 83,
  //    "OR" ->83 ,
  //    "XOR" ->118 ,
  //    "SHL" -> 445,
  //    "LSHR" -> 453,
  //    "ASHR" -> 459 ,
  //    "EQ" -> 137,
  //    "NE" -> 137,
  //    "LT" -> 189,
  //    "LE" -> 187,
  //    "SEL" -> 109
  //  )

  //  val area_alu32_map : Map[String, Int] = Map(
  //      "PASS" -> 60,
  //      "ADD" -> 402,
  //      "SUB" -> 340,
  //      "MUL" -> 3895,
  //      "AND" -> 83,
  //      "OR" ->83 ,
  //      "XOR" ->118 ,
  //      "SHL" -> 445,
  //      "LSHR" -> 453,
  //      "ASHR" -> 459 ,
  //      "EQ" -> 137,
  //      "NE" -> 137,
  //      "LT" -> 189,
  //      "LE" -> 187,
  //      "SEL" -> 109
  //    )
 val op_group : Map [List[String] ,String] = Map(
    ( List("ADD","SUB" )->"group1"),
    ( List("AND","OR","XOR" )->"group2"),
    ( List("SHL","LSHR","ASHR" )->"group3"),
    ( List("MUL" )->"group4"),
    ( List("EQ","NE","LT","LE" )->"group5"),
    ( List("PASS" )->"group6")
  );
  val area_alu32_map : Map[String, Int] = Map(
    "PASS" -> 61,
    "ADD" -> 403,
    "SUB" -> 342,
    "MUL" -> 4289,
    "AND" -> 85,
    "OR" ->83 ,
    "XOR" ->118 ,
    "SHL" -> 447,
    "LSHR" -> 454,
    "ASHR" -> 463 ,
    "EQ" -> 137,//
    "NE" -> 137,
    "LT" -> 189,//
    "LE" -> 187,
    "SEL" -> 112,
    "group1" -> 403,
    "group2" -> 118,
    "group3" -> 454,
    "group4" -> 4289,
    "group5" -> 189,
    "group6" -> 61
  )
  val area_regnxt32 = 230 //暂时先忽略
  //  val area_rf32 = 338 //目前所有rf都是一个把
  val area_rf32 = 340

  val area_cfgpre32 = 11

  val area_const32 = 0

  val cycle = 5
  val reduce_rate = 0.2

}

