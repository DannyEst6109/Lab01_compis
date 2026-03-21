"""
Analizador léxico generado automáticamente por YALex.
No edites este archivo a mano — vuelve a generarlo desde el .yal.
"""

# ┌──────────────────────────────────────────────────────────────────────────┐
# │  Clase de error léxico                                                   │
# └──────────────────────────────────────────────────────────────────────────┘

class LexError(Exception):
    """Excepción lanzada cuando el lexer encuentra un error léxico."""
    pass

# ┌──────────────────────────────────────────────────────────────────────────┐
# │  Tablas del DFA — generadas automáticamente por YALex                    │
# └──────────────────────────────────────────────────────────────────────────┘

_INITIAL = 0

_TRANSITIONS: dict[int, dict[str, int]] = {
    0: {'\t': 1, '\n': 1, ' ': 1, '-': 7, '0': 2, '1': 2, '2': 2, '3': 2, '4': 2, '5': 2, '6': 2, '7': 2, '8': 2, '9': 2, '=': 3, 'A': 4, 'B': 4, 'C': 4, 'D': 4, 'E': 4, 'F': 4, 'G': 4, 'H': 4, 'I': 4, 'J': 4, 'K': 4, 'L': 4, 'M': 4, 'N': 4, 'O': 4, 'P': 4, 'Q': 4, 'R': 4, 'S': 4, 'T': 4, 'U': 4, 'V': 4, 'W': 4, 'X': 4, 'Y': 4, 'Z': 4, 'a': 4, 'b': 4, 'c': 4, 'd': 4, 'e': 4, 'f': 4, 'g': 4, 'h': 4, 'i': 4, 'j': 4, 'k': 4, 'l': 4, 'm': 4, 'n': 4, 'o': 4, 'p': 4, 'q': 4, 'r': 4, 's': 4, 't': 4, 'u': 4, 'v': 4, 'w': 4, 'x': 4, 'y': 4, 'z': 4, '*': 5, '+': 6},
    1: {'\t': 1, '\n': 1, ' ': 1},
    2: {'0': 2, '1': 2, '2': 2, '3': 2, '4': 2, '5': 2, '6': 2, '7': 2, '8': 2, '9': 2},
    3: {},
    4: {'0': 4, '1': 4, '2': 4, '3': 4, '4': 4, '5': 4, '6': 4, '7': 4, '8': 4, '9': 4, 'A': 4, 'B': 4, 'C': 4, 'D': 4, 'E': 4, 'F': 4, 'G': 4, 'H': 4, 'I': 4, 'J': 4, 'K': 4, 'L': 4, 'M': 4, 'N': 4, 'O': 4, 'P': 4, 'Q': 4, 'R': 4, 'S': 4, 'T': 4, 'U': 4, 'V': 4, 'W': 4, 'X': 4, 'Y': 4, 'Z': 4, 'a': 4, 'b': 4, 'c': 4, 'd': 4, 'e': 4, 'f': 4, 'g': 4, 'h': 4, 'i': 4, 'j': 4, 'k': 4, 'l': 4, 'm': 4, 'n': 4, 'o': 4, 'p': 4, 'q': 4, 'r': 4, 's': 4, 't': 4, 'u': 4, 'v': 4, 'w': 4, 'x': 4, 'y': 4, 'z': 4},
    5: {},
    6: {},
    7: {'0': 2, '1': 2, '2': 2, '3': 2, '4': 2, '5': 2, '6': 2, '7': 2, '8': 2, '9': 2},
}

# Cada estado aceptor mapea a (prioridad, nombre_token).
# Menor prioridad = el patrón fue definido primero en el .yal.
_ACCEPTING: dict[int, tuple[int, str]] = {
    1: (0, None),
    2: (2, None),
    3: (5, None),
    4: (1, None),
    5: (4, None),
    6: (3, None),
}

# ┌──────────────────────────────────────────────────────────────────────────┐
# │  Acciones por token                                                      │
# └──────────────────────────────────────────────────────────────────────────┘

def _run_action(state: int, lxm: str):
    """
    Ejecuta la acción del estado aceptor que reconoció el lexema.
    Retorna el valor producido, o None si el token debe ignorarse.
    """
    if state == 1:
        return None  # token ignorado (ej. whitespace)
    if state == 2:
        print("Número\n")
    if state == 3:
        print("Operador de asignación\n")
    if state == 4:
        print("Identificador\n")
    if state == 5:
        print("Operador de multiplicación\n")
    if state == 6:
        print("Operador de suma\n")
    return None  # estado no registrado → ignorar

# ┌──────────────────────────────────────────────────────────────────────────┐
# │  Función principal: tokens(buffer)                                       │
# └──────────────────────────────────────────────────────────────────────────┘

def tokens(buffer: str) -> list:
    """
    Analiza `buffer` y retorna la lista de tokens reconocidos.
    Las acciones con print() producen salida como efecto secundario.
    Los errores léxicos se imprimen y se salta el carácter inválido.
    """
    tokens: list = []
    pos: int = 0
    n: int = len(buffer)
    line: int = 1     # número de línea actual (base 1)
    line_start: int = 0  # posición en buffer donde empieza la línea actual

    while pos < n:
        state = _INITIAL

        # Variables del último estado aceptor encontrado
        last_accept_pos:   int   = -1
        last_accept_state: int   = -1
        last_accept_token: str   = ''
        last_accept_prio:  float = float('inf')

        cur = pos

        # ── Longest-match: avanza mientras haya transición válida ──
        while cur < n:
            ch         = buffer[cur]
            next_state = _TRANSITIONS.get(state, {}).get(ch, -1)
            if next_state == -1:
                break
            state = next_state
            cur  += 1

            # Si el nuevo estado es aceptor, lo recordamos
            if state in _ACCEPTING:
                prio, tok = _ACCEPTING[state]
                # Lexema más largo siempre gana (cur solo crece).
                # La prioridad solo desempata tokens distintos a igual longitud.
                if cur > last_accept_pos or prio < last_accept_prio:
                    last_accept_pos   = cur
                    last_accept_state = state
                    last_accept_token = tok
                    last_accept_prio  = prio

        # ── ¿Se encontró algún lexema válido? ──────────────────────
        if last_accept_pos == -1:
            col = pos - line_start + 1
            print(f'Error léxico en la línea {line}, posición {col}: caracter no válido {buffer[pos]!r}.')
            # Actualiza contadores de línea si el caracter inválido es \n
            if buffer[pos] == '\n':
                line += 1
                line_start = pos + 1
            pos += 1  # salta el caracter inválido y continúa
            continue

        lxm    = buffer[pos:last_accept_pos]
        result = _run_action(last_accept_state, lxm)
        if result is not None:
            tokens.append(result)

        # Actualiza contadores de línea según los \n consumidos en el lexema
        offset = 0
        for ch in lxm:
            if ch == '\n':
                line += 1
                line_start = pos + offset + 1
            offset += 1
        pos = last_accept_pos  # avanza al siguiente lexema

    return tokens
