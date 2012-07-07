# exprllm.py

'''
Project 5 : Generate LLVM
=========================
In this project, you're going to translate the SSA intermediate code
into LLVM IR.    Once you're done, your code will be runnable.  It
is strongly advised that you do *all* of the steps of Exercise 5
prior to starting this project.   Don't rush into it.

The basic idea of this project is exactly the same as the interpreter
in Project 4.   You'll make a class that walks through the instruction
sequence and triggers a method for each kind of instruction.  Instead
of running the instruction however, you'll be generating LLVM 
instructions.

Further instructions are contained in the comments.
'''

# LLVM imports. Don't change this.
from llvm.core import Module, Builder, Function, Type, Constant, GlobalVariable
from llvm.ee import ExecutionEngine

# Declare the LLVM type objects that you want to use for the types
# in our intermediate code.  Basically, you're going to need to 
# declare your integer, float, and string types here.

int_type    = Type.int()         # 32-bit integer
float_type  = Type.double()      # 64-bit float
string_type = None               # Up to you (leave until the end)

# A dictionary that maps the typenames used in IR to the corresponding
# LLVM types defined above.   This is mainly provided for convenience
# so you can quickly look up the type object given its type name.
typemap = {
    'int' : int_type,
    'float' : float_type,
    'string' : string_type
}

# The following class is going to generate the LLVM instruction stream.  
# The basic features of this class are going to mirror the experiments
# you tried in Exercise 5.  The execution module is very similar
# to the interpreter written in Project 4.  See specific comments 
# in the class. 

import exprast
from collections import defaultdict

import ctypes
ctypes._dlopen("./ex5.so", ctypes.RTLD_GLOBAL)

# STEP 1: Map map operator symbol names such as +, -, *, /
# to actual opcode names 'add','sub','mul','div' to be emitted in
# the SSA code.   This is easy to do using dictionaries:

binary_ops = {
    '+' : 'add',
    '-' : 'sub',
    '*' : 'mul',
    '/' : 'div',
}

unary_ops = {
    '+' : 'uadd',
    '-' : 'usub'
}

# STEP 2: Implement the following Node Visitor class so that it creates
# a sequence of SSA instructions in the form of tuples.  Use the
# above description of the allowed op-codes as a guide.
class GenerateLLVM(exprast.NodeVisitor):
    '''
    Node visitor class that creates 3-address encoded instruction sequences.
    '''
    def __init__(self):
        super(GenerateLLVM, self).__init__()

        # version dictionary for temporaries
        self.versions = defaultdict(int)

        # The generated code (list of tuples)
        self.code = []

        # A list of external declarations (and types)
        self.externs = []

        # LLVM
        self.init_llvm()

    def init_llvm(self):
        mod = Module.new("exprllvm")
        self.engine = ExecutionEngine.new(mod)

        # functions
        self.llvm_functions = {}
        func = Function.new(mod, Type.function(
            Type.void(), [], False), "main")
        self.llvm_functions['main'] = func
        block = func.append_basic_block("entry")

        # builder
        builder = Builder.new(block)
        self.builder = builder

        # add some pre-defined functions
        print_int = Function.new(mod, Type.function(
            Type.void(), [Type.int()], False), "print_int")
        self.llvm_functions['print_int'] = print_int

        self.builder.call(print_int, [Constant.int(Type.int(),3)])
        self.builder.ret_void()


    def new_temp(self,typeobj):
        '''
        Create a new temporary variable of a given type.
        '''
        name = "__%s_%d" % (typeobj.name, self.versions[typeobj.name])
        self.versions[typeobj.name] += 1
        return name

    # You must implement visit_Nodename methods for all of the other
    # AST nodes.  In your code, you will need to make instructions
    # and append them to the self.code list.
    #
    # A few sample methods follow.  You may have to adjust depending
    # on the names of the AST nodes you've defined.

    def visit_Literal(self,node):
        # Create a new temporary variable name 
        target = self.new_temp(node.type)

        # Make the SSA opcode and append to list of generated instructions
        inst = ('literal_'+node.type.name, node.value, target)
        self.code.append(inst)

        # Save the name of the temporary variable where the value was placed 
        node.gen_location = target

    def visit_BinaryOp(self,node):
        # Visit the left and right expressions
        self.visit(node.left)
        self.visit(node.right)

        # Make a new temporary for storing the result
        target = self.new_temp(node.type)

        # Create the opcode and append to list
        opcode = binary_ops[node.op] + "_"+node.left.type.name
        inst = (opcode, node.left.gen_location, node.right.gen_location, target)
        self.code.append(inst)

        # Store location of the result on the node
        node.gen_location = target

    def visit_PrintStatement(self,node):
        # Visit the printed expression
        self.visit(node.expr)

        # Create the opcode and append to list
        inst = ('print_'+node.expr.type.name, node.expr.gen_location)
        self.code.append(inst)
        self.builder

    def visit_Program(self,node):
        self.visit(node.program)

    #def visit_Statements(self,node):
    #    self.visit(node.expr)
    #    inst = ('print_'+node.expr.type.name, node.expr.gen_location)
    #    self.code.append(inst)

    #def visit_Statement(self,node):
    #    self.visit(node.expr)
    #    inst = ('print_'+node.expr.type.name, node.expr.gen_location)
    #    self.code.append(inst)

    def visit_ConstDeclaration(self,node):
        # allocate in memory
        inst = ('alloc_'+node.type.name, 
                    node.id)
        self.code.append(inst)
        # store init val
        self.visit(node.value)
        inst = ('store_'+node.type.name,
                node.value.gen_location,
                node.id)
        self.code.append(inst)

    def visit_VarDeclaration(self,node):
        # allocate in memory
        inst = ('alloc_'+node.type.name, 
                    node.id)
        self.code.append(inst)
        # store pot. init val
        if node.value:
            self.visit(node.value)
            inst = ('store_'+node.type.name,
                    node.value.gen_location,
                    node.id)
            self.code.append(inst)

    def visit_LoadLocation(self,node):
        target = self.new_temp(node.type)
        inst = ('load_'+node.type.name,
                node.name,
                target)
        self.code.append(inst)
        node.gen_location = target

    #def visit_Extern(self,node):
    #    self.visit(node.expr)
    #    inst = ('print_'+node.expr.type.name, node.expr.gen_location)
    #    self.code.append(inst)

    #def visit_FuncPrototype(self,node):
    #    self.visit(node.expr)
    #    inst = ('print_'+node.expr.type.name, node.expr.gen_location)
    #    self.code.append(inst)

    #def visit_Parameters(self,node):
    #    self.visit(node.expr)
    #    inst = ('print_'+node.expr.type.name, node.expr.gen_location)
    #    self.code.append(inst)
    #    node.gen_location = target

    #def visit_ParamDecl(self,node):
    #    self.visit(node.expr)
    #    inst = ('print_'+node.expr.type.name, node.expr.gen_location)
    #    self.code.append(inst)

    def visit_AssignmentStatement(self,node):
        self.visit(node.value)
        
        inst = ('store_'+node.value.type.name, 
                node.value.gen_location, 
                node.location)
        self.code.append(inst)

    def visit_UnaryOp(self,node):
        self.visit(node.left)
        target = self.new_temp(node.type)
        opcode = unary_ops[node.op] + "_" + node.left.type.name
        inst = (opcode, node.left.gen_location)
        self.code.append(inst)
        node.gen_location = target

    #def visit_Group(self,node):
    #    self.visit(node.expr)
    #    inst = ('print_'+node.expr.type.name, node.expr.gen_location)
    #    self.code.append(inst)

    #def visit_FunCall(self,node):
    #    self.visit(node.expr)
    #    inst = ('print_'+node.expr.type.name, node.expr.gen_location)
    #    self.code.append(inst)

    #def visit_ExprList(self,node):
    #    self.visit(node.expr)
    #    inst = ('print_'+node.expr.type.name, node.expr.gen_location)
    #    self.code.append(inst)


# STEP 3: Testing
# 
# Try running this program on the input file Project4/Tests/good.e and viewing
# the resulting SSA code sequence.
#
#     bash % python exprcode.py good.e
#     ... look at the output ...
#
# Sample output can be found in Project4/Tests/good.out.  While coding,
# you may want to break the code down into more manageable chunks.
# Think about unit testing.

# ----------------------------------------------------------------------
#                       DO NOT MODIFY ANYTHING BELOW       
# ----------------------------------------------------------------------
def generate_code(node):
    '''
    Generate LLVM code from the supplied AST node.
    '''
    gen = GenerateLLVM()
    gen.visit(node)
    return gen

if __name__ == '__main__':
    import exprlex
    import exprparse
    import exprcheck
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
            code = generate_code(program)
            # Emit the code sequence
            #for inst in code.code:
            #    print(inst)
            print "BEFORE"
            code.engine.run_function(code.llvm_functions['main'], [])


