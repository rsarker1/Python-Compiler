# Name: Rahul Sarker
# NetID: rsarker
# Student ID: 113414194

class ClassRecord:
    def __init__(self, name = "", super_name = "", constructors = None, methods = None, fields = None):
        self.name = name 
        self.super_name = super_name 
        
        if methods is None:
            self.methods = []
        else:
            self.methods = methods 
        if constructors is None:
            self.constructors = []
        else:
            self.constructors = constructors 
        if fields is None:
            self.fields = []
        else:
            self.fields = fields 

class ConstructorRecord:
    def __init__(self, id = -1, visibility = "", parameters = None, variableTable = None, body = None):
        self.id = id 
        self.visibility = visibility 
        self.body = body 
        
        if parameters is None:
            self.parameters = []
        else:
            self.parameters = parameters
        if variableTable is None:
            self.variableTable = []
        else:
            self.variableTable = variableTable

class MethodRecord:
    def __init__(self, name = "", id = -1, containingClass = "", visibility = "", applicability = "", body = None, variableTable = None, returnType = None, parameters = None):
        self.name = name 
        self.id = id 
        self.containingClass = containingClass 
        self.visibility = visibility 
        self.applicability = applicability 
        self.body = body 
        self.returnType = returnType 

        if variableTable is None:
            self.variableTable = []
        else:
            self.variableTable = variableTable
        if parameters is None:
            self.parameters = []
        else:
            self.parameters = parameters

class FieldRecord:
    def __init__(self, name = "", id = -1, containingClass = "", visibility = "", applicability = "", type = None):
        self.name = name 
        self.id = id 
        self.containingClass = containingClass 
        self.visibility = visibility 
        self.applicability = applicability 
        self.type = type 

class VariableRecord:
    def __init__(self, name = "", id = -1, kind = "", type = None):
        self.name = name 
        self.id = id 
        self.kind = kind 
        self.type = type 

class TypeRecord:
    def __init__(self, name = ""):
        self.name = name 

class Statement:
    def __init__(self, lineRange = None, kind = '', attributes = None):
        self.kind = kind 
        
        if attributes is None:
            self.attributes = {}
        else:
            self.attributes = attributes
        if lineRange is None:
            self.lineRange = []
        else:
            self.lineRange = lineRange
             
        self.isTypeCorrect = False

class Expression:
    def __init__(self, lineRange = None, kind = '', attributes = None):
        self.kind = kind 
        
        if attributes is None:
            self.attributes = {}
        else:
            self.attributes = attributes
        if lineRange is None:
            self.lineRange = []
        else:
            self.lineRange = lineRange
            
        self.type = None
        self.isTypeCorrect = False

class AST:
    def __init__(self): 
        self.classes = []

        scanInt = MethodRecord(name = "scan_int", id = 1, containingClass = "In", visibility = "public", applicability = "static", returnType = TypeRecord(name = "int"))
        scanFloat = MethodRecord(name = "scan_float", id = 2, containingClass = "In", visibility = "public", applicability = "static", returnType = TypeRecord(name = "float"))
        in_Methods = [scanInt, scanFloat]
        in_Class = ClassRecord(name = "In", methods = in_Methods)
        
        i = VariableRecord(name = "i", id = 1, kind = "formal", type = TypeRecord(name = "int"))
        f = VariableRecord(name = "f", id = 2, kind = "formal", type = TypeRecord(name = "float"))
        b = VariableRecord(name = "b", id = 3, kind = "formal", type = TypeRecord(name = "boolean"))
        s = VariableRecord(name = "s", id = 4, kind = "formal", type = TypeRecord(name = "string"))
        print1 = MethodRecord(name = "print", id = 1, containingClass = "Out", visibility = "public", applicability = "static", parameters = [i], variableTable = [i], returnType  =  TypeRecord('void'))
        print2 = MethodRecord(name = "print", id = 2, containingClass = "Out", visibility = "public", applicability = "static", parameters = [f], variableTable = [f], returnType  =  TypeRecord('void'))
        print3 = MethodRecord(name = "print", id = 3, containingClass = "Out", visibility = "public", applicability = "static", parameters = [b], variableTable = [b], returnType  =  TypeRecord('void'))
        print4 = MethodRecord(name = "print", id = 4, containingClass = "Out", visibility = "public", applicability = "static", parameters = [s], variableTable = [s], returnType  =  TypeRecord('void'))
        out_Methods = [print1, print2, print3, print4]
        out_Class = ClassRecord(name = "Out", methods = out_Methods)

        self.classes.append(in_Class)
        self.classes.append(out_Class)

    def get_classes(self):
        cnames = []
        for c in self.classes:
            cnames.append(c.name)
        return cnames

    def add_class(self, clss):
        self.classes.append(clss)

    def print_table(self):
        sep = '--------------------------------------------------------------------------'
        print(sep)
        base_classes = 0
        for clss in self.classes:
            if base_classes < 2:
                base_classes += 1
                continue
            self.print_class(clss)
            print(sep)

    def print_class(self, clss):
        print("Class Name: ", clss.name)
        print("Superclass Name: ", clss.super_name)
        print("Fields: ")
        for f in clss.fields:
            self.print_field(f)
        print("Constructors: ")
        for c in clss.constructors:
            self.print_constructor(c)
        print("Methods: ")
        for m in clss.methods:
            self.print_method(m)

    def print_field(self, f):
        built_in = ['int', 'float', 'boolean']
        check_type = f.type.name
        if check_type not in built_in:
                check_type = f"user({str(f.type.name)})"
        print(f"FIELD: {str(f.id)}, {f.name}, {f.containingClass}, {f.visibility}, {f.applicability}, {check_type}")

    def print_constructor(self, c):
        print(f"CONSTRUCTOR: {str(c.id)} {c.visibility}")
        param_str = ''
        for p in c.parameters:
            if(param_str == ''):
                param_str = str(p.id)
            else:
                param_str += ', ' + str(p.id)
        print(f"Constructor Parameters: {param_str}")
        self.print_var_table(c.variableTable)
        print("Constructor Body: ")
        self.print_body(c.body)

    def print_method(self, m):
        print(f"METHOD: {m.id}, {m.name}, {m.containingClass}, {m.visibility}, {m.applicability}, {m.returnType.name}")
        param_str = ''
        for p in m.parameters:
            if(param_str == ''):
                param_str = str(p.id)
            else:
                param_str += ', ' + str(p.id)
        print(f"Method Parameters: {param_str}")
        self.print_var_table(m.variableTable)
        print("Method Body: ")
        self.print_body(m.body)

    def print_var_table(self, var_table):
        print("Variable Table: ")
        built_in = ['int', 'float', 'boolean']
        for t in var_table:
            check_type = t.type.name
            if check_type not in built_in:
                check_type = f"user({str(t.type.name)})"
            print(f"VARIABLE {str(t.id)}, {t.name}, {t.kind}, {check_type}")

    def print_body(self, stmt):
        if stmt is None or stmt is list:
            return
        body = ''
        if(stmt.kind == 'Block'):
            body = self.create_block(stmt.attributes['stmts'])
        else:
            body = self.create_stmt(stmt)
        print(body)

    def create_block(self, stmts):
        body = ''
        for stmt in stmts:
            if type(stmt) is list:
                continue
            elif stmt.kind == 'Block':
                body += self.create_block(stmt.attributes['stmts']) + ', '
            else:
                tmp = self.create_stmt(stmt)
                if tmp != '':
                    body += self.create_stmt(stmt) + ', '
        body = body[0:-2] 
        s = f"Block ([\n{body}\n])"
        return s

    def create_stmt(self, stmt):
        body = ''
        if stmt.kind == 'Skip':
            return body
        for val in stmt.attributes.values():
            if type(val) is Statement:
                if val.kind == 'Block':
                    body += self.create_block(val.attributes['stmts'])
                elif val.kind == 'Skip':
                    continue
                else:
                    body += self.create_stmt(val)
            elif type(val) is Expression:
                body += self.create_expr(val)
            elif val != None:
                content += str(val)
            body += ', '
    
        if body == '':
            s = stmt.kind
        else:
            s = f"{stmt.kind} ({body[0:-2]})" 
        return s
    
    def create_expr(self, expr):
        body = ''
        if 'var_name' in expr.attributes.keys():
            del expr.attributes['var_name']
        
        for val in expr.attributes.values():
            if type(val) is Expression:
                body += self.create_expr(val)
            elif type(val) is list and len(val) > 0 and type(val[0]) is Expression:
                body += self.create_expr_list(val)
            else:
                body += str(val)
            body += ', '

        if body == '':
            s = expr.kind
        else:
            s = f"{expr.kind} ({body[0:-2]})"
        return s

    def create_expr_list(self, list):
        body = ''
        for expr in list:
            body += f"{self.create_expr(expr)}, " 
        return f"[{body[0:-2]}]"