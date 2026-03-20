#Archivo LexerGenerator.py
# Conecta la salida del YALexParser con el pipeline del Lab 01 + Lab 02 para construir un AFD multi-token: un solo AFD que reconoce TODOS los
# tokens definidos en el archivo .yal y sabe cuál aceptó en cada estado.
#El parser del Lab 01 trata | * + ? ( ) como operadores. pero el yalex produce  \+ \* \( \) etc. para literales
#Antes de pasar la regex al Lab 01, reemplazamos cada \c por un carácter placeholder para que sean compatibles.
#El algoritmo de Hopcroft del Lab 02 parte de {aceptantes | no-aceptantes}. Para un lexer correcto, la partición inicial debe separar por token:
#{estados-INT} | {estados-ID} | {estados-PLUS} | {no-aceptantes} Esto garantiza que dos estados que aceptan tokens distintos NUNCA se fusionen, aunque tengan el mismo perfil de transiciones.
#Implementamos esta variante sin tocar el código del Lab 02.

import sys
import os
from collections import deque, defaultdict

#importar Lab 01 y Lab 02 sin modificarlos
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _root)

from Laboratorio1.src.regex_parser import add_explicit_concat, to_postfix
from Laboratorio1.src.syntax_tree  import build_syntax_tree, compute_functions
from Laboratorio2.src.minimize_dfa import compare_dfas

#  TABLA DE CARACTERES ESPECIALES
_PLACEHOLDER_BASE = 0xE000   # \+ → chr(0xE002), \* → chr(0xE001), etc.
_MARKER_BASE      = 0xE100   # Mint = chr(0xE100), Mid = chr(0xE101), ...
_GLOBAL_END       = '#'      # Lab 01 ya excluye '#'; lo reutilizamos

# Secuencias de escape del YALex parser → placeholder char
_ESC_TO_PLACEHOLDER = {
    '\\|': chr(_PLACEHOLDER_BASE + 0),
    '\\*': chr(_PLACEHOLDER_BASE + 1),
    '\\+': chr(_PLACEHOLDER_BASE + 2),
    '\\(': chr(_PLACEHOLDER_BASE + 3),
    '\\)': chr(_PLACEHOLDER_BASE + 4),
    '\\?': chr(_PLACEHOLDER_BASE + 5),
    '\\.': chr(_PLACEHOLDER_BASE + 6),
    '\\#': chr(_PLACEHOLDER_BASE + 7),
}

# Placeholder → carácter original (para display en tablas)
_PLACEHOLDER_TO_CHAR = {v: k[1] for k, v in _ESC_TO_PLACEHOLDER.items()}


def _is_marker(ch: str) -> bool:
    #True si el carácter es un marcador interno (no es input real).
    return ch == _GLOBAL_END or (_MARKER_BASE <= ord(ch) <= 0xE1FF)


def _display(ch: str) -> str:
    #Convierte un char interno a su representación legible.
    return _PLACEHOLDER_TO_CHAR.get(ch, ch)


#  PREPROCESAR ESCAPES
# Reemplaza secuencias \c en la regex expandida por placeholders.
#El YALex parser produce \+ para un '+' literal, pero el parser del Lab 01 trata '+' como operador. Al reemplazar \+ por chr(0xE002),
# el Lab 01 lo trata como un símbolo normal (no operador).
def _preprocess_escapes(regex: str) -> str:
    result = []
    i = 0
    while i < len(regex):
        if regex[i] == '\\' and i + 1 < len(regex):
            seq = regex[i: i + 2]
            if seq in _ESC_TO_PLACEHOLDER:
                result.append(_ESC_TO_PLACEHOLDER[seq])
                i += 2
                continue
        result.append(regex[i])
        i += 1
    return ''.join(result)



# CONSTRUIR REGEX COMBINADa
#Une todas las regexes en UNA sola expresión augmented con marcadores.
# Para cada regla (regex_i, token_i, prioridad_i):
# 1. Preprocesa los escapes de la regex
# 2. Le asigna un marcador único: chr(0xE100 + i)
# 3. Construye el fragmento:  (regex_preprocesada)MARCADOR_i

#Retorna: combined   : str  — regex lista para pasar a add_explicit_concat
# y mk_tokens  : dict — {marker_char: (token_name, prioridad)}

def _build_combined(rules: list) -> tuple:
    parts    = []
    mk_tokens = {}    # char → (token_name, prioridad)

    for i, (regex, token, priority) in enumerate(rules):
        marker = chr(_MARKER_BASE + i)
        mk_tokens[marker] = (token, priority)

        processed = _preprocess_escapes(regex)
        parts.append(f"({processed}){marker}")

    joined   = '|'.join(parts)
    combined = f"({joined}){_GLOBAL_END}"   # '#' global al final
    return combined, mk_tokens



#  CONSTRUIR AFD MULTI-TOKE: Versión extendida de build_dfa (Lab 01) para múltiples tokens.
# Recibe `dfa_alphabet` ya filtrado (sin '#' ni marcadores).
#   - Un estado es de aceptación si contiene la posición de CUALQUIER
#     marcador de token.
#   - `accepting_tokens[estado]` = token del marcador encontrado.
#     Si un estado contiene varios marcadores (raro pero posible),
#     gana el de menor prioridad (= el que aparece primero en el .yal).
def _build_multi_dfa(root, followpos, pos_to_symbol, dfa_alphabet, marker_positions):
    start_state = frozenset(root.firstpos)

    states    = [start_state]
    state_ids = {start_state: "S0"}
    transitions      = {}
    accepting_states = set()
    accepting_tokens = {}    # nombre_estado → token_name (puede ser None)

    queue = deque([start_state])

    while queue:
        current_state = queue.popleft()
        current_name  = state_ids[current_state]

        # ¿Acepta algún token? 
        # Buscar todos los marcadores presentes en este estado.
        # Si hay varios, gana el de menor prioridad (primero en el .yal).
        best_token    = None
        best_priority = float('inf')

        for pos in current_state:
            if pos in marker_positions:
                tok, pri = marker_positions[pos]
                if pri < best_priority:
                    best_priority = pri
                    best_token    = tok

        if best_token is not None or best_priority < float('inf'):
            # best_token puede ser None (regla de skip) pero el estado
            # igualmente "acepta" (el lexer avanza y descarta el lexema)
            accepting_states.add(current_name)
            accepting_tokens[current_name] = best_token

        #Transiciones (solo sobre chars reales) 
        transitions[current_name] = {}

        for symbol in dfa_alphabet:
            next_positions = set()

            for pos in current_state:
                if pos_to_symbol[pos] == symbol:
                    next_positions.update(followpos[pos])

            if next_positions:
                frozen_next = frozenset(next_positions)

                if frozen_next not in state_ids:
                    new_name              = f"S{len(state_ids)}"
                    state_ids[frozen_next] = new_name
                    states.append(frozen_next)
                    queue.append(frozen_next)

                transitions[current_name][symbol] = state_ids[frozen_next]
            else:
                transitions[current_name][symbol] = "-"

    named_states = [(state_ids[s], set(s)) for s in states]
    return named_states, transitions, accepting_states, accepting_tokens


# MINIMIZACIÓN MULTI-TOKEN (Hopcroft con partición por token)
# Minimización de Hopcroft adaptada para lexers multi-token.
# pese a que ya teníamos una función similar dentro del laboratorio 2, se creó una nueva con las siguiente diferencias para un funcionamiento optimo
# anteriormete se partían los estados entre acpetables y no aceptables, lo cual es incorrecto para un lexer ya que si dos estados aceptan tokens distintos
# tienen, distintos comportamientos y no deben de fusionarse. por lo que para el proyecto se realizan particiones dependiendo de los grupos de tokens y rules

def _minimize_multi_dfa(states, transitions, accepting_states, accepting_tokens, alphabet):

    state_names = [name for name, _ in states]

    # Partición inicial: un grupo por token 
    token_groups  = defaultdict(set)
    non_accepting = set()

    for s in state_names:
        if s in accepting_tokens:
            # La clave agrupa por token (incluyendo None para skip-rules)
            key = accepting_tokens[s]   # puede ser None
            token_groups[key].add(s)
        else:
            non_accepting.add(s)

    partitions = [frozenset(g) for g in token_groups.values() if g]
    if non_accepting:
        partitions.append(frozenset(non_accepting))

    # Iteraciones de Hopcroft 
    def find_part(state):
        #Índice de la partición a la que pertenece `state`.
        if state == "-":
            return None
        for idx, group in enumerate(partitions):
            if state in group:
                return idx
        return None

    def same_signature(s1, s2):
        #True si s1 y s2 transicionan a la misma partición en todo el alfabeto.
        for sym in alphabet:
            d1 = transitions[s1].get(sym, "-")
            d2 = transitions[s2].get(sym, "-")
            if find_part(d1) != find_part(d2):
                return False
        return True

    def split(group):
        #Divide un grupo en subgrupos de estados indistinguibles.
        lst  = list(group)
        subs = []
        for s in lst:
            placed = False
            for sub in subs:
                if same_signature(s, sub[0]):
                    sub.append(s)
                    placed = True
                    break
            if not placed:
                subs.append([s])
        return [frozenset(sg) for sg in subs]

    changed = True
    while changed:
        changed    = False
        new_parts  = []
        for group in partitions:
            splits = split(group)
            new_parts.extend(splits)
            if len(splits) > 1:
                changed = True
        partitions = new_parts

    # Construir AFD mínimo 
    start_state = state_names[0]
    start_part  = next(p for p in partitions if start_state in p)
    ordered     = [start_part] + [p for p in partitions if p is not start_part]

    new_name     = {id(p): f"S{i}" for i, p in enumerate(ordered)}
    state_to_grp = {s: grp for grp in ordered for s in grp}
    old_pos      = {name: pos for name, pos in states}

    new_states      = []
    new_transitions = {}
    new_accepting   = set()
    new_acc_tokens  = {}

    for group in ordered:
        name = new_name[id(group)]

        # Posiciones: unión de todos los estados del grupo
        merged = set()
        for s in group:
            merged.update(old_pos.get(s, set()))
        new_states.append((name, merged))

        # Token: todos los del grupo tienen el mismo (por diseño)
        group_token = None
        for s in group:
            if s in accepting_tokens:
                new_accepting.add(name)
                group_token = accepting_tokens[s]
                break
        if name in new_accepting:
            new_acc_tokens[name] = group_token

        # Transiciones usando el representante del grupo
        rep = next(iter(group))
        new_transitions[name] = {}
        for sym in alphabet:
            dest = transitions[rep].get(sym, "-")
            if dest == "-":
                new_transitions[name][sym] = "-"
            else:
                new_transitions[name][sym] = new_name[id(state_to_grp[dest])]

    return new_states, new_transitions, new_accepting, new_acc_tokens


#  API PÚBLICA — build_lexer: rules → AFD multi-token.
def build_lexer(rules: list, minimize: bool = True, verbose: bool = True) -> dict:
    if not rules:
        raise ValueError("La lista de reglas está vacía.")

    # Filtrar reglas EOF / eof (son manejadas por el lexer a nivel superior)
    active_rules = [(r, t, p) for r, t, p in rules if t != 'EOF']
    if len(active_rules) < len(rules):
        if verbose:
            print(f"  [build_lexer] Regla EOF omitida del AFD "
                  f"(se maneja en el lexer directamente)")

    if verbose:
        print(f"\n{'═'*56}")
        print(f"  BUILD LEXER — {len(active_rules)} regla(s)")
        print(f"{'═'*56}")

    # Regex combinada con marcadores 
    combined_str, mk_tokens = _build_combined(active_rules)

    if verbose:
        preview = combined_str[:100]
        ellipsis = "..." if len(combined_str) > 100 else ""
        print(f"\n[1] Regex combinada ({len(combined_str)} chars):")
        print(f"    {preview}{ellipsis}")

    # Pipeline Lab 01 
    if verbose:
        print("\n[2] Árbol sintáctico y followpos (Lab 01)...")

    with_concat = add_explicit_concat(combined_str)
    postfix     = to_postfix(with_concat)

    root, pos_to_symbol, end_marker_pos = build_syntax_tree(postfix)

    # Posiciones de los marcadores de token
    marker_positions = {}   # pos → (token_name, prioridad)
    for pos, sym in pos_to_symbol.items():
        if sym in mk_tokens:
            marker_positions[pos] = mk_tokens[sym]

    followpos = {pos: set() for pos in pos_to_symbol}
    compute_functions(root, followpos)

    if verbose:
        print(f"    Posiciones totales: {len(pos_to_symbol)}")
        print(f"    Marcadores de token: {len(marker_positions)}")

    # Alfabeto para el AFD (sin marcadores ni '#') 
    marker_chars = set(mk_tokens.keys()) | {_GLOBAL_END}
    dfa_alphabet = sorted(
        {sym for sym in pos_to_symbol.values() if sym not in marker_chars},
        key=ord
    )

    if verbose:
        display_alpha = [_display(c) for c in dfa_alphabet]
        print(f"\n[3] Alfabeto del AFD ({len(dfa_alphabet)} símbolos):")
        print(f"    {display_alpha[:30]}"
              f"{'...' if len(display_alpha) > 30 else ''}")

    # Construir AFD multi-token 
    if verbose:
        print("\n[4] Construyendo AFD multi-token...")

    states, transitions, accepting_states, accepting_tokens = _build_multi_dfa(
        root, followpos, pos_to_symbol, dfa_alphabet, marker_positions
    )

    if verbose:
        print(f"    AFD directo: {len(states)} estados, "
              f"{len(accepting_states)} de aceptación")
        for sname, tok in sorted(accepting_tokens.items()):
            tok_str = tok if tok is not None else "(skip)"
            print(f"      {sname} → {tok_str}")

    # Minimizar 
    min_states      = states
    min_transitions = transitions
    min_accepting   = accepting_states
    min_acc_tokens  = accepting_tokens

    if minimize:
        if verbose:
            print("\n[5] Minimizando (Hopcroft con partición por token)...")

        min_states, min_transitions, min_accepting, min_acc_tokens = \
            _minimize_multi_dfa(
                states, transitions, accepting_states,
                accepting_tokens, dfa_alphabet
            )

        if verbose:
            print(f"    AFD mínimo: {len(min_states)} estados")
            compare_dfas(
                states, transitions,
                min_states, min_transitions,
                dfa_alphabet
            )

    # Mapas de display 
    display_map  = {c: _display(c) for c in dfa_alphabet}
    user_alphabet = [_display(c) for c in dfa_alphabet]

    if verbose:
        print(f"\n{'═'*56}")
        print(f"  RESULTADO FINAL")
        print(f"  Estados: {len(min_states)}   "
              f"Aceptantes: {len(min_accepting)}   "
              f"Alfabeto: {len(dfa_alphabet)} símbolos")
        print(f"{'═'*56}\n")

    return {
        "states":           min_states,
        "transitions":      min_transitions,
        "accepting_states": min_accepting,
        "accepting_tokens": min_acc_tokens,
        "alphabet":         dfa_alphabet,      # chars internos (con placeholders)
        "user_alphabet":    user_alphabet,     # chars legibles para display
        "display_map":      display_map,
        "n_rules":          len(active_rules),
    }


# ══════════════════════════════════════════════════════════════════════
#  UTILIDADES DE DISPLAY: Imprime la tabla de transición del AFD multi-token.
#  - Columnas: estado | transición por cada char del alfabeto | token
#     - Solo muestra chars del 'user_alphabet' (sin marcadores internos)
#     - Los chars placeholder se muestran como su char real (\+ → +)
#     - La columna Token muestra el nombre del token o '(skip)'
def print_multi_dfa(result: dict):
    states          = result["states"]
    transitions     = result["transitions"]
    accepting_states= result["accepting_states"]
    accepting_tokens= result["accepting_tokens"]
    user_alpha      = result["user_alphabet"]
    alpha_internal  = result["alphabet"]
    display_map     = result["display_map"]

    # Construir encabezados
    disp_alpha = [display_map.get(c, c) for c in alpha_internal]
    headers    = ["Estado"] + disp_alpha + ["Token"]
    col_w      = [10] + [max(7, len(h) + 2) for h in disp_alpha] + [14]

    print("\n--- Tabla de transición del AFD multi-token ---")
    for h, w in zip(headers, col_w):
        print(f"{h:<{w}}", end="")
    print()
    print("-" * sum(col_w))

    for state_name, _ in states:
        print(f"{state_name:<10}", end="")
        for j, sym in enumerate(alpha_internal):
            dest = transitions[state_name].get(sym, "-")
            print(f"{dest:<{col_w[j+1]}}", end="")

        if state_name in accepting_tokens:
            tok = accepting_tokens[state_name]
            tok_str = tok if tok is not None else "(skip)"
        else:
            tok_str = ""
        print(f"{tok_str:<14}")

#Imprime un resumen compacto del AFD generado.
def summary(result: dict):
    print(f"\n{'═'*56}")
    print(f"  Resumen del AFD multi-token")
    print(f"{'═'*56}")
    print(f"  Reglas combinadas : {result['n_rules']}")
    print(f"  Total estados     : {len(result['states'])}")
    print(f"  Estados aceptantes: {len(result['accepting_states'])}")
    print(f"  Tamaño alfabeto   : {len(result['alphabet'])} chars")
    print(f"\n  Tokens reconocidos:")
    seen = set()
    for tok in result["accepting_tokens"].values():
        lbl = tok if tok is not None else "(skip/ignorar)"
        if lbl not in seen:
            seen.add(lbl)
            print(f"    · {lbl}")
    print(f"{'═'*56}\n")


#  PUNTO DE ENTRADA — prueba standalone
if __name__ == "__main__":

    # Agregar el directorio del script al path para encontrar yalex_parser
    sys.path.insert(0, os.path.dirname(__file__))
    from ParserYal import YALexParser

    yal_file = sys.argv[1] if len(sys.argv) > 1 else "ejemplo.yal"

    print(f"Archivo: {yal_file}")

    # Parsear el .yal
    parser = YALexParser().parse(yal_file)

    # Usar get_all_rules() para incluir también las reglas de skip
    all_rules = parser.get_all_rules()

    print(f"\nReglas (incluyendo skip):")
    for regex, token, pri in all_rules:
        tok_str = token if token is not None else "(skip)"
        print(f"  [{pri}] {tok_str:12} → {regex[:50]}")

    # Construir el AFD multi-token
    result = build_lexer(all_rules, minimize=True, verbose=True)

    # Mostrar tabla y resumen
    print_multi_dfa(result)
    summary(result)