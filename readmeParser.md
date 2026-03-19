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




 #  ELIMINAR COMENTARIOS  (* ... *)
    #Elimina todos los bloques (* comentario *) del texto. Soporta comentarios anidados: (* a (* b *) c *)
    #Funciona al recorrer cada caracter con un contador de profundidad de anidamiento
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


#  PARSEAR SECCIÓN RULE: Localiza 'rule ENTRYPOINT =' y parsea todos los pares
    #
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



    #  LECTURA DE TOKENS INDIVIDUALES (bajo nivel) #Lee un carácter entre comillas simples desde la posición `pos`.

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


def _esc(self, char: str) -> str:
        """
        Escapa un carácter si es un operador especial en el formato Lab 01.

        Los operadores del Lab 01 son: | * + ? ( )
        Si uno de estos aparece como literal en el .yal (por ejemplo '+'),
        se convierte en '\\+' para que Lab 01 lo trate como literal.



Extrae el nombre del token de la cadena de acción.

        Casos reconocidos:
            "return INT"        → "INT"        token normal
            "return PLUS"       → "PLUS"       token normal
            "return int(lxm)"   → "int(lxm)"  valor calculado
            "return lexbuf"     → None         skip (ignorar, no emitir token)
            "return None"       → None         skip
            "raise(...)"        → "EOF"        fin de buffer
            ""                  → None         acción vacía → ignorar