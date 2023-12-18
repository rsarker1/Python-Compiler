# Name: Rahul Sarker
# NetID: rsarker
# Student ID: 113414194

import decaf_absmc
import decaf_ast
from decaf_compiler import AST_tree
local_var_list = []
label_scope = []

curr_loop_cont_label = None
curr_enter_then_label = None
curr_break_out_else_label = None
non_static_field_offset = 0
currMethod = None

def push_labels():
    global label_scope
    global curr_loop_cont_label, curr_enter_then_label, curr_break_out_else_label
    label_scope.append(curr_loop_cont_label)
    label_scope.append(curr_enter_then_label)
    label_scope.append(curr_break_out_else_label)

def pop_labels():
    global label_scope
    global curr_loop_cont_label, curr_enter_then_label, curr_break_out_else_label
    curr_break_out_else_label = label_scope.pop()
    curr_enter_then_label = label_scope.pop()
    curr_loop_cont_label = label_scope.pop()

def offsets_nonstatic(clss):
    global non_static_field_offset
    if clss.super_name != '':
        offsets_nonstatic(clss.super_name)

    for field in clss.fields:
        if field.applicability == 'instance':
            field.offset = non_static_field_offset
            non_static_field_offset += 1

    clss.size = non_static_field_offset

def offsets_static(clss):
    for field in clss.fields:
        if field.applicability == 'static':
            field.offset = decaf_absmc.machine.static_data
            decaf_absmc.machine.add_static_field()

def setup_offsets(clss):
    global non_static_field_offset
    offsets_static(clss)
    non_static_field_offset = 0
    offsets_nonstatic(clss)

def generate_code(class_list):
    for clss in class_list[2:]:
        setup_offsets(clss)
        
    for clss in class_list[2:]:
        generate_class_code(clss)

def setup_registers(method):
    if method.applicability == 'static':
        decaf_absmc.Register.count = 0
    else:
        decaf_absmc.Register.count = 1
    
    for var in method.parameters:
        var.reg = decaf_absmc.Register('a')
        print(f'# var {var.name} given {var.reg}')

    decaf_absmc.Register.count = 0
    
    for var in method.variableTable:
        var.reg = decaf_absmc.Register('t')
        print(f'# var {var.name} given {var.reg}')

def generate_class_code(clss):
    global currMethod
    for method in clss.methods:
        setup_registers(method)
        currMethod = method
        method.returned = False
        decaf_absmc.MethodLabel(method.name, method.id)
        gen_code(method.body)
        if not method.returned:
            decaf_absmc.ProcedureInstruct('ret')
    for construct in clss.constructors:
        setup_registers(construct)
        currMethod = construct
        construct.returned = False
        decaf_absmc.ConstructorLabel(construct.id)
        gen_code(construct.body) 
        if not construct.returned:
            decaf_absmc.ProcedureInstruct('ret')  

def gen_code(stmt):
    global curr_loop_cont_label, curr_enter_then_label, curr_break_out_else_label, local_var_list
    if type(stmt) is list and isinstance(stmt[0], decaf_ast.VariableRecord):
        for index_stmt in stmt:
            local_var_list.append(index_stmt)
        return         
    stmt.end_reg = None
    push_labels()
    
    if stmt.kind == 'Block':
        for selected_stmt in stmt.attributes['stmts']:
            gen_code(selected_stmt)
    elif stmt.kind == 'Expr':
        gen_code(stmt.attributes['expression'])
    elif stmt.kind == 'Assign':
        gen_code(stmt.attributes['right'])
        gen_code(stmt.attributes['left'])
        
        if stmt.attributes['left'].type == 'float' and stmt.attributes['right'].type == 'int':
            convert = decaf_absmc.ConvertInstruct('itof', stmt.attributes['right'].end_reg)
            stmt.attributes['right'].end_reg = convert.dst
        if stmt.attributes['left'].kind == 'Field_access':
            decaf_absmc.MoveInstruct('move', stmt.attributes['left'].end_reg, stmt.attributes['right'].end_reg)
        else:
            decaf_absmc.HeapInstruct('hstore', stmt.attributes['left'].attributes['base'].end_reg, stmt.attributes['left'].offset_reg, stmt.attributes['right'].end_reg)
    elif stmt.kind == 'Variable': # FIX THIS LINE
        if stmt.reg == None:
            for var in local_var_list:
                if var.name == stmt.name:
                    stmt.end_reg = var.reg
        else:
            stmt.end_reg = stmt.reg
    elif stmt.kind == 'Constant':
        reg = decaf_absmc.Register()
        const_stmt = stmt.attributes['Expression']

        if const_stmt.type == 'Integer_constant': # FIX LATER
            decaf_absmc.MoveInstruct('move_immed_i', reg, const_stmt.attributes['value'], True)
        elif const_stmt.type == 'Float_constant':
            decaf_absmc.MoveInstruct('move_immed_f', reg, const_stmt.attributes['value'], True)
        elif const_stmt.type == 'String_constant':
            pass
        elif const_stmt.kind == 'true':
            decaf_absmc.MoveInstruct('move_immed_i', reg, 1, True)
        elif const_stmt.kind == 'false':
            decaf_absmc.MoveInstruct('move_immed_i', reg, 0, True)
        elif const_stmt.kind == 'null':
            decaf_absmc.MoveInstruct('move_immed_i', reg, 'Null', True)
        const_stmt.end_reg = reg
        
    elif stmt.kind == 'Binary':
        oper = stmt.attributes['operator']
        if oper not in ['and', 'or']:
            op1 = stmt.attributes['operand1']
            op2 = stmt.attributes['operand2']
            gen_code(op1)
            gen_code(op2)

            reg = decaf_absmc.Register()
            if op1.type == 'float' or op2.type == 'float':
                expr_type = 'f'
            else:
                expr_type = 'i'

            if op1.type == 'int' and op2.type == 'float':
                convert = decaf_absmc.Convert('itof', op1.end_reg)
                op1.end_reg = convert.dst
            elif op1.type == 'float' and op2.type == 'int':
                convert = decaf_absmc.Convert('itof', op2.end_reg)
                op2.end_reg = convert.dst

            if oper in ['add', 'sub', 'mul', 'div', 'gt', 'geq', 'lt', 'leq']:
                decaf_absmc.ArithInstruct(oper, reg, op1.end_reg, op2.end_reg, expr_type)

            elif oper == 'eq' or oper == 'neq':
                decaf_absmc.ArithInstruct('sub', reg, op1.end_reg, op2.end_reg, expr_type)

            if oper == 'eq':
                ieq_set = decaf_absmc.BranchLabel(stmt.lineRange, 'SET_EQ')
                ieq_out = decaf_absmc.BranchLabel(stmt.lineRange, 'SET_EQ_OUT')
                decaf_absmc.BranchInstruct('bz', ieq_set, reg)
                decaf_absmc.MoveInstruct('move_immed_i', reg, 0, True)
                decaf_absmc.BranchInstruct('jmp', ieq_out)

                ieq_set.add_to_code()
                decaf_absmc.MoveInstruct('move_immed_i', reg, 1, True)
                ieq_out.add_to_code()

        if oper == 'and':
            and_skip = decaf_absmc.BranchLabel(stmt.lineRange, 'AND_SKIP')
            gen_code(op1)
            reg = decaf_absmc.Register()
            decaf_absmc.MoveInstruct('move', reg, op1.end_reg)
            decaf_absmc.BranchInstruct('bz', and_skip, op1.end_reg)
            gen_code(op2)
            decaf_absmc.MoveInstruct('move', reg, op2.end_reg)
            and_skip.add_to_code()

        if oper == 'or':
            or_skip = decaf_absmc.BranchLabel(stmt.lineRange, 'OR_SKIP')
            gen_code(op1)
            reg = decaf_absmc.Register()
            decaf_absmc.MoveInstruct('move', reg, op1.end_reg)
            decaf_absmc.BranchInstruct('bnz', or_skip, op1.end_reg)
            gen_code(op2)
            decaf_absmc.MoveInstruct('move', reg, op2.end_reg)
            or_skip.add_to_code()

        stmt.end_reg = reg
    
    elif stmt.kind == 'For':
        gen_code(stmt.attributes['initialize_expression'])

        cond_label = decaf_absmc.BranchLabel(stmt.lineRange, 'FOR_COND')
        curr_enter_then_label = entry_label = decaf_absmc.BranchLabel(stmt.lineRange, 'FOR_ENTRY')
        curr_loop_cont_label = continue_label = decaf_absmc.BranchLabel(stmt.lineRange, 'FOR_UPDATE')
        curr_break_out_else_label = out_label = decaf_absmc.BranchLabel(stmt.lineRange, 'FOR_OUT')

        cond_label.add_to_code()
        gen_code(stmt.attributes['loop_condition'])
        decaf_absmc.BranchInstruct('bz', out_label, stmt.attributes['loop_condition'].end_reg)

        entry_label.add_to_code()
        gen_code(stmt.attributes['loop_body'])

        continue_label.add_to_code()
        gen_code(stmt.attributes['update_expression'])

        decaf_absmc.BranchInstruct('jmp', cond_label)

        out_label.add_to_code()
        
    elif stmt.kind == 'Auto':
        gen_code(stmt.attributes['operand']) 
 
        if stmt.attributes['order'] == 'post':
            tmp_reg = decaf_absmc.Register()
            decaf_absmc.MoveInstruct('move', tmp_reg, stmt.attributes['operand'].end_reg)

        one_reg = decaf_absmc.Register()
        decaf_absmc.MoveInstruct('move_immed_i', one_reg, 1, True)

        decaf_absmc.ArithInstruct('add' if stmt.attributes['operation'] == 'inc' else 'dec', stmt.attributes['operand'].end_reg, stmt.attributes['operand'].end_reg, one_reg)

        if stmt.attributes['order'] == 'post':
            stmt.end_reg = tmp_reg
        else:
            stmt.end_reg = stmt.attributes['operand'].end_reg
            
    elif stmt.kind == 'Skip':
        pass

    elif stmt.kind == 'Return':
        currMethod.returned = True
        if stmt.attributes['expression'] is None:
            decaf_absmc.ProcedureInstruct('ret')
            return
        gen_code(stmt.attributes['expression'])

        decaf_absmc.MoveInstruct('move', decaf_absmc.Register('a', 0), stmt.attributes['expression'].end_reg)
        decaf_absmc.ProcedureInstruct('ret')

    elif stmt.kind == 'While':
        curr_loop_cont_label = cond_label = decaf_absmc.BranchLabel(stmt.lineRange, 'WHILE_COND')
        curr_enter_then_label = entry_label = decaf_absmc.BranchLabel(stmt.lineRange, 'WHILE_ENTRY')
        curr_break_out_else_label = out_label = decaf_absmc.BranchLabel(stmt.lineRange, 'WHILE_OUT')
        
        cond_label.add_to_code()
        gen_code(stmt.attributes['loop_condition'])
        decaf_absmc.BranchInstruct('bz', out_label, stmt.attributes['loop_condition'].end_reg)
        entry_label.add_to_code()
        gen_code(stmt.attributes['loop_body'])
        decaf_absmc.BranchInstruct('jmp', cond_label)
        out_label.add_to_code()

    elif stmt.kind == 'Break':
        decaf_absmc.BranchInstruct('jmp', curr_break_out_else_label)

    elif stmt.kind == 'Continue':
        decaf_absmc.BranchInstruct('jmp', curr_loop_cont_label)
        
    elif stmt.kind == 'If':
        curr_enter_then_label = then_part = decaf_absmc.BranchLabel(stmt.lineRange, 'THEN_PART')
        curr_break_out_else_label = else_part = decaf_absmc.BranchLabel(stmt.lineRange, 'ELSE_PART')
        out_label = decaf_absmc.BranchLabel(stmt.lineRange, 'IF_STMT_OUT')

        gen_code(stmt.attributes['condition'])

        decaf_absmc.BranchInstruct('bz', else_part, stmt.condition.end_reg)

        then_part.add_to_code()
        gen_code(stmt.attributes['then'])

        decaf_absmc.BranchInstruct('jmp', out_label)

        else_part.add_to_code()

        gen_code(stmt.attributes['else'])

        out_label.add_to_code()
        
    elif stmt.kind == 'Field_access':
        gen_code(stmt.attributes['base'])
        found_field = ''

        for clsses in AST_tree.classes:
            if clsses.name == stmt.attributes['base'].name:
                for fields in clsses.fields: 
                    if fields.id == stmt.attributes['field_name']:
                        found_field = fields

        offset_reg = decaf_absmc.Register()
        ret_reg = decaf_absmc.Register()

        decaf_absmc.MoveInstruct('move_immed_i', offset_reg, found_field.offset, True)
        decaf_absmc.HeapInstruct('hload', ret_reg, stmt.base.end_reg, offset_reg)

        stmt.offset_reg = offset_reg
        stmt.end_reg = ret_reg

    elif stmt.kind == 'Class_reference':
        stmt.end_reg = decaf_absmc.Register('sap')

    elif stmt.kind == 'New_object':
        recd_addr_reg = decaf_absmc.Register()
        size_reg = decaf_absmc.Register()
        clss = ''
        for clsses in AST_tree.classes:
            if clsses.name == stmt.attributes['class_name']:
                clss = clsses
        decaf_absmc.MoveInstruct('move_immed_i', size_reg, clss.size, True)
        decaf_absmc.HeapInstruct('halloc', recd_addr_reg, size_reg)

        if stmt.attributes['id'] is None:
            stmt.end_reg = recd_addr_reg
            return
        saved_regs = []
        saved_regs.append(recd_addr_reg)
        if currMethod.applicability != 'static':
            saved_regs.append(decaf_absmc.Register('a', 0))

        for blk in range(0, len(currMethod.body)): # FIX THIS. User var_exprs
            for var in currMethod.body[blk].values():
                saved_regs.append(var.reg)

        for reg in saved_regs:
            decaf_absmc.ProcedureInstruct('save', reg)

        decaf_absmc.MoveInstruct('move', decaf_absmc.Register('a', 0), recd_addr_reg)
        arg_reg_index = 1
        for arg in stmt.attributes['arguments']:
            gen_code(arg)
            decaf_absmc.MoveInstruct('move', decaf_absmc.Register('a', arg_reg_index), arg.end_reg)
            arg_reg_index += 1

        decaf_absmc.ProcedureInstruct('call', f"C_{stmt.attributes['id']}")
        for reg in reversed(saved_regs):
            decaf_absmc.ProcedureInstruct('restore', reg)

        stmt.end_reg = recd_addr_reg

    elif stmt.kind == 'This':
        stmt.end_reg = decaf_absmc.Register('a', 0)
        
    elif stmt.kind == 'Method_call':
        gen_code(stmt.attributes['base'])
        
        for clsses in AST_tree.classes:
            if clsses.name == stmt.attributes['base'].name:
                for mtd in clsses.methods:
                    if stmt.attributes['method_name'] == mtd.name:
                        break
        saved_regs = []
        arg_reg_index = 0

        if mtd.applicability != 'static':
            arg_reg_index += 1
        if currMethod.applicability != 'static':
            saved_regs.append(decaf_absmc.Register('a', 0))
        for blk in range(0, len(currMethod.body)): # FIX THIS
            for var in currMethod.body[blk].values():
                saved_regs.append(var.reg)

        for reg in saved_regs:
            decaf_absmc.ProcedureInstruct('save', reg)

        if mtd.applicability != 'static':
            decaf_absmc.MoveInstruct('move', decaf_absmc.Register('a', 0), stmt.base.end_reg)

        for arg in stmt.attributes['arguments']:
            gen_code(arg)
            decaf_absmc.MoveInstruct('move', decaf_absmc.Register('a', arg_reg_index), arg.end_reg)
            arg_reg_index += 1

        decaf_absmc.ProcedureInstruct('call', f"M_{mtd.name}_{mtd.id}")
        stmt.end_reg = decaf_absmc.Register()
        decaf_absmc.MoveInstruct('move', stmt.end_reg, decaf_absmc.Register('a', 0))
        for reg in reversed(saved_regs):
            decaf_absmc.ProcedureInstruct('restore', reg)

    elif stmt.kind == 'Unary':
        gen_code(stmt.attributes['operand'])

        ret = decaf_absmc.Register()
        if stmt.attributes['operator'] == 'uminus':
            zero_reg = decaf_absmc.Register()
            if stmt.attributes['operand'].type == 'float':
                prefix = 'f'
            else:
                prefix = 'i'
            decaf_absmc.MoveInstruct(f"move_immed_{prefix}", zero_reg, 0, True)
            decaf_absmc.ArithInstruct('sub', ret, zero_reg, stmt.attributes['operand'].end_reg, prefix)
        else:
            set_one_label = decaf_absmc.BranchLabel(stmt.lineRange, 'SET_ONE')
            out_label = decaf_absmc.BranchLabel(stmt.lineRange, 'UNARY_OUT')

            decaf_absmc.BranchInstruct('bz', set_one_label, stmt.attributes['operand'].end_reg)
            decaf_absmc.MoveInstruct('move_immed_i', ret, 0, True)
            decaf_absmc.BranchInstruct('jmp', out_label)

            set_one_label.add_to_code()

            decaf_absmc.MoveInstruct('move_immed_i', ret, 1, True)

            out_label.add_to_code()

        stmt.end_reg = ret

    elif stmt.kind == 'Super':
        stmt.end_reg = decaf_absmc.Register('a', 0)

    pop_labels()
  