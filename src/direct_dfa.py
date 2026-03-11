from collections import deque


def build_dfa(root, followpos, pos_to_symbol, alphabet, end_marker_pos):
    start_state = frozenset(root.firstpos)

    states = [start_state]
    state_ids = {start_state: "S0"}
    transitions = {}
    accepting_states = set()

    queue = deque([start_state])

    while queue:
        current_state = queue.popleft()
        current_name = state_ids[current_state]

        if end_marker_pos in current_state:
            accepting_states.add(current_name)

        transitions[current_name] = {}

        for symbol in alphabet:
            next_positions = set()

            for pos in current_state:
                if pos_to_symbol[pos] == symbol:
                    next_positions.update(followpos[pos])

            if next_positions:
                frozen_next = frozenset(next_positions)

                if frozen_next not in state_ids:
                    new_name = f"S{len(state_ids)}"
                    state_ids[frozen_next] = new_name
                    states.append(frozen_next)
                    queue.append(frozen_next)

                transitions[current_name][symbol] = state_ids[frozen_next]
            else:
                transitions[current_name][symbol] = "-"

    named_states = [(state_ids[s], set(s)) for s in states]
    return named_states, transitions, accepting_states


def print_followpos_table(followpos, pos_to_symbol):
    print("\n--- Tabla de followpos ---")
    print(f"{'Pos':<8}{'Símbolo':<10}{'Followpos'}")
    print("-" * 40)
    for pos in sorted(followpos.keys()):
        print(f"{pos:<8}{pos_to_symbol[pos]:<10}{sorted(followpos[pos])}")


def print_transition_table(states, transitions, accepting_states, alphabet):
    print("\n--- Tabla de transición del AFD ---")

    headers = ["Estado", "Posiciones"] + alphabet + ["Aceptación"]
    widths = [10, 25] + [10] * len(alphabet) + [12]

    for h, w in zip(headers, widths):
        print(f"{h:<{w}}", end="")
    print()

    print("-" * sum(widths))

    for state_name, positions in states:
        print(f"{state_name:<10}{str(sorted(positions)):<25}", end="")

        for symbol in alphabet:
            print(f"{transitions[state_name].get(symbol, '-'): <10}", end="")

        is_accepting = "Sí" if state_name in accepting_states else "No"
        print(f"{is_accepting:<12}")