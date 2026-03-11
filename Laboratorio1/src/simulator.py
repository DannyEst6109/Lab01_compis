def simulate_dfa(transitions, accepting_states, input_string: str):
    current_state = "S0"
    path = [current_state]

    for char in input_string:
        if current_state not in transitions:
            return False, path

        next_state = transitions[current_state].get(char, "-")
        if next_state == "-":
            path.append(f"∅({char})")
            return False, path

        current_state = next_state
        path.append(current_state)

    return current_state in accepting_states, path