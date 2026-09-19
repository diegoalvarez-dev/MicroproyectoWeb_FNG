"""
models.py
Estructuras de datos base para representar una Gramática Libre de Contexto (GLC)
y sus producciones, usadas en todo el pipeline de conversión FNC -> FNG.

Convenciones adoptadas para este proyecto (confirmadas con el usuario):
- No terminal (Vnt): letra mayúscula, opcionalmente seguida de un número o
  sufijo como ".1" (ej: A, B, X6, X6.1).
- Terminal (Vt): letra minúscula o dígito (ej: a, b, 1, 2).
- En FNC de entrada solo se aceptan estas combinaciones de cuerpo de producción:
    VntVnt, VtVt, VtVnt, VntVt, Vt
  (no se aceptan producciones unitarias ni producción vacía epsilon, ya que
  se asume que la gramática de entrada ya fue depurada en el proyecto de FNC).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import re

# Un símbolo de la gramática es simplemente un string. Distinguimos su tipo
# con las funciones utilitarias de abajo.

class ExplosionDeProducciones(Exception):
    """Se lanza cuando la conversión crece más allá de un límite de seguridad
    razonable, para abortar de forma controlada en vez de agotar memoria."""
    pass


TERMINAL_RE = re.compile(r'^[a-z0-9]$')
# No terminal: una letra mayúscula, opcionalmente seguida de dígitos y/o
# un sufijo ".n" (para las variables auxiliares tipo X6.1, X6.1.1, etc.)
NO_TERMINAL_RE = re.compile(r'^[A-Z][0-9]*(\.[0-9]+)*$')


def es_terminal(simbolo: str) -> bool:
    return bool(TERMINAL_RE.match(simbolo))


def es_no_terminal(simbolo: str) -> bool:
    return bool(NO_TERMINAL_RE.match(simbolo))


def tipo_simbolo(simbolo: str) -> str:
    if es_terminal(simbolo):
        return "Vt"
    if es_no_terminal(simbolo):
        return "Vnt"
    return "?"


@dataclass
class Produccion:
    """Una producción X -> cuerpo, donde cuerpo es una lista de símbolos."""
    cabeza: str
    cuerpo: List[str]

    def __str__(self) -> str:
        return f"{self.cabeza} -> {''.join(self.cuerpo)}"

    def es_vacia(self) -> bool:
        return len(self.cuerpo) == 0 or self.cuerpo == ['ε'] or self.cuerpo == ['epsilon']

    def clonar(self) -> "Produccion":
        return Produccion(self.cabeza, list(self.cuerpo))

    def patron_forma(self) -> str:
        """Devuelve el patrón de tipos del cuerpo, ej: 'VntVnt', 'Vt'."""
        return "".join(tipo_simbolo(s) for s in self.cuerpo)


@dataclass
class Gramatica:
    variables: List[str]           # no terminales, en el orden declarado por el usuario
    terminales: List[str]
    inicial: str
    producciones: List[Produccion] = field(default_factory=list)

    def clonar(self) -> "Gramatica":
        return Gramatica(
            variables=list(self.variables),
            terminales=list(self.terminales),
            inicial=self.inicial,
            producciones=[p.clonar() for p in self.producciones],
        )

    def producciones_de(self, variable: str) -> List[Produccion]:
        return [p for p in self.producciones if p.cabeza == variable]

    def agregar(self, cabeza: str, cuerpo: List[str]) -> Produccion:
        p = Produccion(cabeza, list(cuerpo))
        self.producciones.append(p)
        return p

    def eliminar(self, produccion: Produccion) -> None:
        self.producciones.remove(produccion)

    def texto(self) -> str:
        """Representación compacta agrupada por variable, en el orden de self.variables."""
        lineas = []
        for v in self.variables:
            cuerpos = [''.join(p.cuerpo) if p.cuerpo else 'ε' for p in self.producciones_de(v)]
            if cuerpos:
                lineas.append(f"{v} -> " + " | ".join(cuerpos))
        return "\n".join(lineas)


MAX_PRODUCCIONES = 4000
# Límite de seguridad: la conversión a FNG puede crecer de forma
# combinatoria (es una propiedad conocida del algoritmo, no un error).
# Si una gramática supera este límite durante el proceso, se aborta con
# un mensaje claro en vez de agotar la memoria del proceso (RNF11).


class GramaticaDemasiadoGrandeError(Exception):
    pass


def deduplicar(g: "Gramatica") -> int:
    """
    Elimina producciones exactamente duplicadas (misma cabeza y mismo
    cuerpo). Cumple RNF07 (impedir duplicación innecesaria de
    producciones), que aparece naturalmente durante las sustituciones del
    algoritmo cuando dos caminos distintos generan la misma producción.
    Devuelve cuántas se eliminaron.
    """
    vistos = set()
    nuevas = []
    eliminadas = 0
    for p in g.producciones:
        clave = (p.cabeza, tuple(p.cuerpo))
        if clave in vistos:
            eliminadas += 1
            continue
        vistos.add(clave)
        nuevas.append(p)
    g.producciones = nuevas
    return eliminadas


def verificar_limite(g: "Gramatica") -> None:
    if len(g.producciones) > MAX_PRODUCCIONES:
        raise GramaticaDemasiadoGrandeError(
            f"La gramática superó el límite de {MAX_PRODUCCIONES} producciones durante la "
            f"conversión (tiene {len(g.producciones)}). El crecimiento combinatorio es una "
            f"característica conocida del algoritmo de Greibach; pruebe con una gramática "
            f"más pequeña o con menos recursividad."
        )


def parsear_produccion(texto: str) -> Produccion:
    """
    Parsea una línea tipo 'A -> AB' o 'A -> BB/12/AB' (con '/' o '|' como
    separador de alternativas) en una lista de Producciones individuales.
    Nota: esta función parsea UNA alternativa; usar parsear_lineas_gramatica
    para separar por '/' o '|' primero.
    """
    cabeza, cuerpo_txt = texto.split("->")
    cabeza = cabeza.strip()
    cuerpo_txt = cuerpo_txt.strip()
    cuerpo = tokenizar_cuerpo(cuerpo_txt)
    return Produccion(cabeza, cuerpo)


def tokenizar_cuerpo(cuerpo_txt: str) -> List[str]:
    """
    Convierte un string de cuerpo de producción en lista de símbolos.
    Reconoce no terminales tipo 'X6', 'X6.1', 'A1' como un solo símbolo,
    y terminales como caracteres individuales.
    """
    if cuerpo_txt in ("ε", "epsilon", ""):
        return []
    simbolos = []
    i = 0
    n = len(cuerpo_txt)
    while i < n:
        c = cuerpo_txt[i]
        if c.isupper():
            j = i + 1
            # consumir dígitos y sufijos .n mientras sigan siendo parte del mismo símbolo
            while j < n and (cuerpo_txt[j].isdigit() or
                              (cuerpo_txt[j] == '.' and j + 1 < n and cuerpo_txt[j + 1].isdigit())):
                if cuerpo_txt[j] == '.':
                    j += 2
                else:
                    j += 1
            simbolos.append(cuerpo_txt[i:j])
            i = j
        else:
            # terminal: un solo caracter (letra minúscula o dígito)
            simbolos.append(c)
            i += 1
    return simbolos


def parsear_lineas_gramatica(variables: List[str], terminales: List[str],
                              inicial: str, lineas: List[str]) -> Gramatica:
    """
    lineas: lista de strings tipo 'S -> A1Y1/c/BY2' (separador '/' o '|')
    """
    g = Gramatica(variables=variables, terminales=terminales, inicial=inicial)
    for linea in lineas:
        cabeza, cuerpos_txt = linea.split("->")
        cabeza = cabeza.strip()
        alternativas = re.split(r'[/|]', cuerpos_txt.strip())
        for alt in alternativas:
            alt = alt.strip()
            g.agregar(cabeza, tokenizar_cuerpo(alt))
    return g
