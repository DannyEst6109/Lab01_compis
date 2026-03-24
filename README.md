# Proyecto 1 - Diseño de lenguajes de programación
Este proyecto está conformado por varios laboratorios, estos se encuentran dentro de las carpetas corresponientes al nombre del laboratorio.

## Laboratorio 01 - Conversión directa de ER a AFD

Proyecto en Python que implementa el método directo para construir un Autómata Finito Determinista (AFD) a partir de una expresión regular, sin pasar por AFN.

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
Este laboratorio consiste en extender la funcionalidad desarrollada en el Laboratorio 01 (construcción de AFD a partir de expresiones regulares mediante el método directo) para implementar el algoritmo de minimización de autómatas finitos deterministas (AFD).

El objetivo principal es optimizar el autómata generado, reduciendo el número de estados sin alterar el lenguaje que reconoce


### Funcionalidades del laboratorio 02

El programa desarrollado permite:
- Ingresar una expresión regular. 
- Construir el AFD usando el método directo.
- Generar la tabla de transición del AFD original.
- Aplicar el algoritmo de minimización.
- Generar la tabla de transición del AFD minimizado.
- Mostrar:
    Número de estados (original vs minimizado)
    Número de transiciones (original vs minimizado)
- Ingresar una cadena de prueba.
- Determinar si la cadena Pertenece o no al lenguaje

### Mejoras respecto al Laboratorio 01

Se añade la optimización del autómata
Reducción de complejidad
Mejora en eficiencia de reconocimiento
Comparación entre versiones del AFD

## Ejecución laboratorio 02

```bash
python main.py
```

El programa ofrece dos modos:

1. **Interactivo**: ingresas una expresión y una cadena.
2. **Demo**: ejecuta 3 casos listos para mostrar en video (aceptada y rechazada por cada ER).

--- 
## Proyecto en terminal
Primero, ejecutar lexer-inador.py, colocando la ruta del .yal al que se quiere analizar su léxico. 
La verificación de cadenas se ejecuta como `python3 run_thelexer.py mini_example_T.txt` en la terminal. Tomando en cuenta cual es el que se quiere probar. 
* calc.yal -> calc_example_F.txt / calc_example_T.txt
* lang.yal -> lang_example_T.txt / lang_example_F.txt
* minipython.yal -> mini_example_T.txt / mini_example_F.txt

---

## Interfaz gráfica (producto terminado)
También pueden usar una interfaz gráfica integrada para generar el lexer, visualizar el AFD y analizar archivos de entrada sin editar rutas manualmente.

### Ejecución GUI
```bash
python3 app_gui.py
```

### Flujo dentro de la GUI
1. Seleccionar archivo `.yal` (receta de tokens).
2. Seleccionar archivo `.txt` (entrada a analizar).
3. Clic en **"1) Generar lexer + AFD"**.
4. Clic en **"2) Analizar entrada"**.

La GUI:
- Genera `myToken.py` y `thelexer.py` automáticamente.
- Dibuja el autómata finito determinista minimizado.
- Muestra tabla de transiciones, tokens detectados y errores léxicos.

## Requisitos

- Python 3.10+
