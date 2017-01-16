#!/usr/bin/python

import argparse
import os
from sicxe import *

class AssembleError(BaseException):
    pass

class Line:
    def __init__(self, assembly, lineno):
        self.src = assembly
        self.assembly = assembly.split('.')[0]
        self.code = ""
        self.lineno = lineno
        self.fmt = 0
        self.loc = None
        self.base = -1
    
    def __str__(self):
        return self.assembly

    def __repr__(self):
        return str(self)

    def tokenize(self):
        return self.assembly.split()

    def listing_tuple(self):
        locfmt = ""
        codefmt = ""
        if self.loc != None:
            locfmt = "%04X" % self.loc
        if self.code != "":
            codefmt = "%%0%dX" % (self.fmt * 2)
            codefmt = codefmt % self.code
        return (self.lineno, locfmt, self.src.expandtabs(8), codefmt)

class Program:
    def __init__(self, source):
        self.source = os.path.basename(source)
        self.name = ''
        self.start_addr = 0x0
        self.start_exec = -1
        self.started = False
        self.LOCCTR = 0
        self.lineno = 0
        self.content = list(Line(line.strip('\n'), lineno) for lineno, line in enumerate(open(source, "r").readlines(), 1))
        self.symtab = PRELOAD_SYMTAB.copy()
        self.base = -1

    def error(self, msg, line = None):
        if line == None:
            line = self.current_line()
        print("\n%s:%s" % (self.source, str(line.lineno)) + "  " + str(line))
        print("Error : " + msg + '\n')
        raise AssembleError

    def assemble(self):
        for line in self.content:
            program.lineno += 1
            line.loc = self.LOCCTR
            line.base = self.base
            if line.assembly == '':
                line.loc = None
                continue

            tokens = line.tokenize()

            self.lineno = line.lineno
            if has_directives(self, tokens):
                continue
            elif has_instructions(self, tokens):
                continue
            else:
                program.error("Except a directive, opcde or label.")

    def listing(self, filename):
        stmt_len = len(max(self.content, key=lambda stmt: len(stmt.src)).src) + 10
        fmt = "\n%%-8s%%-8s%%-%ds%%-10s" % stmt_len
        with open(filename, "w") as f:
            f.write(fmt % ("Lineno", "LOCCTR", "Source Statements", "Object Code"))
            for line in self.content:
                f.write(fmt % line.listing_tuple())

    def current_line(self):
        return self.content[self.lineno - 1]

    def output(self, file_name):
        with open(file_name, "w") as f:
            f.write("H%-6s%06X%06X" % (self.name, self.start_addr, self.LOCCTR - self.start_addr))
            M_list = []
            newrecord = True
            colcount = 0
            i = 0
            line = self.content[0]
            last = line
            brk = False
            while i < len(self.content):
                line = self.content[i]
                if newrecord:
                    if line.loc == None:
                        i += 1
                        continue
                    rec = "\nT%06XLL" % line.loc
                    newrecord = False
                    colcount = 0

                # INSTRUCTIONS OR BYTE/WORD
                if line.code != "":
                    codefmt = "%%0%dX" % (line.fmt * 2)
                    code = codefmt % line.code
                # other directives or empty line
                else:
                    i += 1
                    continue

                # check if have to break the record
                # too far to last instruction
                if line.code != "" and line.loc != None and last.code != "" and (line.loc > last.loc + last.fmt * 2) and not brk:
                    newrecord = True
                    brk = True
                # exceed record length
                elif colcount + len(code) > 60:
                    newrecord = True

                # need to relocate
                if line.fmt == 4 and line.code & ((DEFAULT_ADDR ^ IMM_ADDR) << BYTESIZE):
                    M_list.append(line)

                if newrecord:
                    rec = rec.replace("LL", "%02X" % (colcount // 2))
                    f.write(rec)
                    continue
                else:
                    colcount += len(code)
                    rec += code
                    last = line
                    i += 1
                    if brk:
                        brk = False
            rec = rec.replace("LL", "%02X" % (colcount // 2))
            f.write(rec)
            for line in M_list:
                f.write("\nM%06X%02X" % (line.loc + 1, 5))
            f.write("\nE%06X" % self.start_exec)


def handler_START(program, tokens):
    if "START" in tokens:
        # validate format
        if program.started:
            program.error("Multiple START detected.")
        elif tokens[0] == "START":
            program.error("Must specify a name for program before START.")
        elif tokens[2] == "START":
            program.error("Multiple tokens were specified before START.")
        if "CHECK PROGRAM NAME FORMAT" != 0:
            pass

        program.name = tokens[0]
        if len(program.name) > 6:
            program.error("Program name must not longer than 6 characters.")
        try:
            program.start_addr = int(tokens[2], 16)
        except ValueError:
            program.error("%s is an invalid value for starting address (hexadecimal is required)." % tokens[2])
        program.started = True
        program.current_line().loc = None

def handler_END(program, tokens):
    program.current_line().loc = Nones

def handler_BYTE(program, tokens):
    if tokens[0] == "BYTE":
        program.error("Must specify a label for the allocated space.")
    elif tokens[2] == "BYTE":
        program.error("Multiple label were specified for BYTE.")
    elif len(tokens) < 3:
        program.error("Requires an value for BYTE.")

    "CHECK LABEL NAME"
    value = tokens[2]
    if value[0] == 'C':
        "CHECK MATCHING QUOTION MARKS"
        hexstr = ''.join(["%2X" % c for c in value[2:-1].encode()])
        program.current_line().code = int(hexstr, 16)
        program.current_line().fmt = len(value[2:-1])
        if tokens[0] in program.symtab and type(program.symtab[tokens[0]]) == list:
            fill_forward(program.symtab[tokens[0]], program.LOCCTR, program)
        program.symtab[tokens[0]] = program.LOCCTR
        program.LOCCTR += len(value[2:-1])
    elif value[0] == 'X':
        try:
            "CHECK QUOTION MARKS"
            program.current_line().code = int(value[2:-1], 16)
            program.current_line().fmt = 1
            if tokens[0] in program.symtab and type(program.symtab[tokens[0]]) == list:
                fill_forward(program.symtab[tokens[0]], program.LOCCTR, program)
            program.symtab[tokens[0]] = program.LOCCTR
            program.LOCCTR += 1
        except ValueError:
            program.error("The \"X\" requires a hex value, but %s is not." % value[2:-1])

def handler_WORD(program, tokens):
    pass

def handler_RESW(program, tokens):
    if tokens[0] == "RESW":
        program.error("Must specify a label for the allocated space.")
    elif tokens[2] == "RESW":
        program.error("Multiple label were specified for RESW.")
    elif len(tokens) < 3:
        program.error("Requires an length for RESW.")

    "CHECK LABEL NAME"
    "LENGTH IS DECIMAL"
    if tokens[0] in program.symtab and type(program.symtab[tokens[0]]) == list:
        fill_forward(program.symtab[tokens[0]], program.LOCCTR, program)
    program.symtab[tokens[0]] = program.LOCCTR
    program.LOCCTR += int(tokens[2]) * 3

def handler_RESB(program, tokens):
    if tokens[0] == "RESB":
        program.error("Must specify a label for the allocated space.")
    elif tokens[2] == "RESB":
        program.error("Multiple label were specified for RESB.")
    elif len(tokens) < 3:
        program.error("Requires an length for RESB.")

    "CHECK LABEL NAME"
    "LENGTH IS DECIMAL"
    if tokens[0] in program.symtab and type(program.symtab[tokens[0]]) == list:
        fill_forward(program.symtab[tokens[0]], program.LOCCTR, program)
    program.symtab[tokens[0]] = program.LOCCTR
    program.LOCCTR += int(tokens[2])

def handler_BASE(program, tokens):
    program.base = tokens[1]
    program.current_line().loc = None

def handler_NOBASE(program, tokens):
    program.base = -1
    program.current_line().loc = None

DIRTAB = {
    "START" : handler_START,
    "END"   : handler_END,
    "BYTE"  : handler_BYTE,
    "WORD"  : handler_WORD,
    "RESB"  : handler_RESB,
    "RESW"  : handler_RESW,
    "BASE"  : handler_BASE,
    "NOBASE" : handler_NOBASE,
}

def fill_forward(fwd_lst, addr, program):
    for line, ref, reftype in fwd_lst:
        if reftype == REF_OP:
            if line.fmt == 3:
                disp = (addr - (line.loc + line.fmt))
                if -2048 <= disp < 2048:
                    line.code |= (disp & 0xFFF) | PC_RELATIVE
                elif line.base != -1:
                    # if base is defined
                    if line.base in program.symtab and type(program.symtab[line.base]) != list:
                        disp = (program.symtab[operand] - program.symtab[line.base])
                        if 0 <= disp < 4096:
                            code |= (disp & 0xFFF) | BASE_RELATIVE
                        else:
                            program.error("no enough length to hold the displacement, try format 4.", line)
                    # forward base reference
                    elif line.base in program.symtab:
                        program.symtab[line.base].append((program.current_line(), REF_BASE))
                    else:
                        program.symtab[line.base] = [(program.current_line(), REF_BASE)]
                else:
                    program.error("no enough length to hold the displacement, try format 4.", line)
            elif line.fmt == 4:
                line.code |= addr
        elif reftype == REF_BASE:
            disp = program.symtab[ref] - addr
            if 0 <= disp < 4096:
                line.code |= (disp & 0xFFF) | BASE_RELATIVE
            else:
                program.error("no enough length to hold the displacement, try format 4.", line)



def has_directives(program, tokens):
    for token in tokens:
        if token in DIRTAB:
            DIRTAB[token](program, tokens)
            return True
    return False

def has_instructions(program, tokens):
    if len(tokens) == 0:
        return False

    inst = ""
    operand = ""
    operand2 = ""
    fmt = 0
    for idx, token in enumerate(tokens):
        # instruction hasn't meet yet (instruction or label)
        if inst == "":
            # instruction without prefix
            if token in OPTAB:
                inst = token
            # instruction with prefix
            elif token[1:] in OPTAB:
                prefix = token[0]
                inst = token[1:]
                if prefix != '+':
                    program.error("invalid instruction prefix \"%s\"." % prefix)
                elif not (OPTAB[inst].inf & FORMAT4):
                    program.error("%s does not support format 4." % inst)
                else:
                    fmt = 4
            # is label
            else:
                label = tokens[0]
                # check label format
                if label in OPTAB:
                    program.error("symbol name \"%s\" is same as an insturction." % label)
                elif label in program.symtab and type(program.symtab[label]) != list:
                    program.error("redefined symbol \"%s\"." % label)
                elif label in program.symtab:
                    fill_forward(program.symtab[label], program.LOCCTR, program)
                program.symtab[label] = program.LOCCTR
                continue
        # instruction met (operand)
        else:
            if token.find(',') != -1:
                operand, operand2, *dummy = token.split(',')
                if len(dummy) > 1:
                    program.error("too many operands")
            else:
                operand = token

    # compute the instruction format
    if fmt != 4:
        mask = OPTAB[inst].inf & (FORMAT1 | FORMAT2 | FORMAT3)
        while mask != 0b1000:
            mask >>= 1
            fmt += 1
        fmt = (5 - fmt)

    # validate the foramt
    if (operand2 != "" and fmt != 2) and operand2 != 'X':
        program.error("Only format 2 insturctions allow two operands.")
    if fmt < 3 and operand2 == 'X':
        program.error("Only format 3 and 4 allow indexed addresing")

    # generate opcode
    code = OPTAB[inst].opcode
    # parse the prefix for format 3 & 4 instructions
    if (fmt == 3 or fmt == 4) and inst != "RSUB":
        prefix = ""
        # parse the operand
        if not operand[0].isalnum():
            prefix = operand[0]
            operand = operand[1:]

        # generate the addressing mask (nixbpe)
        mask = DEFAULT_ADDR
        if prefix == '#':
            mask = IMM_ADDR
        elif prefix == '@':
            mask = INDR_ADDR
        elif prefix != "":
            program.error("Unrecognized addressing prefix \"%s\"." % prefix)

        if operand2 == 'X':
            mask |= INDEX_ADDR
        if fmt == 4:
            mask |= EXTEND_FMT

        code |= mask
    # handle format 3/4 instruction which has no operand
    elif inst == "RSUB":
        code |= DEFAULT_ADDR
    
    # shift format 4 instructions
    if fmt == 4:
        code <<= BYTESIZE

    # generate operand
    if inst != "RSUB":
        if operand.isnumeric():
            operand = int(operand)
            if (fmt == 3 and operand > 2**12 - 1) or (fmt == 4 and operand > 2**20 - 1):
                program.error("operand with value = %d is out of range." % operand)
            else:
                code |= operand
        elif operand in program.symtab and type(program.symtab[operand]) != list:
            if fmt == 2:
                # some format 2 instruction accept 2 operands
                if inst in ["ADDR", "COMPR", "DIVR", "MULR", "RMO", "SHIFTL", "SHIFTR", "SUBR"]:
                    code |= program.symtab[operand2]
                "VALIDATE FORMAT2"
                code |= program.symtab[operand] << 4
            elif fmt == 3:
                disp = (program.symtab[operand] - (program.LOCCTR + fmt))
                # try to use PC-realtive
                if -2048 <= disp < 2048:
                    code |= (disp & 0xFFF) | PC_RELATIVE
                # try to use base-relative
                elif program.base != -1:
                    # if base is defined
                    if program.base in program.symtab and type(program.symtab[program.base]) != list:
                        disp = (program.symtab[operand] - program.symtab[program.base]) & 0xFFF
                        if 0 <= disp < 4096:
                            code |= (disp & 0xFFF) | BASE_RELATIVE
                        else:
                            program.error("no enough length to hold the displacement, try format 4.")
                    # forward base reference
                    elif program.base in program.symtab:
                        program.symtab[program.base].append((program.current_line(), operand, REF_BASE))
                    else:
                        program.symtab[program.base] = [(program.current_line(), operand, REF_BASE)]

                else:
                    program.error("no enough length to hold the displacement, try format 4.")
            elif fmt == 4:
                code |= program.symtab[operand]
        elif operand in program.symtab:
            program.symtab[operand].append((program.current_line(), operand, REF_OP))
        else:
            program.symtab[operand] = [(program.current_line(), operand, REF_OP)]

    # find the first executable location
    if program.start_exec == -1:
        program.start_exec = program.LOCCTR
    program.LOCCTR += fmt
    program.current_line().fmt = fmt
    program.current_line().code = code
    return True

if __name__ == "__main__":
    # Parse the arguments
    parser = argparse.ArgumentParser(description="A Python SIC/XE Assembler")
    parser.add_argument('-o', '--output', help='the output file.', default='a.out')
    parser.add_argument('-L', '--listing', help='generate assembly listing.')
    parser.add_argument('input', nargs='+', help='the source assembly file(s).')
    args = parser.parse_args()

    print("SIC/XE Assembler")

    # Open files in the list
    for file_name in args.input:
        program = Program(file_name)
        try:
            print("\nStarting assemble %s ..." % program.source)
            program.assemble()
            print("Done.")
            if args.listing:
                program.listing(args.listing)
            program.output(args.output)
        except AssembleError:
            print("Assemble failed.")
            continue

