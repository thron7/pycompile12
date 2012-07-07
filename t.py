code='''
if a<0:
    a+b
else:
    a-b
'''

import ast
top=ast.parse(code)
print 'foo'
