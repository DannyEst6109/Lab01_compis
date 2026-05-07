# Colección de gramáticas libres de contexto predefinidas.
# Cada una es una instancia de Grammar lista para usar.

from grammar import Grammar, EPSILON

# Gramática 1 – Expresiones aritméticas (con factorización izquierda)
#
#   E  → T E'
#   E' → + T E' | ε
#   T  → F T'
#   T' → * F T' | ε
#   F  → ( E ) | id
GRAMMAR_EXPR = Grammar(
    productions={
        "E" : [["T", "E'"]],
        "E'": [["+", "T", "E'"], [EPSILON]],
        "T" : [["F", "T'"]],
        "T'": [["*", "F", "T'"], [EPSILON]],
        "F" : [["(", "E", ")"], ["id"]],
    },
    start_symbol="E",
    name="Expresiones aritméticas (LL(1))",
)


# Gramática 2 – Sentencias if-then-else
#
#   S  → i E t S S' | a
#   S' → e S | ε
#   E  → b
#
#   (i = if, t = then, e = else, a = assign, b = bool-expr)
GRAMMAR_IF = Grammar(
    productions={
        "S" : [["i", "E", "t", "S", "S'"], ["a"]],
        "S'": [["e", "S"], [EPSILON]],
        "E" : [["b"]],
    },
    start_symbol="S",
    name="Sentencias if-then-else",
)


# Gramática 3 – Listas y asignaciones simples
#
#   P  → L
#   L  → L ; S | S
#   S  → id := E | id
#   E  → E + id | id
GRAMMAR_LIST = Grammar(
    productions={
        "P": [["L"]],
        "L": [["L", ";", "S"], ["S"]],
        "S": [["id", ":=", "E"], ["id"]],
        "E": [["E", "+", "id"], ["id"]],
    },
    start_symbol="P",
    name="Listas y asignaciones (con recursión izquierda)",
)


# Gramática 4 – Declaraciones simples
#
#   D  → T id L
#   L  → , id L | ;
#   T  → int | float
GRAMMAR_DECL = Grammar(
    productions={
        "D": [["T", "id", "L"]],
        "L": [[",", "id", "L"], [";"]],
        "T": [["int"], ["float"]],
    },
    start_symbol="D",
    name="Declaraciones simples",
)


# Gramática 5 – Paréntesis balanceados con producciones anidadas
#
#   S → ( S ) S | ε
GRAMMAR_PARENS = Grammar(
    productions={
        "S": [["(", "S", ")", "S"], [EPSILON]],
    },
    start_symbol="S",
    name="Paréntesis balanceados",
)


# Catálogo público  (nombre → instancia)
PREDEFINED: dict[str, Grammar] = {
    "1": GRAMMAR_EXPR,
    "2": GRAMMAR_IF,
    "3": GRAMMAR_LIST,
    "4": GRAMMAR_DECL,
    "5": GRAMMAR_PARENS,
}