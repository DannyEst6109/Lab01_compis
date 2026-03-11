OPERATORS = {"|", ".", "*", "+", "?", "(", ")"}
UNARY_OPERATORS = {"*", "+", "?"}
BINARY_OPERATORS = {"|", "."}


def is_symbol(char: str) -> bool:
    return char not in OPERATORS


def validate_regex(regex: str) -> None:
    if not regex:
        raise ValueError("La expresión regular no puede estar vacía.")

    balance = 0
    previous = None

    for i, token in enumerate(regex):
        if token == "(":
            balance += 1
        elif token == ")":
            balance -= 1
            if balance < 0:
                raise ValueError("Paréntesis desbalanceados: ')' sin apertura.")

        if token in BINARY_OPERATORS:
            if i == 0 or i == len(regex) - 1:
                raise ValueError(f"Operador binario '{token}' en posición inválida.")
            if previous in BINARY_OPERATORS or previous == "(":
                raise ValueError(f"Secuencia inválida antes de '{token}'.")

        if token in UNARY_OPERATORS and previous in BINARY_OPERATORS:
            raise ValueError(f"Operador unario '{token}' sin operando válido.")

        previous = token

    if balance != 0:
        raise ValueError("Paréntesis desbalanceados en la expresión regular.")


def needs_concat(c1: str, c2: str) -> bool:
    left_ok = is_symbol(c1) or c1 in {")", "*", "+", "?"}
    right_ok = is_symbol(c2) or c2 == "("
    return left_ok and right_ok


def add_explicit_concat(regex: str) -> str:
    result = []
    for i, c1 in enumerate(regex):
        result.append(c1)
        if i + 1 < len(regex):
            c2 = regex[i + 1]
            if needs_concat(c1, c2):
                result.append(".")
    return "".join(result)


def prepare_regex(regex: str) -> str:
    """
    Agrega marcador de fin '#':
      (regex).#
    y concatenación explícita.
    """
    regex = regex.replace(" ", "")
    validate_regex(regex)

    augmented = f"({regex})#"
    return add_explicit_concat(augmented)


def precedence(op: str) -> int:
    if op in {"*", "+", "?"}:
        return 3
    if op == ".":
        return 2
    if op == "|":
        return 1
    return 0


def to_postfix(regex: str) -> str:
    output = []
    stack = []

    for token in regex:
        if is_symbol(token):
            output.append(token)
        elif token == "(":
            stack.append(token)
        elif token == ")":
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            if not stack:
                raise ValueError("Paréntesis desbalanceados.")
            stack.pop()
        else:
            while (
                stack
                and stack[-1] != "("
                and precedence(stack[-1]) >= precedence(token)
            ):
                output.append(stack.pop())
            stack.append(token)

    while stack:
        top = stack.pop()
        if top in {"(", ")"}:
            raise ValueError("Paréntesis desbalanceados.")
        output.append(top)

    return "".join(output)


def extract_alphabet(pos_to_symbol: dict) -> list:
    alphabet = sorted({sym for sym in pos_to_symbol.values() if sym != "#"})
    return alphabet
