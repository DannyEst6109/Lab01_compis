from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Tuple

from models import Grammar, SLRTables


@dataclass
class ParseResult:
    accepted: bool
    actions: List[str]
    errors: List[str]


def normalize_lexer_output(raw: Any) -> List[Tuple[str, str]]:
    """Normaliza salida del lexer a lista de (token, lexema)."""
    tokens: List[Tuple[str, str]] = []
    if raw is None:
        return tokens

    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, tuple) and len(item) >= 2:
                tokens.append((str(item[0]), str(item[1])))
            elif isinstance(item, str):
                tokens.append((item, item))
            elif hasattr(item, "type"):
                lex = getattr(item, "value", getattr(item, "lexeme", str(item.type)))
                tokens.append((str(item.type), str(lex)))
    return tokens


def tokenize_input(input_text: str, lexer_module: Any | None = None) -> Tuple[List[Tuple[str, str]], List[str]]:
    """Tokeniza con lexer externo si existe; fallback: tokens por espacio."""
    errors: List[str] = []

    if lexer_module is None:
        return [(p, p) for p in input_text.split() if p.strip()], errors

    if hasattr(lexer_module, "tokenize"):
        try:
            raw = lexer_module.tokenize(input_text)
            return normalize_lexer_output(raw), errors
        except Exception as exc:
            errors.append(f"Error léxico: {exc}")
            return [], errors

    if hasattr(lexer_module, "tokens"):
        try:
            raw = lexer_module.tokens(input_text)
            normalized = normalize_lexer_output(raw)
            if not normalized:
                errors.append("El lexer no retornó tokens; usa formato separado por espacios o adapta el lexer.")
            return normalized, errors
        except Exception as exc:
            errors.append(f"Error léxico: {exc}")
            return [], errors

    errors.append("No se encontró función tokenize() ni tokens() en el lexer.")
    return [], errors


def slr_parse(token_stream: List[Tuple[str, str]], grammar: Grammar, tables: SLRTables) -> ParseResult:
    actions: List[str] = []
    errors: List[str] = []

    filtered = [(t, l) for (t, l) in token_stream if t not in grammar.ignored_tokens]
    filtered.append(("$", "$"))

    state_stack: List[int] = [0]
    symbol_stack: List[str] = []
    i = 0

    while True:
        state = state_stack[-1]
        lookahead, lexeme = filtered[i]
        action = tables.action.get((state, lookahead))

        if action is None:
            expected = sorted([t for (s, t), _ in tables.action.items() if s == state])
            errors.append(
                f"Error sintáctico en token '{lookahead}' (lexema='{lexeme}'). "
                f"Estado={state}, esperados={expected if expected else 'ninguno'}."
            )
            return ParseResult(False, actions, errors)

        if action[0] == "shift":
            next_state = action[1]
            symbol_stack.append(lookahead)
            state_stack.append(next_state)
            actions.append(f"SHIFT  token={lookahead:<12} -> estado {next_state}")
            i += 1
            continue

        if action[0] == "reduce":
            prod_idx = action[1]
            head, body = grammar.productions[prod_idx]
            pop_count = len(body)

            if pop_count > 0:
                del symbol_stack[-pop_count:]
                del state_stack[-pop_count:]

            goto_state = tables.goto.get((state_stack[-1], head))
            if goto_state is None:
                errors.append(f"Error interno: GOTO faltante para ({state_stack[-1]}, {head}).")
                return ParseResult(False, actions, errors)

            symbol_stack.append(head)
            state_stack.append(goto_state)
            rhs = " ".join(body) if body else "ε"
            actions.append(f"REDUCE prod[{prod_idx}] {head} -> {rhs}; goto {goto_state}")
            continue

        if action[0] == "accept":
            actions.append("ACCEPT")
            return ParseResult(True, actions, errors)

        errors.append(f"Acción inválida: {action}")
        return ParseResult(False, actions, errors)
