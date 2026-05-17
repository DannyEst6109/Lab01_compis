# yalp_lexer.py
# --------------
# Convierte el texto crudo de un archivo .yalp en una lista de tokens.
# NO usa regex ni la librería re. Todo es lectura carácter a carácter.
#
# Tipos de token que produce:
#   PERCENT_KW   -> %token, %left, %right, etc.
#   IGNORE_KW    -> IGNORE
#   WORD         -> cualquier identificador (terminal o no terminal)
#   COLON        -> :
#   PIPE         -> |
#   SEMICOLON    -> ;
#   DOUBLE_PCT   -> %%  (separador de secciones)
#   EOF          -> fin de archivo

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Tipos de token del lexer
# ---------------------------------------------------------------------------

class TT:  # Token Types
    PERCENT_KW  = "PERCENT_KW"   # %token, %left …
    IGNORE_KW   = "IGNORE_KW"    # IGNORE
    WORD        = "WORD"          # cualquier identificador
    COLON       = "COLON"         # :
    PIPE        = "PIPE"          # |
    SEMICOLON   = "SEMICOLON"     # ;
    DOUBLE_PCT  = "DOUBLE_PCT"    # %%
    EOF         = "EOF"


@dataclass
class Token:
    type:  str
    value: str
    line:  int   # número de línea (para mensajes de error)

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line})"


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------

class YalpLexer:
    """
    Convierte el source de un .yalp en una secuencia de Token.
    Avanza carácter a carácter manteniendo posición y línea actual.
    """

    def __init__(self, source: str):
        self.source  = source
        self.pos     = 0          # índice actual en source
        self.line    = 1          # línea actual (para errores)
        self.tokens: list[Token] = []

    # ------------------------------------------------------------------
    # Helpers de navegación
    # ------------------------------------------------------------------

    def _current(self) -> str:
        """Devuelve el carácter actual o '' si llegamos al final."""
        if self.pos < len(self.source):
            return self.source[self.pos]
        return ""

    def _peek(self, offset: int = 1) -> str:
        """Mira hacia adelante sin avanzar."""
        idx = self.pos + offset
        if idx < len(self.source):
            return self.source[idx]
        return ""

    def _advance(self) -> str:
        """Devuelve el carácter actual y avanza el puntero."""
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
        return ch

    def _is_alpha(self, ch: str) -> bool:
        """Letra o guión bajo (inicio/cuerpo de identificador)."""
        return ch == "_" or ("a" <= ch <= "z") or ("A" <= ch <= "Z")

    def _is_alnum(self, ch: str) -> bool:
        """Letra, dígito o guión bajo (cuerpo de identificador)."""
        return self._is_alpha(ch) or ("0" <= ch <= "9")

    # ------------------------------------------------------------------
    # Saltar espacios y comentarios
    # ------------------------------------------------------------------

    def _skip_whitespace(self) -> None:
        """Avanza mientras el carácter sea espacio, tab o nueva línea."""
        while self._current() in (" ", "\t", "\n", "\r"):
            self._advance()

    def _skip_line_comment(self) -> None:
        """Salta un comentario de línea que empieza con //"""
        while self._current() and self._current() != "\n":
            self._advance()

    def _skip_block_comment(self) -> None:
        """
        Salta un comentario de bloque /* ... */
        Llama a esto después de haber consumido '/*'.
        """
        while self._current():
            if self._current() == "*" and self._peek() == "/":
                self._advance()  # '*'
                self._advance()  # '/'
                return
            self._advance()
        raise SyntaxError(f"Comentario de bloque sin cerrar (línea {self.line})")

    # ------------------------------------------------------------------
    # Leer palabras e identificadores
    # ------------------------------------------------------------------

    def _read_word(self) -> str:
        """
        Lee un identificador completo (letras, dígitos, guiones bajos).
        El primer carácter ya fue validado como alfa antes de llamar aquí.
        """
        word = []
        while self._is_alnum(self._current()):
            word.append(self._advance())
        return "".join(word)

    # ------------------------------------------------------------------
    # Tokenización principal
    # ------------------------------------------------------------------

    def tokenize(self) -> list[Token]:
        """
        Recorre todo el source y produce la lista de Token.
        Retorna la misma lista para encadenamiento.
        """
        while True:
            self._skip_whitespace()
            ch = self._current()

            # ── Fin de archivo ────────────────────────────────────────
            if ch == "":
                self.tokens.append(Token(TT.EOF, "", self.line))
                break

            # ── Comentario de línea: // ───────────────────────────────
            if ch == "/" and self._peek() == "/":
                self._advance()   # '/'
                self._advance()   # '/'
                self._skip_line_comment()
                continue

            # ── Comentario de bloque: /* ... */ ──────────────────────
            if ch == "/" and self._peek() == "*":
                self._advance()   # '/'
                self._advance()   # '*'
                self._skip_block_comment()
                continue

            # ── Separador de secciones: %% ───────────────────────────
            if ch == "%" and self._peek() == "%":
                self._advance()   # '%'
                self._advance()   # '%'
                self.tokens.append(Token(TT.DOUBLE_PCT, "%%", self.line))
                continue

            # ── Directiva: %token, %left, etc. ───────────────────────
            if ch == "%":
                self._advance()   # '%'
                # El nombre de la directiva sigue inmediatamente
                if not self._is_alpha(self._current()):
                    raise SyntaxError(
                        f"Se esperaba nombre de directiva tras '%' (línea {self.line})"
                    )
                keyword = self._read_word()
                self.tokens.append(Token(TT.PERCENT_KW, keyword, self.line))
                continue

            # ── Colon ────────────────────────────────────────────────
            if ch == ":":
                self._advance()
                self.tokens.append(Token(TT.COLON, ":", self.line))
                continue

            # ── Pipe ─────────────────────────────────────────────────
            if ch == "|":
                self._advance()
                self.tokens.append(Token(TT.PIPE, "|", self.line))
                continue

            # ── Semicolon ────────────────────────────────────────────
            if ch == ";":
                self._advance()
                self.tokens.append(Token(TT.SEMICOLON, ";", self.line))
                continue

            # ── Identificador o palabra clave IGNORE ─────────────────
            if self._is_alpha(ch):
                word = self._read_word()
                if word == "IGNORE":
                    self.tokens.append(Token(TT.IGNORE_KW, word, self.line))
                else:
                    self.tokens.append(Token(TT.WORD, word, self.line))
                continue

            # ── Carácter desconocido ──────────────────────────────────
            raise SyntaxError(
                f"Carácter inesperado {ch!r} en línea {self.line}"
            )

        return self.tokens