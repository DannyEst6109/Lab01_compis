# Proyecto 1 - Diseño de lenguajes de programación
Este proyecto está conformado por varios laboratorios, estos se encuentran dentro de las carpetas corresponientes al nombre del laboratorio.

## Laboratorio 01 - Conversión directa de ER a AFD

Proyecto en Python que implementa el **método directo** para construir un **Autómata Finito Determinista (AFD)** a partir de una **expresión regular**, sin pasar por AFN.

También permite simular el AFD para validar si una cadena pertenece al lenguaje.

### Funcionalidades del laboratorio 01

- Ingreso de expresión regular.
- Construcción del árbol sintáctico.
- Cálculo de `nullable`, `firstpos`, `lastpos` y `followpos`.
- Construcción de estados y transiciones del AFD.
- Impresión de:
  - tabla `followpos`
  - tabla de transición del AFD
- Simulación de cadenas sobre el AFD.
- Modo de demostración con **3 expresiones regulares** (incluye todos los operadores requeridos).

## Operadores soportados dentro del laboratorio 01

- Unión: `|`
- Concatenación implícita
- Cerradura de Kleene: `*`
- Cerradura positiva: `+`
- Opcional: `?`

## Ejecución laboratorio 01

```bash
python main.py
```

El programa ofrece dos modos:

1. **Interactivo**: ingresas una expresión y una cadena.
2. **Demo**: ejecuta 3 casos listos para mostrar en video (aceptada y rechazada por cada ER).

---
## Laboratorio 02

---
## Requisitos

- Python 3.10+
