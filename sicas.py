#!/usr/bin/python

import argparse
import os
from sicxe import *

class AssembleError(BaseException):
    pass

class Line:
    def __init__(self, assembly, lineno):
        self.assembly = assembly
        self.code = ""
        self.lineno = lineno
        self.fmt = 0
        self.loc = 0
    
    def __str__(self):
        return self.assembly

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
        return (self.lineno, locfmt, self.assembly.expandtabs(8), codefmt)

class Program:
    def __init__(self, source):
        self.source = os.path.basename(source)
        self.name = ''
        self.start_addr = 0x0
        self.started = False
        self.LOCCTR = 0
        self.lineno = 0
        self.content = list(Line(line.strip('\n'), lineno) for lineno, line in enumerate(open(source, "r").readlines(), 1))
        self.symtab = PRELOAD_SYMTAB.copy()

    def error(self, msg):
        print("\n%s:%s" % (self.source, str(self.lineno)) + "  " + str(self.content[self.lineno - 1]))
        print("Error : " + msg + '\n')
        raise AssembleError

    def assemble(self):
        for line in self.content:
            program.lineno += 1
            line.loc = self.LOCCTR
            if line.assembly[0] == '.':
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

    def listing(self):
        print("Lineno  LOCCTR  Source Statement              Object Code")
        for line in self.content:
            print("%-8d%-8s%-30s%-10s" % line.listing_tuple())

    def current_line(self):
        return self.content[self.lineno - 1]

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
        try:
            program.start_addr = int(tokens[2], 16)
        except ValueError:
           program.error("%s is an invalid value for starting address (hexadecimal is required)." % tokens[2])
        program.started = True
        program.current_line().loc = None

def handler_END(program_inf, tokens):
    program.current_line().loc = None
    pass

def handler_BYTE(program_inf, tokens):
    if tokens[0] == "BYTE":
        program.error("Must specify a label for the allocated space.")
    elif tokens[2] == "BYTE":
        program.error("Multiple label were specified for BYTE.")
    elif len(tokens) < 3:
        program.error("Requires an value for BYTE.")

    "CHECK LABEL NAME"
    value = tokens[2]
    if value[0] == 'C':
        "CHECK QUOTION MARKS"
        program.symtab[tokens[0]] = program.LOCCTR
        program.LOCCTR += len(tokens[2][2:-1])
    elif value[0] == 'X':
        try:
            "CHECK QUOTION MARKS"
            program.symtab[tokens[0]] = program.LOCCTR
            program.LOCCTR += 1
        except ValueError:
            program.error("The \"X\" requires a hex value, but %s is not." % value[2:-1])

def handler_WORD(program_inf, tokens):
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
    program.symtab[tokens[0]] = program.LOCCTR
    program.LOCCTR += int(tokens[2]) * 3

def handler_RESB(program_inf, tokens):
    if tokens[0] == "RESB":
        program.error("Must specify a label for the allocated space.")
    elif tokens[2] == "RESB":
        program.error("Multiple label were specified for RESB.")
    elif len(tokens) < 3:
        program.error("Requires an length for RESB.")

    "CHECK LABEL NAME"
    "LENGTH IS DECIMAL"
    program.symtab[tokens[0]] = program.LOCCTR
    program.LOCCTR += int(tokens[2])

def handler_BASE(program_inf, tokens):
    program.current_line().loc = None
    pass

DIRTAB = {
    "START" : handler_START,
    "END"   : handler_END,
    "BYTE"  : handler_BYTE,
    "WORD"  : handler_WORD,
    "RESB"  : handler_RESB,
    "RESW"  : handler_RESW,
    "BASE"  : handler_BASE,
}

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
            # without prefix
            if token in OPTAB:
                inst = token
            # with prefix
            elif token[1:] in OPTAB:
                prefix = token[0]
                inst = token[1:]
                if prefix != '+':
                    program.error("invalid instruction prefix \"%s\"" % prefix)
                elif not (OPTAB[inst].inf & FORMAT4):
                    program.error("%s does not support format 4." % inst)
                else:
                    fmt = 4
            else:
                "CHECK LABEL"
                program.symtab[tokens[0]] = program.LOCCTR
                continue
        # instruction met (operand)
        elif operand == "":
            operand = token
        else:
            operand2 = token

    # compute the instruction format
    if fmt != 4:
        mask = OPTAB[inst].inf & (FORMAT1 | FORMAT2 | FORMAT3)
        while mask != 0b1000:
            mask >>= 1
            fmt += 1
        fmt = (5 - fmt)
    program.LOCCTR += fmt

    # validate the foramt
    if operand2 != "" and fmt != 2:
        program.error("Only format 2 insturctions allow two operands")

    # codegen
    code = OPTAB[inst].opcode

    # parse the prefix for format 3 & 4 instructions
    if (fmt == 3 or fmt == 4) and inst != "RSUB":
        prefix = ""
        # parse the operand
        if not operand[0].isalnum():
            prefix = operand[0]
            operand = operand[1:]

        # not sure if no prefix has to mask
        mask = DEFAULT_ADDR
        if prefix == '#':
            mask = IMM_ADDR
        elif prefix == '@':
            mask = INDR_ADDR
        elif prefix != "":
            program.error("Unrecognized addressing prefix %s" % prefix)
        code |= mask << (BYTESIZE * 2)
    # handle instruction(s) which has no operand
    elif inst == "RSUB":
        code |= DEFAULT_ADDR << (BYTESIZE * 2)
    
    if fmt == 4:
        code <<= BYTESIZE
        code |= EXTEND_FMT

    if operand.isnumeric():
        code |= int(operand)
    elif operand in program.symtab:
        if fmt == 2:
            # some format 2 instruction accept 2 operand
            "VALIDATE FORMAT2"
            code |= program.symtab[operand] << 4
        else:
            code |= program.symtab[operand]
    else:
        pass

    program.content[program.lineno - 1].fmt = fmt
    program.content[program.lineno - 1].code = code
    return True

def has_labels(program_inf, tokens):
    pass


if __name__ == "__main__":
    # Parse the arguments
    parser = argparse.ArgumentParser(description="A Python SIC/XE Assembler")
    parser.add_argument('-o', '--output', help='the output file.', default='a.out')
    parser.add_argument('-L', '--listing', help='generate assembly listing.', action='store_true')
    parser.add_argument('input', nargs='+', help='the source assembly file(s).')
    args = parser.parse_args()
    input_files = args.input
    listing = args.listing

    print("SIC/XE Assembler")

    # Open files in the list
    for file_name in input_files:
        program = Program(file_name)
        try:
            print("\nStarting assemble %s ..." % program.source)
            program.assemble()
            print("Done.")
            if listing:
                program.listing()
            symlist = list(program.symtab.items())
            symlist.sort(key=lambda x : (x[1], x[0]))
            for x in symlist:
                print("%s\t\t: 0x%04X" %(x[0], x[1]))
        except AssembleError:
            print("Assemble failed.")
            continue
