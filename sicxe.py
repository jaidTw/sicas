BYTESIZE = 8

MODE_C = 0x1
MODE_F = 0x2
MODE_X = 0x4
MODE_P = 0x8

FORMAT4 = 0x10
FORMAT3 = 0x20
FORMAT2 = 0x40
FORMAT1 = 0x80


PC_RELATE = 0b000010 << 12
BASE_RELATE = 0b000100 << 12

IMM_ADDR = 0b010000 << 12
INDR_ADDR = 0b100000 << 12
INDEX_ADDR = 0b001000 << 12
DEFAULT_ADDR = 0b110000 << 12
EXTEND_FMT = 0b000001 << 12

class instruction:
    def __init__(self, opcode, fmt, mode=""):
        self.opcode = opcode << ((fmt - 1) * BYTESIZE)
        self.inf = 0x10 << (4 - fmt)
        if self.inf & FORMAT3:
            self.inf |= FORMAT4
        if "P" in mode:
            self.inf |= MODE_P
        if "X" in mode:
            self.inf |= MODE_X
        if "F" in mode:
            self.inf |= MODE_F
        if "C" in mode:
            self.inf |= MODE_C

    def __str__(self):
        return "instruction(%x, %s)" % (self.opcode, bin(self.inf))

    def __repr__(self):
        return str(self)

PRELOAD_SYMTAB = {
    "A" : 0,
    "X" : 1,
    "L" : 2,
    "B" : 3,
    "S" : 4,
    "T" : 5,
    "F" : 6,
    "PC" : 8,
    "SW" : 9
}

OPTAB = {
    "ADD"    : instruction(0x18, 3),
    "ADDF"   : instruction(0x58, 3, "XF"),
    "ADDR"   : instruction(0x90, 2, "X"),
    "AND"    : instruction(0x40, 3),
    "CLEAR"  : instruction(0xB4, 2, "X"),
    "COMP"   : instruction(0x28, 3),
    "COMPF"  : instruction(0x88, 3, "XFC"),
    "COMPR"  : instruction(0xA0, 2, "XFC"),
    "DIV"    : instruction(0x24, 3),
    "DIVF"   : instruction(0x64, 3, "XF"),
    "DIVR"   : instruction(0x9C, 2, "X"),
    "FIX"    : instruction(0xC4, 1, "XF"),
    "FLOAT"  : instruction(0xC0, 1, "XF"),
    "HIO"    : instruction(0xF4, 1, "PX"),
    "J"      : instruction(0x3C, 3),
    "JEQ"    : instruction(0x30, 3),
    "JGT"    : instruction(0x34, 3),
    "JLT"    : instruction(0x38, 3),
    "JSUB"   : instruction(0x48, 3),
    "LDA"    : instruction(0x00, 3),
    "LDB"    : instruction(0x68, 3, "X"),
    "LDCH"   : instruction(0x50, 3),
    "LDF"    : instruction(0x70, 3, "XF"),
    "LDL"    : instruction(0x08, 3),
    "LDS"    : instruction(0x6C, 3, "X"),
    "LDT"    : instruction(0x74, 3, "X"),
    "LDX"    : instruction(0x04, 3),
    "LPS"    : instruction(0xD0, 3, "PX"),
    "MUL"    : instruction(0x20, 3),
    "MULF"   : instruction(0x60, 3, "XF"),
    "MULR"   : instruction(0x98, 2, "X"),
    "NORM"   : instruction(0xC8, 1, "XF"),
    "OR"     : instruction(0x44, 3),
    "RD"     : instruction(0xD8, 3, "P"),
    "RMO"    : instruction(0xAC, 2, "X"),
    "RSUB"   : instruction(0x4C, 3),
    "SHIFTL" : instruction(0xA4, 2, "X"),
    "SHIFTR" : instruction(0xA8, 2, "X"),
    "SIO"    : instruction(0xF0, 1, "PX"),
    "SSK"    : instruction(0xEC, 3, "PX"),
    "STA"    : instruction(0x0C, 3),
    "STB"    : instruction(0x78, 3, "X"),
    "STCH"   : instruction(0x54, 3),
    "STF"    : instruction(0x80, 3, "X"),
    "STI"    : instruction(0xD4, 3, "PX"),
    "STL"    : instruction(0x14, 3),
    "STS"    : instruction(0x7C, 3, "X"),
    "STSW"   : instruction(0xE8, 3, "P"),
    "STT"    : instruction(0x84, 3, "X"),
    "STX"    : instruction(0x10, 3),
    "SUB"    : instruction(0x1C, 3),
    "SUBF"   : instruction(0x5C, 3, "XF"),
    "SUBR"   : instruction(0x94, 2, "X"),
    "SVC"    : instruction(0xB0, 2, "X"),
    "TD"     : instruction(0xE0, 3, "PC"),
    "TIO"    : instruction(0xF8, 1, "PXC"),
    "TIX"    : instruction(0x2C, 3, "C"),
    "TIXR"   : instruction(0xB8, 2, "XC"),
    "WD"     : instruction(0xDC, 3, "P"),
}
