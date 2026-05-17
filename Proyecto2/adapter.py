# =============================================================================
# adapter.py — Convierte el Grammar de la Parte 1 al formato de la Parte 2
# =============================================================================
#
# La Parte 1 entrega:
#   - grammar   : instancia de grammar.Grammar  (producciones como dict)
#   - first     : dict  { "A": set() }  ← salida de compute_first()
#   - follow    : dict  { "A": set() }  ← salida de compute_follow()
#   - ignored   : list  ["WS", ...]     ← tokens a ignorar del .yalp
#
# Este archivo convierte todo eso al Grammar de models.py que usa la Parte 2.
# Solo este archivo conoce el formato interno de la Parte 1.

from models import Grammar as SLRGrammar

# EPSILON tal como lo define la Parte 1
EPSILON = 'ε'


def adapt_grammar(
    grammar,            # instancia de grammar.Grammar (Parte 1)
    first:  dict,       # salida de compute_first()
    follow: dict,       # salida de compute_follow()
    ignored: list = [], # tokens a ignorar (del archivo .yalp)
) -> SLRGrammar:
    """
    Convierte el objeto Grammar de la Parte 1 al formato que espera slr_builder.

    Diferencias que resuelve este adaptador:
      1. productions: dict-of-lists  →  list-of-tuples
      2. terminals / non_terminals:  set  →  list  (orden determinista)
      3. Épsilon: ["ε"]  →  []  (cuerpo vacío)
      4. Agrega '$' a terminals si no está
      5. Adjunta ignored_tokens, first y follow al objeto resultante
    """

    # ── 1. Aplanar producciones: dict → lista de tuplas ──────────────────────
    #
    #   Entrada:  { "E": [["T", "E'"], ...], "E'": [["+", "T"], ["ε"]] }
    #   Salida:   [ ("E", ["T", "E'"]), ("E'", ["+", "T"]), ("E'", []) ]
    #
    # El orden importa: la PRIMERA producción de la lista es el símbolo inicial
    # (ya que grammar.start_symbol define cuál es). Nos aseguramos que vaya primero.

    productions = []

    # El símbolo inicial va primero
    start = grammar.start_symbol
    for body in grammar.productions.get(start, []):
        adapted_body = [] if body == [EPSILON] else list(body)
        productions.append((start, adapted_body))

    # El resto de los no-terminales
    for head, bodies in grammar.productions.items():
        if head == start:
            continue                        # ya lo agregamos
        for body in bodies:
            adapted_body = [] if body == [EPSILON] else list(body)
            productions.append((head, adapted_body))

    # ── 2. Terminales y no-terminales como listas ordenadas ──────────────────
    #
    # Usamos listas (no sets) para que el orden sea predecible.
    # Agregamos '$' a terminales si la Parte 1 no lo incluyó.

    non_terminals = [start] + [nt for nt in grammar.productions if nt != start]
    terminals     = sorted(grammar.terminals)
    if '$' not in terminals:
        terminals.append('$')

    # ── 3. Limpiar first/follow: quitar 'ε' de los conjuntos ─────────────────
    #
    # slr_builder usa follow para saber cuándo reducir.
    # 'ε' en follow no tiene sentido para las tablas SLR; lo removemos.

    clean_first  = {nt: (s - {EPSILON}) for nt, s in first.items()}
    clean_follow = {nt: (s - {EPSILON}) for nt, s in follow.items()}

    return SLRGrammar(
        terminals     = terminals,
        non_terminals = non_terminals,
        productions   = productions,
        start_symbol  = start,
        ignored_tokens= list(ignored),
        first         = clean_first,
        follow        = clean_follow,
    )