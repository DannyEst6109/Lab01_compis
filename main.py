from src.regex_parser import prepare_regex, to_postfix, extract_alphabet
from src.syntax_tree import build_syntax_tree, compute_functions
from src.direct_dfa import build_dfa, print_transition_table, print_followpos_table
from src.simulator import simulate_dfa


def process_regex(regex: str):
    prepared = prepare_regex(regex)
    postfix = to_postfix(prepared)

    root, pos_to_symbol, end_marker_pos = build_syntax_tree(postfix)
    followpos = {pos: set() for pos in pos_to_symbol.keys()}

    compute_functions(root, followpos)

    alphabet = extract_alphabet(pos_to_symbol)
    states, transitions, accepting_states = build_dfa(
        root=root,
        followpos=followpos,
        pos_to_symbol=pos_to_symbol,
        alphabet=alphabet,
        end_marker_pos=end_marker_pos
    )

    return {
        "original_regex": regex,
        "prepared_regex": prepared,
        "postfix": postfix,
        "root": root,
        "pos_to_symbol": pos_to_symbol,
        "followpos": followpos,
        "alphabet": alphabet,
        "states": states,
        "transitions": transitions,
        "accepting_states": accepting_states,
        "end_marker_pos": end_marker_pos,
    }


def interactive_mode():
    print("=" * 70)
    print(" Conversión directa de una expresión regular a un AFD")
    print("=" * 70)

    while True:
        regex = input("\nIngrese una expresión regular (o 'salir'): ").strip()
        if regex.lower() == "salir":
            print("Programa finalizado.")
            break

        try:
            result = process_regex(regex)

            print("\n--- Expresión procesada ---")
            print(f"Original : {result['original_regex']}")
            print(f"Preparada: {result['prepared_regex']}")
            print(f"Postfix  : {result['postfix']}")

            print_followpos_table(result["followpos"], result["pos_to_symbol"])
            print_transition_table(
                result["states"],
                result["transitions"],
                result["accepting_states"],
                result["alphabet"]
            )

            while True:
                s = input("\nIngrese una cadena a validar ('nueva' para otra ER): ").strip()
                if s.lower() == "nueva":
                    break

                accepted, path = simulate_dfa(
                    transitions=result["transitions"],
                    accepting_states=result["accepting_states"],
                    input_string=s
                )

                print("\nRecorrido:")
                print(" -> ".join(path))

                if accepted:
                    print(f"Resultado: La cadena '{s}' SÍ pertenece al lenguaje.")
                else:
                    print(f"Resultado: La cadena '{s}' NO pertenece al lenguaje.")

        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    interactive_mode()