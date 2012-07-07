# exprcode.py
'''
Project 4 - Part 1
==================
Code generation for the Expr language.  In this project, you are going to turn
the AST into an intermediate machine code known as Single Static Assignment (SSA).
There are a few important parts you'll need to make this work.  Please read 
carefully before beginning:

Single Static Assignment
========================
The first problem is how to decompose complex expressions into
something that can be handled more simply.  One way to do this is
to decompose all expressions into a sequence of simple assignments
involving binary or unary operations.  

As an example, suppose you had a mathematical expression like this:

        2 + 3*4 - 5

Here is one possible way to decompose the expression into simple
operations:

        int_1 = 2
        int_2 = 3
        int_3 = 4
        int_4 = int_2 * int_3
        int_5 = int_1 + int_4
        int_6 = 5
        int_7 = int_5 - int_6

In this code, the int_n variables are simply temporaries used while
carrying out the calculation.  A critical feature of SSA is that such
temporary variables are only assigned once (single assignment) and
never reused.  Thus, if you were to evaluate another expression, you
would simply keep incrementing the numbers. For example, if you were
to evaluate 10+20+30, you would have code like this:

        int_8 = 10
        int_9 = 20
        int_10 = int_8 + int_9
        int_11 = 30
        int_12 = int_11 + int_11

SSA is meant to mimic the low-level instructions one might carry out 
on a CPU.  For example, the above instructions might be translated to
low-level machine instructions (for a hypothetical CPU) like this:

        MOVI   #2, R1
        MOVI   #3, R2
        MOVI   #4, R3
        MUL    R2, R3, R4
        ADD    R4, R1, R5
        MOVI   #5, R6
        SUB    R5, R6, R7

Another benefit of SSA is that it is very easy to encode and
manipulate using simple data structures such as tuples. For example,
you could encode the above sequence of operations as a list like this:

       [ 
         ('movi', 2, 'int_1'),
         ('movi', 3, 'int_2'),
         ('movi', 4, 'int_3'),
         ('mul', 'int_2', 'int_3', 'int_4'),
         ('add', 'int_1', 'int_4', 'int_5'),
         ('movi', 5, 'int_6'),
         ('sub', 'int_5','int_6','int_7'),
       ]

Dealing with Variables
======================
In your program, you are probably going to have some variables that get
used and assigned different values.  For example:

       a = 10 + 20;
       b = 2 * a;
       a = a + 1;

In "pure SSA", all of your variables would actually be versioned just
like temporaries in the expressions above.  For example, you would
emit code like this:

       int_1 = 10
       int_2 = 20
       a_1 = int_1 + int_2
       int_3 = 2
       b_1 = int_3 * a_1
       int_4 = 1 
       a_2 = a_1 + int_4
       ...

For reasons that will make sense later, we're going to treat declared
variables as memory locations and access them using load/store
instructions.  For example:

       int_1 = 10
       int_2 = 20
       int_3 = int_1 + int_2
       store(int_3, "a")
       int_4 = 2
       int_5 = load("a")
       int_6 = int_4 * int_5
       store(int_6,"b")
       int_7 = load("a")
       int_8 = 1
       int_9 = int_7 + int_8
       store(int_9, "a")

A Word About Types
==================
At a low-level, CPUs can only operate a few different kinds of 
data such as ints and floats.  Because the semantics of the
low-level types might vary slightly, you'll need to take 
some steps to handle them separately.

In our intermediate code, we're simply going to tag temporary variable
names and instructions with an associated type low-level type.  For
example:

      2 + 3*4          (ints)
      2.0 + 3.0*4.0    (floats)

The generated intermediate code might look like this:

      ('literal_int', 2, 'int_1')
      ('literal_int', 3, 'int_2')
      ('literal_int', 4, 'int_3')
      ('mul_int', 'int_2', 'int_3', 'int_4')
      ('add_int', 'int_1', 'int_4', 'int_5')

      ('literal_float', 2.0, 'float_1')
      ('literal_float', 3.0, 'float_2')
      ('literal_float', 4.0, 'float_3')
      ('mul_float', 'float_2', 'float_3', 'float_4')
      ('add_float', 'float_1', 'float_4', 'float_5')

Note: These types may or may not correspond directly to the type names
used in the input program.   For example, during translation, higher
level data structures would be reduced to a low-level operations.

Your Task
=========
Your task is as follows: Write a AST Visitor() class that takes an
Expr program and flattens it to a single sequence of SSA code instructions
represented as tuples of the form 

       (operation, operands, ..., destination)

To start, your SSA code should only contain the following operators:

       ('alloc_type',varname)             # Allocate a variable of a given type
       ('literal_type', value, target)    # Load a literal value into target
       ('load_type', varname, target)     # Load the value of a variable into target
       ('store_type',source, varname)     # Store the value of source into varname
       ('add_type', left, right, target ) # target = left + right
       ('sub_type',left,right,target)     # target = left - right
       ('mul_type',left,right,target)     # target = left * right
       ('div_type',left,right,target)     # target = left / right  (integer truncation)
       ('uadd_type',source,target)        # target = +source
       ('uneg_type',source,target)        # target = -source
       ('print_type',source)              # Print value of source
'''

import exprast
import exprblock
from exprblock import BasicBlock, IfBlock, WhileBlock
from collections import defaultdict

# STEP 1: Map map operator symbol names such as +, -, *, /
# to actual opcode names 'add','sub','mul','div' to be emitted in
# the SSA code.   This is easy to do using dictionaries:

binary_ops = {
    '+' : 'add',
    '-' : 'sub',
    '*' : 'mul',
    '/' : 'div',
    '<' : 'lt',
    '>' : 'gt',
    '==': 'eq',
    '!=': 'ne',
    '<=': 'le',
    '>=': 'ge',
    '&&': 'land',
    '||': 'lor',
}

unary_ops = {
    '+' : 'uadd',
    '-' : 'usub',
    '!' : 'lnot',
}

# STEP 2: Implement the following Node Visitor class so that it creates
# a sequence of SSA instructions in the form of tuples.  Use the
# above description of the allowed op-codes as a guide.
class GenerateCode(exprast.NodeVisitor):
    '''
    Node visitor class that creates 3-address encoded instruction sequences.
    '''
    def __init__(self):
        super(GenerateCode, self).__init__()

        # version dictionary for temporaries
        self.versions = defaultdict(int)

        # The generated code (list of tuples)
        self.code = BasicBlock()
        self.start_block = self.code

        # A list of external declarations (and types)
        self.externs = []

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

    def visit_RelationalOp(self,node):
        # Visit the left and right expressions
        self.visit(node.left)
        self.visit(node.right)

        # Make a new temporary for storing the result
        target = self.new_temp(node.type)

        # Create the opcode and append to list
        #opcode = binary_ops[node.op] + "_"+node.left.type.name
        opcode = "cmp" + "_"+node.left.type.name
        inst = (opcode, binary_ops[node.op], node.left.gen_location, node.right.gen_location, target)
        self.code.append(inst)

        # Store location of the result on the node
        node.gen_location = target

    def visit_PrintStatement(self,node):
        # Visit the printed expression
        self.visit(node.expr)

        # Create the opcode and append to list
        inst = ('print_'+node.expr.type.name, node.expr.gen_location)
        self.code.append(inst)

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

    def visit_IfStatement(self,node):
        if_block = IfBlock()
        self.code.next_block = if_block
        # condition
        self.switch_block(if_block)
        self.visit(node.condition)
        if_block.test = node.condition.gen_location
        # then branch
        if_block.if_branch = BasicBlock()
        self.switch_block(if_block.if_branch)
        self.visit(node.then_b)
        # else branch
        if node.else_b:
            if_block.else_branch = BasicBlock()
            self.switch_block(if_block.else_branch)
            self.visit(node.else_b)
        # set up next block
        if_block.next_block = BasicBlock()
        self.switch_block(if_block.next_block)

    def visit_WhileStatement(self, node):
        while_block = WhileBlock()
        self.code.next_block = while_block
        # condition
        self.switch_block(while_block)
        self.visit(node.condition)
        while_block.test = node.condition.gen_location
        # body
        while_block.body = BasicBlock()
        self.switch_block(while_block.body)
        self.visit(node.body)
        while_block.next_block = BasicBlock()
        self.switch_block(while_block.next_block)

    def switch_block(self, next_block):
        self.code = next_block

    def visit_Group(self,node):
        self.visit(node.expression)
        node.gen_location = node.expression.gen_location

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
    Generate SSA code from the supplied AST node.
    '''
    gen = GenerateCode()
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
            exprblock.PrintBlocks().visit(code.start_block)
            #for inst in code.code:
            #    print(inst)
