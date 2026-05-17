# test_ejemplos.py
# -----------------
# Prueba los 4 archivos .yalp y verifica su estructura esperada.
# Ejecutar con: python test_ejemplos.py

import sys
import os
from pathlib import Path


# Asegurar que el parser está en el path
sys.path.insert(0, os.path.dirname(__file__))

from yalp_parser import parse_yalp_file, Grammar

# ---------------------------------------------------------------------------
# Framework de verificación
# ---------------------------------------------------------------------------

passed = 0
failed = 0

def check(label: str, actual, expected):
    global passed, failed
    ok = actual == expected
    status = "✓" if ok else "✗"
    print(f"  {status} {label}")
    if not ok:
        print(f"      esperado : {expected}")
        print(f"      obtenido : {actual}")
        failed += 1
    else:
        passed += 1

def section(title: str):
    print(f"\n{'═'*55}")
    print(f"  {title}")
    print('═'*55)

# ---------------------------------------------------------------------------
# CASO 1 — calc.yalp
# ---------------------------------------------------------------------------
section("calc.yalp  ←  calc.yal")

BASE_DIR = Path(__file__).resolve().parent

archivo = BASE_DIR / "Ejemplos" / "calc.yalp"



g: Grammar = parse_yalp_file(archivo)
print()
print(g.summary())

print("\n── Verificaciones ──")
check("start_symbol",
      g.start_symbol,
      "programa")

check("tokens declarados",
      sorted(g.tokens),
      sorted(["ENTERO","SUMA","RESTA","MULT","DIV","LPAREN","RPAREN"]))

check("ignorados",
      g.ignored,
      ["ESPACIO"])

check("no terminales",
      sorted(g.non_terminals),
      sorted(["programa","expr","termino","factor"]))

check("terminales",
      sorted(g.terminals),
      sorted(["ENTERO","SUMA","RESTA","MULT","DIV","LPAREN","RPAREN"]))

check("producciones de expr",
      g.productions["expr"],
      [["expr","SUMA","termino"],
       ["expr","RESTA","termino"],
       ["termino"]])

check("producciones de factor",
      g.productions["factor"],
      [["LPAREN","expr","RPAREN"],
       ["ENTERO"]])

check("factor NO es nullable",
      g.nullable("factor"),
      False)

# ---------------------------------------------------------------------------
# CASO 2 — ejemplo.yalp
# ---------------------------------------------------------------------------
section("ejemplo.yalp  ←  ejemplo.yal")
ejemplo = BASE_DIR / "Ejemplos" / "ejemplo.yalp"
g = parse_yalp_file(ejemplo)
print()
print(g.summary())

print("\n── Verificaciones ──")
check("start_symbol",
      g.start_symbol,
      "programa")

check("tokens declarados",
      sorted(g.tokens),
      sorted(["INT","FLOAT","ID","PLUS","MINUS","TIMES","DIV",
              "LPAREN","RPAREN","ASSIGN","EOL","EOF"]))

check("ignorados",
      g.ignored,
      ["WS"])

check("no terminales",
      sorted(g.non_terminals),
      sorted(["programa","sentencia","expr","termino","factor"]))

check("terminales",
      sorted(g.terminals),
      sorted(["INT","FLOAT","ID","PLUS","MINUS","TIMES","DIV",
              "LPAREN","RPAREN","ASSIGN","EOL","EOF"]))

check("sentencia tiene 2 alternativas",
      len(g.productions["sentencia"]),
      2)

check("primera alt de sentencia es asignación",
      g.productions["sentencia"][0],
      ["ID","ASSIGN","expr"])

check("factor incluye FLOAT, INT e ID",
      ["FLOAT"] in g.productions["factor"] and
      ["INT"]   in g.productions["factor"] and
      ["ID"]    in g.productions["factor"],
      True)

# ---------------------------------------------------------------------------
# CASO 3 — lang.yalp
# ---------------------------------------------------------------------------
section("lang.yalp  ←  lang.yal")
lang = BASE_DIR / "Ejemplos" / "lang.yalp"
g = parse_yalp_file(lang)
print()
print(g.summary())

print("\n── Verificaciones ──")
check("start_symbol",
      g.start_symbol,
      "programa")

check("tokens incluyen IF, WHILE, RETURN",
      all(t in g.tokens for t in ["IF","WHILE","RETURN"]),
      True)

check("tokens incluyen comparadores",
      all(t in g.tokens for t in ["EQ","NEQ","LT","GT"]),
      True)

check("ignorados",
      sorted(g.ignored),
      sorted(["ESPACIO","COMENTARIO"]))

check("no terminales",
      sorted(g.non_terminals),
      sorted(["programa","decl","sentencia","si","mientras",
              "bloque","condicion","expr","termino","factor"]))

check("si tiene 2 alternativas (con y sin else)",
      len(g.productions["si"]),
      2)

check("bloque tiene 2 alternativas (con y sin cuerpo)",
      len(g.productions["bloque"]),
      2)

check("condicion tiene exactamente 4 alternativas",
      len(g.productions["condicion"]),
      4)

check("expr tiene 3 alternativas",
      len(g.productions["expr"]),
      3)

check("FLOTANTE y ENTERO son terminales",
      "FLOTANTE" in g.terminals and "ENTERO" in g.terminals,
      True)

# ---------------------------------------------------------------------------
# CASO 4 — minipython.yalp
# ---------------------------------------------------------------------------
section("minipython.yalp  ←  minipython.yal")

minipython = BASE_DIR / "Ejemplos" / "minipython.yalp"
g = parse_yalp_file(minipython)
print()
print(g.summary())

print("\n── Verificaciones ──")
check("start_symbol",
      g.start_symbol,
      "programa")

check("tokens incluyen palabras clave de Python",
      all(t in g.tokens for t in
          ["DEF","CLASS","IF","ELIF","ELSE","WHILE","FOR","IN",
           "RETURN","TRUE","FALSE","AND","OR","NOT","NONE"]),
      True)

check("tokens incluyen operadores compuestos",
      all(t in g.tokens for t in
          ["PLUS_ASSIGN","MINUS_ASSIGN","EQ","NEQ","LEQ","GEQ"]),
      True)

check("ignorados",
      sorted(g.ignored),
      sorted(["ESPACIO","COMENTARIO"]))

check("no terminales incluyen jerarquía de expresiones",
      all(nt in g.non_terminals for nt in
          ["expr","exprAnd","exprNot","exprComp","exprSuma","exprMult"]),
      True)

check("no terminales incluyen estructuras de control",
      all(nt in g.non_terminals for nt in
          ["si","mientras","para","retorno","defFuncion","defClase"]),
      True)

check("asignacion tiene 3 alternativas",
      len(g.productions["asignacion"]),
      3)

check("retorno tiene 2 alternativas (con y sin expr)",
      len(g.productions["retorno"]),
      2)

check("retorno sin expr es ['RETURN']",
      ["RETURN"] in g.productions["retorno"],
      True)

check("factor incluye listas y llamadas a función",
      ["LBRACKET","RBRACKET"] in g.productions["factor"],
      True)

check("exprNot es recursivo",
      ["NOT","exprNot"] in g.productions["exprNot"],
      True)

check("exprComp tiene 7 alternativas",
      len(g.productions["exprComp"]),
      7)

# ---------------------------------------------------------------------------
# Resumen final
# ---------------------------------------------------------------------------
total = passed + failed
print(f"\n{'═'*55}")
print(f"  Resultado: {passed}/{total} verificaciones pasaron", end="")
print("  ✓" if failed == 0 else f"  ({failed} fallaron)")
print('═'*55)