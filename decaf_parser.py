# Name: Rahul Sarker
# NetID: rsarker
# Student ID: 113414194

from decaf_lexer import tokens
import decaf_lexer as lexer
import decaf_ast as ast

con_ID = field_ID = method_ID = var_ID = 1
currentClass = ''
AST_tree = ast.AST()

precedence = (
    ('right', 'ASSIGN'),
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQUALITY', 'NOT_EQUAL'),
    ('nonassoc', 'LESSER', 'GREATER', 'GREATER_EQ', 'LESSER_EQ'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'U_PLUS', 'U_MINUS', 'NOT')
)

def p_program(p):
    '''program : class_decl
               | empty
    class_decl : class_decl class_decl 
    '''                         
    
def p_class_id(p):
    '''class_id : ID '''
    global currentClass
    currentClass = p[1]
    p[0] = p[1]                  
    
def p_class_decl(p): 
    '''class_decl : CLASS class_id EXTENDS ID '{' class_body_decl '}'
                  | CLASS class_id '{' class_body_decl '}' 
    '''
    global field_ID
    global method_ID
    global var_ID
    global con_ID
    global currentClass
     
    p[0] = ast.ClassRecord()        
    p[0].name = p[2]           
    currentClass = p[2] 
    body_index = 4          
    if p[3] == 'extends':         
        body_index = 6
        p[0].super_name = p[4]
        
    for record in p[body_index]:
        if type(record) is ast.ConstructorRecord:
            record.containingClass = currentClass
            record.id = con_ID
            con_ID = con_ID + 1
            p[0].constructors.append(record)
        elif type(record) is ast.MethodRecord:
            record.containingClass = currentClass
            record.id = method_ID
            method_ID = method_ID + 1
            p[0].methods.append(record)
        else:  
            for field in record:
                field.containingClass = currentClass
                field.id = field_ID
                field_ID = field_ID + 1
                p[0].fields.append(field)
            
    for clss in AST_tree.classes[2:]:   
        if(clss.name == p[0].name):
            print("Error: Duplicate class names")
            exit()

    for i in range(len(p[0].fields)):
        for j in range(len(p[0].fields)):
            if i == j:
                continue
            if p[0].fields[i].name == p[0].fields[j].name:
                print("Error: Duplicate field names")
                exit()
                
    for methd in p[0].methods:
        for i in range(len(methd.variableTable)):
            for j in range(len(methd.variableTable)):
                if i == j:
                    continue
                if methd.variableTable[i].name == methd.variableTable[j].name:
                    print("Error: Duplicate variable names")
                    exit()
    
    AST_tree.add_class(p[0])
                  
def p_class_body_decl(p):
    '''class_body_decl : class_body_decl class_body_decl
                       | field_decl
                       | method_decl
                       | constructor_decl 
    '''
    if len(p) == 3:
        p[0] = p[1] + p[2]
    if len(p) == 2:
        p[0] = [p[1]]
        
def p_type(p):
    '''type : INT
            | FLOAT
            | BOOLEAN
            | ID 
    '''
    p[0] = ast.TypeRecord(p[1])
                              
def p_modifier(p):
    '''modifier : PRIVATE STATIC
                | PRIVATE
                | PUBLIC STATIC
                | PUBLIC
                | STATIC
                | empty
    '''
    p[0] = p[1:]

def p_var_decl(p):
    '''var_decl : type variables ';' '''
    p[0] = []
    for var_name in p[2]:
        p[0] += [ast.VariableRecord(name = var_name, id = -1, kind = 'local', type = p[1])]

def p_variables(p):
    '''variables : variable
                 | variable ',' variables
    '''
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    if len(p) == 2:
        p[0] = [p[1]]

def p_variable(p):
    '''variable  : ID '''
    p[0] = p[1]
    
def p_fields(p):
    '''field_decl : modifier var_decl '''
    visibility = ''
    applicability = ''

    modifiers = p[1]
    if 'public' in modifiers:
        visibility = 'public'
    else:
        visibility = 'private'

    if 'static' in modifiers:
        applicability = 'static'
    else:
        applicability = 'instance'

    variables = p[2]     
    type = variables[0].type
    p[0] = []
    for var in variables:
        field = ast.FieldRecord(name = var.name, id = var.id, containingClass = currentClass, visibility = visibility, applicability = applicability, type = type)
        p[0] += [field]
        
def p_method_decl(p):
    '''method_decl : modifier type ID '(' optional_formals ')' block
                   | modifier VOID ID '(' optional_formals ')' block
    '''
    methodType = ''
    if p[2] == 'void':
        methodType = ast.TypeRecord('void')
    else:
        methodType = p[2]
        
    visibility = ''
    applicability = ''
    modifiers = p[1]
    if 'public' in modifiers:
        visibility = 'public'
    else:
        visibility = 'private'

    if 'static' in modifiers:
        applicability = 'static'
    else:
        applicability = 'instance'
        
    parameters = p[5]
    method_body = p[7]
    var_tab = []
    for param in parameters:
        param.kind = 'formal'
        var_tab.append(param)
    block_list = [method_body]
    while len(block_list) != 0:
        block = block_list.pop()
        block_list += block.attributes['inners']
        var_tab += block.attributes['var_tab']
    id = 1
    for stored_var in var_tab:
        if stored_var.kind != 'formal':
            stored_var.kind = 'local'
        stored_var.id = id
        id += 1
    add_vars(body = method_body, variableTable = var_tab)
    
    p[0] = ast.MethodRecord(name = p[3], id = 1, containingClass = currentClass, visibility = visibility, applicability = applicability, body = method_body, variableTable = var_tab, returnType = methodType, parameters = parameters)

def p_optional_formals(p):
    '''optional_formals : formals
                        | empty
    '''
    if p[1] is None:
        p[0] = []
    else:
        p[0] = p[1]

def p_formals(p):
    '''formals  : formal_param
                | formal_param ',' formals
    '''
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    if len(p) == 2:
        p[0] = [p[1]]

def p_formal_param(p):
    '''formal_param : type variable '''
    p[0] = ast.VariableRecord(name = p[2], id = 1, kind = 'formal', type = p[1])
    
def p_constructor_decl(p):
    '''constructor_decl : modifier ID '(' optional_formals ')' block '''
    visibility = ''
    modifiers = p[1]

    if 'public' in modifiers:
        visibility = 'public'
    else:
        visibility = 'private'
    parameters = p[4]
    body = p[6]
    var_tab = []
    for param in parameters:
        param.kind = 'formal'
        var_tab.append(param)

    block_list = [body]
    while len(block_list) != 0:
        block = block_list.pop()
        block_list += block.attributes['inners']
        var_tab += block.attributes['var_tab']
    id = 1
    for stored_var in var_tab:
        if stored_var.kind != 'formal':
            stored_var.kind = 'local'
        stored_var.id = id
        id += 1
    add_vars(body = body, variableTable = var_tab)
    
    p[0] = ast.ConstructorRecord(id = 1, visibility = visibility, parameters = parameters, variableTable = var_tab, body = body)

def add_vars(body = None, variableTable = None):
    if body == None or variableTable == None:
        return
    new_var_tab = body.attributes['var_tab']
    former_vars = []
    for stored_var in variableTable:
        if stored_var.kind == 'formal':
            former_vars.append(stored_var)
    new_var_tab += former_vars
    body.attributes['var_tab'] = new_var_tab
    block_list = [body]
    
    while len(block_list) != 0:   
        block = block_list.pop(0)
        block_list += block.attributes['inners']
        var_stmts = block.attributes['var_exprs']
        available_vars = {}
        i = 1
        max = -1
        available_vars[0] = block.attributes['var_tab']
        curr_block = block.attributes['outers']
        
        while curr_block != None:
            available_vars[i] = curr_block.attributes['var_tab']
            curr_block = curr_block.attributes['outers']
            i += 1
        max = i
        for stmt in var_stmts:
            target = stmt.attributes['var_name']
            level = 0
            found = False
            while level <= max:
                if level not in available_vars.keys():
                    break
                for stored_var in available_vars[level]:
                    if stored_var.name == target:
                        id = stored_var.id
                        stmt.attributes['id'] = id
                        found = True
                        break
                if found:
                    break
                level += 1

def p_block(p):
    '''block : '{' optional_stmts '}' '''
    p[0] = ast.Statement()
    p[0].kind = 'Block'
    p[0].attributes['stmts'] = p[2]
    stmt_queue = []
    var_tab = []
    for stmt in p[2]:
        if type(stmt) is list:
            for stored_var in stmt:
                var_tab.append(stored_var)
        else:
            stmt_queue.append(stmt)
    p[0].attributes['var_tab'] = var_tab
    
    inners = []
    expr_queue = []
    while len(stmt_queue) != 0:
        stmt = stmt_queue.pop()
        if stmt.kind == 'Block':
            inners.append(stmt)
        elif stmt.kind == 'If':
            stmt_queue.append(stmt.attributes['then'])
            expr_queue.append(stmt.attributes['condition'])
            if 'else' in stmt.attributes.keys():
                stmt_queue.append(stmt.attributes['else'])
        elif stmt.kind == 'While':
            stmt_queue.append(stmt.attributes['loop_body'])
            expr_queue.append(stmt.attributes['loop_condition'])
        elif stmt.kind == 'For':
            stmt_queue.append(stmt.attributes['loop_body'])
            expr_queue.append(stmt.attributes['initialize_expression'])
            expr_queue.append(stmt.attributes['loop_condition'])
            expr_queue.append(stmt.attributes['update_expression'])
        elif stmt.kind == 'Return':
            expr_queue.append(stmt.attributes['return_expression'])
        elif stmt.kind == 'Expr':
            expr_queue.append(stmt.attributes['expression'])
            
    p[0].attributes['inners'] = inners
    p[0].attributes['outers'] = None
    for block in inners:
        block.attributes.update({'outers' : p[0]})
    
    var_exprs = []
    while len(expr_queue) != 0:
        expr = expr_queue.pop()
        if expr is None:
            continue
        if expr.kind == 'Variable':
            var_exprs.append(expr)
        elif expr.kind == 'Auto' or expr.kind == 'Unary':
            expr_queue.append(expr.attributes['operand'])
        elif expr.kind == 'Assign':
            expr_queue.append(expr.attributes['left'])
            expr_queue.append(expr.attributes['right'])            
        elif expr.kind == 'Binary':
            expr_queue.append(expr.attributes['operand1'])
            expr_queue.append(expr.attributes['operand2'])
        elif expr.kind == 'Method_call' or expr.kind == 'New_object':
            if 'arguments' in expr.attributes.keys():
                for e in expr.attributes['arguments']:
                    expr_queue.append(e)
            if expr.kind == 'Method_call':
                if 'base' in expr.attributes.keys():
                    expr_queue.append(expr.attributes['base'])
        elif expr.kind == 'Field-access':
            if expr.attributes['base'].kind == 'Variable':
                var_exprs.append(expr.attributes['base'])
    p[0].attributes['var_exprs'] = var_exprs

    start_left, end_left = p.linespan(1)    
    start_right, end_right = p.linespan(len(p) - 1)    
    p[0].lineRange = [start_left, end_right]     
        
def p_optional_stmts(p):
    '''optional_stmts : stmt optional_stmts
                      | empty
    '''
    if len(p) == 3:
        if p[2] is None: 
            p[0] = [p[1]]
        else: 
            p[0] = [p[1]] + p[2]
    else: 
        p[0] = []
                
def p_statements(p):
    '''stmt : IF '(' expr ')' stmt ELSE stmt
            | IF '(' expr ')' stmt
            | WHILE '(' expr ')' stmt
            | FOR '(' optional_stmt_expr ';' optional_expr ';' optional_stmt_expr ')' stmt
            | RETURN optional_expr ';'
            | stmt_expr ';'
            | BREAK ';'
            | CONTINUE ';'
            | block
            | var_decl
            | ';'
    '''
    p[0] = ast.Statement()
    start_left, end_left = p.linespan(1)    
    start_right, end_right = p.linespan(len(p) - 1)    
    p[0].lineRange = [start_left, end_right]

    if p[1] == 'if':
        p[0].kind = 'If'
        p[0].attributes.update({'condition' : p[3]})
        p[0].attributes.update({'then' : p[5]})
        if len(p) > 6:
            p[0].attributes.update({'else' : p[7]})
    elif p[1] == 'for':
        p[0].kind = 'For'
        p[0].attributes.update({'initialize_expression' : p[3]})
        p[0].attributes.update({'loop_condition' : p[5]})
        p[0].attributes.update({'update_expression' : p[7]})
        p[0].attributes.update({'loop_body' : p[9]})
    elif p[1] == 'while':
        p[0].kind = 'While'
        p[0].attributes.update({'loop_condition' : p[3]})
        p[0].attributes.update({'loop_body' : p[5]})
    elif p[1] == 'return':
        p[0].kind = 'Return'
        p[0].attributes.update({'return_expression' : p[2]})
    elif len(p) == 3 and type(p[1]) is ast.Expression and p[2] == ';':
        p[0].kind = 'Expr'
        p[0].attributes.update({'expression' : p[1]})
    elif p[1] == 'break':
        p[0].kind = 'Break'
    elif p[1] == 'continue':
        p[0].kind = 'Continue'
    elif type(p[1]) is ast.Statement and p[1].kind == 'Block':
        p[0] = p[1]
    elif type(p[1]) is list and len(p[1]) != 0:      
        p[0] = p[1]
    else:
        p[0].kind = 'Skip'
        
def p_optional_expr(p):
    '''optional_expr : expr
                     | empty
  optional_stmt_expr : stmt_expr
                     | empty
    '''
    p[0] = p[1]
    
def p_literal(p):
    '''literal : INT_CONST
               | FLOAT_CONST
               | STRING_CONST
               | NULL
               | TRUE
               | FALSE
    '''
    p[0] = ast.Expression()
    start_left, end_left = p.linespan(1)    
    start_right, end_right = p.linespan(len(p) - 1)    
    p[0].lineRange = [start_left, end_right]

    p[0].kind = 'Constant'
    const_expr = ast.Expression() 
    values = ['true', 'false', 'null']

    if type(p[1]) is int:
        const_expr.kind = 'Integer_constant'
    elif type(p[1]) is float:
        const_expr.kind = 'Float_constant'
    elif type(p[1]) is str and p[1] not in values:
        const_expr.kind = 'String_constant'
    else:
        const_expr.kind = p[1] 
    if p[1] not in values: 
        const_expr.attributes.update({'value' : p[1]})

    p[0].attributes.update({'Expression' : const_expr})
    
def p_expr(p):
    '''expr : primary
            | assign
            | expr arith_op expr
            | expr bool_op expr
            | unary_op expr
    '''
    p[0] = ast.Expression()
    start_left, end_left = p.linespan(1)    
    start_right, end_right = p.linespan(len(p) - 1)    
    p[0].lineRange = [start_left, end_right]

    if len(p) == 2: 
        p[0] = p[1]
    elif len(p) == 3:
        p[0].kind = 'Unary'
        if p[1] != '':
            p[0].attributes.update({'operator' : p[1]})
        p[0].attributes.update({'operand' : p[2]})
    elif len(p) == 4: 
        p[0].kind = 'Binary'
        p[0].attributes.update({'operator' : p[2]})
        p[0].attributes.update({'operand1' : p[1]})
        p[0].attributes.update({'operand2' : p[3]})
        
def p_field_access(p):
    '''field_access : primary '.' ID
                    | ID
    '''
    p[0] = ast.Expression()
    p[0].kind = 'Field_access'
    start_left, end_left = p.linespan(1)    
    start_right, end_right = p.linespan(len(p) - 1)    
    p[0].lineRange = [start_left, end_right]
    if len(p) == 4:
        p[0].attributes.update({'base' : p[1]}) 
        p[0].attributes.update({'field_name' : p[3]}) 
    else: 
        if p[1] in AST_tree.get_classes() or p[1] == currentClass:
            p[0].kind = 'Class_reference'
            p[0].attributes.update({'class_name' : p[1]})
        else:            
            p[0].attributes.update({'var_name' : p[1]})
            p[0].kind = 'Variable'
            p[0].attributes.update({'id' : -1})
            
def p_assign_auto(p):
    '''assign : field_access ASSIGN expr
              | field_access INCREMENT
              | INCREMENT field_access
              | field_access DECREMENT
              | DECREMENT field_access
    '''
    p[0] = ast.Expression()
    start_left, end_left = p.linespan(1)    
    start_right, end_right = p.linespan(len(p) - 1)    
    p[0].lineRange = [start_left, end_right]
    ops = {
        '++': 'inc',
        '--': 'dec'
    }
    if len(p) == 3:
        order = 'invalid' 
        p[0].kind = 'Auto'
        if type(p[1]) is ast.Expression:
            order = 'post'
            p[0].attributes.update({'operand' : p[1]})
            p[0].attributes.update({'operation' : ops[p[2]]})
        elif type(p[2]) is ast.Expression:
            order = 'pre'
            p[0].attributes.update({'operand' : p[2]})
            p[0].attributes.update({'operation' : ops[p[1]]})
            
        p[0].attributes.update({'order' : order})
    else:
        p[0].kind = 'Assign'
        p[0].attributes.update({'left' : p[1]})
        p[0].attributes.update({'right' : p[3]})
        
def p_method_invocation(p):
    '''method_invocation : field_access '(' arguments ')'
                         | field_access '(' ')'
    '''
    p[0] = ast.Expression()
    start_left, end_left = p.linespan(1)    
    start_right, end_right = p.linespan(len(p) - 1)    
    p[0].lineRange = [start_left, end_right]
    p[0].kind = 'Method_call'

    if p[1].kind == 'Field_access':
        p[0].attributes.update({'base' : p[1].attributes['base']})
        p[0].attributes.update({'method_name' : p[1].attributes['field_name']})

    if len(p) == 5: 
        p[0].attributes.update({'arguments' : p[3]})
    else:
        p[0].attributes.update({'arguments' : []})
        
def p_arguments(p):
    '''arguments : expr
                 | expr ',' arguments
    '''
    p[0] = []
    p[0].append(p[1])
    if len(p) == 4:
        p[0] += p[3]

def p_expressions(p):
    '''primary : literal
               | THIS
               | SUPER
               | '(' expr ')'
               | NEW ID '(' arguments ')'
               | NEW ID '(' ')'
               | field_access
               | method_invocation
     stmt_expr : assign
               | method_invocation
    '''
    p[0] = ast.Expression()
    start_left, end_left = p.linespan(1)    
    start_right, end_right = p.linespan(len(p) - 1)    
    p[0].lineRange = [start_left, end_right]

    if len(p) == 2:
        if p[1] == 'this':
            p[0].kind = 'This'
        elif p[1] == 'super':
            p[0].kind = 'Super'
        else:
            p[0] = p[1]
    elif p[1] == 'new':
        p[0].kind = 'New_object'
        p[0].attributes.update({'class_name' : p[2]})
        if type(p[4]) is list:
            p[0].attributes.update({'arguments' : p[4]})
        else:
            p[0].attributes.update({'arguments' : []})
    elif len(p) == 4:
        p[0] = p[2]

def p_binary_op(p):
    '''arith_op : PLUS
                | MINUS
                | TIMES
                | DIVIDE
        bool_op : AND
                | OR
                | EQUALITY
                | NOT_EQUAL
                | LESSER
                | GREATER
                | LESSER_EQ
                | GREATER_EQ
    '''
    bin_operands = {
        '+': 'add',
        '-': 'sub', 
        '*': 'mul', 
        '/': 'div', 
        '&&': 'and', 
        '||': 'or', 
        '==': 'eq', 
        '!=': 'neq', 
        '<': 'lt', 
        '<=': 'leq', 
        '>': 'gt', 
        '>=': 'geq'
    }
    p[0] = bin_operands[p[1]]

def p_unary_op(p):
    '''unary_op : PLUS %prec U_PLUS
                | MINUS %prec U_MINUS
                | NOT
    '''
    un_ops = {
        '-': 'uminus',
        '!': 'neg',
        '+': ''
    }
    p[0] = un_ops[p[1]]
    
def p_empty(p):
    'empty :'
    pass

def p_error(p):
    if p is not None:
        print(f'Error: Syntax error on line: {p.lexer.lineno}, column: {p.lexpos - lexer.start_ind}')
    else:
        print('Unexpected error')
    exit()