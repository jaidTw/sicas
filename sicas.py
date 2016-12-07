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
    
    def __str__(self):
        return self.assembly

    def tokenize(self):
        return self.assembly.split()

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
            if line.assembly[0] == '.':
                continue
            #print("%04X\t %s" % (self.LOCCTR, line))
            tokens = line.tokenize()

            self.lineno = line.lineno
            if has_directives(self, tokens):
                continue
            elif has_instructions(self, tokens):
                continue
            else:
                program.error("Except a directive, opcde or label.")

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

def handler_END(program_inf, tokens):
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
    for idx, token in enumerate(tokens):
        prefix = ""
        inst = ""
        fmt = 0
        if token in OPTAB:
            inst = token

            if idx == 1:
                "CHECK LABEL"
                program.symtab[tokens[0]] = program.LOCCTR
        elif token[1:] in OPTAB:
            prefix = token[0]
            inst = token[1:]
            if prefix == '+' and not (OPTAB[inst].inf & FORMAT4):
                program.error("%s does not support format 4." % inst)
            else:
                fmt = 4

            if idx == 1:
                "CHECK LABEL"
                program.symtab[tokens[0]] = program.LOCCTR
        else:
            continue

        if fmt != 4:
            mask = OPTAB[inst].inf & 0xE0
            while mask != 0x8:
                mask >>= 1
                fmt += 1
            fmt = (5 - fmt)
        program.LOCCTR += fmt

        return True
    return False

def has_labels(program_inf, tokens):
    pass


if __name__ == "__main__":
    # Parse the arguments
    parser = argparse.ArgumentParser(description="A Python SIC/XE Assembler")
    parser.add_argument('-o', help='the output file.', default='a.out')
    parser.add_argument('--listing', help='generate assembly listing.')
    parser.add_argument('input', nargs='+', help='the source assembly file(s).')
    args = parser.parse_args()
    input_files = args.input

    print("SIC/XE Assembler")

    # Open files in the list
    for file_name in input_files:
        program = Program(file_name)
        try:
            print("\nStarting assemble %s ..." % program.source)
            program.assemble()
            print("Done.")
            symlist = list(program.symtab.items())
            symlist.sort(key=lambda x : x[1])
            for x in symlist:
                print("%s\t\t: 0x%4X" %(x[0], x[1]))
        except AssembleError:
            print("Assemble failed.")
            continue
