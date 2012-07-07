# exprtype.py
'''
Expr Type System
================
This file defines classes representing types.  There is a general
class used to represent all types.  Each type is then a singleton
instance of the type class.

class ExprType(object):
      pass

int_type = ExprType("int",...)
float_type = ExprType("float",...)
string_type = ExprType("string", ...)

The contents of the type class is entirely up to you.  However, you
will minimally need to encode some information about:

   a.  What operators are supported (+, -, *, etc.).
   b.  Default values
   c.  ????
   d.  Profit!

Once you have defined the built-in types, you will need to
make sure they get registered with any symbol tables or
code that checks for type names in 'exprcheck.py'.
'''

class ExprType(object):
    '''
    Class that represents a type in the Expr language.  Types 
    are declared as singleton instances of this type.
    '''
    def __init__(self, name, bin_ops=set(), un_ops=set()):
        '''
        You must implement yourself and figure out what to store.
        '''
        self.name = name
        self.bin_ops = bin_ops
        self.un_ops = un_ops


# Create specific instances of types. You will need to add
# appropriate arguments depending on your definition of ExprType
int_type = ExprType("int",
    set(('PLUS', 'MINUS', 'TIMES', 'DIVIDE',
         'LE', 'LT', 'EQ', 'NE', 'GT', 'GE')),
    set(('PLUS', 'MINUS')),
    )
float_type = ExprType("float",
    set(('PLUS', 'MINUS', 'TIMES', 'DIVIDE',
         'LE', 'LT', 'EQ', 'NE', 'GT', 'GE')),
    set(('PLUS', 'MINUS')),
    )
string_type = ExprType("string",
    set(('PLUS',)),
    set(),
    )
boolean_type = ExprType("bool",
    set(('LAND', 'LOR', 'EQ', 'NE')),
    set(('LNOT',))
    )
# In your type checking code, you will need to reference the
# above type objects.   Think of how you will want to access
# them.

          




