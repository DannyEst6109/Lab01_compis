# =============================================================================
# models.py — Estructuras de datos compartidas entre las 3 partes del proyecto
# =============================================================================
# Este archivo lo usan las 3 partes. No lo modifiques sin consultarlo con el grupo.

from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional, FrozenSet


# -----------------------------------------------------------------------------
# Producido por la PARTE 1
# -----------------------------------------------------------------------------

@dataclass
class Grammar:
    """
    Representa la gramática libre de contexto extraída del archivo .yalp.
    La Parte 1 produce este objeto; la Parte 2 lo consume.
    """
    terminals: List[str]                        # Tokens en MAYÚSCULA, ej. ["TOKEN_1", "TOKEN_2", "$"]
    non_terminals: List[str]                    # Producciones en minúscula, ej. ["production1"]
    productions: List[Tuple[str, List[str]]]    # (cabeza, cuerpo), ej. ("prod1", ["prod1", "TOKEN_2"])
    start_symbol: str                           # Primera producción declarada en el .yalp
    ignored_tokens: List[str]                   # Tokens a ignorar, ej. ["WS"]
    first: Dict[str, Set[str]]                  # FIRST sets por símbolo
    follow: Dict[str, Set[str]]                 # FOLLOW sets por no-terminal (incluye "$")


# -----------------------------------------------------------------------------
# Producido por la PARTE 2
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class LRItem:
    """
    Un ítem LR(0): una producción con un punto (•) que indica cuánto hemos leído.
    
    Ejemplo: production1 → production1 • TOKEN_2 production2
    significa que ya vimos 'production1' y esperamos ver 'TOKEN_2' a continuación.
    
    Es frozen=True (inmutable) para poder usarlo en sets y como llave de diccionarios.
    """
    head: str               # Lado izquierdo de la producción
    body: Tuple[str, ...]   # Lado derecho como tupla (inmutable)
    dot: int                # Posición del punto (0 = al inicio, len(body) = al final)

    def is_complete(self) -> bool:
        """El punto llegó al final → podemos reducir."""
        return self.dot >= len(self.body)

    def next_symbol(self) -> Optional[str]:
        """El símbolo inmediatamente a la derecha del punto, o None si está completo."""
        if self.is_complete():
            return None
        return self.body[self.dot]

    def advance(self) -> 'LRItem':
        """Devuelve un nuevo ítem con el punto avanzado una posición."""
        return LRItem(self.head, self.body, self.dot + 1)

    def __repr__(self) -> str:
        """Representación visual: production1 → prod1 • TOKEN_2 prod2"""
        body_list = list(self.body)
        body_list.insert(self.dot, '•')
        body_str = ' '.join(body_list) if body_list else 'ε'
        return f"{self.head} → {body_str}"


@dataclass
class State:
    """
    Un estado del autómata LR(0).
    Contiene un conjunto de ítems LR(0) (su 'núcleo' más la clausura).
    """
    id: int
    items: FrozenSet[LRItem]

    def __repr__(self) -> str:
        items_str = '\n  '.join(str(i) for i in sorted(self.items, key=str))
        return f"Estado {self.id}:\n  {items_str}"


@dataclass
class LR0Automaton:
    """
    El autómata LR(0) completo.
    La Parte 3 usa esto para visualizarlo como grafo.
    """
    states: List[State]
    transitions: Dict[Tuple[int, str], int]     # (estado_origen, símbolo) → estado_destino


@dataclass
class SLRTables:
    """
    Las tablas ACTION y GOTO del parser SLR.
    La Parte 3 usa esto para ejecutar el parsing.

    action[(estado, terminal)] puede ser:
        ("shift",  estado_destino)   → mover token a la pila e ir al estado
        ("reduce", índice_producción) → reducir usando la producción grammar.productions[índice]
        ("accept",)                   → ¡parsing exitoso!
        (no existe la clave)          → error sintáctico

    goto[(estado, no_terminal)] → estado_destino  (después de una reducción)
    """
    action: Dict[Tuple[int, str], Tuple]        # (estado, terminal) → acción
    goto: Dict[Tuple[int, str], int]            # (estado, no_terminal) → estado
    conflicts: List[str]                        # Lista de conflictos detectados (vacía = sin ambigüedad)