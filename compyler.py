import csv


def toInt(op):
    if op.isnumeric():
        return op
    if op.__contains__("$"):
        return str(int(op.split("$")[1], 16))
    if op.__contains__("@"):
        return str(int(op.split("@")[1], 8))
    if op.__contains__("%"):
        return str(int(op.split("%")[1], 2))


def idxgetn(op):
    # toma el operador que no es rr
    n = op.split(",")[0]
    if n == "":
        n = 0
    return int(n)


def idxtype(op):
    # Si dentro del operador lleva rr
    if op.__contains__("X") or op.__contains__("Y") or op.__contains__("SP") or op.__contains__("PC"):
        # toma el operador que no es rr
        n = idxgetn(op)
        # identifica el numero de formula
        if op.__contains__("["):
            return 3
        if n >= -16 and n <= 15:
            return 1
        else:
            return 2
    else:
        return 0


def idxcop(nformula, op):
    cop = ""
    rr = ""
    n = idxgetn(op)
    z = "0"
    if n > 255 or n < 256:
        z = "1"
    # signo 0 = positivo 1 = negativo
    s = "0"
    if n < 0:
        s = "1"
        max = 16
        fill = 4
        if nformula == 2:
            if z == 1:
                max = 65536
                fill = 16
            else:
                max = 256
                fill = 8
        n = (max+n)
        n = str(bin(n).replace("0b", "")).replace("-","").zfill(fill)
    else:
        n = str(bin(n).replace("0b", ""))
    if op.__contains__("X"):
        rr = "00"
    elif op.__contains__("Y"):
        rr = "01"
    elif op.__contains__("SP"):
        rr = "10"
    elif op.__contains__("PC"):
        rr = "11"
    if nformula == 1:
        cop = rr+"0"+s+n
    elif nformula == 2:
        cop = "111"+rr+"0"+z+s+n
    return int(cop, 2)


def searchinst(mnem, imm, op):
    if op == None:
        op = "0"
    loc = 0
    idxType = idxtype(op)
    hexop = int("0x0", 16)
    if len(op) > 1:
        hexstr = "".join([n for n in op if n.isdigit()])
        if op.__contains__("$"):
            hexop = int(hexstr, 16)
        else:
            hexop = int(hexstr)
    with open("tabcop.csv") as tabcop:
        tabcop = csv.reader(tabcop, delimiter=',')
        # 0 = mnemonico
        # 1 = modo de direccionamiento
        # 2 = longitud de instruccion
        # 3 = codigo de operacion
        for inst in tabcop:
            # encuentra el mnemonico
            if inst[0] == mnem:
                loc = inst[2]
                if inst[1] == "INH" and hexop > 0:
                    return ["FDR", "", inst[2]]
                # encuentra el modo de operacion correcto
                if (imm and inst[1] != "IMM") or (idxType != 0 and inst[1] != "IDX"):
                    continue
                elif hexop > 0xFF and inst[1] != "EXT" and not imm:
                    continue
                else:
                    if hexop < 0x0 or (hexop > 0xFF**(int(inst[2])-1) and inst[1] != "EXT"):
                        return ["FDR", "", inst[2]]
                    if inst[1] == "INH":
                        op = ""
                        hexop = ""
                    inst[0] += " "+op
                    inst[1] = inst[1]+"(LI="+inst[2]+")"
                    return inst
        return ["No encontrado", "", loc]

locs = ["0x0"]
vars = [] 
def paso1():
    i = 0
    with open("asms/P11.asm", "r") as asm:
        for line in asm:
            i+=1
            if len(locs) < i:
                locs.append(locs[-1])
            prevloc = locs[-1] if i > 0 else 0
            # ignora comentarios
            line = line.split(";")[0]
            if line == "":
                continue
            instruccion = line.split()
            imm = False
            if line.__contains__("ORG"):
                locs.append(hex(int("0x"+instruccion[1].split("$")[1], 16)))
                continue
            if line.__contains__("START"):
                locs.append(hex(int("0x0", 16)))
                continue
            if line.__contains__("EQU"):
                vars.append({instruccion[0]: instruccion[2]})
                continue
            if line.__contains__("DC."):
                s = 0
                ops = []
                if len(instruccion) > 1:
                    ops = instruccion[1].split(",")
                if line.__contains__("DC.B"):
                    for i in range(len(ops)):
                        s = s+1
                        ops[i] = hex(int(ops[i]))
                    if not ops:
                        s = 1
                        ops = ["00"]
                if line.__contains__("DC.W"):
                    for i in range(len(ops)):
                        s = s+2
                        ops[i] = hex(int(ops[i]))
                    if not ops:
                        s = 2
                        ops = ["00", "00"]
                locs.append(hex(int(prevloc, 16)+int(str(s), 16)))
                continue
            if line.__contains__("BSZ") or line.__contains__("ZMB"):
                ops = []
                for i in range(int(instruccion[2])):
                    ops.append("00")
                locs.append(hex(int(prevloc, 16)+int(instruccion[2])))
                continue
            if line.__contains__("FCB"):
                s = 0
                ops = instruccion[1].split(",")
                for i in range(len(ops)):
                    s = s+1
                    ops[i] = hex(int(ops[i]))
                locs.append(hex(int(prevloc, 16)+int(str(s), 16)))
                continue
            if line.__contains__("FCC"):
                cc = instruccion[1].split("/")[1]
                ops = []
                sum = 0
                for i in cc:
                    op = int(str(ord(i)))
                    ops.append(hex(op))
                    sum = sum+op
                locs.append(hex(int(prevloc, 16)+sum))
                continue
            if line.__contains__("FILL"):
                lc = instruccion[1].split(",")
                ops = []
                for i in range(int(lc[1])):
                    ops.append(hex(int(lc[0])))
                locs.append(hex(int(prevloc, 16)+int(str(lc[1]), 16)))
                continue
            inst = searchinst(instruccion[0], imm, "0")
            inst.insert(0, str(prevloc))
            op = instruccion[1] if len(instruccion) > 1 else ""
            idxType = idxtype(op)
            if line.__contains__("#"):
                imm = True
                op = op.replace("#","")
            if idxType == 0:
                op = toInt(op)
            inst = searchinst(instruccion[0], imm, op)
            if inst[0] == "No encontrado":
                vars.append({instruccion.pop(0): prevloc})
                if len(instruccion)>1:
                    op = instruccion[1] if len(instruccion) > 1 else ""
                    idxType = idxtype(op)
                    if op.__contains__("#"):
                        imm = True
                        op = op.replace("#","")
                    if idxType == 0:
                        op = toInt(op)
                    inst = searchinst(instruccion[0], imm, op)
                    if inst[0] == "No encontrado":
                        continue
                else:                    
                    continue
            if idxType != 0:
                op = idxcop(idxType, op)
            if op == "" or op == None:
                op = "0"
            locs.append(hex(int(prevloc, 16)+int(inst[2] if len(inst) > 2 else 0, 16)))
            if inst[1] != "FDR":
                inst.pop()
                inst.pop()

def paso2():
    out = []
    outcl = []
    i = -1
    with open("asms/P11.asm", "r") as asm:
        for line in asm:
            i+=1
            # ignora comentarios
            line = line.split(";")[0]
            if line == "":
                continue
            instruccion = line.split()
            imm = False
            tag = ""
            if line.__contains__(":"):
                # etiqueta
                tag = instruccion.pop(0)
            if line.__contains__("ORG"):
                outcl.append([str(locs[i]), " ".join(instruccion), ""])
                instruccion.insert(0, str(locs[i]))
                out.append(instruccion)
                continue
            if line.__contains__("START"):
                outcl.append([str(locs[i]), " ".join(instruccion), ""])
                instruccion.insert(0, str(locs[i]))
                out.append(instruccion)
                continue
            if line.__contains__("EQU"):
                outcl.append([str(locs[i]), " ".join(instruccion), ""])
                instruccion.insert(0, str(locs[i]))
                out.append(instruccion)
                continue
            if line.__contains__("DC."):
                s = 0
                ops = []
                if len(instruccion) > 1:
                    ops = instruccion[1].split(",")
                if line.__contains__("DC.B"):
                    for i in range(len(ops)):
                        s = s+1
                        ops[i] = hex(int(ops[i]))
                    if not ops:
                        s = 1
                        ops = ["00"]
                if line.__contains__("DC.W"):
                    for i in range(len(ops)):
                        s = s+2
                        ops[i] = hex(int(ops[i]))
                    if not ops:
                        s = 2
                        ops = ["00", "00"]
                instruccion.insert(0, str(locs[i]))
                outcl.append([str(locs[i]), " ".join(instruccion), " ".join(ops)])
                out.append(instruccion)
                continue
            if line.__contains__("BSZ") or line.__contains__("ZMB"):
                instruccion.insert(0, str(locs[i]))
                ops = []
                for i in range(int(instruccion[2])):
                    ops.append("00")
                outcl.append([str(locs[i]), " ".join(instruccion), " ".join(ops)])
                out.append(instruccion)
                continue
            if line.__contains__("FCB"):
                s = 0
                ops = instruccion[1].split(",")
                for i in range(len(ops)):
                    s = s+1
                    ops[i] = hex(int(ops[i]))
                instruccion.insert(0, str(locs[i]))
                outcl.append([str(locs[i]), " ".join(instruccion), " ".join(ops)])
                out.append(instruccion)
                continue
            if line.__contains__("FCC"):
                cc = instruccion[1].split("/")[1]
                instruccion.insert(0, str(locs[i]))
                ops = []
                sum = 0
                for i in cc:
                    op = int(str(ord(i)))
                    ops.append(hex(op))
                    sum = sum+op
                outcl.append([str(locs[i]), " ".join(instruccion), " ".join(ops)])
                out.append(instruccion)
                continue
            if line.__contains__("FILL"):
                lc = instruccion[1].split(",")
                ops = []
                for i in range(int(lc[1])):
                    ops.append(hex(int(lc[0])))
                instruccion.insert(0, str(locs[i]))
                outcl.append([str(locs[i]), " ".join(instruccion), " ".join(ops)])
                out.append(instruccion)
                continue
            inst = searchinst(instruccion[0], imm, "0")
            if inst[0] == "No encontrado":
                outcl.append([str(locs[i]), " ".join(instruccion), " "])
                instruccion.insert(0, str(locs[i]))
                out.append(instruccion)
                continue
            if line.__contains__("END"):
                instruccion.insert(0, str(locs[i]))
                out.append(instruccion)
                outcl.append([str(locs[i]), " ".join(instruccion), ""])
                break
            op = instruccion[1] if len(instruccion) > 1 else ""
            idxType = idxtype(op)
            if line.__contains__("#"):
                imm = True
                op = op.split("#")[1]
            if idxType == 0:
                op = toInt(op)
            for v in vars:
                if op in v:
                    op = toInt(v[op])
            inst = searchinst(instruccion[0], imm, op)
            inst.insert(0, str(locs[i]))
            if idxType != 0:
                op = idxcop(idxType, op)
            if op == "" or op == None:
                op = "0"
            outcl.append([str(locs[i]), " ".join(instruccion), inst[4],hex(int(op)) if not inst[2].__contains__("INH") else ""])
            if inst[1] != "FDR":
                inst.pop()
                inst.pop()
            out.append(inst)

        with open("lsts/P11.lst", "w") as lst:
            for line in out:
                for part in line:
                    if part.__contains__("0x"):
                        part = part.replace("0x", "")
                        part = part.zfill(4)
                    lst.write(part+"\t")
                lst.write("\n")

        with open("contlocs/P11.contloc", "w") as contloc:
            contloc.write("contloc\tLinea de programa\tcop\n")
            for line in outcl:
                for part in line:
                    if part.__contains__("0x"):
                        part = part.replace("0x", "")
                        if len(part) > 2 or part == line[0].replace("0x", ""):
                            part = part.zfill(4)
                        else:
                            part = part.zfill(2)
                    contloc.write(part+"\t\t\t")
                contloc.write("\n")

        with open("tabsims/P11.tabsim", "w") as tabsim:
            for line in vars:
                for i in line:
                    tabsim.write(i+": "+line[i])
                tabsim.write("\n")

paso1()
paso2()