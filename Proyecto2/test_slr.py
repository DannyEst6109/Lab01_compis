# =============================================================================
# test_slr.py — Prueba usando el formato REAL de la Parte 1
# =============================================================================
#
# Simula exactamente lo que la Parte 1 entregará:
#   - Un objeto grammar.Grammar con producciones como dict
#   - Los dicts first y follow que salen de compute_first / compute_follow
#   - La lista de tokens a ignorar
#
# Gramática usada: la del PDF de YAPar
#   production1 → production1 TOKEN_2 production2 | production2
#   production2 → production2 TOKEN_2 production3 | production3
#   production3 → TOKEN_3 production1 TOKEN_4     | TOKEN_1

EPSILON = 'ε'


class MockGrammar:
    """
    Replica mínima del grammar.Grammar de la Parte 1.
    En producción, reemplazá esto por:
        from grammar import Grammar
    y eliminá esta clase.
    """
    def __init__(self, productions: dict, start_symbol: str = None):
        self.productions   = productions
        self.start_symbol  = start_symbol or list(productions.keys())[0]
        self.non_terminals = set(productions.keys())
        self.terminals     = self._find_terminals()

    def _find_terminals(self) -> set:
        terminals = set()
        for prods in self.productions.values():
            for prod in prods:
                for sym in prod:
                    if sym != EPSILON and sym not in self.non_terminals:
                        terminals.add(sym)
        return terminals


def make_part1_output():
    """
    Simula la salida completa de la Parte 1 para la gramática del PDF.
    """
    productions = {
        "production1": [
            ["production1", "TOKEN_2", "production2"],
            ["production2"],
        ],
        "production2": [
            ["production2", "TOKEN_2", "production3"],
            ["production3"],
        ],
        "production3": [
            ["TOKEN_3", "production1", "TOKEN_4"],
            ["TOKEN_1"],
        ],
    }

    grammar = MockGrammar(productions, start_symbol="production1")

    first = {
        "production1": {"TOKEN_3", "TOKEN_1"},
        "production2": {"TOKEN_3", "TOKEN_1"},
        "production3": {"TOKEN_3", "TOKEN_1"},
    }

    follow = {
        "production1": {"$", "TOKEN_2", "TOKEN_4"},
        "production2": {"$", "TOKEN_2", "TOKEN_4"},
        "production3": {"$", "TOKEN_2", "TOKEN_4"},
    }

    ignored = ["WS"]

    return grammar, first, follow, ignored


if __name__ == "__main__":
    from adapter import adapt_grammar
    from slr_builder import build_parser, print_automaton, print_slr_tables

    print("=" * 60)
    print("PRUEBA: Usando el formato real de la Parte 1")
    print("=" * 60)

    # 1. Obtener la salida de la Parte 1
    grammar_p1, first, follow, ignored = make_part1_output()

    print(f"\nGrammar de la Parte 1:")
    print(f"  Terminales    : {sorted(grammar_p1.terminals)}")
    print(f"  No terminales : {sorted(grammar_p1.non_terminals)}")
    print(f"  Producciones  : {sum(len(v) for v in grammar_p1.productions.values())} reglas")
    print(f"  Ignorados     : {ignored}")

    # 2. Adaptar al formato de la Parte 2
    print("\nAdaptando Grammar al formato de la Parte 2...")
    my_grammar = adapt_grammar(grammar_p1, first, follow, ignored)
    print(f"  Producciones como tuplas:")
    for head, body in my_grammar.productions:
        print(f"    {head} → {' '.join(body) if body else 'ε'}")

    # 3. Ejecutar la Parte 2
    aug_grammar, automaton, tables = build_parser(my_grammar)

    # 4. Mostrar resultados
    print_automaton(automaton)
    print_slr_tables(tables, aug_grammar)

    # 5. Resumen
    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    print(f"  Estados en el autómata : {len(automaton.states)}")
    print(f"  Transiciones           : {len(automaton.transitions)}")
    print(f"  Entradas en ACTION     : {len(tables.action)}")
    print(f"  Entradas en GOTO       : {len(tables.goto)}")
    print(f"  Conflictos detectados  : {len(tables.conflicts)}")

    print("\n" + "="*60)
    print("INTERFAZ HACIA LA PARTE 3")
    print("  aug_grammar → Grammar aumentada (saber qué producción es cuál)")
    print("  automaton   → LR0Automaton      (visualizar el grafo de estados)")
    print("  tables      → SLRTables         (ejecutar el parser)")
    print("="*60)
    print("\n✅ Prueba completada.")
