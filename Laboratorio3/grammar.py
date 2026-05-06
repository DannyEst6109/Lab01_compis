"""
grammar.py
Definición de la clase Grammar y utilidades para manejar
gramáticas libres de contexto.
"""

EPSILON = 'ε'


class Grammar:
    """
    Representa una gramática libre de contexto.

    Las producciones se almacenan como un diccionario:
        { 'NO_TERMINAL': [ ['símbolo1', 'símbolo2', ...], ... ] }

    Ejemplo:
        {
            'E' : [['T', "E'"]],
            "E'": [['+', 'T', "E'"], ['ε']],
            'T' : [['F', "T'"]],
            "T'": [['*', 'F', "T'"], ['ε']],
            'F' : [['(', 'E', ')'], ['id']]
        }
    """

    def __init__(self, productions: dict, start_symbol: str = None, name: str = ""):
        """
        Parameters
        ----------
        productions  : diccionario de producciones (ver formato arriba)
        start_symbol : símbolo inicial (por defecto la primera clave)
        name         : nombre descriptivo de la gramática
        """
        if not productions:
            raise ValueError("La gramática no puede estar vacía.")

        self.productions  = productions
        self.start_symbol = start_symbol or list(productions.keys())[0]
        self.name         = name

        # Los no terminales son exactamente las claves del diccionario
        self.non_terminals: set = set(productions.keys())

        # Los terminales son todos los símbolos que no son no terminales ni ε
        self.terminals: set = self._find_terminals()

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _find_terminals(self) -> set:
        terminals = set()
        for prods in self.productions.values():
            for prod in prods:
                for sym in prod:
                    if sym != EPSILON and sym not in self.non_terminals:
                        terminals.add(sym)
        return terminals

    # ------------------------------------------------------------------
    # Métodos públicos
    # ------------------------------------------------------------------

    def display(self):
        """Imprime la gramática de forma legible."""
        titulo = f" Gramática: {self.name} " if self.name else " Gramática "
        print(f"\n{'='*50}")
        print(titulo.center(50))
        print('='*50)
        print(f"  Símbolo inicial : {self.start_symbol}")
        print(f"  No terminales   : {{ {', '.join(sorted(self.non_terminals))} }}")
        print(f"  Terminales      : {{ {', '.join(sorted(self.terminals))} }}")
        print("  Producciones:")
        for nt, prods in self.productions.items():
            rhs_list = [' '.join(p) for p in prods]
            rhs = ' | '.join(rhs_list)
            print(f"    {nt:10s} → {rhs}")
        print('='*50)

    def validate(self):
        """
        Comprueba que el símbolo inicial exista en las producciones
        y que toda referencia a un no terminal tenga al menos una producción.
        Lanza ValueError si hay inconsistencias.
        """
        if self.start_symbol not in self.productions:
            raise ValueError(
                f"El símbolo inicial '{self.start_symbol}' no tiene producciones."
            )
        for nt, prods in self.productions.items():
            if not prods:
                raise ValueError(f"El no terminal '{nt}' no tiene producciones.")
            for prod in prods:
                if not prod:
                    raise ValueError(
                        f"Producción vacía en '{nt}'. Use ['{EPSILON}'] para épsilon."
                    )