# Name: Rahul Sarker
# NetID: rsarker
# Student ID: 113414194

reserved = {
    'boolean': 'BOOLEAN',
    'break': 'BREAK',
    'continue': 'CONTINUE',
    'class': 'CLASS',
    'do': 'DO',
    'else': 'ELSE',
    'extends': 'EXTENDS',
    'false': 'FALSE',
    'float': 'FLOAT',
    'for': 'FOR',
    'if': 'IF',
    'int': 'INT',
    'new': 'NEW',
    'null': 'NULL',
    'private': 'PRIVATE',
    'public': 'PUBLIC',
    'return': 'RETURN',
    'static': 'STATIC',
    'super': 'SUPER',
    'this': 'THIS',
    'true': 'TRUE',
    'void': 'VOID',
    'while': 'WHILE'
}

tokens = list(reserved.values()) + ['ID', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'INCREMENT', 'DECREMENT',
                                    'STRING_CONST', 'FLOAT_CONST', 'INT_CONST', 'NOT', 'ASSIGN', 'EQUALITY', 
                                    'GREATER', 'LESSER', 'GREATER_EQ', 'LESSER_EQ', 'NOT_EQUAL', 'AND', 'OR']

t_ignore = ' \t'
t_ignore_COMMENT = r'\/\/.*'
literals = ['(', ')', '{', '}', '.', ',', ';']

t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_INCREMENT = r'\+\+'
t_DECREMENT = r'--'
t_ASSIGN = r'='
t_EQUALITY = r'=='
t_NOT = r'!'
t_GREATER = r'>'
t_LESSER = r'<'
t_GREATER_EQ = r'>='
t_LESSER_EQ = r'<='
t_NOT_EQUAL = r'!='
t_AND = r'&&'
t_OR = r'\|\|'
start_ind = 1

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    global start_ind
    start_ind = t.lexpos + 1

def t_multi_line_comment(t):
    r'\/\*(.|\n)*?\*\/'
    t.lexer.lineno += t.value.count('\n')

def t_ID(t):
    r'[a-zA-Z][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'ID')  
    return t

def t_STRING_CONST(t):
    r'\".*?\"'
    t.value = t.value[1:len(t.value) - 1]
    return t

def t_FLOAT_CONST(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_INT_CONST(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_error(t):
    print(f"Error: Illegal character {t.value[0]} on line: {t.lexer.lineno}, column: {(t.lexpos - start_ind) + 1}")
    exit()