"""
main.py
Programa principal para calcular los conjuntos PRIMERO y SIGUIENTE
de gramáticas libres de contexto.

Estructura del proyecto:
    grammar.py - Clase Grammar
    first_follow.py - Algoritmos PRIMERO y SIGUIENTE
    predefined_grammars.py - Gramáticas de ejemplo
    grammar_input.py - Ingreso interactivo de gramáticas
    main.py - Este archivo (menú y control)
"""

from grammar import Grammar
from primero_siguiente import compute_first, compute_follow, display_results
from gramatica_predefinida import PREDEFINED
from ingreso_gramatica import input_grammar



# Función central: analizar una gramática
def analyze_grammar(g: Grammar):
    """Muestra la gramática, calcula y presenta PRIMERO y SIGUIENTE."""
    g.display()
    first  = compute_first(g)
    follow = compute_follow(g, first)
    display_results(g, first, follow)



# Menú de gramáticas predefinidas
def menu_predefined():
    print("")
    print("*.° GRAMÁTICAS PREDEFINIDAS °.*")
    print("")
    for key, g in PREDEFINED.items():
        print(f"{key}. {g.name:<42}")
    print("0. Volver al menú principal")
    print("")

    choice = input("Seleccione una gramática: ").strip()
    if choice == '0':
        return
    if choice in PREDEFINED:
        analyze_grammar(PREDEFINED[choice])
    else:
        print(" Opción no válida.")
    input("\nPresione Enter para continuar...")



# Menú principal
def main_menu():
    while True:
        print()
        print("   *.° CALCULADORA DE CONJUNTOS PRIMERO y SIGUIENTE °.*")     
        print("          *.° Gramáticas Libres de Contexto °.*")  
        print(" Creado por Melisa Mendizabal, Renato Rojas y Daniel Estada") 
        print("")          

        print("--- Menú ---")
        print("  1. Usar una gramática predefinida")
        print("  2. Ingresar una gramática manualmente")
        print("  0. Salir")
        print()
        choice = input("Opción: ").strip()

        if choice == '1':
            menu_predefined()

        elif choice == '2':
            g = input_grammar()
            analyze_grammar(g)
            input("\nPresione Enter para continuar...")

        elif choice == '0':
            print("\n¡Hasta luego!\n")
            break

        else:
            print(" Opción no válida. Intente de nuevo.\n")


#¿if main para utilizar funciones en futuros programas
if __name__ == "__main__":
    main_menu()