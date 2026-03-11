class SyntaxNode:
    def __init__(self, value, left=None, right=None, position=None):
        self.value = value
        self.left = left
        self.right = right
        self.position = position

        self.nullable = False
        self.firstpos = set()
        self.lastpos = set()

    def is_leaf(self):
        return self.position is not None


def is_operator(token: str) -> bool:
    return token in {"|", ".", "*", "+", "?"}


def build_syntax_tree(postfix: str):
    stack = []
    position_counter = 1
    pos_to_symbol = {}
    end_marker_pos = None

    for token in postfix:
        if not is_operator(token):
            node = SyntaxNode(value=token, position=position_counter)
            pos_to_symbol[position_counter] = token

            if token == "#":
                end_marker_pos = position_counter

            stack.append(node)
            position_counter += 1

        elif token in {"*", "+", "?"}:
            if not stack:
                raise ValueError(f"Operador unario '{token}' sin operando.")
            child = stack.pop()
            stack.append(SyntaxNode(value=token, left=child))

        elif token in {"|", "."}:
            if len(stack) < 2:
                raise ValueError(f"Operador binario '{token}' sin suficientes operandos.")
            right = stack.pop()
            left = stack.pop()
            stack.append(SyntaxNode(value=token, left=left, right=right))

    if len(stack) != 1:
        raise ValueError("La expresión postfix es inválida.")

    if end_marker_pos is None:
        raise ValueError("No se encontró el marcador de fin '#'.")

    return stack[0], pos_to_symbol, end_marker_pos


def compute_functions(node: SyntaxNode, followpos: dict):
    if node is None:
        return

    if node.left:
        compute_functions(node.left, followpos)
    if node.right:
        compute_functions(node.right, followpos)

    # Hoja
    if node.is_leaf():
        node.nullable = False
        node.firstpos = {node.position}
        node.lastpos = {node.position}
        return

    # Unión
    if node.value == "|":
        node.nullable = node.left.nullable or node.right.nullable
        node.firstpos = node.left.firstpos | node.right.firstpos
        node.lastpos = node.left.lastpos | node.right.lastpos
        return

    # Concatenación
    if node.value == ".":
        node.nullable = node.left.nullable and node.right.nullable

        if node.left.nullable:
            node.firstpos = node.left.firstpos | node.right.firstpos
        else:
            node.firstpos = set(node.left.firstpos)

        if node.right.nullable:
            node.lastpos = node.left.lastpos | node.right.lastpos
        else:
            node.lastpos = set(node.right.lastpos)

        for i in node.left.lastpos:
            followpos[i].update(node.right.firstpos)
        return

    # Kleene *
    if node.value == "*":
        node.nullable = True
        node.firstpos = set(node.left.firstpos)
        node.lastpos = set(node.left.lastpos)

        for i in node.left.lastpos:
            followpos[i].update(node.left.firstpos)
        return

    # Positiva +
    if node.value == "+":
        node.nullable = node.left.nullable
        node.firstpos = set(node.left.firstpos)
        node.lastpos = set(node.left.lastpos)

        for i in node.left.lastpos:
            followpos[i].update(node.left.firstpos)
        return

    # Opcional ?
    if node.value == "?":
        node.nullable = True
        node.firstpos = set(node.left.firstpos)
        node.lastpos = set(node.left.lastpos)
        return