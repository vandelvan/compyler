import csv


def searchinst(mnem, imm, op):
    loc = 0
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
                if imm and inst[1] != "IMM":
                    continue
                elif hexop > 0xFF and inst[1] != "EXT" and not imm:
                    continue
                else:
                    if hexop < 0x0 or (hexop > 0xFF**(int(inst[2])-1) and inst[1] != "EXT"):
                        return ["FDR", "", inst[2]]
                    inst[0] += " "+op
                    inst[1] = inst[1]+"(LI="+inst[2]+")"
                    return inst
        return ["No encontrado", "", loc]


with open("asms/P7.asm", "r") as asm:
    out = []
    outcl = []
    loc = 0
    vars = []
    for line in asm:
        # ignora comentarios
        line = line.split(";")[0]
        instruccion = line.split()
        imm = False
        tag = ""
        if line.__contains__(":"):
            # etiqueta
            tag = instruccion.pop(0)
        if line.__contains__("ORG"):
            outcl.append([str(loc), " ".join(instruccion), ""])
            loc = hex(int("0x"+instruccion[1].split("$")[1], 16))
            out.append(instruccion)
            continue
        if line.__contains__("START"):
            instruccion.insert(0, str(loc))
            outcl.append([str(loc), " ".join(instruccion), ""])
            loc = hex(int("0x0", 16))
            out.append(instruccion)
            continue
        if line.__contains__("EQU"):
            vars.append({instruccion[0]: instruccion[2]})
            out.append(instruccion)
            outcl.append([str(loc), " ".join(instruccion), ""])
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
            instruccion.insert(0, str(loc))
            outcl.append([str(loc), " ".join(instruccion), " ".join(ops)])
            loc = hex(int(loc, 16)+int(str(s), 16))
            out.append(instruccion)
            continue
        if line.__contains__("BSZ") or line.__contains__("ZMB"):
            instruccion.insert(0, str(loc))
            ops = []
            for i in range(int(instruccion[2])):
                ops.append("00")
            outcl.append([str(loc), " ".join(instruccion), " ".join(ops)])
            loc = hex(int(loc, 16)+int(instruccion[2]))
            out.append(instruccion)
            continue
        if line.__contains__("FCB"):
            s = 0
            ops = instruccion[1].split(",")
            for i in range(len(ops)):
                s = s+1
                ops[i] = hex(int(ops[i]))
            instruccion.insert(0, str(loc))
            outcl.append([str(loc), " ".join(instruccion), " ".join(ops)])
            loc = hex(int(loc, 16)+int(str(s), 16))
            out.append(instruccion)
            continue
        if line.__contains__("FCC"):
            cc = instruccion[1].split("/")[1]
            instruccion.insert(0, str(loc))
            ops = []
            sum = 0
            for i in cc:
                op = int(str(ord(i)))
                ops.append(hex(op))
                sum = sum+op
            outcl.append([str(loc), " ".join(instruccion), " ".join(ops)])
            loc = hex(int(loc, 16)+sum)
            out.append(instruccion)
            continue
        if line.__contains__("FILL"):
            lc = instruccion[1].split(",")
            ops = []
            for i in range(int(lc[1])):
                ops.append(hex(int(lc[0])))
            instruccion.insert(0, str(loc))
            outcl.append([str(loc), " ".join(instruccion), " ".join(ops)])
            loc = hex(int(loc, 16)+int(str(lc[1]), 16))
            out.append(instruccion)
            continue
        inst = searchinst(instruccion[0], imm, "0")
        if inst[0] == "No encontrado":
            vars.append({instruccion[0]: instruccion[1]})
        if line.__contains__("END"):
            instruccion.insert(0, str(loc))
            out.append(instruccion)
            outcl.append([str(loc), " ".join(instruccion), ""])
            break
        op = instruccion[1] if len(instruccion) > 1 else ""
        if line.__contains__("#"):
            imm = True
            op = op.split("#")[1]
        for i in vars:
            if op in i:
                op = int(i[op])
        inst = searchinst(instruccion[0], imm, op)
        if inst[0] == "No encontrado":
            vars.append({instruccion[0]: instruccion[1]})
        inst.insert(0, str(loc))
        outcl.append([str(loc), " ".join(instruccion), hex(int(op))])
        loc = hex(int(loc, 16)+int(inst[3] if len(inst) > 2 else 0, 16))
        if inst[1] != "FDR":
            inst.pop()
            inst.pop()
        out.append(inst)

    with open("lsts/P7.lst", "w") as lst:
        for line in out:
            for part in line:
                lst.write(part+"\t")
            lst.write("\n")

    with open("contlocs/P7.contloc", "w") as contloc:
        contloc.write("contloc\tLinea de programa\tcop\n")
        for line in outcl:
            for part in line:
                contloc.write(part+"\t\t\t")
            contloc.write("\n")

    with open("tabsims/P7.tabsim", "w") as tabsim:
        for line in vars:
            for i in line:
                tabsim.write(i+": "+line[i])
            tabsim.write("\n")
