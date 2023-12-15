# Name: Rahul Sarker
# NetID: rsarker
# Student ID: 113414194

currClass = None
currFunc = None
tree = None
error_flag = False
base_types = ['int', 'float', 'boolean', 'string']

def check_types(ast):
    global currClass
    global tree
    tree = ast

    classes = []
    for i in range(2, len(tree.classes)):
        classes.append(tree.classes[i])

    while len(classes) > 0:
        currClass = classes.pop()
        check_funcs(currClass.constructors)
        check_funcs(currClass.methods)
    return

def check_funcs(funcs):
    global currFunc
    for func in funcs:
        currFunc = func
        check_block(func.body)
    return

def check_block(block):
    block_queue = [block]
    while len(block_queue) != 0:
        block = block_queue.pop()
        block_queue += block.attributes['inners']
        type_block(block)
    return

def type_block(block):
    for stmt in block.attributes['stmts']:
        if not type_stmt(stmt):
            block.isTypeCorrect = False
            signal_error(f"Error: {stmt.kind} is causing an error at: {stmt.lineRange}")
            return False 
        
    block.isTypeCorrect = True
    return True

def type_stmt(stmt):
    if type(stmt) is list:
        return True
    elif stmt.kind == 'If':
        condition = stmt.attributes['condition']
        stmt.isTypeCorrect = type_expr(condition)
        if not stmt.isTypeCorrect or condition.type != 'boolean':
            stmt.isTypeCorrect = False
            return False
        
        if stmt.isTypeCorrect:
            expr = stmt.attributes['then']
            if expr.kind == 'Block':
                stmt.isTypeCorrecet = type_block(expr)
            else:
                stmt.isTypeCorrect = type_stmt(expr)

        check = True
        if 'else' in stmt.attributes.keys():
            expr = stmt.attributes['else']
            if expr.kind == 'Block':
                check = type_block(expr)
            else:
                check = type_stmt(stmt.attributes['else'])
        stmt.isTypeCorrect = check
        
    elif stmt.kind == 'While':
        condition = stmt.attributes['loop_condition']
        stmt.isTypeCorrect = type_expr(condition)
        if not stmt.isTypeCorrect or condition.type != 'boolean':
            stmt.isTypeCorrect = False
            return False
        
        stmt.isTypeCorrect = type_expr(stmt.attributes['loop_body'])
    elif stmt.kind == 'For':
        condition = stmt.attributes['loop_condition']
        stmt.isTypeCorrect = type_expr(condition)
        if not stmt.isTypeCorrect or condition.type != 'boolean':
            stmt.isTypeCorrect = False
            return False

        if stmt.isTypeCorrect:
            stmt.isTypeCorrect = type_expr(stmt.attributes['initialize_expression'])
        if stmt.isTypeCorrect:
            stmt.isTypeCorrect = type_expr(stmt.attributes['update_expression'])
        if stmt.isTypeCorrect:
            stmt.isTypeCorrect = type_expr(stmt.attributes['loop_body'])
    elif stmt.kind == 'Return':
        ret_type = ''
        if 'return_expression' in stmt.attributes.keys():
            ret_type = ''
            if currFunc.returnType.name not in base_types:
                ret_type = 'user(' + currFunc.returnType.name + ')'
            else:
                ret_type = currFunc.returnType.name

            expr = stmt.attributes['return_expression']
            stmt.isTypeCorrect = type_expr(expr)
            
            if stmt.isTypeCorrect and expr != None:
                stmt.isTypeCorrect = is_subtype(expr.type, ret_type)
        else:
            stmt.isTypeCorrect = ret_type == 'void'
    elif stmt.kind == 'Expr':
        stmt.isTypeCorrect = type_expr(stmt.attributes['expression'])
    elif stmt.kind == 'Block':
        return True
    else:
        stmt.isTypeCorrect = True
    
    return stmt.isTypeCorrect

def type_expr_err(expr):
    expr.type = 'error'
    expr.isTypeCorrect = False

def type_expr(expr):
    if expr == None:
        return True 
    if expr.kind == 'Block':
        type_block(expr)
    elif expr.kind == 'Constant':
        type_constant(expr)
    elif expr.kind == 'Variable':
        type_var(expr)
    elif expr.kind == 'Unary':
        type_unary(expr)
    elif expr.kind == 'Binary':
        type_binary(expr)
    elif expr.kind == 'Assign':
        type_assign(expr)
    elif expr.kind == 'Auto':
        type_auto(expr)
    elif expr.kind == 'Field_access':
        type_field(expr)
    elif expr.kind == 'Method_call':
        type_method_call(expr)
    elif expr.kind == 'New_object':
        type_new_obj(expr)
    elif expr.kind == 'This':
        expr.type = 'user(' + currClass.name + ')'
        expr.isTypeCorrect = True
    elif expr.kind == 'Super':
        if currClass.super_name != '':
            expr.type = 'user(' + currClass.super_name + ')'
            expr.isTypeCorrect = True
        else:
            type_expr_err(expr)
    elif expr.kind == 'Class_reference':
        type_class_ref(expr)

    return expr.isTypeCorrect

def type_constant(expr):
    const_expr = expr.attributes['Expression']
    if const_expr.kind == 'Integer_constant':
        expr.type = 'int'
        const_expr.type = 'int'
    elif const_expr.kind == 'Float_constant':
        expr.type = 'float'
        const_expr.type = 'float'
    elif const_expr.kind == 'String_constant':
        expr.type = 'string'
        const_expr.type = 'string'
    elif const_expr.kind == 'true' or const_expr.kind == 'false':
        expr.type = 'boolean'
        const_expr.type = 'boolean'
    elif const_expr.kind == 'null':
        expr.type = 'null'
        const_expr.type = 'null'
    
    if expr.type != None and const_expr.type != None:
        expr.isTypeCorrect = True
        const_expr.isTypeCorrect = True
    else:
        type_expr_err(expr)

def type_var(expr):
    global currFunc
    var_table = currFunc.variableTable
    for var in var_table:
        if var.id == expr.attributes['id']:
            if var.type.name not in base_types:
                expr.type = 'user(' + var.type.name + ')'
            else:
                expr.type = var.type.name
            expr.isTypeCorrect = True
            return
    type_expr_err(expr)

def type_unary(expr):
    operand = expr.attributes['operand']
    type_expr(operand)
    op = None
    if 'operator' in expr.attributes.keys():
        op = expr.attributes['operator']
    if op == 'uminus':        
        if operand.type == 'int' or operand.type == 'float':
            expr.type = operand.type
            expr.isTypeCorrect = True
        else:
            type_expr_err(expr)
    elif op == 'neg':
        if operand.type == 'boolean':
            expr.type = operand.type
            expr.isTypeCorrect = True
        else:
            type_expr_err(expr)       
    else:
        expr.type = operand.type
        expr.isTypeCorrect = operand.isTypeCorrect

def type_binary(expr):
    arithmetic = ['add', 'sub', 'mul', 'div']
    booleans = ['and', 'or'] 
    comparators = ['lt', 'leq', 'gt', 'geq'] 
    equals = ['eq', 'neq'] 

    operator = expr.attributes['operator']
    op1 = expr.attributes['operand1']
    type_expr(op1)
    op2 = expr.attributes['operand2']
    type_expr(op2)
    if operator in arithmetic:
        valid_types = ['float', 'int']
        if op1.type == 'int' and op2.type == 'int':
            expr.type = 'int'
            expr.isTypeCorrect = True
        elif op1.type in valid_types and op2.type in valid_types:
            expr.type = 'float'
            expr.isTypeCorrect = True
        else:
            type_expr_err(expr)
    elif operator in booleans or operator in comparators:
        valid_types = []
        if operator in booleans:
            valid_types = ['boolean']
        else:
            valid_types = ['int', 'float']
        if op1.type in valid_types and op2.type in valid_types:
            expr.type = 'boolean'
            expr.isTypeCorrect = True
        else:
            type_expr_err(expr)
    elif operator in equals:
        if is_subtype(op1.type, op2.type) or is_subtype(op2.type, op1.type):
            expr.type = 'boolean'
            expr.isTypeCorrect = True
        else:
            type_expr_err(expr)
    else:
        type_expr_err(expr)

def type_assign(expr):
    expr_left = expr.attributes['left']
    type_expr(expr_left)
    expr_right = expr.attributes['right']
    type_expr(expr_right)
    if expr_left.isTypeCorrect and expr_right.isTypeCorrect and is_subtype(expr_right.type, expr_left.type):
        expr.type = expr_right.type
        expr.isTypeCorrect = True
    else:
        type_expr_err(expr)

    expr.attributes['ltype'] = expr_left.type
    expr.attributes['rtype'] = expr_right.type

def type_auto(expr):
    operand = expr.attributes['operand']
    if not type_expr(operand):
        type_expr_err(expr)

    valid_types = ['int', 'float']
    if operand.type in valid_types:
        expr.type = operand.type
        expr.isTypeCorrect = True
    else:
        type_expr_err(expr)

def type_field(expr):
    base = expr.attributes['base']
    field = expr.attributes['field_name']
    if not type_expr(base):
        type_expr_err(expr)
        return

    applicability = ''
    class_name = ''
    if 'user' in base.type:
        applicability = 'instance'
        class_name = base.type[5:base.type.index(')')]
    elif 'class_literal' in base.type:
        applicability = 'static'
        class_name = base.type[14:base.type.index(')')]
    else:
        type_expr_err(expr)

    field_rec = None
    class_rec = None
    for clss in tree.classes:
        if clss.name == class_name:
            class_rec = clss
            break
    if class_rec == None:
        type_expr_err(expr)
        return

    super_rec = None
    if class_rec.super_name != "":
        for clss in tree.classes:
            if class_rec.super_name == clss.name:
                super_rec = clss
                break

    for fldd in class_rec.fields:
        if fldd.name == field:
            field_rec = fldd
            break
    if field_rec == None and super_rec != None:
        for fldd in super_rec.fields:
            if fldd.name == field:
                field_rec = fldd
                break
    if field_rec != None and field_rec.applicability == applicability:
        if field_rec.type.name not in base_types:
            expr.type = 'user(' + field_rec.type.name + ')'
        else:
            expr.type = field_rec.type.name
        expr.isTypeCorrect = True
        expr.attributes['id'] = field_rec.id
    else:
        type_expr_err(expr)

def type_method_call(expr):
    base = expr.attributes['base']
    method_name = expr.attributes['method_name']
    args = expr.attributes['arguments']
    if not type_expr(base):
        type_expr_err(expr)
        return

    applicability = ''
    class_name = ''
    if 'user' in base.type:
        applicability = 'instance'
        class_name = base.type[5:base.type.index(')')]
    elif 'class_literal' in base.type:
        applicability = 'static'
        class_name = base.type[14:base.type.index(')')]
    else:
        type_expr_err(expr)

    class_rec = None
    for clss in tree.classes:
        if clss.name == class_name:
            class_rec = clss
            break
    if class_rec == None:
        type_expr_err(expr)
        return

    super_rec = None
    if class_rec.super_name != "":
        for clss in tree.classes:
            if clss.name == class_rec.super_name:
                super_rec = clss
                break
 
    method_rec = None
    for curr_method in class_rec.methods:
        if curr_method.name == method_name:
            method_rec = curr_method
            break
    if method_rec == None and super_rec != None:
        for curr_method in super_rec.methods:
            if curr_method.name == method_name:
                method_rec = curr_method
                break
    if method_rec == None:
        type_expr_err(expr)
        return
    if not is_subtype(args, method_rec.parameters):
        type_expr_err(expr)
        return

    is_This = class_rec.name != currClass.name
    is_Super = class_rec.name != currClass.super_name
    if is_This and is_Super and method_rec.visibility == 'private':
        type_expr_err(expr)
        return

    if method_rec.applicability == applicability:
        if method_rec.returnType.name not in base_types:
            expr.type = 'user(' + method_rec.returnType.name + ')'
        else:
            expr.type = method_rec.returnType.name
        expr.isTypeCorrect = True
        expr.attributes['id'] = method_rec.id
    else:
        type_expr_err(expr)

def type_new_obj(expr):
    class_name = expr.attributes['class_name']
    args = expr.attributes['arguments']
    
    classRecord = None
    constructorRecord = None
    for clss in tree.classes:
        if clss.name == class_name:
            classRecord = clss
            break
    if classRecord == None:
        type_expr_err(expr)
        return
    for r in classRecord.constructors:
        if len(r.parameters) == len(args):
            constructorRecord = r
            break
    if constructorRecord == None:
        type_expr_err(expr)
        return
    if not is_subtype(args, constructorRecord.parameters):
        type_expr_err(expr)
        return

    if constructorRecord.visibility == "public" or constructorRecord.visibility == "" or currClass.super_name == class_name:
        expr.type = 'user(' + class_name + ')'
        expr.isTypeCorrect = True
        expr.attributes['id'] = constructorRecord.id
    else:
        type_expr_err(expr)    

def type_class_ref(expr):
    class_name = expr.attributes['class_name']
    class_rec = None
    for clss in tree.classes:
        if clss.name == class_name:
            class_rec = clss
            break
    
    if class_rec != None:
        expr.type = 'class_literal(' + class_name + ')'
        expr.isTypeCorrect = True
    else:
        type_expr_err(expr)

def is_subtype(t1, t2):
    if t1 == None or t2 == None:
        return False
    
    if type(t1) is list and type(t2) is list:
        if len(t1) != len(t2):
            return False
        for i in range(0, len(t1)):
            type_expr(t1[i])
            t1 = t1[i].type
            t2 = t2[i].type.name
            if not is_subtype(t1, t2):
                return False
        return True
    if t1 == t2:
        return True
    if t1 == 'int' and t2 == 'float':
        return True
    if t1 == 'null' and 'user' in t2:
        return True

    classA = None
    classB = None
    if 'user' in t1 and 'user' in t2:
        classA = t1[5:t1.index(')')]
        classB = t2[5:t2.index(')')]
    elif 'class_literal' in t1 and 'class_literal' in t2:
        classA = t1[14:t1.index(')')]
        classB = t2[14:t1.index(')')]
    
    if classA != None and classB != None:
        for clss in tree.classes:
            if clss.name == classA:
                return clss.super_name == classB
    
    return False

def signal_error(string):
    global error_flag
    print(string)
    error_flag = True
    exit()