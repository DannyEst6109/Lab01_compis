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
    0: {'\t': 1, '\n': 1, ' ': 1, '-': 2, '/': 3, '0': 4, '1': 4, '2': 4, '3': 4, '4': 4, '5': 4, '6': 4, '7': 4, '8': 4, '9': 4, '*': 5, '+': 6, '(': 7, ')': 8},
    1: {'\t': 1, '\n': 1, ' ': 1},
    2: {},
    3: {},
    4: {'0': 4, '1': 4, '2': 4, '3': 4, '4': 4, '5': 4, '6': 4, '7': 4, '8': 4, '9': 4},
    5: {},
    6: {},
    7: {},
    8: {},
}

# Cada estado aceptor mapea a (prioridad, nombre_token).
# Menor prioridad = el patrón fue definido primero en el .yal.
_ACCEPTING: dict[int, tuple[int, str]] = {
    1: (0, None),
    2: (3, None),
    3: (5, None),
    4: (1, None),
    5: (4, None),
    6: (2, None),
    7: (6, None),
    8: (7, None),
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
        print("RESTA")
    if state == 3:
        print("DIV")
    if state == 4:
        print("ENTERO: " + lxm)
    if state == 5:
        print("MULT")
    if state == 6:
        print("SUMA")
    if state == 7:
        print("LPAREN")
    if state == 8:
        print("RPAREN")
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
