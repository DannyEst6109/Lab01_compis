import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAB3_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "Laboratorio3"))

sys.path.append(LAB3_PATH)

from yalp_parser import parse_yalp_file

from primero_siguiente import (
    compute_first,
    compute_follow,
    display_results
)

# Ruta absoluta al archivo .yalp
YALP_FILE = os.path.join(BASE_DIR, "Ejemplos", "minipython.yalp")

# Leer y parsear
grammar = parse_yalp_file(YALP_FILE)

# FIRST y FOLLOW
first = compute_first(grammar)
follow = compute_follow(grammar, first)

# Mostrar resultados
print(grammar.summary())
display_results(grammar, first, follow)