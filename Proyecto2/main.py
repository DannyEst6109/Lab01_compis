from __future__ import annotations

import os
import sys
from pathlib import Path

from adapter import adapt_grammar
from lexer_bridge import generate_lexer_from_yal, load_generated_lexer, tokenize_with_generated_lexer
from parser_runtime import slr_parse
from primero_siguiente import compute_first, compute_follow, display_results
from slr_builder import build_parser, print_automaton, print_slr_tables
from yalp_parser import parse_yalp_file


BASE_DIR = Path(__file__).resolve().parent


def build_syntax_pipeline(yalp_path: str | os.PathLike[str]):
    print("\n" + "=" * 60)
    print("  PARTE 1 - Parser YAPar + FIRST/FOLLOW")
    print("=" * 60)

    raw_grammar = parse_yalp_file(str(yalp_path))
    print(raw_grammar.summary())

    first = compute_first(raw_grammar)
    follow = compute_follow(raw_grammar, first)
    display_results(raw_grammar, first, follow)

    grammar = adapt_grammar(raw_grammar, first, follow, raw_grammar.ignored)

    print("\n" + "=" * 60)
    print("  PARTE 2 - Automata LR(0) + Tablas SLR")
    print("=" * 60)

    aug_grammar, automaton, tables = build_parser(grammar)
    print_automaton(automaton)
    print_slr_tables(tables, aug_grammar)

    return aug_grammar, automaton, tables


def build_full_pipeline(yal_path: str | os.PathLike[str], yalp_path: str | os.PathLike[str]):
    print("\n" + "=" * 60)
    print("  PARTE 3 - Integracion YALex + YAPar")
    print("=" * 60)
    print(f"  Archivo .yal : {yal_path}")
    print(f"  Archivo .yalp: {yalp_path}")

    lexer_build = generate_lexer_from_yal(yal_path)
    lexer_module = load_generated_lexer(lexer_build.lexer_path)
    print(f"\nLexer generado: {lexer_build.lexer_path}")
    print(f"Entrypoint    : {lexer_build.entrypoint}()")

    aug_grammar, automaton, tables = build_syntax_pipeline(yalp_path)
    return lexer_build, lexer_module, aug_grammar, automaton, tables


def run_input_file(input_path: str | os.PathLike[str], lexer_build, lexer_module, grammar, tables):
    print("\n" + "=" * 60)
    print("  EJECUCION DEL ANALIZADOR")
    print("=" * 60)
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()

    lex_result = tokenize_with_generated_lexer(
        text,
        lexer_module,
        lexer_build.entrypoint,
        grammar_terminals=grammar.terminals,
    )

    for error in lex_result.errors:
        print(error)

    print(f"Tokens: {[token for token, _ in lex_result.tokens]}")
    result = slr_parse(lex_result.tokens, grammar, tables)

    for action in result.actions:
        print(action)
    for error in result.errors:
        print(error)

    print("Resultado final:", "ACEPTADA" if result.accepted else "RECHAZADA")
    return result


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else BASE_DIR / p


def _usage() -> None:
    print("Uso:")
    print("  python main.py                         # abre la GUI")
    print("  python main.py archivo.yalp            # solo construye YAPar/SLR")
    print("  python main.py archivo.yal archivo.yalp [entrada.txt]")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        from ui_parsinator import App

        App().mainloop()
        raise SystemExit(0)

    if len(sys.argv) == 2 and sys.argv[1] in {"-h", "--help"}:
        _usage()
        raise SystemExit(0)

    if len(sys.argv) == 2:
        yalp_file = _resolve(sys.argv[1])
        if not yalp_file.exists():
            print(f"Error. Archivo no encontrado: {yalp_file}")
            raise SystemExit(1)
        build_syntax_pipeline(yalp_file)
        raise SystemExit(0)

    if len(sys.argv) in {3, 4}:
        yal_file = _resolve(sys.argv[1])
        yalp_file = _resolve(sys.argv[2])
        if not yal_file.exists():
            print(f"Error. Archivo .yal no encontrado: {yal_file}")
            raise SystemExit(1)
        if not yalp_file.exists():
            print(f"Error. Archivo .yalp no encontrado: {yalp_file}")
            raise SystemExit(1)

        lexer_build, lexer_module, grammar, _automaton, tables = build_full_pipeline(yal_file, yalp_file)

        if len(sys.argv) == 4:
            input_file = _resolve(sys.argv[3])
            if not input_file.exists():
                print(f"Error. Archivo de entrada no encontrado: {input_file}")
                raise SystemExit(1)
            run_input_file(input_file, lexer_build, lexer_module, grammar, tables)
        raise SystemExit(0)

    _usage()
    raise SystemExit(1)
