from __future__ import annotations

from src.direct_dfa import build_dfa, print_followpos_table, print_transition_table
from src.regex_parser import extract_alphabet, prepare_regex, to_postfix
from src.simulator import simulate_dfa
from src.syntax_tree import build_syntax_tree, compute_functions


EXAMPLES = [
    {
        "regex": "a(b|c)*",
        "valid": "abcb",
        "invalid": "acbd",
        "description": "Unión + cerradura de Kleene",
    },
    {
        "regex": "(ab)+c?",
        "valid": "ababc",
        "invalid": "ac",
        "description": "Cerradura positiva + opcional",
    },
    {
        "regex": "(a|b)?c+",
        "valid": "bcc",
        "invalid": "ab",
        "description": "Unión + opcional + positiva",
    },
]


def compile_regex(regex: str):
    explicit_regex = prepare_regex(regex)
    postfix = to_postfix(explicit_regex)

    root, pos_to_symbol, end_marker_pos = build_syntax_tree(postfix)
    followpos = {pos: set() for pos in pos_to_symbol.keys()}
    compute_functions(root, followpos)

    alphabet = extract_alphabet(pos_to_symbol)
    states, transitions, accepting_states = build_dfa(
        root, followpos, pos_to_symbol, alphabet, end_marker_pos
    )

    return {
        "explicit_regex": explicit_regex,
        "postfix": postfix,
        "alphabet": alphabet,
        "followpos": followpos,
        "pos_to_symbol": pos_to_symbol,
        "states": states,
        "transitions": transitions,
        "accepting_states": accepting_states,
    }


def evaluate_string(compiled: dict, input_string: str) -> bool:
    accepted, path = simulate_dfa(
        compiled["transitions"], compiled["accepting_states"], input_string
    )
    print(f"Recorrido del autómata: {' -> '.join(path)}")
    if accepted:
        print("Resultado: La cadena SÍ pertenece al lenguaje.")
    else:
        print("Resultado: La cadena NO pertenece al lenguaje.")
    return accepted


def show_construction(compiled: dict):
    print(f"Expresión aumentada: {compiled['explicit_regex']}")
    print(f"Postfix: {compiled['postfix']}")
    print(f"Alfabeto: {compiled['alphabet']}")
    print_followpos_table(compiled["followpos"], compiled["pos_to_symbol"])
    print_transition_table(
        compiled["states"],
        compiled["transitions"],
        compiled["accepting_states"],
        compiled["alphabet"],
    )


def run_interactive():
    print("=== Conversión directa ER -> AFD y simulación ===")
    regex = input("Ingrese una expresión regular: ").strip()
    compiled = compile_regex(regex)
    show_construction(compiled)

    test_string = input("Ingrese una cadena a validar: ").strip()
    evaluate_string(compiled, test_string)


def run_demo():
    print("=== Modo demo para video (3 expresiones) ===")
    for i, case in enumerate(EXAMPLES, start=1):
        print("\n" + "=" * 72)
        print(f"Caso {i}: {case['description']}")
        print(f"Expresión regular: {case['regex']}")

        compiled = compile_regex(case["regex"])
        show_construction(compiled)

        print("\nPrueba aceptada:")
        print(f"Cadena: {case['valid']}")
        evaluate_string(compiled, case["valid"])

        print("\nPrueba rechazada:")
        print(f"Cadena: {case['invalid']}")
        evaluate_string(compiled, case["invalid"])


def main():
    print("Seleccione un modo:")
    print("1) Interactivo")
    print("2) Demo (3 expresiones para la entrega)")
    option = input("Opción: ").strip()

    try:
        if option == "2":
            run_demo()
        else:
            run_interactive()
    except ValueError as exc:
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()
