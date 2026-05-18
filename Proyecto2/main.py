# =============================================================================
# main.py — Integración Parte 1 (YAPar parser) + Parte 2 (Autómata SLR)
# =============================================================================
#
# Uso:
#   python main.py                        → usa calc.yalp por defecto
#   python main.py Ejemplos/ejemplo.yalp  → usa el archivo indicado
#

import sys
import os

# ── Importaciones Parte 1 ─────────────────────────────────────────────────────
from yalp_parser import parse_yalp_file
from primero_siguiente import compute_first, compute_follow, display_results

# ── Importaciones Parte 2 ─────────────────────────────────────────────────────
from adapter import adapt_grammar
from slr_builder import build_parser, print_automaton, print_slr_tables


def run(yalp_path: str):
    print("\n" + "-"*60)
    print(f"  Archivo: {yalp_path}")
    print("-"*60)

    # ── PARTE 1: parsear el .yalp y calcular FIRST / FOLLOW ──────────────────
    print("\n" + "="*60)
    print("  PARTE 1 — Parser YAPar + FIRST / FOLLOW")
    print("="*60)

    grammar = parse_yalp_file(yalp_path)

    print(grammar.summary())

    first  = compute_first(grammar)
    follow = compute_follow(grammar, first)
    display_results(grammar, first, follow)

    # ── ADAPTADOR: convertir al formato de la Parte 2 ────────────────────────
    # grammar.ignored contiene los tokens declarados con IGNORE en el .yalp
    my_grammar = adapt_grammar(grammar, first, follow, grammar.ignored)

    # ── PARTE 2: construir autómata LR(0) y tablas SLR ───────────────────────
    print("\n" + "="*60)
    print("  PARTE 2 — Autómata LR(0) + Tablas SLR")
    print("="*60)

    aug_grammar, automaton, tables = build_parser(my_grammar)

    print_automaton(automaton)
    print_slr_tables(tables, aug_grammar)

    # ── Resumen final ─────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("  RESUMEN FINAL")
    print("="*60)
    print(f"  Tokens declarados   : {my_grammar.terminals}")
    print(f"  Tokens ignorados    : {my_grammar.ignored_tokens}")
    print(f"  No terminales       : {my_grammar.non_terminals}")
    print(f"  Producciones        : {len(my_grammar.productions)}")
    print(f"  Estados del autómata: {len(automaton.states)}")
    print(f"  Conflictos SLR      : {len(tables.conflicts)}")

    # Lo que exportamos a la Parte 3
    return aug_grammar, automaton, tables


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    if len(sys.argv) > 1:
        yalp_file = sys.argv[1]
        if not os.path.isabs(yalp_file):
            yalp_file = os.path.join(BASE_DIR, yalp_file)
    else:
        yalp_file = os.path.join(BASE_DIR, "Ejemplos", "calc.yalp")

    if not os.path.exists(yalp_file):
        print(f"Error. Archivo no encontrado: {yalp_file}")
        sys.exit(1)

    run(yalp_file)