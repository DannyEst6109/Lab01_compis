"""
lexer_generator_yalex.py
==================
Generador de analizadores léxicos para YALex.

Recibe un DFA combinado (producido por el módulo de autómatas del equipo)
y escribe un archivo .py autónomo que implementa el analizador léxico.

Estructura esperada de `dfa_result`
------------------------------------
{
    "initial_state": 0,

    "transitions": {
        # { estado (int): { símbolo (str): siguiente_estado (int) } }
        0: {"a": 1, "+": 5, " ": 8},
        1: {"b": 2},
        ...
    },

    "accepting_states": {
        # { estado (int): { ... } }
        3: {
            "priority": 0,               # 0 = primer patrón en el .yal
            "token":    "INT",           # nombre del token
            "action":   "return ('INT', lxm)"  # código exacto del .yal
        },
        5: {
            "priority": 1,
            "token":    "PLUS",
            "action":   "return ('PLUS', lxm)"
        },
        8: {
            "priority": 2,
            "token":    "WS",
            "action":   ""               # cadena vacía → ignorar token
        },
    },

    "entrypoint": "gettoken",   # nombre de la función en el .yal
    "header":     "...",        # contenido de { header } del .yal, o ""
    "trailer":    "",           # contenido de { trailer } del .yal, o ""
}

Uso
---
    from lexer_generator import generate_lexer
    generate_lexer(dfa_result, "thelexer.py")

El archivo generado (thelexer.py) es completamente autónomo:
    from thelexer import gettoken
    tokens = gettoken("3 + 42")
"""

from __future__ import annotations
from typing import Any


# ═══════════════════════════════════════════════════════════════════════════════
# Validación del DFA recibido
# ═══════════════════════════════════════════════════════════════════════════════

def _validate(dfa: dict) -> None:
    """Lanza ValueError si la estructura del DFA está incompleta."""
    required = ("initial_state", "transitions", "accepting_states", "entrypoint")
    for key in required:
        if key not in dfa:
            raise ValueError(f"dfa_result le falta la clave obligatoria: '{key}'")

    if not isinstance(dfa["transitions"], dict):
        raise ValueError("'transitions' debe ser un dict.")

    if not isinstance(dfa["accepting_states"], dict):
        raise ValueError("'accepting_states' debe ser un dict.")

    for state, info in dfa["accepting_states"].items():
        for field in ("priority", "token", "action"):
            if field not in info:
                raise ValueError(
                    f"Estado aceptor {state} le falta el campo '{field}'."
                )


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers de escritura
# ═══════════════════════════════════════════════════════════════════════════════

def _w(lines: list[str], text: str = "") -> None:
    """Agrega una línea a la lista de salida."""
    lines.append(text)


def _section(lines: list[str], title: str) -> None:
    """Agrega un encabezado de sección decorativo."""
    bar = "─" * 74
    _w(lines, f"# ┌{bar}┐")
    _w(lines, f"# │  {title:<72}│")
    _w(lines, f"# └{bar}┘")


# ═══════════════════════════════════════════════════════════════════════════════
# Generación del código del lexer
# ═══════════════════════════════════════════════════════════════════════════════

def _fix_imports(line: str) -> str:
    """
    Convierte 'import X' → 'from X import *' para que los nombres
    definidos en el módulo (EOL, INT, PLUS, etc.) sean accesibles
    directamente en las acciones del lexer generado.
    Deja intactos 'from X import ...' y cualquier otra línea.
    """
    stripped = line.lstrip()
    if stripped.startswith("import ") and "from " not in stripped:
        indent = line[: len(line) - len(stripped)]
        module = stripped[len("import "):].strip()
        return f"{indent}from {module} import *"
    return line


def _gen_header(lines: list[str], header: str) -> None:
    if not header.strip():
        return
    _section(lines, "Header (copiado del .yal)")
    _w(lines)
    for line in header.splitlines():
        _w(lines, _fix_imports(line))
    _w(lines)


def _gen_tables(lines: list[str], dfa: dict) -> None:
    _section(lines, "Tablas del DFA — generadas automáticamente por YALex")
    _w(lines)

    # Estado inicial
    _w(lines, f"_INITIAL = {dfa['initial_state']!r}")
    _w(lines)

    # Tabla de transiciones
    _w(lines, "_TRANSITIONS: dict[int, dict[str, int]] = {")
    for state, symbol_map in dfa["transitions"].items():
        _w(lines, f"    {state!r}: {symbol_map!r},")
    _w(lines, "}")
    _w(lines)

    # Estados de aceptación: estado → (prioridad, nombre_token)
    _w(lines, "# Cada estado aceptor mapea a (prioridad, nombre_token).")
    _w(lines, "# Menor prioridad = el patrón fue definido primero en el .yal.")
    _w(lines, "_ACCEPTING: dict[int, tuple[int, str]] = {")
    for state, info in dfa["accepting_states"].items():
        _w(lines, f"    {state!r}: ({info['priority']!r}, {info['token']!r}),")
    _w(lines, "}")
    _w(lines)


def _gen_actions(lines: list[str], dfa: dict) -> None:
    _section(lines, "Acciones por token")
    _w(lines)
    # Despachamos por estado (no por nombre de token) para ser robustos
    # ante DFAs donde varios estados aceptores comparten el mismo nombre.
    _w(lines, "def _run_action(state: int, lxm: str):")
    _w(lines, '    """')
    _w(lines, "    Ejecuta la acción del estado aceptor que reconoció el lexema.")
    _w(lines, "    Retorna el valor producido, o None si el token debe ignorarse.")
    _w(lines, '    """')

    for state, info in dfa["accepting_states"].items():
        action = info["action"].strip()
        _w(lines, f"    if state == {state!r}:")
        if action:
            for action_line in action.splitlines():
                _w(lines, f"        {action_line}")
        else:
            _w(lines, "        return None  # token ignorado (ej. whitespace)")

    _w(lines, "    return None  # estado no registrado → ignorar")
    _w(lines)


def _gen_lexer_function(lines: list[str], dfa: dict) -> None:
    ep = dfa["entrypoint"]
    _section(lines, f"Función principal: {ep}(buffer)")
    _w(lines)

    _w(lines, f"def {ep}(buffer: str) -> list:")
    _w(lines, '    """'  )
    _w(lines, "    Analiza `buffer` y retorna la lista de tokens reconocidos.")
    _w(lines, "    Las acciones con print() producen salida como efecto secundario.")
    _w(lines, "    Los errores léxicos se imprimen y se salta el carácter inválido.")
    _w(lines, '    """'  )
    _w(lines, "    tokens: list = []")
    _w(lines, "    pos: int = 0")
    _w(lines, "    n: int = len(buffer)")
    _w(lines, "    line: int = 1     # número de línea actual (base 1)")
    _w(lines, "    line_start: int = 0  # posición en buffer donde empieza la línea actual")
    _w(lines)
    _w(lines, "    while pos < n:")
    _w(lines, "        state = _INITIAL")
    _w(lines)
    _w(lines, "        # Variables del último estado aceptor encontrado")
    _w(lines, "        last_accept_pos:   int   = -1")
    _w(lines, "        last_accept_state: int   = -1")
    _w(lines, "        last_accept_token: str   = ''")
    _w(lines, "        last_accept_prio:  float = float('inf')")
    _w(lines)
    _w(lines, "        cur = pos")
    _w(lines)
    _w(lines, "        # ── Longest-match: avanza mientras haya transición válida ──")
    _w(lines, "        while cur < n:")
    _w(lines, "            ch         = buffer[cur]")
    _w(lines, "            next_state = _TRANSITIONS.get(state, {}).get(ch, -1)")
    _w(lines, "            if next_state == -1:")
    _w(lines, "                break")
    _w(lines, "            state = next_state")
    _w(lines, "            cur  += 1")
    _w(lines)
    _w(lines, "            # Si el nuevo estado es aceptor, lo recordamos")
    _w(lines, "            if state in _ACCEPTING:")
    _w(lines, "                prio, tok = _ACCEPTING[state]")
    _w(lines, "                # Lexema más largo siempre gana (cur solo crece).")
    _w(lines, "                # La prioridad solo desempata tokens distintos a igual longitud.")
    _w(lines, "                if cur > last_accept_pos or prio < last_accept_prio:")
    _w(lines, "                    last_accept_pos   = cur")
    _w(lines, "                    last_accept_state = state")
    _w(lines, "                    last_accept_token = tok")
    _w(lines, "                    last_accept_prio  = prio")
    _w(lines)
    _w(lines, "        # ── ¿Se encontró algún lexema válido? ──────────────────────")
    _w(lines, "        if last_accept_pos == -1:")
    _w(lines, "            col = pos - line_start + 1")
    _w(lines, "            print(f'Error léxico en la línea {line}, posición {col}: caracter no válido {buffer[pos]!r}.')")
    _w(lines, "            # Actualiza contadores de línea si el caracter inválido es \\n")
    _w(lines, "            if buffer[pos] == '\\n':")
    _w(lines, "                line += 1")
    _w(lines, "                line_start = pos + 1")
    _w(lines, "            pos += 1  # salta el caracter inválido y continúa")
    _w(lines, "            continue")
    _w(lines)
    _w(lines, "        lxm    = buffer[pos:last_accept_pos]")
    _w(lines, "        result = _run_action(last_accept_state, lxm)")
    _w(lines, "        if result is not None:")
    _w(lines, "            tokens.append(result)")
    _w(lines)
    _w(lines, "        # Actualiza contadores de línea según los \\n consumidos en el lexema")
    _w(lines, "        offset = 0")
    _w(lines, "        for ch in lxm:")
    _w(lines, "            if ch == '\\n':")
    _w(lines, "                line += 1")
    _w(lines, "                line_start = pos + offset + 1")
    _w(lines, "            offset += 1")
    _w(lines, "        pos = last_accept_pos  # avanza al siguiente lexema")
    _w(lines)
    _w(lines, "    return tokens")
    _w(lines)


def _gen_error_class(lines: list[str]) -> None:
    _section(lines, "Clase de error léxico")
    _w(lines)
    _w(lines, "class LexError(Exception):")
    _w(lines, '    """Excepción lanzada cuando el lexer encuentra un error léxico."""')
    _w(lines, "    pass")
    _w(lines)


def _gen_trailer(lines: list[str], trailer: str) -> None:
    if not trailer.strip():
        return
    _section(lines, "Trailer (copiado del .yal)")
    _w(lines)
    for line in trailer.splitlines():
        _w(lines, line)
    _w(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Puntos de entrada públicos
# ═══════════════════════════════════════════════════════════════════════════════

def generate_token_module(dfa_result: dict[str, Any], output_path: str) -> None:
    """
    Genera el módulo de tokens (myToken.py) a partir del DFA combinado.
    Extrae todos los nombres de tokens de los estados aceptores y los
    define como constantes de cadena.

    Parámetros
    ----------
    dfa_result  : el mismo dict que se pasa a generate_lexer.
    output_path : ruta del archivo a crear (ej. "myToken.py").
    """
    _validate(dfa_result)

    # Recopilar tokens únicos en orden de prioridad (orden del .yal)
    tokens_by_priority: list[tuple[int, str]] = []
    seen: set[str] = set()

    for info in dfa_result["accepting_states"].values():
        name     = info["token"]
        priority = info["priority"]
        if name is None or name in seen:
            continue
        seen.add(name)
        tokens_by_priority.append((priority, name))

    tokens_by_priority.sort()   # ordena por prioridad (= orden en el .yal)

    lines: list[str] = []
    _w(lines, '"""')
    _w(lines, "myToken.py — módulo de tokens generado automáticamente por YALex.")
    _w(lines, "No edites este archivo a mano — vuelve a generarlo desde el .yal.")
    _w(lines, '"""')
    _w(lines)

    for _, name in tokens_by_priority:
        _w(lines, f"{name} = {name!r}")

    _w(lines)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅  Módulo de tokens generado exitosamente → {output_path}")


def generate_lexer(dfa_result: dict[str, Any], output_path: str) -> None:
    """
    Genera el analizador léxico a partir del DFA combinado.

    Parámetros
    ----------
    dfa_result  : dict con la estructura documentada al inicio del módulo.
    output_path : ruta del archivo .py a crear (ej. "thelexer.py").
    """
    _validate(dfa_result)

    header  = dfa_result.get("header",  "")
    trailer = dfa_result.get("trailer", "")

    lines: list[str] = []

    _w(lines, '"""')
    _w(lines, f"Analizador léxico generado automáticamente por YALex.")
    _w(lines, "No edites este archivo a mano — vuelve a generarlo desde el .yal.")
    _w(lines, '"""')
    _w(lines)

    _gen_header(lines, header)
    _gen_error_class(lines)
    _gen_tables(lines, dfa_result)
    _gen_actions(lines, dfa_result)
    _gen_lexer_function(lines, dfa_result)
    _gen_trailer(lines, trailer)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅  Lexer generado exitosamente → {output_path}")