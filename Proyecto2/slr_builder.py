# =============================================================================
# slr_builder.py — Parte 2: Construcción del Autómata LR(0) y Tablas SLR
# =============================================================================
#
# FLUJO GENERAL:
#   Grammar (Parte 1)
#       → augment_grammar()          → agrega S' → S
#       → build_lr0_automaton()      → construye los estados y transiciones
#       → build_slr_tables()         → llena ACTION y GOTO con los FOLLOW sets
#       → LR0Automaton + SLRTables  (para la Parte 3)

from models import Grammar, LRItem, State, LR0Automaton, SLRTables
from typing import FrozenSet, Dict, List, Tuple, Set


# =============================================================================
# PASO 1: Gramática Aumentada
# =============================================================================

def augment_grammar(grammar: Grammar) -> Grammar:
    """
    Agrega la producción S' → S al inicio.

    ¿Por qué? El algoritmo LR(0) necesita un único punto de aceptación.
    Al agregar S' → S, cuando el parser reduzca S' → S, sabe que terminó.

    Ejemplo:
        Antes: start_symbol = "production1"
        Después: se agrega ("production1'", ["production1"]) al inicio
    """
    new_start = grammar.start_symbol + "'"

    # Nos aseguramos que el símbolo nuevo no choque con algo existente
    while new_start in grammar.non_terminals:
        new_start += "'"

    augmented_productions = [(new_start, [grammar.start_symbol])] + grammar.productions

    # Actualizar FOLLOW: el símbolo inicial aumentado tiene $ en su FOLLOW
    augmented_follow = dict(grammar.follow)
    augmented_follow[new_start] = {'$'}

    original_start = grammar.start_symbol
    augmented_follow[original_start] = augmented_follow.get(original_start, set()) | {'$'}

    return Grammar(
        terminals=grammar.terminals + (['$'] if '$' not in grammar.terminals else []),
        non_terminals=[new_start] + grammar.non_terminals,
        productions=augmented_productions,
        start_symbol=new_start,
        ignored_tokens=grammar.ignored_tokens,
        first=grammar.first,
        follow=augmented_follow,
    )


# =============================================================================
# PASO 2: Clausura (Closure)
# =============================================================================

def closure(items: FrozenSet[LRItem], grammar: Grammar) -> FrozenSet[LRItem]:
    """
    Calcula la clausura de un conjunto de ítems LR(0).

    REGLA: Si tenemos el ítem  A → α • B β  (el punto está antes de B, un no-terminal),
           entonces para cada producción B → γ en la gramática,
           agregamos el ítem  B → • γ  al conjunto.

    Repetimos hasta que no haya más ítems nuevos que agregar.

    Ejemplo:
        Items iniciales: { production1' → • production1 }
        Clausura agrega: { production1 → • production1 TOKEN_2 production2,
                           production1 → • production2,
                           production2 → • production2 TOKEN_2 production3,
                           ... y así sucesivamente }
    """
    closure_set: Set[LRItem] = set(items)

    changed = True
    while changed:
        changed = False
        new_items: Set[LRItem] = set()

        for item in closure_set:
            next_sym = item.next_symbol()

            # Solo nos interesa si el símbolo después del punto es un NO-TERMINAL
            if next_sym and next_sym in grammar.non_terminals:
                for head, body in grammar.productions:
                    if head == next_sym:
                        candidate = LRItem(head, tuple(body), 0)
                        if candidate not in closure_set:
                            new_items.add(candidate)
                            changed = True

        closure_set |= new_items

    return frozenset(closure_set)


# =============================================================================
# PASO 3: Función GOTO
# =============================================================================

def goto(items: FrozenSet[LRItem], symbol: str, grammar: Grammar) -> FrozenSet[LRItem]:
    """
    Calcula GOTO(items, símbolo): a qué estado vamos si leemos 'símbolo'.

    REGLA: Toma todos los ítems donde el punto está justo antes de 'símbolo',
           avanza el punto, y calcula la clausura del resultado.

    Ejemplo:
        GOTO({ production1 → prod1 • TOKEN_2 prod2 }, TOKEN_2)
           → clausura({ production1 → prod1 TOKEN_2 • prod2 })
    """
    moved: Set[LRItem] = set()

    for item in items:
        if item.next_symbol() == symbol:
            moved.add(item.advance())

    if not moved:
        return frozenset()

    return closure(frozenset(moved), grammar)


# =============================================================================
# PASO 4: Colección Canónica de Estados (el autómata LR(0))
# =============================================================================

def build_lr0_automaton(grammar: Grammar) -> LR0Automaton:
    """
    Construye todos los estados del autómata LR(0) usando un algoritmo BFS.

    ALGORITMO:
        1. Estado inicial = clausura del ítem S' → • S
        2. Para cada estado y cada símbolo posible, calcula GOTO
        3. Si el resultado es un conjunto nuevo, crea un estado nuevo
        4. Registra la transición
        5. Repite hasta no haber estados nuevos

    NOTA: La gramática que llega aquí ya debe estar aumentada.
    """
    # Ítem inicial: S' → • start_symbol
    aug_head, aug_body = grammar.productions[0]    # S' → S es siempre la primera
    start_item = LRItem(aug_head, tuple(aug_body), 0)
    start_items = closure(frozenset([start_item]), grammar)

    # state_map: frozenset de ítems → id del estado (para no duplicar)
    state_map: Dict[FrozenSet[LRItem], int] = {}
    states: List[State] = []
    transitions: Dict[Tuple[int, str], int] = {}

    # Crear estado 0
    state_0 = State(id=0, items=start_items)
    states.append(state_0)
    state_map[start_items] = 0

    # BFS: procesamos estados pendientes
    worklist: List[State] = [state_0]
    all_symbols = grammar.terminals + grammar.non_terminals

    while worklist:
        current_state = worklist.pop(0)

        for symbol in all_symbols:
            next_items = goto(current_state.items, symbol, grammar)

            if not next_items:
                continue    # GOTO vacío → no hay transición por este símbolo

            if next_items not in state_map:
                # Estado nuevo
                new_id = len(states)
                new_state = State(id=new_id, items=next_items)
                states.append(new_state)
                state_map[next_items] = new_id
                worklist.append(new_state)

            # Registrar transición: (estado_actual, símbolo) → estado_destino
            transitions[(current_state.id, symbol)] = state_map[next_items]

    return LR0Automaton(states=states, transitions=transitions)


# =============================================================================
# PASO 5: Construcción de las Tablas SLR
# =============================================================================
def build_slr_tables(automaton: LR0Automaton, grammar: Grammar) -> SLRTables:
    action: Dict[Tuple[int, str], Tuple] = {}
    goto_table: Dict[Tuple[int, str], int] = {}
    conflicts: List[str] = []

    # ── CAMBIO: usa start_symbol en lugar de productions[0] ──────────
    aug_start = grammar.start_symbol   # siempre es "programa'" (o S')
    # ─────────────────────────────────────────────────────────────────

    def set_action(state_id, symbol, new_action):
        key = (state_id, symbol)
        if key in action:
            existing = action[key]
            if existing != new_action:
                conflict_msg = (
                    f"!!! Conflicto en Estado {state_id}, símbolo '{symbol}': "
                    f"{existing} vs {new_action}"
                )
                if conflict_msg not in conflicts:
                    conflicts.append(conflict_msg)
                if new_action[0] == 'shift':
                    action[key] = new_action
        else:
            action[key] = new_action

    for state in automaton.states:
        for item in state.items:
            next_sym = item.next_symbol()

            if next_sym is not None:
                if next_sym in grammar.terminals:
                    if (state.id, next_sym) in automaton.transitions:
                        target = automaton.transitions[(state.id, next_sym)]
                        set_action(state.id, next_sym, ("shift", target))
                elif next_sym in grammar.non_terminals:
                    if (state.id, next_sym) in automaton.transitions:
                        goto_table[(state.id, next_sym)] = automaton.transitions[(state.id, next_sym)]
            else:
                # ── CAMBIO: basta comparar item.head con aug_start ────
                if item.head == aug_start:
                    set_action(state.id, '$', ("accept",))
                # ─────────────────────────────────────────────────────
                else:
                    prod_index = _find_production_index(grammar, item.head, list(item.body))
                    follow_set = grammar.follow.get(item.head, set())
                    for terminal in follow_set:
                        set_action(state.id, terminal, ("reduce", prod_index))

    return SLRTables(action=action, goto=goto_table, conflicts=conflicts)

def _find_production_index(grammar: Grammar, head: str, body: List[str]) -> int:
    """Devuelve el índice de la producción (head, body) en grammar.productions."""
    for i, (h, b) in enumerate(grammar.productions):
        if h == head and b == body:
            return i
    raise ValueError(f"Producción no encontrada: {head} → {' '.join(body)}")


# =============================================================================
# FUNCIÓN PRINCIPAL: construir todo desde una Grammar
# =============================================================================

def build_parser(grammar: Grammar) -> Tuple[Grammar, LR0Automaton, SLRTables]:
    """
    Punto de entrada de la Parte 2.
    Recibe el Grammar de la Parte 1 y devuelve todo lo que necesita la Parte 3.

    Uso:
        from slr_builder import build_parser
        augmented_grammar, automaton, tables = build_parser(grammar)

    Returns:
        augmented_grammar : Grammar con la producción S' → S agregada
        automaton         : LR0Automaton con todos los estados y transiciones
        tables            : SLRTables con ACTION, GOTO y lista de conflictos
    """
    print("Aumentando gramática...")
    aug_grammar = augment_grammar(grammar)

    print(f"   Símbolo inicial aumentado: {aug_grammar.start_symbol}")
    print(f"   Producciones totales: {len(aug_grammar.productions)}")

    print("\nConstruyendo autómata LR(0)...")
    automaton = build_lr0_automaton(aug_grammar)

    print(f"   Estados generados: {len(automaton.states)}")
    print(f"   Transiciones: {len(automaton.transitions)}")

    print("\nConstruyendo tablas SLR...")
    tables = build_slr_tables(automaton, aug_grammar)

    print(f"   Entradas en ACTION: {len(tables.action)}")
    print(f"   Entradas en GOTO:   {len(tables.goto)}")

    if tables.conflicts:
        print(f"\n⚠  Se detectaron {len(tables.conflicts)} conflicto(s):")
        for c in tables.conflicts:
            print(f"   {c}")
    else:
        print("\n :D Sin conflictos. La gramática es SLR(1).")

    return aug_grammar, automaton, tables


# =============================================================================
# UTILIDADES DE DEPURACIÓN (útiles para ti mientras desarrollas)
# =============================================================================

def print_automaton(automaton: LR0Automaton):
    """Imprime todos los estados del autómata en formato legible."""
    print("\n" + "="*60)
    print("AUTÓMATA LR(0)")
    print("="*60)
    for state in automaton.states:
        print(f"\n{state}")
        # Mostrar transiciones que salen de este estado
        for (src, sym), dst in sorted(automaton.transitions.items()):
            if src == state.id:
                print(f"  --[{sym}]--> Estado {dst}")


def print_slr_tables(tables: SLRTables, grammar: Grammar):
    """
    Imprime las tablas ACTION y GOTO en formato de tabla.
    """
    all_states = sorted(set(k[0] for k in tables.action) | set(k[0] for k in tables.goto))
    terminals = sorted(set(k[1] for k in tables.action))
    non_terms = sorted(set(k[1] for k in tables.goto))

    print("\n" + "="*60)
    print("TABLA ACTION")
    print("="*60)
    header = f"{'Estado':>8} | " + " | ".join(f"{t:>12}" for t in terminals)
    print(header)
    print("-" * len(header))
    for state_id in all_states:
        row = f"{state_id:>8} | "
        cells = []
        for t in terminals:
            act = tables.action.get((state_id, t))
            if act is None:
                cells.append(f"{'':>12}")
            elif act[0] == 'shift':
                cells.append(f"{'s'+str(act[1]):>12}")
            elif act[0] == 'reduce':
                cells.append(f"{'r'+str(act[1]):>12}")
            elif act[0] == 'accept':
                cells.append(f"{'acc':>12}")
        row += " | ".join(cells)
        print(row)

    print("\n" + "="*60)
    print("TABLA GOTO")
    print("="*60)
    header = f"{'Estado':>8} | " + " | ".join(f"{n:>14}" for n in non_terms)
    print(header)
    print("-" * len(header))
    for state_id in all_states:
        row = f"{state_id:>8} | "
        cells = []
        for n in non_terms:
            g = tables.goto.get((state_id, n))
            cells.append(f"{str(g) if g is not None else '':>14}")
        row += " | ".join(cells)
        print(row)