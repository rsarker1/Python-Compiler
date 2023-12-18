# Name: Rahul Sarker
# NetID: rsarker
# Student ID: 113414194

class AbstractMachine(object):
    def __init__(self):
        self.static_data = 0
        self.instruct_list = []
        self.labels = []
    def add_instruct(self, instructors):
        if len(self.labels) > 0:
            instructors.label = ':\n'.join([str(label) for label in self.labels])
            self.labels = []
        self.instruct_list.append(instructors)
    def add_label(self, label):
        self.labels.append(label)
    def add_static_field(self):
        self.static_data += 1
    def machine_code_str(self):
        str_list = []
        str_list.append(f".static_data {self.static_data}")
        str_list.extend([str(instr) for instr in self.instruct_list])
        return '\n'.join(str_list)
    
class Instruction(object):
    def __init__(self, opcode, args, label = None):
        self.opcode = opcode
        self.args = args
        self.label = label
        abstract_machine.add_instruct(self)
    def __str__(self):
        arg_list = [str(arg) for arg in self.args]
        label_string = ''
        if self.label is not None:
            label_string = f"{self.label}:\n"

        return f"{label_string}\t{self.opcode} {', '.join(arg_list)}"

class Label(object):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return f"{self.name}"

class Register(object):
    count = 0
    def __init__(self, r_type='t', r_num=None):
        self.r_type = r_type
        self.r_num = r_num

        if self.r_num is None and self.r_type != 'sap':
            self.r_num = Register.count
            Register.count += 1

    def __str__(self):
        if self.r_type == 'sap':
            return f"{self.r_type}"
        else:
            return f"{self.r_type}{self.r_num}"
        
class MethodLabel(Label):
    def __init__(self, name, id):
        if name == 'main':
            name = '__main__'
        else:
            name = f"M_{name}_{id}"
        super(MethodLabel, self).__init__(name)
        abstract_machine.add_label(self)

class ConstructorLabel(Label):
    def __init__(self, id):
        super(ConstructorLabel, self).__init__(f"C_{id}")
        abstract_machine.add_label(self)

class BranchLabel(Label):
    unique_int = 1
    def __init__(self, lines, name):
        super(BranchLabel, self).__init__(f"L_{lines}_{name}_{BranchLabel.unique_int}")
        BranchLabel.unique_int += 1

    def add_to_code(self):
        abstract_machine.add_label(self)

class ProcedureInstruct(Instruction):
    def __init__(self, opcode, arg=None):
        if arg is None:
            args = []
        else:
            args = [arg]
        super(ProcedureInstruct, self).__init__(opcode, args)

class ConvertInstruct(Instruction):
    def __init__(self, opcode, reg):
        self.dst = Register()
        super(ConvertInstruct, self).__init__(opcode, [self.dst, reg])

class BranchInstruct(Instruction):
    def __init__(self, opcode, label=None, reg=None):
        if label is None:
            args = []
        elif reg is None:
            args = [label]
        else:
            args = [reg, label]
        super(BranchInstruct, self).__init__(opcode, args)

class MoveInstruct(Instruction):
    def __init__(self, opcode, dst, src, val_is_const=False):
        self.is_src_const = val_is_const
        super(MoveInstruct, self).__init__(opcode, [dst, src])

class ArithInstruct(Instruction):
    def __init__(self, opcode, dst, src1, src2, type = 'i'):
        super(ArithInstruct, self).__init__(type + opcode, [dst, src1, src2])

class HeapInstruct(Instruction):
    def __init__(self, opcode, r1, r2, r3 = None):
        if r3 is None:
            args = [r1, r2]
        else:
            args = [r1, r2, r3]
        super(HeapInstruct, self).__init__(opcode, args)

abstract_machine = AbstractMachine()