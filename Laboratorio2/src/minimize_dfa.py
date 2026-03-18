"""
Minimización de AFD usando el algoritmo de particiones (Hopcroft).

Formatos esperados (idénticos a direct_dfa.py del Lab01):
  states           : list[ (state_name: str, positions: set) ]
  transitions      : dict[ state_name ][ symbol ] -> state_name | "-"
  accepting_states : set[ state_name ]
  alphabet         : list[ str ]
"""


# Función principal
def minimize_dfa(states, transitions, accepting_states, alphabet):
    """
    Recibe el AFD generado por el método directo y devuelve el AFD mínimo
    en el mismo formato que build_dfa() de direct_dfa.py.

    Retorna: (new_states, new_transitions, new_accepting_states)
    """
    state_names = [name for name, _ in states]

    # Paso 1: partición inicial
    accepting     = frozenset(s for s in state_names if s in accepting_states)
    non_accepting = frozenset(s for s in state_names if s not in accepting_states)

    partitions = []
    if accepting:
        partitions.append(accepting)
    if non_accepting:
        partitions.append(non_accepting)

    # Paso 2: iteraciones
    changed = True
    while changed:
        changed = False
        new_partitions = []
        for group in partitions:
            splits = _split_group(group, partitions, transitions, alphabet)
            new_partitions.extend(splits)
            if len(splits) > 1:
                changed = True
        partitions = new_partitions

    # Paso 3: construir AFD mínimo 
    start_state = state_names[0]   # S0 siempre es el estado inicial
    return _build_minimized_dfa(
        partitions, states, transitions, accepting_states, alphabet, start_state
    )


# Helpers internos
def _find_partition_index(state, partitions):
    """Devuelve el índice de la partición a la que pertenece `state`, o None si es '-'."""
    if state == "-":
        return None
    for i, group in enumerate(partitions):
        if state in group:
            return i
    return None


def _split_group(group, partitions, transitions, alphabet):
    """
    Intenta dividir `group` en subgrupos de estados indistinguibles.
    Dos estados son indistinguibles si, para todo símbolo del alfabeto,
    sus destinos caen en la misma partición actual.
    """
    group_list = list(group)
    subgroups  = []                  # list[ list[state_name] ]

    for state in group_list:
        placed = False
        for subgroup in subgroups:
            rep = subgroup[0]
            if _same_signature(state, rep, partitions, transitions, alphabet):
                subgroup.append(state)
                placed = True
                break
        if not placed:
            subgroups.append([state])

    return [frozenset(sg) for sg in subgroups]


def _same_signature(s1, s2, partitions, transitions, alphabet):
    """True si s1 y s2 tienen exactamente la misma firma de transición."""
    for symbol in alphabet:
        dest1 = transitions[s1].get(symbol, "-")
        dest2 = transitions[s2].get(symbol, "-")
        if _find_partition_index(dest1, partitions) != _find_partition_index(dest2, partitions):
            return False
    return True


def _build_minimized_dfa(partitions, old_states, old_transitions,
                         old_accepting, alphabet, start_state):
    """Construye el nuevo AFD a partir de las particiones finales."""

    # Reordenar para que la partición del estado inicial quede primero (→ "S0")
    start_part = next(p for p in partitions if start_state in p)
    ordered = [start_part] + [p for p in partitions if p is not start_part]

    # Nombre nuevo para cada grupo
    new_name = {id(p): f"S{i}" for i, p in enumerate(ordered)}

    # Mapa: estado viejo -> frozenset de su grupo
    state_to_group = {}
    for group in ordered:
        for s in group:
            state_to_group[s] = group

    # Posiciones originales de cada estado viejo
    old_positions = {name: pos for name, pos in old_states}

    new_states      = []
    new_transitions = {}
    new_accepting   = set()

    for group in ordered:
        name = new_name[id(group)]

        # Posiciones: unión de las posiciones de todos los estados del grupo
        merged_pos = set()
        for s in group:
            merged_pos.update(old_positions.get(s, set()))
        new_states.append((name, merged_pos))

        # Estado de aceptación si alguno del grupo lo era
        if any(s in old_accepting for s in group):
            new_accepting.add(name)

        # Transiciones usando el representante del grupo
        rep = next(iter(group))
        new_transitions[name] = {}
        for symbol in alphabet:
            dest = old_transitions[rep].get(symbol, "-")
            if dest == "-":
                new_transitions[name][symbol] = "-"
            else:
                dest_group = state_to_group[dest]          # objeto correcto
                new_transitions[name][symbol] = new_name[id(dest_group)]

    return new_states, new_transitions, new_accepting


# ---------------------------------------------------------------------------
# Comparación y estadísticas
# ---------------------------------------------------------------------------

def compare_dfas(original_states, original_transitions,
                 min_states, min_transitions, alphabet):
    """
    Imprime una comparación entre el AFD directo y el minimizado.
    """
    def count_transitions(trans, alph):
        return sum(
            1
            for state_trans in trans.values()
            for sym in alph
            if state_trans.get(sym, "-") != "-"
        )

    orig_n  = len(original_states)
    min_n   = len(min_states)
    orig_t  = count_transitions(original_transitions, alphabet)
    min_t   = count_transitions(min_transitions, alphabet)

    print("\n╔══════════════════════════════════════════════╗")
    print("║         Comparación AFD directo vs mínimo    ║")
    print("╠══════════════════════════════════════╦═══════╣")
    print(f"║ {'Métrica':<36} {'Directo':>4} │ {'Mínimo':>5} ║")
    print("╠══════════════════════════════════════╬═══════╣")
    print(f"║ {'Número de estados':<36} {orig_n:>4}  │ {min_n:>5}  ║")
    print(f"║ {'Número de transiciones reales':<36} {orig_t:>4}  │ {min_t:>5}  ║")
    print("╠══════════════════════════════════════╬═══════╣")

    if orig_n == min_n:
        print("║  ✔  El AFD directo YA era mínimo.              ║")
    else:
        saved_s = orig_n - min_n
        saved_t = orig_t - min_t
        print(f"║  ✔  Estados reducidos : {saved_s:>2}                      ║")
        print(f"║  ✔  Transiciones red. : {saved_t:>2}                      ║")

    print("╚══════════════════════════════════════════════╝")