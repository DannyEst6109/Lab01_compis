# Lab01_compis

# Laboratorio 01 - Conversión directa de una expresión regular a un AFD

Proyecto en Python que implementa el **método directo** para convertir una **expresión regular** en un **AFD** y simular su funcionamiento.

## Objetivo
- Ingresar una expresión regular
- Construir el AFD usando el método directo
- Mostrar la tabla de transición
- Validar cadenas de entrada

## Operadores soportados
- Unión: `|`
- Concatenación implícita
- Cerradura de Kleene: `*`
- Cerradura positiva: `+`
- Opcional: `?`

## Restricción
No se utilizan librerías de expresiones regulares.

## Requisitos
- Python 3.10 o superior

## Cómo ejecutar

```bash
python main.py


Ingrese una expresión regular: a(b|c)*
Ingrese una cadena a validar: abcb
Resultado: La cadena SÍ pertenece al lenguaje.