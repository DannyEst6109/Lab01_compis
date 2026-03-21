#main 2 
from thelexer import tokens

check_input = """var @ -4
2var 1
"""

tokensu = tokens(check_input)
print(tokensu)
