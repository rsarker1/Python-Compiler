import ast
import absmc

# TODO:
# ??

####################################################################################################

# Global vars that hold label objects for different expressions / statements
label_scope = []

# This holds the label used for a `continue` statement in a loop
# For `for` loops, this points to the update expression
# For `while` loops, this points to the condition expression

current_loop_continue_label = None

# This holds the entrance of a loop, or the then part of an if statement
current_enter_then_label = None

# This holds the loop's exit or the else part of an if statement
current_break_out_else_label = None

# Examples:
# if we're in an if stmt where:
#
# if (x < y && x == z) {
#   x++;
# } else {
#   x--;
# }
# then if x < y BinaryExpr evals to false, we know to jump to the else branch
# and use the label called 'current_break_out_else_label'
# similarly, if we're in a loop where:
#
# while (x < y || x < z) {
#   x++;
# }
#
# if x < y evals to true, jump into the body of the loop
# which is the label held by current_enter_then_label

non_static_field_offset = 0
current_method = None

def push_labels():
    global label_scope
    global current_loop_continue_label, current_enter_then_label, current_break_out_else_label

    label_scope.append(current_loop_continue_label)
    label_scope.append(current_enter_then_label)
    label_scope.append(current_break_out_else_label)

def pop_labels():
    global label_scope
    global current_loop_continue_label, current_enter_then_label, current_break_out_else_label

    current_break_out_else_label = label_scope.pop()
    current_enter_then_label = label_scope.pop()
    current_loop_continue_label = label_scope.pop()

def calc_nonstatic_offsets(cls):
    '''Calculates the offsets for all instance fields of a class.

    Walks up the hierarchy and assigns each instance field a unique offset.
    At the end, it sets the class's size to number of instance fields.'''
    global non_static_field_offset

    if cls.superclass is not None:
        calc_nonstatic_offsets(cls.superclass)

    for field in cls.fields.viewvalues():
        if field.storage == 'instance':
            field.offset = non_static_field_offset
            print '# field {} given {}'.format(field.name, non_static_field_offset)
            non_static_field_offset += 1

    cls.size = non_static_field_offset


def calc_static_offsets(cls):
    for field in cls.fields.viewvalues():
        if field.storage == 'static':
            field.offset = absmc.machine.static_data
            absmc.machine.add_static_field()


def preprocess(cls):
    global non_static_field_offset

    calc_static_offsets(cls)

    non_static_field_offset = 0
    calc_nonstatic_offsets(cls)


def generate_code(classtable):

    for cls in classtable.viewvalues():
        preprocess(cls)

    for cls in classtable.viewvalues():
        generate_class_code(cls)


def setup_registers(method):
    # block 0 are the formals, which go into args
    # if static, first arg is a0,
    # if instance, first arg is a1, as `this` goes in a0

    if isinstance(method, ast.Method) and method.storage == 'static':
        absmc.Register.count = 0
    else:
        absmc.Register.count = 1

    for var in method.vars.vars[0].values():
        var.reg = absmc.Register('a')
        print '# var {} given {}'.format(var.name, var.reg)

    absmc.Register.count = 0
    # rest of the vars in the method go into t registers
    for block in range(1, len(method.vars.vars)):
        for var in method.vars.vars[block].values():
            var.reg = absmc.Register('t')
            print '# var {} given {}'.format(var.name, var.reg)


def generate_class_code(cls):
    global current_method

    for method in cls.methods:
        setup_registers(method)
        current_method = method
        method.returned = False
        absmc.MethodLabel(method.name, method.id)
        gen_code(method.body)
        if not method.returned:
            absmc.ProcedureInstr('ret')
    for constr in cls.constructors:
        setup_registers(constr)
        current_method = constr
        constr.returned = False
        absmc.ConstructorLabel(constr.id)
        gen_code(constr.body)
        if not constr.returned:
            absmc.ProcedureInstr('ret')  # We assume constrs don't have a return


def gen_code(stmt):
    global current_loop_continue_label, current_enter_then_label, current_break_out_else_label
    # stmt.end_reg is the destination register for each expression
    stmt.end_reg = None
    push_labels()

    if isinstance(stmt, ast.BlockStmt):
        for stmt_line in stmt.stmtlist:
            gen_code(stmt_line)

    elif isinstance(stmt, ast.ExprStmt):
        gen_code(stmt.expr)

    elif isinstance(stmt, ast.AssignExpr):
        gen_code(stmt.rhs)
        gen_code(stmt.lhs)

        if stmt.lhs.type == ast.Type('float') and stmt.rhs.type == ast.Type('int'):
            conv = absmc.ConvertInstr('itof', stmt.rhs.end_reg)
            stmt.rhs.end_reg = conv.dst

        if not isinstance(stmt.lhs, ast.FieldAccessExpr):
            absmc.MoveInstr('move', stmt.lhs.end_reg, stmt.rhs.end_reg)
        else:
            absmc.HeapInstr('hstore', stmt.lhs.base.end_reg, stmt.lhs.offset_reg, stmt.rhs.end_reg)

    elif isinstance(stmt, ast.VarExpr):
        stmt.end_reg = stmt.var.reg

    elif isinstance(stmt, ast.ConstantExpr):
        reg = absmc.Register()

        if stmt.kind == 'int':
            absmc.MoveInstr('move_immed_i', reg, stmt.int, True)
        elif stmt.kind == 'float':
            absmc.MoveInstr('move_immed_f', reg, stmt.float, True)
        elif stmt.kind == 'string':
            pass
        elif stmt.kind == 'True':
            absmc.MoveInstr('move_immed_i', reg, 1, True)
        elif stmt.kind == 'False':
            absmc.MoveInstr('move_immed_i', reg, 0, True)
        elif stmt.kind == 'Null':
            absmc.MoveInstr('move_immed_i', reg, 'Null', True)


        stmt.end_reg = reg

    elif isinstance(stmt, ast.BinaryExpr):
        if stmt.bop not in ['and', 'or']:
            gen_code(stmt.arg1)
            gen_code(stmt.arg2)

            reg = absmc.Register()
            flt = ast.Type('float')
            intg = ast.Type('int')
            if stmt.arg1.type == flt or stmt.arg2.type == flt:
                expr_type = 'f'
            else:
                expr_type = 'i'

            if stmt.arg1.type == intg and stmt.arg2.type == flt:
                conv = absmc.Convert('itof', stmt.arg1.end_reg)
                stmt.arg1.end_reg = conv.dst
            elif stmt.arg1.type == flt and stmt.arg2.type == intg:
                conv = absmc.Convert('itof', stmt.arg2.end_reg)
                stmt.arg2.end_reg = conv.dst

            if stmt.bop in ['add', 'sub', 'mul', 'div', 'gt', 'geq', 'lt', 'leq']:
                absmc.ArithInstr(stmt.bop, reg, stmt.arg1.end_reg, stmt.arg2.end_reg, expr_type)

            elif stmt.bop == 'eq' or stmt.bop == 'neq':
                absmc.ArithInstr('sub', reg, stmt.arg1.end_reg, stmt.arg2.end_reg, expr_type)

            if stmt.bop == 'eq':

                # check if r2 == r3
                # 1. perform sub r1, r2, r3 (done above)
                # 2. branch to set_one if r1 is zero
                # 3. else, fall through and set r1 to zero
                # 4. jump out so we don't set r1 to one by accident

                ieq_set = absmc.BranchLabel(stmt.lines, 'SET_EQ')
                ieq_out = absmc.BranchLabel(stmt.lines, 'SET_EQ_OUT')

                absmc.BranchInstr('bz', ieq_set, reg)
                absmc.MoveInstr('move_immed_i', reg, 0, True)
                absmc.BranchInstr('jmp', ieq_out)

                ieq_set.add_to_code()
                absmc.MoveInstr('move_immed_i', reg, 1, True)

                ieq_out.add_to_code()

        if stmt.bop == 'and':
            and_skip = absmc.BranchLabel(stmt.lines, 'AND_SKIP')
            gen_code(stmt.arg1)
            reg = absmc.Register()
            absmc.MoveInstr('move', reg, stmt.arg1.end_reg)
            absmc.BranchInstr('bz', and_skip, stmt.arg1.end_reg)
            gen_code(stmt.arg2)
            absmc.MoveInstr('move', reg, stmt.arg2.end_reg)
            and_skip.add_to_code()

        if stmt.bop == 'or':
            or_skip = absmc.BranchLabel(stmt.lines, 'OR_SKIP')
            gen_code(stmt.arg1)
            reg = absmc.Register()
            absmc.MoveInstr('move', reg, stmt.arg1.end_reg)
            absmc.BranchInstr('bnz', or_skip, stmt.arg1.end_reg)
            gen_code(stmt.arg2)
            absmc.MoveInstr('move', reg, stmt.arg2.end_reg)
            or_skip.add_to_code()

        stmt.end_reg = reg

    elif isinstance(stmt, ast.ForStmt):

        # for-loop:
        # for (i = 0; i < 10; i++) {
        #   body
        # }

        # set i's reg equal to 0
        # create a label after this, as this is where we jump back to at end of loop
        # also create the 'out' label which is what we jump to when breaking out of loop
        # generate code for the 'cond' (test if i's reg is less than 10's reg)
        # test if the cond evaluated to false with 'bz', if so, break out of loop
        # else, fall through into the body of the for-loop
        # when body is over, generate code to update the var (i++)
        # jump unconditionally back to the cond_label, where we eval if i is still < 10
        gen_code(stmt.init)

        cond_label = absmc.BranchLabel(stmt.lines, 'FOR_COND')
        current_enter_then_label = entry_label = absmc.BranchLabel(stmt.lines, 'FOR_ENTRY')
        current_loop_continue_label = continue_label = absmc.BranchLabel(stmt.lines, 'FOR_UPDATE')
        current_break_out_else_label = out_label = absmc.BranchLabel(stmt.lines, 'FOR_OUT')

        cond_label.add_to_code()

        gen_code(stmt.cond)
        absmc.BranchInstr('bz', out_label, stmt.cond.end_reg)

        entry_label.add_to_code()
        gen_code(stmt.body)

        continue_label.add_to_code()
        gen_code(stmt.update)

        absmc.BranchInstr('jmp', cond_label)

        out_label.add_to_code()

    elif isinstance(stmt, ast.AutoExpr):
        gen_code(stmt.arg)

        if stmt.when == 'post':
            tmp_reg = absmc.Register()
            absmc.MoveInstr('move', tmp_reg, stmt.arg.end_reg)

        one_reg = absmc.Register()

        # Load 1 into a register
        absmc.MoveInstr('move_immed_i', one_reg, 1, True)

        absmc.ArithInstr('add' if stmt.oper == 'inc' else 'sub', stmt.arg.end_reg, stmt.arg.end_reg, one_reg)

        if stmt.when == 'post':
            stmt.end_reg = tmp_reg
        else:
            stmt.end_reg = stmt.arg.end_reg

    elif isinstance(stmt, ast.SkipStmt):
        pass

    elif isinstance(stmt, ast.ReturnStmt):
        current_method.returned = True
        if stmt.expr is None:
            absmc.ProcedureInstr('ret')
            return
        gen_code(stmt.expr)

        # Load the result into a0
        absmc.MoveInstr('move', absmc.Register('a', 0), stmt.expr.end_reg)

        # Return to caller
        absmc.ProcedureInstr('ret')

    elif isinstance(stmt, ast.WhileStmt):

        current_loop_continue_label = cond_label = absmc.BranchLabel(stmt.lines, 'WHILE_COND')
        current_enter_then_label = entry_label = absmc.BranchLabel(stmt.lines, 'WHILE_ENTRY')
        current_break_out_else_label = out_label = absmc.BranchLabel(stmt.lines, 'WHILE_OUT')

        cond_label.add_to_code()

        gen_code(stmt.cond)

        absmc.BranchInstr('bz', out_label, stmt.cond.end_reg)

        entry_label.add_to_code()

        gen_code(stmt.body)

        absmc.BranchInstr('jmp', cond_label)

        out_label.add_to_code()

    elif isinstance(stmt, ast.BreakStmt):
        absmc.BranchInstr('jmp', current_break_out_else_label)

    elif isinstance(stmt, ast.ContinueStmt):
        absmc.BranchInstr('jmp', current_loop_continue_label)

    elif isinstance(stmt, ast.IfStmt):

        # if (x == y)
        #   ++x;
        # else
        #   --x;

        # generate 2 labels, for the else part, and the out part
        # test if x == y
        # if not true, jump to the else part
        # if true, we're falling through to the then part, then must jump
        # out right before hitting the else part straight to the out part

        current_enter_then_label = then_part = absmc.BranchLabel(stmt.lines, 'THEN_PART')
        current_break_out_else_label = else_part = absmc.BranchLabel(stmt.lines, 'ELSE_PART')
        out_label = absmc.BranchLabel(stmt.lines, 'IF_STMT_OUT')

        gen_code(stmt.condition)

        absmc.BranchInstr('bz', else_part, stmt.condition.end_reg)

        then_part.add_to_code()
        gen_code(stmt.thenpart)

        absmc.BranchInstr('jmp', out_label)

        else_part.add_to_code()

        gen_code(stmt.elsepart)

        out_label.add_to_code()

    elif isinstance(stmt, ast.FieldAccessExpr):
        gen_code(stmt.base)

        cls = ast.lookup(ast.classtable, stmt.base.type.typename)
        field = ast.lookup(cls.fields, stmt.fname)

        offset_reg = absmc.Register()
        ret_reg = absmc.Register()

        absmc.MoveInstr('move_immed_i', offset_reg, field.offset, True)
        absmc.HeapInstr('hload', ret_reg, stmt.base.end_reg, offset_reg)

        stmt.offset_reg = offset_reg
        stmt.end_reg = ret_reg

    elif isinstance(stmt, ast.ClassReferenceExpr):
        stmt.end_reg = absmc.Register('sap')

    elif isinstance(stmt, ast.NewObjectExpr):
        recd_addr_reg = absmc.Register()
        size_reg = absmc.Register()
        absmc.MoveInstr('move_immed_i', size_reg, stmt.classref.size, True)
        absmc.HeapInstr('halloc', recd_addr_reg, size_reg)

        if stmt.constr_id is None:
            stmt.end_reg = recd_addr_reg
            return

        saved_regs = []

        saved_regs.append(recd_addr_reg)

        # add a0 if the current method is not static
        if current_method.storage != 'static':
            saved_regs.append(absmc.Register('a', 0))

        # for each var in each block of the current method, add to save list
        for block in range(0, len(current_method.vars.vars)):
            for var in current_method.vars.vars[block].values():
                saved_regs.append(var.reg)

        # save each reg in the saved list
        for reg in saved_regs:
            absmc.ProcedureInstr('save', reg)

        absmc.MoveInstr('move', absmc.Register('a', 0), recd_addr_reg)

        arg_reg_index = 1

        for arg in stmt.args:
            gen_code(arg)
            absmc.MoveInstr('move', absmc.Register('a', arg_reg_index), arg.end_reg)
            arg_reg_index += 1

        absmc.ProcedureInstr('call', 'C_{}'.format(stmt.constr_id))

        # restore regs from the now-reversed save list
        for reg in reversed(saved_regs):
            absmc.ProcedureInstr('restore', reg)

        stmt.end_reg = recd_addr_reg

    elif isinstance(stmt, ast.ThisExpr):
        stmt.end_reg = absmc.Register('a', 0)

    elif isinstance(stmt, ast.MethodInvocationExpr):
        gen_code(stmt.base)

        cls = ast.lookup(ast.classtable, stmt.base.type.typename)
        for method in cls.methods:
            if stmt.mname == method.name:
                break

        saved_regs = []

        arg_reg_index = 0

        # first arg goes into a1 if desired method is not static
        if method.storage != 'static':
            arg_reg_index += 1

        # add a0 if the current method is not static
        if current_method.storage != 'static':
            saved_regs.append(absmc.Register('a', 0))

        # for each var in each block of the current method, add to save list
        for block in range(0, len(current_method.vars.vars)):
            for var in current_method.vars.vars[block].values():
                saved_regs.append(var.reg)

        # save each reg in the saved list
        for reg in saved_regs:
            absmc.ProcedureInstr('save', reg)

        if method.storage != 'static':
            absmc.MoveInstr('move', absmc.Register('a', 0), stmt.base.end_reg)

        for arg in stmt.args:
            gen_code(arg)
            absmc.MoveInstr('move', absmc.Register('a', arg_reg_index), arg.end_reg)
            arg_reg_index += 1

        absmc.ProcedureInstr('call', 'M_{}_{}'.format(method.name, method.id))

        # Store the result in a temporary register
        stmt.end_reg = absmc.Register()
        absmc.MoveInstr('move', stmt.end_reg, absmc.Register('a', 0))

        # restore regs from the reversed save list
        for reg in reversed(saved_regs):
            absmc.ProcedureInstr('restore', reg)

    elif isinstance(stmt, ast.UnaryExpr):
        gen_code(stmt.arg)

        ret = absmc.Register()
        if stmt.uop == 'uminus':
            zero_reg = absmc.Register()
            if stmt.arg.type == ast.Type('float'):
                prefix = 'f'
            else:
                prefix = 'i'
            # if uminus, put 0 - <reg> into the return reg
            absmc.MoveInstr('move_immed_{}'.format(prefix), zero_reg, 0, True)
            absmc.ArithInstr('sub', ret, zero_reg, stmt.arg.end_reg, prefix)
        else:
            # if it's a 0, branch to set 1
            # if it's a 1, we're falling through, setting to 0, and jumping out
            set_one_label = absmc.BranchLabel(stmt.lines, 'SET_ONE')
            out_label = absmc.BranchLabel(stmt.lines, 'UNARY_OUT')

            absmc.BranchInstr('bz', set_one_label, stmt.arg.end_reg)
            absmc.MoveInstr('move_immed_i', ret, 0, True)
            absmc.BranchInstr('jmp', out_label)

            set_one_label.add_to_code()

            absmc.MoveInstr('move_immed_i', ret, 1, True)

            out_label.add_to_code()

        stmt.end_reg = ret

    elif isinstance(stmt, ast.SuperExpr):
        stmt.end_reg = absmc.Register('a', 0)

    elif isinstance(stmt, ast.ArrayAccessExpr):
        # Create fake register.
        stmt.end_reg = absmc.Register('n', 0)
        print 'Found an array access. Arrays are not supported.'

    elif isinstance(stmt, ast.NewArrayExpr):
        # Create fake register.
        stmt.end_reg = absmc.Register('n', 0)
        print 'Found an array creation. Arrays are not supported.'

    else:
        print 'need instance ' + str(type(stmt))

    pop_labels()