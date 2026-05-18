from __future__ import annotations

import contextlib
import importlib
import importlib.util
import io
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from parser_runtime import normalize_lexer_output


PROJECT_ROOT = Path(__file__).resolve().parent
LEXER_PROJECT = PROJECT_ROOT.parent / "Proyecto1"
GENERATED_DIR = PROJECT_ROOT / "generated"


@dataclass
class LexerBuildResult:
    lexer_path: Path
    token_path: Path
    entrypoint: str
    dfa: dict[str, Any]
    log: str


@dataclass
class LexerRunResult:
    tokens: list[tuple[str, str]]
    errors: list[str]
    log: str


def _ensure_project1_imports() -> None:
    """Expose Proyecto1 modules without requiring the user to run from its folder."""
    project1 = str(LEXER_PROJECT)
    if project1 not in sys.path:
        sys.path.insert(0, project1)


def generate_lexer_from_yal(
    yal_path: str | os.PathLike[str],
    output_dir: str | os.PathLike[str] = GENERATED_DIR,
    minimize: bool = True,
) -> LexerBuildResult:
    """Build an independent lexer module from a .yal file using Proyecto1."""
    _ensure_project1_imports()

    from ParserYal import YALexParser
    from LexerGenerator import build_dfa_dict
    from lexer_generator_yalex import generate_lexer, generate_token_module

    yal_path = Path(yal_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    lexer_path = output_dir / f"{yal_path.stem}_lexer.py"
    token_path = output_dir / "myToken.py"

    log_buffer = io.StringIO()
    with contextlib.redirect_stdout(log_buffer):
        parser = YALexParser().parse(str(yal_path))
        rules = parser.get_all_rules()
        dfa = build_dfa_dict(rules, parser=parser, minimize=minimize, verbose=True)
        generate_token_module(dfa, str(token_path))
        generate_lexer(dfa, str(lexer_path))

    return LexerBuildResult(
        lexer_path=lexer_path,
        token_path=token_path,
        entrypoint=dfa.get("entrypoint", "tokens"),
        dfa=dfa,
        log=log_buffer.getvalue(),
    )


def load_generated_lexer(lexer_path: str | os.PathLike[str]) -> Any:
    """Import a generated lexer module from disk."""
    lexer_path = Path(lexer_path)
    output_dir = str(lexer_path.parent)
    if output_dir not in sys.path:
        sys.path.insert(0, output_dir)

    # The generated lexer imports myToken.py by name. If the user rebuilds
    # from another .yal in the same GUI session, discard the previous constants.
    sys.modules.pop("myToken", None)
    importlib.invalidate_caches()

    module_name = f"generated_lexer_{lexer_path.stem}_{abs(hash(str(lexer_path)))}"
    spec = importlib.util.spec_from_file_location(module_name, lexer_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo cargar el lexer generado: {lexer_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tokenize_with_generated_lexer(
    input_text: str,
    lexer_module: Any,
    entrypoint: str = "tokens",
    grammar_terminals: Iterable[str] | None = None,
) -> LexerRunResult:
    """
    Run the generated lexer and return parser-ready tokens.

    Supports both styles used in the existing .yal examples:
    - actions like `return INT`, where the generated lexer returns token names;
    - actions like `print("INT")`, where the token name is recovered from stdout.
    """
    errors: list[str] = []
    terminals = set(grammar_terminals or [])

    fn = getattr(lexer_module, entrypoint, None)
    if fn is None:
        fn = getattr(lexer_module, "tokens", None) or getattr(lexer_module, "tokenize", None)
    if fn is None:
        return LexerRunResult([], [f"El lexer no tiene funcion '{entrypoint}', tokens() ni tokenize()."], "")

    log_buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(log_buffer):
            raw = fn(input_text)
    except Exception as exc:
        return LexerRunResult([], [f"Error lexico: {exc}"], log_buffer.getvalue())

    log = log_buffer.getvalue()
    tokens = normalize_lexer_output(raw)

    if not tokens:
        parsed_from_stdout, stdout_errors = parse_printed_tokens(log, terminals)
        tokens = parsed_from_stdout
        errors.extend(stdout_errors)

    return LexerRunResult(tokens, errors, log)


def parse_printed_tokens(log: str, grammar_terminals: set[str] | None = None) -> tuple[list[tuple[str, str]], list[str]]:
    tokens: list[tuple[str, str]] = []
    errors: list[str] = []
    grammar_terminals = grammar_terminals or set()

    for raw_line in log.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        lowered = line.lower()
        if "error" in lowered and "lex" in lowered:
            errors.append(line)
            continue

        if ":" in line:
            name, lexeme = line.split(":", 1)
            token_name = name.strip()
            token_lexeme = lexeme.strip()
        else:
            token_name = line.strip()
            token_lexeme = line.strip()

        if grammar_terminals and token_name not in grammar_terminals:
            continue
        tokens.append((token_name, token_lexeme))

    return tokens, errors


def lexer_dfa_to_text(dfa: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("AFD lexico generado desde YALex")
    lines.append(f"Estado inicial: {dfa.get('initial_state', 0)}")
    lines.append("")
    lines.append("Estados aceptantes:")
    for state, info in sorted(dfa.get("accepting_states", {}).items()):
        token = info.get("token") or "(accion/ignorar)"
        lines.append(f"  {state}: {token} prioridad={info.get('priority')}")
    lines.append("")
    lines.append("Transiciones:")
    for state, transitions in sorted(dfa.get("transitions", {}).items()):
        for symbol, target in sorted(transitions.items(), key=lambda x: repr(x[0])):
            display = symbol.encode("unicode_escape").decode("ascii")
            lines.append(f"  {state} -- {display} --> {target}")
    return "\n".join(lines)
