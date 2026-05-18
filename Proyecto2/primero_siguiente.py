# primero_siguiente.py
# Copiado exactamente igual del Laboratorio 3. Se copia aquí para que la integración
# funcione sin depender de rutas relativas entre laboratorios (porque qué dolor).

EPSILON = 'ε'


def first_of_symbol(X: str, grammar, memo: dict) -> set:
    if X in memo:
        return memo[X]
    if X in grammar.terminals or X == EPSILON:
        return {X}
    memo[X] = set()
    for prod in grammar.productions.get(X, []):
        if prod == [EPSILON]:
            memo[X].add(EPSILON)
            continue
        _add_first_of_string(prod, grammar, memo, memo[X])
    return memo[X]


def _add_first_of_string(symbols, grammar, memo, target):
    all_nullable = True
    for sym in symbols:
        if sym in grammar.terminals:
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
            target.add(sym)
            all_nullable = False
            break
    if all_nullable:
        target.add(EPSILON)
    return all_nullable


def compute_first(grammar) -> dict:
    memo = {}
    for nt in grammar.non_terminals:
        first_of_symbol(nt, grammar, memo)
    return {nt: memo[nt] for nt in grammar.non_terminals}


def compute_follow(grammar, first: dict) -> dict:
    follow = {nt: set() for nt in grammar.non_terminals}
    follow[grammar.start_symbol].add('$')
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
                    beta = prod[i + 1:]
                    if not beta:
                        new = follow[A] - {EPSILON}
                        if not new.issubset(follow[B]):
                            follow[B].update(new)
                            changed = True
                    else:
                        first_beta = _first_of_string_using_first(beta, grammar, first)
                        new = first_beta - {EPSILON}
                        if not new.issubset(follow[B]):
                            follow[B].update(new)
                            changed = True
                        if EPSILON in first_beta:
                            new = follow[A] - {EPSILON}
                            if not new.issubset(follow[B]):
                                follow[B].update(new)
                                changed = True
    return follow


def _first_of_string_using_first(symbols, grammar, first) -> set:
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


def display_results(grammar, first: dict, follow: dict):
    print(f"\n{'─'*50}")
    print("  CONJUNTOS PRIMERO y SIGUIENTE")
    print(f"{'─'*50}")
    col_w = max(len(nt) for nt in grammar.non_terminals) + 2
    print(f"  {'No Terminal':<{col_w}}  {'PRIMERO':<28}  SIGUIENTE")
    print(f"  {'─'*col_w}  {'─'*28}  {'─'*28}")
    for nt in grammar.productions:
        f_str = "{ " + ", ".join(sorted(first[nt]))  + " }"
        s_str = "{ " + ", ".join(sorted(follow[nt])) + " }"
        print(f"  {nt:<{col_w}}  {f_str:<28}  {s_str}")
    print(f"{'─'*50}\n")