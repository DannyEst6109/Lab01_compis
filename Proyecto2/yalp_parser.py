# yalp_parser.py
# ---------------
# Consume la lista de Token producida por YalpLexer y construye
# un objeto Grammar con toda la información de la gramática.
#
# Gramática que reconoce este parser (en pseudo-BNF):
#
#   file        ::= declarations DOUBLE_PCT rules
#   declarations::= declaration*
#   declaration ::= PERCENT_KW WORD+          (%token A B C …)
#                 | IGNORE_KW  WORD+          (IGNORE WS NL …)
#   rules       ::= rule*
#   rule        ::= WORD COLON body SEMICOLON
#   body        ::= alternative (PIPE alternative)*
#   alternative ::= WORD*                     (puede ser vacía → ε)

from dataclasses import dataclass, field
from typing import Optional

from yalp_lexer import YalpLexer, Token, TT


# ---------------------------------------------------------------------------
# Estructura de datos de la gramática
# ---------------------------------------------------------------------------

EPSILON = "ε"   # símbolo especial para producciones vacías


@dataclass
class Grammar:
    """
    Contenedor central de la gramática parseada.
    Está diseñado para ser consumido directamente por los algoritmos
    de FIRST y FOLLOW en la siguiente etapa.
    """

    # Declaraciones de la sección de cabecera
    tokens:   list[str] = field(default_factory=list)   # %token
    ignored:  list[str] = field(default_factory=list)   # IGNORE

    # Producciones: { "expr": [["expr","PLUS","term"], ["term"]], … }
    productions: dict[str, list[list[str]]] = field(default_factory=dict)

    # Primer LHS encontrado → símbolo inicial
    start_symbol: Optional[str] = None

    # Conjuntos de símbolos (se llenan al final del parsing)
    non_terminals: set[str] = field(default_factory=set)
    terminals:     set[str] = field(default_factory=set)

    # ----------------------------------------------------------------
    # Helpers de consulta (útiles para FIRST / FOLLOW)
    # ----------------------------------------------------------------

    def is_terminal(self, symbol: str) -> bool:
        return symbol in self.terminals

    def is_non_terminal(self, symbol: str) -> bool:
        return symbol in self.non_terminals

    def nullable(self, symbol: str) -> bool:
        """
        Devuelve True si el símbolo puede derivar en ε directamente.
        (Útil como punto de partida antes de calcular FIRST completo.)
        """
        if symbol not in self.productions:
            return False
        return any(alt == [EPSILON] for alt in self.productions[symbol])

    # ----------------------------------------------------------------
    # Representación legible
    # ----------------------------------------------------------------

    def summary(self) -> str:
        lines = [
            "╔══════════════════════════════╗",
            "║         GRAMÁTICA            ║",
            "╚══════════════════════════════╝",
            f"  Símbolo inicial : {self.start_symbol}",
            f"  Tokens (%token) : {self.tokens}",
            f"  Ignorados       : {self.ignored}",
            f"  No terminales   : {sorted(self.non_terminals)}",
            f"  Terminales      : {sorted(self.terminals)}",
            "",
            "  Producciones:",
        ]
        for nt, alts in self.productions.items():
            for i, alt in enumerate(alts):
                lhs   = nt if i == 0 else " " * len(nt)
                arrow = "->" if i == 0 else " |"
                rhs   = " ".join(alt)
                lines.append(f"    {lhs} {arrow} {rhs}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parser de tokens
# ---------------------------------------------------------------------------

class YalpParser:
    """
    Recorre la lista de Token de YalpLexer aplicando descenso recursivo
    para construir un objeto Grammar.
    """

    def __init__(self, tokens: list[Token]):
        self.tokens  = tokens
        self.pos     = 0           # índice actual en la lista de tokens
        self.grammar = Grammar()

    # ------------------------------------------------------------------
    # Helpers de navegación sobre la lista de tokens
    # ------------------------------------------------------------------

    def _current(self) -> Token:
        """Token en la posición actual."""
        return self.tokens[self.pos]

    def _peek(self, offset: int = 1) -> Token:
        """Mira hacia adelante sin consumir."""
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]   # devuelve EOF de forma segura

    def _advance(self) -> Token:
        """Devuelve el token actual y avanza el puntero."""
        tok = self.tokens[self.pos]
        if tok.type != TT.EOF:
            self.pos += 1
        return tok

    def _expect(self, token_type: str) -> Token:
        """
        Consume el token actual si es del tipo esperado.
        Lanza SyntaxError si no coincide.
        """
        tok = self._current()
        if tok.type != token_type:
            raise SyntaxError(
                f"Se esperaba {token_type!r} pero se encontró "
                f"{tok.type!r} ({tok.value!r}) en línea {tok.line}"
            )
        return self._advance()

    def _at(self, *types: str) -> bool:
        """True si el token actual es de alguno de los tipos dados."""
        return self._current().type in types

    # ------------------------------------------------------------------
    # Punto de entrada
    # ------------------------------------------------------------------

    def parse(self) -> Grammar:
        """Parsea el archivo completo y devuelve la Grammar."""
        self._parse_declarations()
        self._expect(TT.DOUBLE_PCT)
        self._parse_rules()
        self._classify_symbols()
        return self.grammar

    # ------------------------------------------------------------------
    # Sección 1: declaraciones (antes de %%)
    # ------------------------------------------------------------------

    def _parse_declarations(self) -> None:
        """
        declarations ::= declaration*
        Se detiene cuando encuentra %% o EOF.
        """
        while not self._at(TT.DOUBLE_PCT, TT.EOF):
            self._parse_one_declaration()

    def _parse_one_declaration(self) -> None:
        """
        declaration ::= PERCENT_KW WORD+
                      | IGNORE_KW  WORD+
        """
        tok = self._current()

        # ── %token A B C … ───────────────────────────────────────────
        if tok.type == TT.PERCENT_KW and tok.value == "token":
            self._advance()   # consume 'token'
            words = self._read_word_list()
            if not words:
                raise SyntaxError(
                    f"'%token' sin nombres de token en línea {tok.line}"
                )
            self.grammar.tokens.extend(words)

        # ── IGNORE A B … ─────────────────────────────────────────────
        elif tok.type == TT.IGNORE_KW:
            self._advance()   # consume 'IGNORE'
            words = self._read_word_list()
            if not words:
                raise SyntaxError(
                    f"'IGNORE' sin nombres de token en línea {tok.line}"
                )
            self.grammar.ignored.extend(words)

        # ── Directiva desconocida: saltar ─────────────────────────────
        else:
            self._advance()

    def _read_word_list(self) -> list[str]:
        """
        Consume cero o más WORD consecutivos y los devuelve como lista.
        Se detiene ante cualquier token que no sea WORD.
        """
        words = []
        while self._at(TT.WORD):
            words.append(self._advance().value)
        return words

    # ------------------------------------------------------------------
    # Sección 2: reglas de producción (después de %%)
    # ------------------------------------------------------------------

    def _parse_rules(self) -> None:
        """
        rules ::= rule*
        Se detiene en EOF.
        """
        while not self._at(TT.EOF):
            self._parse_one_rule()

    def _parse_one_rule(self) -> None:
        """
        rule ::= WORD COLON body SEMICOLON

        El WORD es el no terminal (LHS).
        body contiene las alternativas separadas por '|'.
        """
        # LHS: nombre del no terminal
        lhs_tok = self._expect(TT.WORD)
        lhs = lhs_tok.value

        # Registrar símbolo inicial con el primero que aparezca
        if self.grammar.start_symbol is None:
            self.grammar.start_symbol = lhs

        # Marcar como no terminal
        self.grammar.non_terminals.add(lhs)

        self._expect(TT.COLON)

        # Cuerpo: alternativas
        alternatives = self._parse_body()

        self._expect(TT.SEMICOLON)

        # Guardar (puede haber varias reglas para el mismo LHS)
        if lhs in self.grammar.productions:
            self.grammar.productions[lhs].extend(alternatives)
        else:
            self.grammar.productions[lhs] = alternatives

    def _parse_body(self) -> list[list[str]]:
        """
        body        ::= alternative (PIPE alternative)*
        alternative ::= WORD*

        Una alternativa vacía se representa como [EPSILON].
        """
        alternatives = [self._parse_alternative()]

        while self._at(TT.PIPE):
            self._advance()   # consume '|'
            alternatives.append(self._parse_alternative())

        return alternatives

    def _parse_alternative(self) -> list[str]:
        """
        alternative ::= WORD*

        Recoge WORDs hasta encontrar '|', ';' o EOF.
        Si no hay ninguno, devuelve [EPSILON].
        """
        symbols = []
        while self._at(TT.WORD):
            symbols.append(self._advance().value)
        return symbols if symbols else [EPSILON]

    # ------------------------------------------------------------------
    # Clasificar terminales vs no terminales
    # ------------------------------------------------------------------

    def _classify_symbols(self) -> None:
        """
        Terminal = símbolo que aparece en algún RHS
                   y NO está en non_terminals,
                   UNIÓN los tokens declarados con %token.
        """
        rhs_symbols: set[str] = set()
        for alts in self.grammar.productions.values():
            for alt in alts:
                for sym in alt:
                    if sym != EPSILON:
                        rhs_symbols.add(sym)

        self.grammar.terminals = (
            (rhs_symbols - self.grammar.non_terminals)
            | set(self.grammar.tokens)
        )


# ---------------------------------------------------------------------------
# Funciones de conveniencia
# ---------------------------------------------------------------------------

def parse_yalp(source: str) -> Grammar:
    """
    Atajo: recibe el texto crudo del .yalp y devuelve la Grammar.
    Combina YalpLexer + YalpParser en una sola llamada.
    """
    tokens = YalpLexer(source).tokenize()
    return YalpParser(tokens).parse()


def parse_yalp_file(path: str) -> Grammar:
    """Lee un archivo .yalp del disco y devuelve la Grammar."""
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    return parse_yalp(source)