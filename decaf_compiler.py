# Name: Rahul Sarker
# NetID: rsarker
# Student ID: 113414194

import sys
import ply.lex as lex
import ply.yacc as yacc
from decaf_parser import AST_tree
import decaf_typecheck
import decaf_codegen
from decaf_absmc import abstract_machine

def main():
    fn = sys.argv[1] if len(sys.argv) > 1 else ""
    if fn == "":
        print("Missing file name for source program.")
        print("USAGE: python3 decaf_checker.py <decaf_source_file_name>")
        sys.exit()
    import decaf_lexer
    import decaf_parser
    lexer = lex.lex(module = decaf_lexer)
    parser = yacc.yacc(module = decaf_parser)

    fh = open(fn, 'r')
    source = fh.read()
    fh.close()
    parser.parse(source, lexer = lexer)
    decaf_typecheck.check_types(AST_tree)
    if not decaf_typecheck.error_flag:
        decaf_codegen.generate_code(AST_tree.classes)
        filename = f"{fn.rpartition('.')[0]}.ami"
        machine_code = open(filename, 'w')
        machine_code.write(abstract_machine.machine_code_str())
        machine_code.close()
        return 

if __name__ == "__main__":
    main()
