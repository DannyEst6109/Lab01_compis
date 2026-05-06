"""
grammar_input.py
Módulo para ingresar gramáticas libres de contexto
de forma interactiva desde la consola.
"""

from grammar import Grammar, EPSILON


def _parse_production(raw: str, nt: str) -> list[list[str]]:
    """
    Convierte una línea de producción en una lista de alternativas.

    Formato esperado:  símbolo1 símbolo2 ... | símbolo1 ...
    Ejemplo:           "+ T E' | eps"  →  [['+', 'T', "E'"], ['ε']]

    'eps', 'epsilon', 'EPSILON' y 'ε' se interpretan como épsilon.
    """
    alternatives = raw.split('|')
    prods = []
    for alt in alternatives:
        symbols = alt.strip().split()
        if not symbols:
            print(f"  ⚠ Alternativa vacía ignorada en '{nt}'.")
            continue
        # Normalizar épsilon
        normalized = []
        for sym in symbols:
            if sym.lower() in ('eps', 'epsilon', 'ε', 'e'):
                normalized.append(EPSILON)
            else:
                normalized.append(sym)
        # Si la alternativa es solo épsilon usamos [ε]
        if len(normalized) == 1 and normalized[0] == EPSILON:
            prods.append([EPSILON])
        else:
            # No permitir mezclar ε con otros símbolos en la misma alternativa
            if EPSILON in normalized and len(normalized) > 1:
                print(f"  ⚠ ε no debe mezclarse con otros símbolos. "
                      f"Se usará solo ε en '{nt}'.")
                prods.append([EPSILON])
            else:
                prods.append(normalized)
    return prods


def input_grammar() -> Grammar:
    """
    Guía al usuario paso a paso para ingresar una gramática
    libre de contexto de forma interactiva.

    Devuelve una instancia de Grammar.
    """
    print("\n" + "="*55)
    print("   INGRESO DE GRAMÁTICA LIBRE DE CONTEXTO")
    print("="*55)
    print("  Instrucciones:")
    print("  • Separe los símbolos con espacios.")
    print("  • Use '|' para separar alternativas en una producción.")
    print(f"  • Escriba 'eps' o 'ε' para representar épsilon (vacío).")
    print("  • El primer no terminal ingresado será el símbolo inicial.")
    print("="*55)

    name = input("\nNombre de la gramática (opcional): ").strip()

    # ── 1. Obtener la lista de no terminales ──────────────────────────
    while True:
        raw_nts = input(
            "\nIngrese los no terminales separados por comas\n"
            "(Ej: E, E', T, T', F): "
        ).strip()
        non_terminals = [nt.strip() for nt in raw_nts.split(',') if nt.strip()]
        if non_terminals:
            break
        print("  ⚠ Debe ingresar al menos un no terminal.")

    start_symbol = non_terminals[0]
    print(f"\n  Símbolo inicial detectado: {start_symbol}")

    # ── 2. Ingresar producciones por no terminal ──────────────────────
    productions = {}
    print("\nIngrese las producciones para cada no terminal.")
    print("Puede usar varias líneas separadas por '|' dentro de la misma línea.")
    print("Ejemplo:  T E' | ε\n")

    for nt in non_terminals:
        while True:
            raw = input(f"  {nt} → ").strip()
            if not raw:
                print(f"  ⚠ '{nt}' necesita al menos una producción.")
                continue
            prods = _parse_production(raw, nt)
            if prods:
                productions[nt] = prods
                break
            print(f"  ⚠ No se pudo parsear la producción. Intente de nuevo.")

    # ── 3. Construir y validar ────────────────────────────────────────
    try:
        g = Grammar(productions, start_symbol=start_symbol, name=name)
        g.validate()
        print("\n  ✔ Gramática ingresada correctamente.")
        return g
    except ValueError as e:
        print(f"\n  ✘ Error en la gramática: {e}")
        print("  Por favor, reintente.")
        return input_grammar()  # reintento recursivo