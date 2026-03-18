import sys
import os

# Rutas
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_path)

from Laboratorio1.main import compile_regex, evaluate_string
from Laboratorio1.src.direct_dfa import print_transition_table
from Laboratorio1.src.simulator import simulate_dfa

from src.minimize_dfa import minimize_dfa, compare_dfas


# Helpers  
def show_dfa(label, states, transitions, accepting_states, alphabet):
    print(f"\n{'═'*55}")
    print(f"  {label}")
    print(f"{'═'*55}")
    print_transition_table(states, transitions, accepting_states, alphabet)
    print(f"  Estados       : {len(states)}")
    real_trans = sum(
        1 for st in transitions.values()
        for sym in alphabet if st.get(sym, "-") != "-"
    )
    print(f"  Transiciones  : {real_trans}")


def run_minimization(regex: str):
    #regex → AFD directo → AFD mínimo → comparación.

    # 1. Construir AFD con método directo
    compiled = compile_regex(regex)

    orig_states      = compiled["states"]
    orig_transitions = compiled["transitions"]
    orig_accepting   = compiled["accepting_states"]
    alphabet         = compiled["alphabet"]

    show_dfa(
        f"AFD directo  ←  regex: {regex}",
        orig_states, orig_transitions, orig_accepting, alphabet,
    )

    # 2. Minimizar
    min_states, min_transitions, min_accepting = minimize_dfa(
        orig_states, orig_transitions, orig_accepting, alphabet
    )

    show_dfa(
        f"AFD mínimo   ←  regex: {regex}",
        min_states, min_transitions, min_accepting, alphabet,
    )

    # 3. Comparación
    compare_dfas(
        orig_states, orig_transitions,
        min_states,  min_transitions,
        alphabet,
    )

    return min_states, min_transitions, min_accepting, alphabet


def ask_string(min_transitions, min_accepting):
    #Solicita una cadena y la simula sobre el AFD mínimo.
    cadena = input("\n  Ingrese una cadena para validar: ").strip()
    accepted, path = simulate_dfa(min_transitions, min_accepting, cadena)
    print(f"  Camino : {' → '.join(path)}")
    if accepted:
        print(f"  *  '{cadena}' SÍ pertenece al lenguaje.")
    else:
        print(f"  *  '{cadena}' NO pertenece al lenguaje.")


def show_string(min_transitions, min_accepting, cadena: str):
    #Simula una cadena predeterminada (sin input, usada en la demo.
    accepted, path = simulate_dfa(min_transitions, min_accepting, cadena)
    print(f"  Cadena : '{cadena}'")
    print(f"  Camino : {' → '.join(path)}")
    if accepted:
        print(f"  ✔  SÍ pertenece al lenguaje.")
    else:
        print(f"  X  NO pertenece al lenguaje.")

DEMO_CASES = [
    (
        "a(b|c)*",
        "abcb",
        "aabcb",
        "en teoría, el AFD directo ya es mínimo; el metodo directo no genera estados redundantes.",
    ),
    (
        "a(a|b)*|b(a|b)*",
        "aabababab",
        "", #este, solo la cadena vacía no acepta (o alguna "c/d" que no pertenezca al alfabeto)
        "en teoría, AFD directo NO es minimo — la minimizacion debería reducir el numero de estados.",
    ),
]


def run_demo():
    print("\n" + "=" * 55)
    print("  MODO DEMO — Laboratorio 02")
    print("=" * 55)
    print("  Se procesaran dos expresiones regulares:")
    print("    Caso 1  ->  AFD directo ya es minimo")
    print("    Caso 2  ->  AFD directo se reduce al minimizar")
 
    for i, (regex, accepted, rejected, note) in enumerate(DEMO_CASES, 1):
        print(f"\n{'-'*55}")
        print(f"  CASO {i}: {regex}")
        print(f"  {note}")
        print(f"{'-'*55}")
 
 
        min_states, min_transitions, min_accepting, alphabet = run_minimization(regex)
 
        print("\n  -- Validacion de cadenas --")
        show_string(min_transitions, min_accepting, accepted)
        show_string(min_transitions, min_accepting, rejected)
 
    print(f"\n{'='*55}")
    print("  Demo finalizada.")
    print(f"{'='*55}")



# menu 
def main():
    print("")
    print("---------  Laboratorio 02 — Minimización de AFD  ------------")
    print("")

    while True:
        print("")
        print("1) Ingresar expresión regular")
        print("2) Demo")
        print("3) Salir")
        opcion = input("Seleccione una opción: ").strip()
        print("")

        if opcion == "1":
            print("Puede ingresar simbolos como () | * + ? ")
            regex = input("Ingrese una expresión regular: ").strip()
            try:
                min_states, min_transitions, min_accepting, alphabet = run_minimization(regex)
            except Exception as e:
                print(f"  X  Error: {e}")
                continue

            # Validar cadenas hasta que el usuario no quiera más
            while True:
                otra = input("\n  ¿Validar una cadena? (s/n): ").strip().lower()
                if otra != "s":
                    break
                ask_string(min_transitions, min_accepting)

        elif opcion == "2":
            run_demo()
        elif opcion == "3":    
            print("  Gracias por utilizar el minimiz-inador! Dr.Doofenshmirtz.")
            break
        else:
            print("  Opción inválida.")


if __name__ == "__main__":
    main()      #otra vez, por si esto se usa eventualmente como módulo
    