import csv


def searchinst(mnem, imm, op):
    loc = 0
    hexop = int("0x0", 16)
    if len(op) > 1:
        hexstr = "".join([n for n in op if n.isdigit()])
        if op.__contains__("$"):
            hexop = int(hexstr)
        else:
            hexop = int(hexstr, 16)
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


with open("asms/P6.asm", "r") as asm:
    out = []
    loc = 0
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
            loc = hex(int("0x"+instruccion[1].split("$")[1],16))
            out.append(instruccion)
            continue
        if line.__contains__("END"):
            instruccion.insert(0, str(loc))
            out.append(instruccion)
            break
        if line.__contains__("#"):
            imm = True
        inst = searchinst(instruccion[0], imm, instruccion[1] if len(
            instruccion) > 1 else "")
        inst.insert(0, str(loc))
        loc = hex(int(loc,16)+int(inst[3] if len(inst) > 2 else 0,16))
        if inst[1] != "FDR":
            inst.pop()
            inst.pop()
        out.append(inst)

    with open("lsts/P6.lst", "w") as lst:
        for line in out:
            for part in line:
                lst.write(part+"\t")
            lst.write("\n")
