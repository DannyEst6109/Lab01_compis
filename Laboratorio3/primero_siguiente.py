
# Implementación de los algoritmos para calcular los conjuntos
# PRIMERO (First) y SIGUIENTE (Follow) de una gramática libre de contexto.

# No se utilizan librerías externas para el cálculo.

from grammar import Grammar, EPSILON


# ======================================================================
# PRIMERO
# ======================================================================

def first_of_symbol(X: str, grammar: Grammar, memo: dict) -> set:
    """
    Calcula PRIMERO(X) para un símbolo X.

    Reglas aplicadas:
      1. Si X es terminal  → PRIMERO(X) = { X }
      2. Si X → ε          → ε ∈ PRIMERO(X)
      3. Si X → Y1 Y2 … Yk → se añaden los PRIMERO de cada Yi
         mientras el anterior pueda derivar ε.
      4. Si todos los Yi pueden derivar ε → ε ∈ PRIMERO(X)
    """
    # Si ya fue calculado, retornamos el valor en caché
    if X in memo:
        return memo[X]

    # Regla 1: terminal
    if X in grammar.terminals or X == EPSILON:
        return {X}

    # Inicializamos (puede haber recursión, el conjunto vacío evita ciclos)
    memo[X] = set()

    for prod in grammar.productions.get(X, []):
        # Regla 2: producción épsilon
        if prod == [EPSILON]:
            memo[X].add(EPSILON)
            continue

        # Reglas 3 y 4
        _add_first_of_string(prod, grammar, memo, memo[X])

    return memo[X]

# Calcula PRIMERO de una cadena de símbolos y lo vuelca en `target`.
# Devuelve True si toda la cadena puede derivar ε.
def _add_first_of_string(symbols: list, grammar: Grammar, memo: dict, target: set):
    all_nullable = True
    for sym in symbols:
        if sym in grammar.terminals:
            # Terminal: solo ese símbolo, sin ε
            target.add(sym)
            all_nullable = False
            break
        elif sym in grammar.non_terminals:
            first_sym = first_of_symbol(sym, grammar, memo)
            target.update(first_sym - {EPSILON})
            if EPSILON not in first_sym:
                all_nullable = False
                break
        else:
            # Símbolo desconocido (no debería ocurrir si la gramática es válida)
            target.add(sym)
            all_nullable = False
            break

    if all_nullable:
        target.add(EPSILON)
    return all_nullable

# Calcula PRIMERO para todos los no terminales de la gramática.
# Devuelve un diccionario  { 'NO_TERMINAL': set_de_símbolos }
def compute_first(grammar: Grammar) -> dict:
    memo = {}
    for nt in grammar.non_terminals:
        first_of_symbol(nt, grammar, memo)
    # Retornamos solo los no terminales (memo también puede tener terminales)
    return {nt: memo[nt] for nt in grammar.non_terminals}



# SIGUIENTE
def compute_follow(grammar: Grammar, first: dict) -> dict:
    """
    Calcula SIGUIENTE para todos los no terminales de la gramática.

    Utiliza los conjuntos PRIMERO ya calculados (parámetro `first`).

    Reglas aplicadas:
      1. $ ∈ SIGUIENTE(S)   (S = símbolo inicial)
      2. A → a B β  → PRIMERO(β) - {ε} ⊆ SIGUIENTE(B)
      3. A → a B  ó  A → a B β  con ε ∈ PRIMERO(β)
                   → SIGUIENTE(A) ⊆ SIGUIENTE(B)
    """
    follow = {nt: set() for nt in grammar.non_terminals}

    # Regla 1
    follow[grammar.start_symbol].add('$')

    # Iteramos hasta que no haya cambios (punto fijo)
    changed = True
    while changed:
        changed = False

        for A, prods in grammar.productions.items():
            for prod in prods:
                if prod == [EPSILON]:
                    continue

                for i, B in enumerate(prod):
                    if B not in grammar.non_terminals:
                        continue

                    beta = prod[i + 1:]  # todo lo que sigue a B

                    if not beta:
                        # Caso: A → α B  (B al final)
                        # Regla 3: SIGUIENTE(A) → SIGUIENTE(B)
                        new = follow[A] - {EPSILON}
                        if not new.issubset(follow[B]):
                            follow[B].update(new)
                            changed = True
                    else:
                        # Caso: A → α B β
                        # Calculamos PRIMERO(β) usando los primeros ya conocidos
                        first_beta = _first_of_string_using_first(beta, grammar, first)

                        # Regla 2: PRIMERO(β) − {ε} → SIGUIENTE(B)
                        new = first_beta - {EPSILON}
                        if not new.issubset(follow[B]):
                            follow[B].update(new)
                            changed = True

                        # Regla 3: si ε ∈ PRIMERO(β) → SIGUIENTE(A) → SIGUIENTE(B)
                        if EPSILON in first_beta:
                            new = follow[A] - {EPSILON}
                            if not new.issubset(follow[B]):
                                follow[B].update(new)
                                changed = True

    return follow

# Calcula PRIMERO de una cadena de símbolos usando el diccionario
# `first` ya computado (evita recalcular desde cero).
def _first_of_string_using_first(symbols: list, grammar: Grammar, first: dict) -> set:
    result = set()
    all_nullable = True

    for sym in symbols:
        if sym in grammar.terminals:
            result.add(sym)
            all_nullable = False
            break
        elif sym in grammar.non_terminals:
            result.update(first[sym] - {EPSILON})
            if EPSILON not in first[sym]:
                all_nullable = False
                break
        else:
            result.add(sym)
            all_nullable = False
            break

    if all_nullable:
        result.add(EPSILON)

    return result



# Función de presentación de resultados
#Muestra los conjuntos PRIMERO y SIGUIENTE de forma alineada
def display_results(grammar: Grammar, first: dict, follow: dict):

    print(f"\n{'─'*50}")
    print("  CONJUNTOS PRIMERO y SIGUIENTE")
    print(f"{'─'*50}")

    col_w = max(len(nt) for nt in grammar.non_terminals) + 2

    header = f"  {'No Terminal':<{col_w}}  {'PRIMERO':<28}  SIGUIENTE"
    print(header)
    print(f"  {'─'*col_w}  {'─'*28}  {'─'*28}")

    for nt in grammar.productions:  # respeta el orden de inserción
        f_str = "{ " + ", ".join(sorted(first[nt]))  + " }"
        s_str = "{ " + ", ".join(sorted(follow[nt])) + " }"
        print(f"  {nt:<{col_w}}  {f_str:<28}  {s_str}")

    print(f"{'─'*50}\n")