# Calculadora de PRIMERO y SIGUIENTE
## Se encuentra en la carpeta llamada Laboratorio3
Implementación en Python de las funciones PRIMERO y SIGUIENTE para gramáticas libres de contexto, como parte del análisis sintáctico de compiladores.

---

## Estructura del proyecto

```
📁 proyecto/
├── main.py                  # Menú principal y punto de entrada
├── grammar.py               # Clase Grammar (estructura de datos)
├── first_follow.py          # Algoritmos PRIMERO y SIGUIENTE
├── predefined_grammars.py   # Gramáticas de ejemplo listas para usar
└── grammar_input.py         # Ingreso interactivo de gramáticas
```

---

## Requisitos

- Python 3.10 o superior
- No requiere librerías externas

---

## Cómo ejecutar

```bash
python main.py
```

Al iniciar, se muestra un menú con dos opciones:

```
1. Usar una gramática predefinida
2. Ingresar una gramática manualmente
3. Salir
```

---

## Gramáticas predefinidas

| # | Nombre |
|---|--------|
| 1 | Expresiones aritméticas (LL(1)) |
| 2 | Sentencias if-then-else |
| 3 | Listas y asignaciones (con recursión izquierda) |
| 4 | Declaraciones simples |
| 5 | Paréntesis balanceados |

---

## Ingreso manual de gramáticas

Al elegir la opción 2, el programa solicita los datos paso a paso:

1. **Nombre** de la gramática (opcional).
2. **No terminales** separados por comas. El primero será el símbolo inicial.
3. **Producciones** para cada no terminal, usando `|` para separar alternativas.

### Ejemplo de ingreso

```
Nombre: mi gramatica

No terminales: E, T, F

E → E + T | T
T → T * F | F
F → ( E ) | id
```

> Para representar **épsilon** use: `eps`, `epsilon` o `ε`

---

## Formato interno de gramáticas

Las gramáticas se representan como diccionarios de Python:

```python
Grammar(
    productions={
        'E' : [['E', '+', 'T'], ['T']],
        'T' : [['T', '*', 'F'], ['F']],
        'F' : [['(', 'E', ')'], ['id']],
    },
    start_symbol='E',
    name='Expresiones aritméticas'
)
```

---

## Ejemplo de salida

```
==================================================
       Gramática: Expresiones aritméticas
==================================================
  Símbolo inicial : E
  No terminales   : { E, F, T }
  Terminales      : { (, ), *, +, id }
  Producciones:
    E          → E + T | T
    T          → T * F | F
    F          → ( E ) | id
==================================================

──────────────────────────────────────────────────
  CONJUNTOS PRIMERO y SIGUIENTE
──────────────────────────────────────────────────
  No Terminal  PRIMERO               SIGUIENTE
  ───────────  ────────────────────  ────────────────────
  E            { (, id }             { $, ), + }
  T            { (, id }             { $, ), *, + }
  F            { (, id }             { $, ), *, + }
──────────────────────────────────────────────────
```

---

## Algoritmos implementados

### PRIMERO
- Si `X` es terminal → `PRIMERO(X) = { X }`
- Si `X → ε` → `ε ∈ PRIMERO(X)`
- Si `X → Y1 Y2 … Yk` → se agregan los PRIMERO de cada `Yi` mientras el anterior pueda derivar `ε`
- Implementado con **recursión + memoización** para manejar gramáticas con recursión mutua.

### SIGUIENTE
- `$ ∈ SIGUIENTE(S)` (símbolo inicial)
- Si `A → α B β` → `PRIMERO(β) − {ε} ⊆ SIGUIENTE(B)`
- Si `ε ∈ PRIMERO(β)` o `B` está al final → `SIGUIENTE(A) ⊆ SIGUIENTE(B)`
- Implementado con **iteración de punto fijo** hasta que ningún conjunto cambie.

---

## Agregar gramáticas predefinidas propias

Para agregar una nueva gramática al catálogo, editar `predefined_grammars.py`:

```python
GRAMMAR_NUEVA = Grammar(
    productions={
        'S': [['a', 'S', 'b'], ['ε']],
    },
    start_symbol='S',
    name='Mi nueva gramática'
)

# Agregar al catálogo
PREDEFINED['6'] = GRAMMAR_NUEVA
```