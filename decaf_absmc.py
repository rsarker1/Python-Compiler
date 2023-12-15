class AbstractMachine(object):
    def __init__(self):
        self.static_data = 0
        self.instr_list = []
        self.labels = []

    def add_instr(self, instr):
        if len(self.labels) > 0:
            instr.label = ':\n'.join([str(label) for label in self.labels])
            self.labels = []
        self.instr_list.append(instr)

    def add_label(self, label):
        self.labels.append(label)

    def add_static_field(self):
        self.static_data += 1

    def __str__(self):
        str_list = []
        str_list.append('.static_data {}'.format(self.static_data))
        str_list.extend([str(instr) for instr in self.instr_list])
        return '\n'.join(str_list)


class Instruction(object):
    def __init__(self, op, args, label=None):
        self.op = op
        self.args = args
        self.label = label
        machine.add_instr(self)

    def __str__(self):
        arg_list = [str(arg) for arg in self.args]
        label_string = ""
        if self.label is not None:
            label_string = '{}:\n'.format(self.label)

        return '{}\t{} {}'.format(label_string, self.op, ', '.join(arg_list))


class Label(object):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return '{}'.format(self.name)


class Register(object):
    count = 0

    def __init__(self, reg_type='t', reg_num=None):
        self.reg_type = reg_type
        self.reg_num = reg_num

        if self.reg_num is None and self.reg_type != 'sap':
            self.reg_num = Register.count
            Register.count += 1

    def __str__(self):
        if self.reg_type == 'sap':
            return '{}'.format(self.reg_type)
        else:
            return '{}{}'.format(self.reg_type, self.reg_num)


class MethodLabel(Label):
    def __init__(self, name, id):
        if name == 'main':
            name = '__main__'
        else:
            name = 'M_{}_{}'.format(name, id)
        super(MethodLabel, self).__init__(name)

        machine.add_label(self)


class ConstructorLabel(Label):
    def __init__(self, id):
        super(ConstructorLabel, self).__init__('C_{}'.format(id))

        machine.add_label(self)


class BranchLabel(Label):
    unique_int = 1

    def __init__(self, lines, name):
        super(BranchLabel, self).__init__('L{}_{}_{}'.format(lines, name, BranchLabel.unique_int))
        BranchLabel.unique_int += 1

    def add_to_code(self):
        machine.add_label(self)


class ProcedureInstr(Instruction):
    '''The procedure instructions are:
    call l
    ret
    save r
    restore r'''
    def __init__(self, op, arg=None):
        if arg is None:
            args = []
        else:
            args = [arg]
        super(ProcedureInstr, self).__init__(op, args)


class ConvertInstr(Instruction):
    '''The conversion instructions are:
    ftoi dst, src
    itof dst, src'''
    def __init__(self, op, reg):
        self.dst = Register()
        super(ConvertInstr, self).__init__(op, [self.dst, reg])


class BranchInstr(Instruction):
    '''The branch instructions are:
    bz r, l
    bnz r, l
    jmp l'''
    def __init__(self, op, label=None, reg=None):
        if label is None:
            args = []
        elif reg is None:
            args = [label]
        else:
            args = [reg, label]
        super(BranchInstr, self).__init__(op, args)


class MoveInstr(Instruction):
    '''The move instructions are:
    move_immed_i r, i
    move_immed_f r, f
    move dst, src'''
    def __init__(self, op, dst, src, val_is_const=False):
        self.is_src_const = val_is_const
        super(MoveInstr, self).__init__(op, [dst, src])


class ArithInstr(Instruction):
    '''The arithmetic instructions are:
    iadd dst, src1, src2
    isub dst, src1, src2
    imul dst, src1, src2
    idiv dst, src1, src2
    imod dst, src1, src2
    igt  dst, src1, src2
    igeq dst, src1, src2
    ilt  dst, src1, src2
    ileq dst, src1, src2

    There also exist floating point operations of the form fadd, fsub, etc.
    for all but the modulus operator (imod exists but fmod doesn't)'''
    def __init__(self, op, dst, src1, src2, type='i'):
        super(ArithInstr, self).__init__(type + op, [dst, src1, src2])


class HeapInstr(Instruction):
    '''The heap instructions are:
    hload  dst, base, off
    hstore base, off, dst
    halloc base, off'''
    def __init__(self, op, reg1, reg2, reg3=None):
        if reg3 is None:
            args = [reg1, reg2]
        else:
            args = [reg1, reg2, reg3]
        super(HeapInstr, self).__init__(op, args)

machine = AbstractMachine()