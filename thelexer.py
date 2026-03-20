"""
Analizador léxico generado automáticamente por YALex.
No edites este archivo a mano — vuelve a generarlo desde el .yal.
"""

# ┌──────────────────────────────────────────────────────────────────────────┐
# │  Header (copiado del .yal)                                               │
# └──────────────────────────────────────────────────────────────────────────┘

from myToken import *

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
    0: {'\t': 1, '\n': 2, ' ': 1, '-': 3, '/': 4, '0': 5, '1': 5, '2': 5, '3': 5, '4': 5, '5': 5, '6': 5, '7': 5, '8': 5, '9': 5, '=': 6, 'A': 7, 'B': 7, 'C': 7, 'D': 7, 'E': 7, 'F': 7, 'G': 7, 'H': 7, 'I': 7, 'J': 7, 'K': 7, 'L': 7, 'M': 7, 'N': 7, 'O': 7, 'P': 7, 'Q': 7, 'R': 7, 'S': 7, 'T': 7, 'U': 7, 'V': 7, 'W': 7, 'X': 7, 'Y': 7, 'Z': 7, 'a': 7, 'b': 7, 'c': 7, 'd': 7, 'e': 7, 'f': 7, 'g': 7, 'h': 7, 'i': 7, 'j': 7, 'k': 7, 'l': 7, 'm': 7, 'n': 7, 'o': 7, 'p': 7, 'q': 7, 'r': 7, 's': 7, 't': 7, 'u': 7, 'v': 7, 'w': 7, 'x': 7, 'y': 7, 'z': 7, '*': 8, '+': 9, '(': 10, ')': 11},
    1: {'\t': 1, ' ': 1},
    2: {},
    3: {},
    4: {},
    5: {'0': 5, '1': 5, '2': 5, '3': 5, '4': 5, '5': 5, '6': 5, '7': 5, '8': 5, '9': 5, '.': 13},
    6: {},
    7: {'0': 7, '1': 7, '2': 7, '3': 7, '4': 7, '5': 7, '6': 7, '7': 7, '8': 7, '9': 7, 'A': 7, 'B': 7, 'C': 7, 'D': 7, 'E': 7, 'F': 7, 'G': 7, 'H': 7, 'I': 7, 'J': 7, 'K': 7, 'L': 7, 'M': 7, 'N': 7, 'O': 7, 'P': 7, 'Q': 7, 'R': 7, 'S': 7, 'T': 7, 'U': 7, 'V': 7, 'W': 7, 'X': 7, 'Y': 7, 'Z': 7, 'a': 7, 'b': 7, 'c': 7, 'd': 7, 'e': 7, 'f': 7, 'g': 7, 'h': 7, 'i': 7, 'j': 7, 'k': 7, 'l': 7, 'm': 7, 'n': 7, 'o': 7, 'p': 7, 'q': 7, 'r': 7, 's': 7, 't': 7, 'u': 7, 'v': 7, 'w': 7, 'x': 7, 'y': 7, 'z': 7},
    8: {},
    9: {},
    10: {},
    11: {},
    12: {'0': 12, '1': 12, '2': 12, '3': 12, '4': 12, '5': 12, '6': 12, '7': 12, '8': 12, '9': 12},
    13: {'0': 12, '1': 12, '2': 12, '3': 12, '4': 12, '5': 12, '6': 12, '7': 12, '8': 12, '9': 12},
}

# Cada estado aceptor mapea a (prioridad, nombre_token).
# Menor prioridad = el patrón fue definido primero en el .yal.
_ACCEPTING: dict[int, tuple[int, str]] = {
    1: (0, None),
    2: (1, 'EOL'),
    3: (6, 'MINUS'),
    4: (8, 'DIV'),
    5: (3, 'INT'),
    6: (11, 'ASSIGN'),
    7: (4, 'ID'),
    8: (7, 'TIMES'),
    9: (5, 'PLUS'),
    10: (9, 'LPAREN'),
    11: (10, 'RPAREN'),
    12: (2, 'FLOAT'),
}

# ┌──────────────────────────────────────────────────────────────────────────┐
# │  Acciones por token                                                      │
# └──────────────────────────────────────────────────────────────────────────┘

def _run_action(token: str, lxm: str):
    """
    Ejecuta la acción asociada al token reconocido.
    Retorna el valor producido por la acción, o None si debe ignorarse.
    """
    if token == None:
        return None
    if token == 'EOL':
        return EOL
    if token == 'MINUS':
        return MINUS
    if token == 'DIV':
        return DIV
    if token == 'INT':
        return INT
    if token == 'ASSIGN':
        return ASSIGN
    if token == 'ID':
        return ID
    if token == 'TIMES':
        return TIMES
    if token == 'PLUS':
        return PLUS
    if token == 'LPAREN':
        return LPAREN
    if token == 'RPAREN':
        return RPAREN
    if token == 'FLOAT':
        return FLOAT
    return None  # acción no reconocida → ignorar

# ┌──────────────────────────────────────────────────────────────────────────┐
# │  Función principal: gettoken(buffer)                                     │
# └──────────────────────────────────────────────────────────────────────────┘

def gettoken(buffer: str) -> list:
    """
    Analiza `buffer` y retorna la lista de tokens reconocidos.

    Cada token es el valor retornado por su acción en el .yal.
    Los tokens cuya acción retorna None son silenciosamente ignorados.

    Lanza LexError si encuentra un carácter no reconocible.
    """
    tokens: list = []
    pos: int = 0
    n: int = len(buffer)

    while pos < n:
        state = _INITIAL

        # Variables del último estado aceptor encontrado
        last_accept_pos:   int   = -1
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
                # Actualiza solo si este patrón tiene mayor prioridad
                if cur > last_accept_pos or prio < last_accept_prio:
                    last_accept_pos   = cur
                    last_accept_token = tok
                    last_accept_prio  = prio

        #    ¿Se encontró algún lexema válido? 
        if last_accept_pos == -1:
            raise LexError(
                f'Error léxico en posición {pos}: carácter {buffer[pos]!r} no reconocido.'
            )

        lxm    = buffer[pos:last_accept_pos]
        result = _run_action(last_accept_token, lxm)
        if result is not None:
            tokens.append(result)

        pos = last_accept_pos  # avanza al siguiente lexema

    return tokens
