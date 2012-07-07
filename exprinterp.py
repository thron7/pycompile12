# exprinterp.py
'''
Project 4 (Part 2) :  Write an Interpreter
==========================================

Once you've got your compiler emitting intermediate code, you should
be able to write a simple interpreter that runs the code.  This
can be useful for prototyping the execution environment, testing,
and other tasks involving the generated code.

Your task is simple, extend the Interpreter class below so that it
can run the code you generated in part 1.  The comments and docstrings
in the class describe it in further details.

When your done, you should be able to run simple programs by
typing:

    bash % python exprinterp.py someprogram.e
'''

import exprblock

class Interpreter(object):
    '''
    Runs an interpreter on the SSA intermediate code generated for
    your compiler.   The implementation idea is as follows.  Given
    a sequence of instruction tuples such as:

         code = [ 
              ('literal_int', 1, '_int_1'),
              ('literal_int', 2, '_int_2'),
              ('add_int', '_int_1', '_int_2, '_int_3')
              ('print_int', '_int_3')
              ...
         ]

    The class executes methods self.run_opcode(args).  For example:

             self.run_literal_int(1, '_int_1')
             self.run_literal_int(2, '_int_2')
             self.run_add_int('_int_1', '_int_2', '_int_3')
             self.run_print_int('_int_3')

    To store the values of variables created in the intermediate
    language, simply use a dictionary.

    For external function declarations, allow specific Python modules
    (e.g., math, os, etc.) to be registered with the interpreter.
    We don't have namespaces in the source language so this is going
    to be a bit of sick hack.
    '''
    def __init__(self,name="module"):
        # Dictionary of currently defined variables
        self.vars = {}

        # List of Python modules to search for external decls
        external_libs = [ 'math', 'os' ]
        self.external_libs = [ __import__(name) for name in external_libs ]

    def run(self, ircode):
        '''
        Run intermediate code in the interpreter.  ircode is a list
        of instruction tuples.  Each instruction (opcode, *args) is 
        dispatched to a method self.run_opcode(*args)
        '''
        self.pc = 0
        while True:
            try:
                op = ircode[self.pc]
            except IndexError:
                if self.pc > len(ircode):
                    print "Wrong PC %d - terminating" % self.pc
                return
            self.pc += 1
            opcode = op[0]
            if hasattr(self, "run_"+opcode):
                getattr(self, "run_"+opcode)(*op[1:])
            else:
                print "Warning: No run_"+opcode+"() method"
        
    # YOU MUST IMPLEMENT:  Methods for different opcodes.  A few sample
    # opcodes are shown below to get you started.

    def run_jump(self, label):
        self.pc = label

    def run_cbranch(self, cond, if_label, else_label):
        if self.vars[cond]:
            self.pc = if_label
        else:
            self.pc = else_label

    def run_literal_int(self, value, target):
        '''
        Create a literal integer value
        '''
        self.vars[target] = value

    def run_add_int(self, left, right, target):
        '''
        Add two integer varibles
        '''
        self.vars[target] = self.vars[left] + self.vars[right]

    def run_print_int(self, source):
        '''
        Output an integer value.
        '''
        print self.vars[source]

    run_literal_float = run_literal_int
    run_literal_string = run_literal_int

    def run_alloc_int(self, name):
        self.vars[name] = 0

    def run_alloc_float(self, name):
        self.vars[name] = 0.0

    def run_alloc_string(self, name):
        self.vars[name] = ''

    def run_store_int(self, source, target):
        self.vars[target] = self.vars[source]

    run_store_float = run_store_int
    run_store_string = run_store_int

    def run_load_int(self, name, target):
        self.vars[target] = self.vars[name]

    run_load_float = run_load_int
    run_load_string = run_load_int

    run_add_float = run_add_int
    run_add_string = run_add_int

    def run_sub_int(self, left, right, target):
        self.vars[target] = self.vars[left] - self.vars[right]

    run_sub_float = run_sub_int

    def run_mul_int(self, left, right, target):
        self.vars[target] = self.vars[left] * self.vars[right]

    run_mul_float = run_mul_int

    def run_div_int(self, left, right, target):
        self.vars[target] = self.vars[left] // self.vars[right]

    def run_div_float(self, left, right, target):
        self.vars[target] = self.vars[left] / self.vars[right]

    def run_uadd_int(self, source, target):
        self.vars[target] = self.vars[source]

    run_uadd_float = run_uadd_int

    def run_usub_int(self, source, target):
        self.vars[target] = -self.vars[source]

    run_usub_float = run_usub_int

    def run_cmp_int(self, op, left, right, target):
        compare = cmp(self.vars[left], self.vars[right])
        if op == 'lt':
            result = bool(compare < 0)
        elif op == 'le':
            result = bool(compare <= 0)
        elif op == 'eq':
            result = bool(compare == 0)
        elif op == 'ne':
            result = bool(compare != 0)
        elif op == 'ge':
            result = bool(compare >= 0)
        elif op == 'gt':
            result = bool(compare > 0)
        elif op == 'land':
            result = self.vars[left] and self.vars[right]
        elif op == 'lor':
            result = self.vars[left] or self.vars[right]
        self.vars[target] = result

    run_cmp_float = run_cmp_int
    run_cmp_bool = run_cmp_int

    run_print_float = run_print_int
    run_print_string = run_print_int

    def run_extern_func(self, name, rettypename, *parmtypenames):
        '''
        Scan the list of external modules for a matching function name.
        Place a reference to the external function in the dict of vars.
        '''
        for module in self.external_libs:
            func = getattr(module, name, None)
            if func:
                self.vars[name] = func
                break
        else:
            raise RuntimeError("No extern function %s found" % name)

    def run_call_func(self, funcname, *args):
        '''
        Call a previously declared external function.
        '''
        target = args[-1]
        func = self.vars.get(funcname)
        argvals = [self.vars[name] for name in args[:-1]]
        self.vars[target] = func(*argvals)

class BlockLinker(exprblock.BlockVisitor):
    def __init__(self):
        self.code = []
        self.code_map = {}
        self.jump_list = []

    def rec_jump(self):
        self.jump_list.append(len(self.code))

    def rec_block(self, block):
        self.code_map[block] = len(self.code)

    def patch_jumps(self):
        for n in self.jump_list:
            self.code[n] = tuple(self.code_map.get(e,e) for e in self.code[n])

    def visit_BasicBlock(self, block):
        self.rec_block(block)
        self.code.extend(block.instructions)
        if block.next_block:
            self.rec_jump()
            self.code.append(('jump', block.next_block))

    def visit_IfBlock(self,block):
        self.rec_block(block)
        self.code.extend(block.instructions)
        # then branch
        self.rec_jump()
        self.code.append(('cbranch', block.test, 
            block.if_branch, 
            block.else_branch if block.else_branch else block.next_block))
        self.visit(block.if_branch)
        self.rec_jump()
        self.code.append(('jump', block.next_block))
        # else branch
        if block.else_branch:
            self.visit(block.else_branch)
            self.rec_jump()
            self.code.append(('jump', block.next_block))

    def visit_WhileBlock(self, block):
        self.rec_block(block)
        self.code.extend(block.instructions)
        self.visit(block.test)
        self.rec_jump()
        self.code.append(('cbranch', block.test,
            block.body, block.next_block))
        self.visit(block.body)
        self.rec_jump()
        self.code.append(('jump', block))


def get_options():
    
    parser = optparse.OptionParser()
    parser.add_option("-c", "--show-instructions",
                     action="store_true", dest="show_code", default=False,
                     help="show linearized 3A instructions")
    options, args = parser.parse_args(sys.argv[1:])
    return options, args


# ----------------------------------------------------------------------
#                       DO NOT MODIFY ANYTHING BELOW       
# ----------------------------------------------------------------------
if __name__ == '__main__':
    import exprlex
    import exprparse
    import exprcheck
    import exprcode
    import sys
    import optparse
    from errors import subscribe_errors, errors_reported

    options, args = get_options()
    lexer = exprlex.make_lexer()
    parser = exprparse.make_parser()
    with subscribe_errors(lambda msg: sys.stdout.write(msg+"\n")):
        program = parser.parse(open(sys.argv[1]).read())
        # Check the program
        exprcheck.check_program(program)
        # If no errors occurred, generate code
        if not errors_reported():
            code = exprcode.generate_code(program)
            linker = BlockLinker()
            linker.visit(code.start_block)
            linker.patch_jumps()

            if options.show_code:
                for n, inst in enumerate(linker.code):
                    print n,":", inst
                print "GIVES"

            interpreter = Interpreter()
            interpreter.run(linker.code)



        
        
        
