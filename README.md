# Laboratorio 01 - Conversión directa de ER a AFD

Proyecto en Python que implementa el **método directo** para construir un **Autómata Finito Determinista (AFD)** a partir de una **expresión regular**, sin pasar por AFN.

También permite simular el AFD para validar si una cadena pertenece al lenguaje.

## ✅ Qué cubre este proyecto

- Ingreso de expresión regular.
- Construcción del árbol sintáctico.
- Cálculo de `nullable`, `firstpos`, `lastpos` y `followpos`.
- Construcción de estados y transiciones del AFD.
- Impresión de:
  - tabla `followpos`
  - tabla de transición del AFD
- Simulación de cadenas sobre el AFD.
- Modo de demostración con **3 expresiones regulares** (incluye todos los operadores requeridos).

## Operadores soportados

- Unión: `|`
- Concatenación implícita
- Cerradura de Kleene: `*`
- Cerradura positiva: `+`
- Opcional: `?`

> Restricción del curso: no se usan librerías de regex para construir ni simular el autómata.

## Requisitos

- Python 3.10+

## Ejecución

```bash
python main.py
```

El programa ofrece dos modos:

1. **Interactivo**: ingresas una expresión y una cadena.
2. **Demo**: ejecuta 3 casos listos para mostrar en video (aceptada y rechazada por cada ER).

## Pruebas automáticas

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Sugerencia para el video (≤ 5 min)

1. Ejecutar `python main.py`.
2. Elegir modo `2` (Demo).
3. Mostrar para cada caso:
   - expresión regular,
   - tabla de transición,
   - cadena aceptada,
   - cadena rechazada.

Así cubres todos los entregables y operadores solicitados.
