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
                break
            self.pc += 1
            opcode = op[0]
            if hasattr(self, "run_"+opcode):
                getattr(self, "run_"+opcode)(*op[1:])
            else:
                print "Warning: No run_"+opcode+"() method"

    def run_jump(self, target):
        self.pc = target

    def run_cbranch(self, testvar, if_true, if_false):
        if self.vars[testvar]:
            self.pc = if_true
        else:
            self.pc = if_false
            
    # YOU MUST IMPLEMENT:  Methods for different opcodes.  A few sample
    # opcodes are shown below to get you started.

    def run_literal_int(self, value, target):
        '''
        Create a literal integer value
        '''
        self.vars[target] = value

    run_literal_float = run_literal_int
    run_literal_string = run_literal_int
    run_literal_bool = run_literal_int
    
    def run_add_int(self, left, right, target):
        '''
        Add two integer varibles
        '''
        self.vars[target] = self.vars[left] + self.vars[right]

    def run_sub_int(self, left, right, target):
        '''
        Subtract two integer varibles
        '''
        self.vars[target] = self.vars[left] - self.vars[right]

    def run_mul_int(self, left, right, target):
        '''
        Multiply two integer varibles
        '''
        self.vars[target] = self.vars[left] * self.vars[right]

    def run_div_int(self, left, right, target):
        '''
        Divide two integer varibles
        '''
        self.vars[target] = self.vars[left] / self.vars[right]

    # Floating point ops (same as int)
    run_add_float = run_add_int
    run_sub_float = run_sub_int
    run_mul_float = run_mul_int
    run_div_float = run_div_int

    # Integer comparisons
    def run_lt_int(self, left, right, target):
        self.vars[target] = self.vars[left] < self.vars[right]
    def run_le_int(self, left, right, target):
        self.vars[target] = self.vars[left] <= self.vars[right]
    def run_gt_int(self, left, right, target):
        self.vars[target] = self.vars[left] > self.vars[right]
    def run_ge_int(self, left, right, target):
        self.vars[target] = self.vars[left] >= self.vars[right]
    def run_eq_int(self, left, right, target):
        self.vars[target] = self.vars[left] == self.vars[right]
    def run_ne_int(self, left, right, target):
        self.vars[target] = self.vars[left] != self.vars[right]

    # Float comparisons
    run_lt_float = run_lt_int
    run_le_float = run_le_int
    run_gt_float = run_gt_int
    run_ge_float = run_ge_int
    run_eq_float = run_eq_int
    run_ne_float = run_ne_int

    # String comparisons
    run_lt_string = run_lt_int
    run_le_string= run_le_int
    run_gt_string = run_gt_int
    run_ge_string = run_ge_int
    run_eq_string = run_eq_int
    run_ne_string = run_ne_int

    # Bool comparisons
    run_eq_bool = run_eq_int
    run_ne_bool = run_ne_int

    # Booleans
    def run_land_bool(self, left, right, target):
        self.vars[target] = self.vars[left] and self.vars[right]

    def run_lor_bool(self, left, right, target):
        self.vars[target] = self.vars[left] or self.vars[right]
        
    # Unary ops
    def run_uadd_int(self, source, target):
        self.vars[target] = self.vars[source]

    def run_usub_int(self, source, target):
        self.vars[target] = -self.vars[source]

    def run_lnot_bool(self, source, target):
        self.vars[target] = not self.vars[source]
        
    run_uadd_float = run_uadd_int
    run_usub_float = run_usub_int
    
    # String ops
    run_add_string = run_add_int

    def run_print_int(self, source):
        '''
        Output an integer value.
        '''
        print self.vars[source]

    run_print_float = run_print_int
    run_print_string = run_print_int
    run_print_bool = run_print_int
    
    # Load/store
    def run_load_int(self, source, target):
        self.vars[target] = self.vars[source]

    run_load_float = run_load_int
    run_load_string = run_load_int
    run_load_bool = run_load_int
    
    def run_store_int(self, source, target):
        self.vars[target] = self.vars[source]

    run_store_float = run_store_int
    run_store_string = run_store_int
    run_store_bool = run_store_int
    
    # Allocation of variables
    def run_alloc_int(self, name):
        self.vars[name] = 0

    def run_alloc_float(self, name):
        self.vars[name] = 0.0

    def run_alloc_string(self, name):
        self.vars[name] = ""

    def run_alloc_bool(self, name):
        self.vars[name] = False
        
    def run_extern_func(self, name, *args):
        '''
        Scan the list of external modules for a matching function name.
        Place a reference to the external function in the dict of vars.
        '''
        rettypename = args[-1]
        parmtypenames = args[:-1]
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

import exprblock

class LinkBlocks(exprblock.BlockVisitor):
    def __init__(self):
        self.code = []     # All code as a single list
        self.block_map = { }    # Maps blocks to index in self.code

    def fix_jumps(self):
        patch_list = [n - 1 for n in self.block_map.values() if n > 0]
        for n in patch_list:
            self.code[n] = tuple(self.block_map.get(x,x) for x in self.code[n])
            
    def visit_BasicBlock(self, block):
        self.block_map[block] = len(self.code)
        self.code.extend(block.instructions)
        if block.next_block:
            self.code.append(('jump', block.next_block))
        
    def visit_IfBlock(self, block):
        self.block_map[block] = len(self.code)        
        self.code.extend(block.instructions)
        # Conditional branch based on test variable
        self.code.append(('cbranch', block.testvar, block.if_branch, block.else_branch))

        self.visit(block.if_branch)
        self.code.append(('jump', block.next_block))

        if block.else_branch:
            self.visit(block.else_branch)
            self.code.append(('jump', block.next_block))

    def visit_WhileBlock(self, block):
        self.block_map[block] = len(self.code)
        self.code.extend(block.instructions)
        self.code.append(('cbranch', block.testvar, block.body, block.next_block))
        # Visit the body of the loop
        self.visit(block.body)
        self.code.append(('jump', block))    # Jump back to start of while block
    
# ----------------------------------------------------------------------
#                       DO NOT MODIFY ANYTHING BELOW       
# ----------------------------------------------------------------------
if __name__ == '__main__':
    import exprlex
    import exprparse
    import exprcheck
    import exprcode
    import sys
    from errors import subscribe_errors, errors_reported

    lexer = exprlex.make_lexer()
    parser = exprparse.make_parser()
    with subscribe_errors(lambda msg: sys.stdout.write(msg+"\n")):
        program = parser.parse(open(sys.argv[1]).read())
        # Check the program
        exprcheck.check_program(program)
        # If no errors occurred, generate code
        if not errors_reported():
            code = exprcode.generate_code(program)
            linker = LinkBlocks()
            linker.visit(code.start)    # Code generator records start block
            linker.fix_jumps()
            
            for n, inst in enumerate(linker.code):
                print n,":", inst
            print "RUNNING"
            interpreter = Interpreter()
            interpreter.run(linker.code)



        
        
        
