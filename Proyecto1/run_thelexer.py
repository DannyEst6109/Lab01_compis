#main 2 
import sys
from thelexer import tokens

if len(sys.argv) < 2:
    print("Le faltaron argumentos. Use: python3 run_thelexer.py archivo.txt")
    sys.exit(1)

filepath = sys.argv[1]


try:
    with open(filepath, "r", encoding="utf-8") as f:
        check_input = f.read()
except FileNotFoundError:
    print(f"Error: no se encontró el archivo '{filepath}'")
    sys.exit(1)

tokens(check_input)

