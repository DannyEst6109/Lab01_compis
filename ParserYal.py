"""
yalex_parser.py
───────────────
Parser para archivos de especificación en formato YALex (.yal).

PROPÓSITO:
    Este módulo es el "Paso 1" del generador de analizadores léxicos.
    Lee un archivo .yal, lo entiende, y produce una lista de pares
    (regex_expandida, nombre_token) lista para pasarle al Lab 01.

RESTRICCIONES:
    ✗ No usa la librería `re` de Python en ningún momento.
    ✗ No usa ninguna otra librería de expresiones regulares.
    ✓ Toda la expansión se hace con lógica de cadenas de texto.

FLUJO INTERNO:
    Archivo .yal
        │
        ▼
    [1] _strip_comments()       → quitar (* comentarios *)
        │
        ▼
    [2] _peel_leading_block()   → extraer { header } del inicio
        │
        ▼
    [3] _parse_lets()           → extraer y expandir definiciones 'let'
        │
        ▼
    [4] _parse_rule_section()   → extraer reglas y sus acciones
        │
        ▼
    get_lab01_rules()
        → [(regex_expandida, token, prioridad), ...]

USO:
    parser = YALexParser()
    parser.parse("mi_archivo.yal")
    parser.summary()
    reglas = parser.get_lab01_rules()
    # reglas es lo que le pasas al constructor de AFD del Lab 01

NOTA SOBRE ESCAPADO:
    Los caracteres que son operadores en Lab 01 (| * + ? ( ))
    se escapan con \\ cuando aparecen como literales en el .yal.
    Ejemplo: el '+' literal en la regex se convierte en '\\+'.
    El Lab 01 debe interpretar '\\c' como "carácter literal c".
"""


class YALexParser:
    """
    Parser completo para archivos YALex (.yal).

    Atributos públicos después de parse():
        header       (str)  contenido del { header } opcional
        trailer      (str)  contenido del { trailer } (no soportado aún)
        entrypoint   (str)  nombre de la función: 'rule NOMBRE ='
        definitions  (dict) {"digit": "(0|1|...|9)", ...}
        rules        (list) lista de dicts por cada regla encontrada
    """

    # Operadores del formato interno de Lab 01.
    # Si uno de estos aparece como literal en el .yal, se escapa con \\.
    OPERATORS = set('|*+?()')

    def __init__(self):
        self.header      = ""
        self.trailer     = ""    # TODO: detección de trailer (ver nota al pie)
        self.entrypoint  = ""
        self.definitions = {}    # {"digit": "(0|1|2|3|4|5|6|7|8|9)"}
        self.rules       = []    # lista de dicts (ver _parse_rule_section)

    # ═══════════════════════════════════════════════════════════
    #  API PÚBLICA
    # ═══════════════════════════════════════════════════════════

    def parse(self, filepath: str) -> "YALexParser":
        """
        Parsea el archivo .yal en `filepath`.
        Retorna self para uso encadenado: YALexParser().parse(path).summary()

        Lanza:
            FileNotFoundError  si el archivo no existe
            SyntaxError        si el archivo tiene errores de estructura
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        print(f"\n{'═'*56}")
        print(f"  Parseando: {filepath}")
        print(f"{'═'*56}")

        # Paso 1: Eliminar todos los comentarios (* ... *)
        text = self._strip_comments(text)

        # Paso 2: Extraer { header } del inicio (si existe)
        text, self.header = self._peel_leading_block(text)
        if self.header:
            print(f"\n[Header encontrado]")

        # Paso 3: Extraer y expandir las definiciones 'let'
        print("\n[Definiciones 'let']")
        text = self._parse_lets(text)

        # Paso 4: Parsear la sección 'rule entrypoint ='
        print("\n[Reglas léxicas]")
        self._parse_rule_section(text)

        return self

    def get_lab01_rules(self) -> list:
        """
        Retorna las reglas en el formato que espera el constructor de AFD
        del Lab 01:

            [(regex_expandida, nombre_token, prioridad), ...]

        Las reglas con token=None (como skip whitespace) se omiten,
        ya que no generan un token y el lexer simplemente las ignora.

        La prioridad 0 es la más alta (la primera en el .yal).
        En caso de empate de longitud de lexema, gana la menor prioridad.
        """
        return [
            (r["regex"], r["token"], r["priority"])
            for r in self.rules
            if r["token"] is not None
        ]

    def get_all_rules(self) -> list:
        """
        Retorna TODAS las reglas incluyendo las de 'ignorar' (token=None).
        Útil si el lexer necesita saber cuándo avanzar sin emitir token.
        """
        return [
            (r["regex"], r["token"], r["priority"])
            for r in self.rules
        ]

    def summary(self):
        """Imprime un resumen legible del resultado del parseo."""
        print(f"\n{'═'*56}")
        print("  RESUMEN DEL PARSER YALEX")
        print(f"{'═'*56}")

        if self.header:
            print(f"\n  [Header]\n{self.header.strip()}")

        print(f"\n  [Definiciones] — {len(self.definitions)} encontradas")
        for name, regex in self.definitions.items():
            print(f"    {name:14} → {regex}")

        print(f"\n  [Reglas] — {len(self.rules)} encontradas")
        for r in self.rules:
            tok = r["token"] if r["token"] is not None else "(ignorar)"
            print(f"    [{r['priority']}] token={tok:10}  raw='{r['raw_regex']}'")
            print(f"         regex expandida: {r['regex']}")

        print(f"{'═'*56}\n")


    # ═══════════════════════════════════════════════════════════
    #  PASO 1 — ELIMINAR COMENTARIOS  (* ... *)
    # ═══════════════════════════════════════════════════════════

    def _strip_comments(self, text: str) -> str:
        """
        Elimina todos los bloques (* comentario *) del texto.
        Soporta comentarios anidados: (* a (* b *) c *) → ''

        Estrategia: recorrer carácter a carácter con un contador
        de profundidad de anidamiento. Solo se conservan los
        caracteres cuando depth == 0.

        Ejemplo:
            "let x = 'a' (* esto se borra *) | 'b'"
            → "let x = 'a'  | 'b'"
        """
        result = []
        i      = 0
        depth  = 0   # 0 = fuera de comentario, >0 = dentro

        while i < len(text):
            # ¿Empieza un comentario?
            if text[i:i+2] == '(*':
                depth += 1
                i += 2
            # ¿Termina un comentario?
            elif text[i:i+2] == '*)':
                if depth > 0:
                    depth -= 1
                i += 2
            # ¿Estamos dentro de un comentario? → ignorar
            elif depth > 0:
                i += 1
            # Carácter normal → conservar
            else:
                result.append(text[i])
                i += 1

        return ''.join(result)


    # ═══════════════════════════════════════════════════════════
    #  PASO 2 — EXTRAER { HEADER }
    # ═══════════════════════════════════════════════════════════

    def _peel_leading_block(self, text: str):
        """
        Si el texto (ya sin comentarios) comienza con '{',
        extrae ese bloque como header.

        Retorna (texto_restante, contenido_del_header).
        Si no hay header, retorna (texto_original, "").

        El header es opcional según la spec de YALex.
        Su contenido se copia al inicio del archivo generado.
        """
        text = text.strip()

        if not text.startswith('{'):
            return text, ""   # sin header

        content, rest = self._extract_block(text, 0)
        return rest.strip(), content


    # ═══════════════════════════════════════════════════════════
    #  PASO 3 — PARSEAR DEFINICIONES LET
    # ═══════════════════════════════════════════════════════════

    def _parse_lets(self, text: str) -> str:
        """
        Extrae y procesa todas las líneas 'let nombre = regex'.
        Cada regex se expande usando las definiciones ya procesadas
        (por eso el orden de los 'let' en el .yal importa).

        Las líneas que NO son 'let' se acumulan y se retornan
        (son la sección 'rule' más cualquier otro texto).

        Ejemplo de procesamiento:
            "let digit = ['0'-'9']"
            → _expand("['0'-'9']") → "(0|1|2|3|4|5|6|7|8|9)"
            → definitions["digit"] = "(0|1|2|3|4|5|6|7|8|9)"

            "let id_start = letter | '_'"
            → definitions["letter"] ya existe
            → _expand("letter | '_'")
                 → "((a|b|...|z|A|B|...|Z))|_"
            → definitions["id_start"] = "((a|b|...|z|A|B|...|Z))|_"
        """
        remaining = []   # líneas que no son 'let'

        for line in text.splitlines(keepends=True):
            stripped = line.strip()

            if not stripped.startswith('let '):
                remaining.append(line)
                continue

            # Formato esperado: "let NOMBRE = EXPRESION"
            body   = stripped[4:]         # quita el 'let '
            eq_pos = body.find('=')

            if eq_pos == -1:
                print(f"  ⚠ Línea 'let' sin '=', ignorada: {stripped}")
                remaining.append(line)
                continue

            name      = body[:eq_pos].strip()
            raw_regex = body[eq_pos + 1:].strip()

            # Expandir la regex usando definiciones previas
            expanded = self._expand(raw_regex)

            self.definitions[name] = expanded
            print(f"  let {name:12} = {raw_regex}")
            print(f"      {' ':12}   → {expanded}")

        return ''.join(remaining)


    # ═══════════════════════════════════════════════════════════
    #  PASO 4 — PARSEAR SECCIÓN RULE
    # ═══════════════════════════════════════════════════════════

    def _parse_rule_section(self, text: str):
        """
        Localiza 'rule ENTRYPOINT =' y parsea todos los pares
        'regexp { action }' que siguen.

        Estructura que parsea:
            rule gettoken =
                ws+         { return None }    ← regla 0
              | ['\n']      { return EOL  }    ← regla 1
              | digit+      { return INT  }    ← regla 2
              ...

        Cada regla se guarda en self.rules como un diccionario:
            {
                "raw_regex": str  — regex tal como está en el .yal
                "regex":     str  — regex expandida al formato Lab 01
                "action":    str  — código de la acción (sin llaves)
                "token":     str  — nombre del token, o None si se ignora
                "priority":  int  — orden (0 = mayor prioridad)
            }

        La prioridad 0 gana sobre la 1 en caso de empate de lexema.
        Esto respeta la regla del .yal: "en caso de empate se prioriza
        por orden de definición de las expresiones".
        """
        text = text.strip()

        # ── Localizar la palabra 'rule' como palabra completa ──
        rule_pos = self._find_whole_word(text, 'rule')
        if rule_pos < 0:
            raise SyntaxError("No se encontró la sección 'rule' en el archivo .yal")

        # ── Leer el nombre del entrypoint (primera palabra después de 'rule') ──
        after_rule = text[rule_pos + 4:].strip()
        ep_end     = 0
        while ep_end < len(after_rule) and (after_rule[ep_end].isalnum() or after_rule[ep_end] == '_'):
            ep_end += 1

        self.entrypoint = after_rule[:ep_end]
        after_ep        = after_rule[ep_end:].strip()

        # ── Saltar hasta el '=' (puede haber argumentos opcionales antes) ──
        eq_pos = after_ep.find('=')
        if eq_pos < 0:
            raise SyntaxError(f"No se encontró '=' en la definición de 'rule {self.entrypoint}'")

        body     = after_ep[eq_pos + 1:]   # todo lo que sigue al '='
        priority = 0

        print(f"  Entrypoint: {self.entrypoint}")

        # ── Consumir reglas una a una ──
        # Cada iteración consume: [|] regex { action }
        while True:
            body = body.strip()
            if not body:
                break

            # Saltar el '|' separador entre reglas
            if body[0] == '|':
                body = body[1:].strip()

            # Encontrar el '{' que inicia la acción de esta regla
            # (ignora los '{' dentro de [], (), y comillas)
            brace = self._find_action_brace(body)
            if brace < 0:
                break   # no quedan más reglas

            # Texto antes del '{' es la regex en crudo
            raw_regex = body[:brace].strip()

            # Extraer el contenido de { action } y avanzar `body`
            action_content, body = self._extract_block(body, brace)
            action_content       = action_content.strip()

            # Expandir la regex al formato del Lab 01
            expanded_regex = self._expand(raw_regex)

            # Extraer el nombre del token de la acción
            token_name = self._token_name(action_content)

            self.rules.append({
                "raw_regex": raw_regex,
                "regex":     expanded_regex,
                "action":    action_content,
                "token":     token_name,
                "priority":  priority,
            })

            tok_display = token_name if token_name is not None else "(ignorar)"
            print(f"  [{priority}] {tok_display:10} | raw='{raw_regex}'")
            print(f"       expandida: {expanded_regex}")
            priority += 1


    # ═══════════════════════════════════════════════════════════
    #  EXPANSIÓN DE EXPRESIONES REGULARES
    # ═══════════════════════════════════════════════════════════

    def _expand(self, raw: str) -> str:
        """
        Convierte una expresión en formato YALex al formato del Lab 01.

        Tabla de conversiones:
        ┌──────────────────┬────────────────────────────────────────┐
        │ YALex            │ Lab 01                                 │
        ├──────────────────┼────────────────────────────────────────┤
        │ 'c'              │ c  (literal, escapado si es operador)  │
        │ '\n'             │ el carácter newline                    │
        │ "abc"            │ (a|b|c)                                │
        │ ['a'-'z']        │ (a|b|c|...|z)                          │
        │ [' ' '\t']       │ ( |\t)                                 │
        │ ident            │ (definición_expandida)                 │
        │ eof              │ EOF                                    │
        │ _                │ . (wildcard, Lab 01 debe soportarlo)   │
        │ * + ? | ( )      │ mismo operador (sin cambio)            │
        │ <espacio>        │ (omitido — Lab 01 usa concat implícita)│
        └──────────────────┴────────────────────────────────────────┘

        NOTA sobre los espacios:
            En YALex, el espacio entre elementos es concatenación.
            En Lab 01, la concatenación también es implícita.
            Por eso simplemente omitimos los espacios al expandir.
            El Lab 01 unirá los elementos por adyacencia.
        """
        out = []
        i   = 0
        raw = raw.strip()

        while i < len(raw):
            c = raw[i]

            # ── Carácter entre comillas simples: 'x' o '\n' ──
            if c == "'":
                val, skip = self._read_quoted_char(raw, i)
                out.append(self._esc(val))
                i += skip

            # ── Cadena entre comillas dobles: "abc" → (a|b|c) ──
            elif c == '"':
                chars, skip = self._read_quoted_string(raw, i)
                if not chars:
                    pass   # cadena vacía → ignorar
                elif len(chars) == 1:
                    out.append(chars[0])
                else:
                    out.append('(' + '|'.join(chars) + ')')
                i += skip

            # ── Conjunto de caracteres: [...] → (a|b|c|...) ──
            elif c == '[':
                close = self._find_bracket_close(raw, i)
                inner = raw[i + 1 : close]
                out.append(self._expand_charset(inner))
                i = close + 1

            # ── Operadores que se conservan igual ──
            elif c in '|*+?()':
                out.append(c)
                i += 1

            # ── Espacio → separador de concatenación implícita ──
            elif c in ' \t\n\r':
                i += 1   # se omite; Lab 01 usa concatenación implícita

            # ── Identificador: let definido, 'eof', o wildcard '_' ──
            elif c.isalpha() or c == '_':
                ident, skip = self._read_ident(raw, i)

                if ident == '_':
                    # Wildcard: cualquier carácter
                    out.append('.')

                elif ident == 'eof':
                    # Fin de buffer — token especial del lexer
                    out.append('EOF')

                elif ident in self.definitions:
                    # Sustituir por la definición expandida.
                    # Se envuelve en () para aislarla correctamente.
                    # Ejemplo: "digit+" con digit=(0|...|9) → ((0|...|9))+
                    out.append('(' + self.definitions[ident] + ')')

                else:
                    # Identificador no reconocido — se deja tal cual
                    # (probablemente un error en el .yal)
                    print(f"  ⚠ Identificador '{ident}' no definido en ningún 'let'")
                    out.append(ident)

                i += skip

            # ── Cualquier otro carácter (e.g. dígitos sin comillas) ──
            else:
                out.append(self._esc(c))
                i += 1

        return ''.join(out)

    def _expand_charset(self, inner: str) -> str:
        """
        Expande el contenido de un conjunto [...] a una unión de chars.

        Formatos soportados:
            'c'           → un carácter literal
            'c1'-'c2'     → rango: todos los chars entre c1 y c2 (inclusive)
                            Se usa ord() y chr() para iterar el rango.
            "abc"         → cada char de la cadena
            (espacio)     → separador entre elementos (se ignora)
            ^             → primer carácter → charset negado [^...]

        Ejemplos completos:
            '0'-'9'         → (0|1|2|3|4|5|6|7|8|9)
            ' ' '\t'        → ( |\t)
            'a'-'z''A'-'Z'  → (a|b|...|z|A|B|...|Z)
            "+-*/"          → (\+|-|\*|/)
            ^'0'-'9'        → [^0123456789]  (ver nota)

        NOTA sobre charsets negados [^...]:
            Se retorna una notación provisional [^chars].
            El Lab 01 necesita soporte explícito para esto.
            Si no se soporta, expandir a (todos_los_chars - charset)
            usando la diferencia de conjuntos ASCII.
        """
        chars   = []
        i       = 0
        negated = False
        inner   = inner.strip()

        # ¿Es un charset negado [^...]?
        if inner.startswith('^'):
            negated = True
            inner   = inner[1:].strip()

        while i < len(inner):
            c = inner[i]

            # ── Carácter entre comillas simples ──
            if c == "'":
                val, skip = self._read_quoted_char(inner, i)
                i += skip   # apunta al carácter siguiente a la comilla de cierre

                # ¿Hay un '-' a continuación? (ignorando espacios) → es un rango
                j = i
                while j < len(inner) and inner[j] in ' \t':
                    j += 1

                if j < len(inner) and inner[j] == '-':
                    # Buscar el carácter de fin del rango
                    k = j + 1
                    while k < len(inner) and inner[k] in ' \t':
                        k += 1

                    if k < len(inner) and inner[k] == "'":
                        val2, skip2 = self._read_quoted_char(inner, k)
                        i = k + skip2   # avanzar después del char de fin

                        # Expandir el rango usando ord() y chr()
                        # Ejemplo: 'a'-'z' → ord('a')=97 ... ord('z')=122
                        for code in range(ord(val), ord(val2) + 1):
                            chars.append(self._esc(chr(code)))
                        continue   # i ya fue actualizado

                # Sin rango → carácter individual
                chars.append(self._esc(val))
                # i ya fue avanzado por 'skip' más arriba

            # ── Cadena entre comillas dobles: "abc" ──
            elif c == '"':
                string_chars, skip = self._read_quoted_string(inner, i)
                chars.extend(string_chars)
                i += skip

            # ── Espacio → separador entre elementos del charset ──
            elif c in ' \t':
                i += 1

            # ── Cualquier otro carácter sin comillas ──
            else:
                chars.append(self._esc(c))
                i += 1

        # ── Construir la expresión de unión ──
        if not chars:
            return ''

        if negated:
            # Placeholder para charset negado
            # Lab 01 debe implementar el soporte para [^...]
            return '[^' + ''.join(chars) + ']'

        if len(chars) == 1:
            return chars[0]   # un solo char: no necesita paréntesis

        return '(' + '|'.join(chars) + ')'


    # ═══════════════════════════════════════════════════════════
    #  LECTURA DE TOKENS INDIVIDUALES (bajo nivel)
    # ═══════════════════════════════════════════════════════════

    def _read_quoted_char(self, text: str, pos: int):
        """
        Lee un carácter entre comillas simples desde la posición `pos`.

        Maneja secuencias de escape:
            \n → newline     \t → tab      \r → carriage return
            \\ → backslash   \' → comilla  \0 → null

        Retorna (char_real, cantidad_de_chars_consumidos_en_text)

        Ejemplos:
            text='a', pos=0  → ('a', 3)       consume: 'a'
            text='\n', pos=0 → ('\\n', 4)     consume: '\n'
            text='\t', pos=0 → ('\\t', 4)     consume: '\t'
        """
        ESCAPE_MAP = {
            'n': '\n', 't': '\t', 'r': '\r',
            '\\': '\\', "'": "'", '"': '"', '0': '\0'
        }
        i = pos + 1   # saltar la comilla de apertura '

        if i < len(text) and text[i] == '\\':
            # Secuencia de escape: \x
            i += 1
            ch = ESCAPE_MAP.get(text[i], text[i]) if i < len(text) else ''
            i += 1
        else:
            # Carácter normal
            ch = text[i] if i < len(text) else ''
            i += 1

        # Saltar la comilla de cierre '
        if i < len(text) and text[i] == "'":
            i += 1

        return ch, i - pos

    def _read_quoted_string(self, text: str, pos: int):
        """
        Lee una cadena entre comillas dobles desde la posición `pos`.
        Cada carácter se escapa si es un operador de Lab 01.

        Retorna (lista_de_chars_escapados, chars_consumidos_en_text)

        Ejemplo:
            text='"a+b"', pos=0 → (['a', '\\+', 'b'], 5)
        """
        ESCAPE_MAP = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\', '"': '"', "'": "'"}
        chars = []
        i     = pos + 1   # saltar la " de apertura

        while i < len(text) and text[i] != '"':
            if text[i] == '\\':
                i += 1
                ch = ESCAPE_MAP.get(text[i], text[i]) if i < len(text) else ''
                chars.append(self._esc(ch))
                i += 1
            else:
                chars.append(self._esc(text[i]))
                i += 1

        i += 1   # saltar la " de cierre
        return chars, i - pos

    def _read_ident(self, text: str, pos: int):
        """
        Lee un identificador (letras, dígitos, guion bajo) desde `pos`.

        Retorna (identificador, chars_consumidos)

        Ejemplos:
            text='digit+', pos=0 → ('digit', 5)
            text='_',      pos=0 → ('_', 1)
            text='id_char',pos=0 → ('id_char', 7)
        """
        i = pos
        while i < len(text) and (text[i].isalnum() or text[i] == '_'):
            i += 1
        return text[pos:i], i - pos


    # ═══════════════════════════════════════════════════════════
    #  MANEJO DE BLOQUES Y LLAVES
    # ═══════════════════════════════════════════════════════════

    def _extract_block(self, text: str, start: int):
        """
        Extrae el contenido de un bloque { ... } balanceado
        que comienza en la posición `start` (debe apuntar a '{').

        Retorna (contenido_sin_llaves, texto_después_del_cierre)

        Ejemplo:
            text = "{ return INT } | ...", start = 0
            → ("return INT ", " | ...")
        """
        if text[start] != '{':
            raise SyntaxError(
                f"Se esperaba '{{' en posición {start}, "
                f"encontrado '{text[start]}' en: ...{text[start:start+20]}..."
            )

        depth = 0
        i     = start

        while i < len(text):
            if   text[i] == '{':   depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    content = text[start + 1 : i]
                    rest    = text[i + 1:]
                    return content, rest
            i += 1

        raise SyntaxError(
            f"Bloque '{{' sin cerrar, iniciado en posición {start}: "
            f"...{text[start:start+30]}..."
        )

    def _find_action_brace(self, text: str) -> int:
        """
        Encuentra el índice del '{' que inicia el bloque de acción.

        Este '{' está al nivel externo, es decir, NO está dentro de:
            ( )  — paréntesis de la regex
            [ ]  — corchetes de charset
            ' '  — comillas simples de char literal
            " "  — comillas dobles de string

        Ejemplos:
            "digit+   { return INT }"     → 10
            "['0'-'9']+ { return INT }"   → 12
            "letter (a|b)* { return ID }" → 14

        Si no se encuentra ningún '{' de acción, retorna -1.
        """
        depth_paren   = 0
        depth_bracket = 0
        i             = 0

        while i < len(text):
            c = text[i]

            # Saltar carácter entre comillas simples: 'x' o '\n'
            if c == "'":
                i += 1
                if i < len(text) and text[i] == '\\':
                    i += 2   # saltar el carácter escapado
                else:
                    i += 1   # saltar el carácter normal
                if i < len(text) and text[i] == "'":
                    i += 1   # saltar la comilla de cierre
                continue

            # Saltar cadena entre comillas dobles: "abc"
            if c == '"':
                i += 1
                while i < len(text) and text[i] != '"':
                    if text[i] == '\\':
                        i += 1
                    i += 1
                i += 1   # saltar la " de cierre
                continue

            # Rastrear profundidades
            if   c == '(':   depth_paren   += 1
            elif c == ')':   depth_paren   -= 1
            elif c == '[':   depth_bracket += 1
            elif c == ']':   depth_bracket -= 1
            elif c == '{' and depth_paren == 0 and depth_bracket == 0:
                return i   # ← este es el '{' de la acción

            i += 1

        return -1   # no se encontró

    def _find_bracket_close(self, text: str, pos: int) -> int:
        """
        Encuentra el ']' que cierra el '[' en la posición `pos`.
        Retorna el índice del ']'.
        """
        i = pos + 1
        while i < len(text):
            if text[i] == ']':
                return i
            i += 1
        raise SyntaxError(
            f"'[' sin cerrar en posición {pos}: ...{text[pos:pos+20]}..."
        )


    # ═══════════════════════════════════════════════════════════
    #  UTILIDADES VARIAS
    # ═══════════════════════════════════════════════════════════

    def _esc(self, char: str) -> str:
        """
        Escapa un carácter si es un operador especial en el formato Lab 01.

        Los operadores del Lab 01 son: | * + ? ( )
        Si uno de estos aparece como literal en el .yal (por ejemplo '+'),
        se convierte en '\\+' para que Lab 01 lo trate como literal.

        REQUISITO para el Lab 01:
            Al parsear la regex expandida, el Lab 01 debe interpretar
            la secuencia '\\c' como "el carácter literal c", no como
            el operador c. Esto es necesario para que el lexer pueda
            reconocer, por ejemplo, el token PLUS cuya regex es '\\+'.
        """
        if char in self.OPERATORS:
            return '\\' + char
        return char

    def _find_whole_word(self, text: str, word: str) -> int:
        """
        Busca `word` como palabra completa en `text`.

        'Palabra completa' significa que el carácter anterior y el
        siguiente (si existen) no son alfanuméricos ni guion bajo.

        Retorna el índice de inicio, o -1 si no se encontró.

        Ejemplo:
            _find_whole_word("let rule_x = ...", "rule") → -1
            (porque 'rule' es parte del identificador 'rule_x')
            _find_whole_word("rule gettoken =", "rule") → 0  ✓
        """
        n = len(word)
        for i in range(len(text) - n + 1):
            if text[i : i + n] != word:
                continue
            before_ok = (i == 0) or not (text[i-1].isalnum() or text[i-1] == '_')
            after_ok  = (i + n >= len(text)) or not (text[i+n].isalnum() or text[i+n] == '_')
            if before_ok and after_ok:
                return i
        return -1

    def _token_name(self, action: str) -> str:
        """
        Extrae el nombre del token de la cadena de acción.

        Casos reconocidos:
            "return INT"        → "INT"        token normal
            "return PLUS"       → "PLUS"       token normal
            "return int(lxm)"   → "int(lxm)"  valor calculado
            "return lexbuf"     → None         skip (ignorar, no emitir token)
            "return None"       → None         skip
            "raise(...)"        → "EOF"        fin de buffer
            ""                  → None         acción vacía → ignorar

        El valor None significa: "procesar el patrón pero no emitir token".
        Esto es lo que pasa con whitespace: se avanza el buffer pero
        no se reporta ningún token al parser.
        """
        a = action.strip()

        if a.startswith('return '):
            tok = a[7:].strip()
            if tok in ('lexbuf', 'None', 'null', ''):
                return None   # skip
            return tok

        if 'raise' in a:
            return 'EOF'

        return None   # acción vacía o no reconocida → ignorar


# ═══════════════════════════════════════════════════════════════
#  PUNTO DE ENTRADA — uso desde línea de comandos
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys

    filepath = sys.argv[1] if len(sys.argv) > 1 else 'ejemplo.yal'

    print(f"Uso: python yalex_parser.py [archivo.yal]")

    parser = YALexParser()
    try:
        parser.parse(filepath)
        parser.summary()

        print("\n[Reglas listas para el Lab 01]")
        print("(esto es lo que pasas al constructor de AFD)")
        print()
        for regex, token, priority in parser.get_lab01_rules():
            print(f"  prioridad={priority:<3} token={token:<12} regex={regex}")

    except FileNotFoundError:
        print(f"\nError: No se encontró el archivo '{filepath}'")
    except SyntaxError as e:
        print(f"\nError de sintaxis en el .yal: {e}")

# ═══════════════════════════════════════════════════════════════
# NOTA SOBRE EL TRAILER { trailer }
# ═══════════════════════════════════════════════════════════════
# El trailer es el { } opcional al FINAL del archivo .yal.
# No está implementado aún porque es ambiguo detectarlo:
# las acciones de las reglas también son bloques { }, y el
# último { action } se confunde con el trailer.
#
# Para implementarlo en el futuro:
#   Opción A: parsear el trailer DESPUÉS de parsear todas las reglas,
#             tomando cualquier { } restante al final.
#   Opción B: requerir que el trailer esté en una nueva línea separado.
#
# Por ahora: no incluir trailer en los archivos .yal de prueba.
# ═══════════════════════════════════════════════════════════════