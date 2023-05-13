def paramspace() -> list:
    params = [
        {'name' : 'num_row',               'type' : 'int', 'lb' : 4, 'ub' : 16},
        {'name' : 'num_colum',             'type' : 'int', 'lb' : 4, 'ub' : 16},
        {'name' : 'num_track',             'type' : 'int', 'lb' : 1, 'ub' : 6},
        {'name' : 'max_delay',             'type' : 'int', 'lb' : 2, 'ub' : 7}, 
        {'name' : 'num_output_ib',         'type' : 'int', 'lb' : 1, 'ub' : 2},
        {'name' : 'num_input_ob',          'type' : 'int', 'lb' : 2, 'ub' : 2},
        {'name' : 'num_input_ib',          'type' : 'int', 'lb' : 1, 'ub' : 2},
        {'name' : 'num_output_ob',         'type' : 'int', 'lb' : 1, 'ub' : 1}, 
        {'name' : 'num_itrack_per_ipin',   'type' : 'int', 'lb' : 2, 'ub' : 8},
        {'name' : 'num_otrack_per_opin',   'type' : 'int', 'lb' : 2, 'ub' : 8},
        {'name' : 'num_ipin_per_opin',     'type' : 'int', 'lb' : 2, 'ub' : 8},
        {'name' : 'num_itrack_per_ipin_l', 'type' : 'int', 'lb' : 2, 'ub' : 4},
        {'name' : 'num_otrack_per_opin_l', 'type' : 'int', 'lb' : 2, 'ub' : 4},
        {'name' : 'num_ipin_per_opin_l',   'type' : 'int', 'lb' : 2, 'ub' : 4},
        {'name' : 'cfg_addr_width',        'type' : 'int', 'lb' : 12, 'ub' : 12},
        {'name' : 'cfg_blk_offset',        'type' : 'int', 'lb' : 1, 'ub' : 2},
        {'name' : 'diag_iopin_connect',    'type' : 'bool'},
        {'name' : 'diag_iopin_connect_l',  'type' : 'bool'}
    ]
    return params

def otherArchPara() -> dict:
    op = { "operations" : [ "PASS", "ADD", "SUB", "MUL", "AND", "OR", "XOR","SHL","LSHR","ASHR","EQ","NE","LT","LE" ],
            "track_reged_mode":1,
            "num_rf_reg":1,
            "data_width":32,
            "cfg_data_width":32,
            "gpe_in_from_dir" : [ 4, 5, 7, 6 ],
            "gpe_out_to_dir" : [ 4, 5, 7, 6 ]
        }
    return op

def formatSpec(sample : dict) -> dict:
    connect_flexibility = {
        'num_otrack_per_opin' : sample['num_otrack_per_opin'],
        'num_itrack_per_ipin' : sample['num_itrack_per_ipin'],
        'num_ipin_per_opin' : sample['num_ipin_per_opin']
    }
    del sample['num_otrack_per_opin']
    del sample['num_itrack_per_ipin']
    del sample['num_ipin_per_opin']
    sample['connect_flexibility'] = connect_flexibility
    return sample

def addGIB(row, col, diag_iopin_connect_h, diag_iopin_connect_l, fclist_h,fclist_l):
    gib = []
    for i in range(row+1):
        gib.append([])
        if(i==0 or i==row):
            for j in range(col+1):
                gib[i].append({"diag_iopin_connect" : diag_iopin_connect_l,"fclist" : fclist_l})
        else:
            for j in range(col+1):
                if(j==0 or j==col):
                    gib[i].append({"diag_iopin_connect" : diag_iopin_connect_l,"fclist" : fclist_l})
                else:
                    gib[i].append({"diag_iopin_connect" : diag_iopin_connect_h,"fclist" : fclist_h})
    return gib


def addGPE(row, col, add, mul, logic, comp, maxDelay):
    gpe = []
    a = int(row*col*add)
    m = int(row*col*mul)
    l = int(row*col*logic)
    c = int(row*col*comp)
    print("ADD need:",a," ","MUL need:",m," ","LOGIC need:",l," ","COMP need:",c)
    atemp = 0
    mtemp = 0
    ltemp = 0
    ctemp = 0
    watch = [[0]*col for i in range(row)]
    for i in range(row):
        gpe.append([])
        for j in range(col):
            if((i+1)%2==0):
                if((j+1)%2!=0):
                    gpe[i].append( {
                    "num_rf_reg" : 1,
                    "operations" : [ "PASS", "ADD", "SUB"],
                    "from_dir" : [ 4, 5, 7, 6 ],
                    "to_dir" : [ 4, 5, 7, 6 ],
                    "max_delay" : maxDelay
                    })
                    atemp = atemp+1
                else:
                    gpe[i].append( {
                    "num_rf_reg" : 1,
                    "operations" : [ "PASS", "MUL"],
                    "from_dir" : [ 4, 5, 7, 6 ],
                    "to_dir" : [ 4, 5, 7, 6 ],
                    "max_delay" : maxDelay
                    })
                    mtemp = mtemp+1
                    watch[i][j] = 1
            else:
                if((j+1)%2!=0):
                    gpe[i].append( {
                    "num_rf_reg" : 1,
                    "operations" : [ "PASS", "MUL"],
                    "from_dir" : [ 4, 5, 7, 6 ],
                    "to_dir" : [ 4, 5, 7, 6 ],
                    "max_delay" : maxDelay
                    })
                    mtemp = mtemp+1
                    watch[i][j] = 1
                else:
                    gpe[i].append( {
                    "num_rf_reg" : 1,
                    "operations" : [ "PASS", "ADD","SUB"],
                    "from_dir" : [ 4, 5, 7, 6 ],
                    "to_dir" : [ 4, 5, 7, 6 ],
                    "max_delay" : maxDelay
                    })
                    atemp = atemp+1
    
    for i in range (row-1):
        if(mtemp >= m):
            for j in range(col-1):
                if(gpe[i+1][j+1]["operations"]==[ "PASS","MUL"]):
                    gpe[i+1][j+1]["operations"]=[ "PASS", "ADD","SUB","MUL"]
                    atemp = atemp+1
                    watch[i+1][j+1]=2
                    if(atemp >= a):
                        break
            else:
                continue
            break
        else:
            for j in range(col-1):
                if(gpe[i+1][j+1]["operations"]==[ "PASS","ADD","SUB"]):
                    gpe[i+1][j+1]["operations"]=[ "PASS", "ADD","SUB","MUL"]
                    mtemp = mtemp+1
                    watch[i+1][j+1]=2
                    if(mtemp >= m-2):
                        break
            else:
                continue
            break

    if(l != 0 or c != 0):
        for i in range (row-1):
            for j in range(col-1):
                if((j+1)%2 == 0 ):
                    gpe[i+1][j+1]["operations"] = gpe[i+1][j+1]["operations"] + ["AND", "OR", "XOR","SHL","LSHR","ASHR"]
                    ltemp = ltemp + 1
                    if(ltemp>=l):
                        break
                else:
                    gpe[i+1][j+1]["operations"] = gpe[i+1][j+1]["operations"] + ["EQ","NE","LT","LE"]
                    ctemp = ctemp + 1
                    if(ctemp>=c):
                        break
            else:
                continue
            break

    print("ADD placed:",atemp," ","MUL placed:",mtemp," ","LOGIC placed:",ltemp," ","COMP placed:",ctemp)
    return gpe

def genSpec(spec : dict, hete : list):
    add   = float(hete[0][0])
    mul   = float(hete[1][0])
    logic = float(hete[2][0])
    comp  = float(hete[3][0])

    track = spec['num_track']
    num_itrack_per_ipin_h = spec["connect_flexibility"]["num_itrack_per_ipin"] if (spec["connect_flexibility"]["num_itrack_per_ipin"] <= 2*track) else 2*track
    num_otrack_per_opin_h = spec["connect_flexibility"]["num_otrack_per_opin"] if (spec["connect_flexibility"]["num_otrack_per_opin"] <= 2*track) else 2*track
    fclist_h = []
    fclist_h.append(num_itrack_per_ipin_h)
    fclist_h.append(num_otrack_per_opin_h)
    fclist_h.append(spec["connect_flexibility"]["num_ipin_per_opin"])

    num_itrack_per_ipin_l = spec["num_itrack_per_ipin_l"] if (spec["num_itrack_per_ipin_l"] <= 2*track) else 2*track
    num_otrack_per_opin_l = spec["num_otrack_per_opin_l"] if (spec["num_otrack_per_opin_l"] <= 2*track) else 2*track
    fclist_l = []
    fclist_l.append(num_itrack_per_ipin_l)
    fclist_l.append(num_otrack_per_opin_l)
    fclist_l.append(spec["num_ipin_per_opin_l"])

    row = spec["num_row"]
    col = spec["num_colum"]
    maxDelay = spec["max_delay"]
    diag_iopin_connect_h = spec["diag_iopin_connect"]
    diag_iopin_connect_l = spec["diag_iopin_connect_l"]
    GIB = {"gibs":addGIB(row,col,diag_iopin_connect_h,diag_iopin_connect_l,fclist_h,fclist_l)}
    spec.update(**GIB)
    GPE = {"gpes":addGPE(row,col,add,mul,logic,comp,maxDelay)}
    spec.update(**GPE)
    return spec