"""
models.py
Estructuras de datos base para representar una Gramática Libre de Contexto (GLC)
y sus producciones, usadas en todo el pipeline de conversión FNC -> FNG.

Convenciones adoptadas para este proyecto:
- No terminal (Vnt): letra mayúscula, opcionalmente seguida de un número o
  sufijo como ".1" (ej: A, B, X6, X6.1).
- Terminal (Vt): letra minúscula o dígito (ej: a, b, 1, 2).
- En FNC de entrada solo se aceptan estas combinaciones de cuerpo de producción:
    VntVnt, VtVt, VtVnt, VntVt, Vt
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import re


class ExplosionDeProducciones(Exception):
    """Se lanza cuando la conversión crece más allá de un límite de seguridad
    razonable, para abortar de forma controlada en vez de agotar memoria."""
    pass


TERMINAL_RE = re.compile(r'^[a-z0-9]$')
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
    cabeza: str
    cuerpo: List[str]

    def __str__(self) -> str:
        return f"{self.cabeza} -> {''.join(self.cuerpo)}"

    def es_vacia(self) -> bool:
        return len(self.cuerpo) == 0 or self.cuerpo == ['ε'] or self.cuerpo == ['epsilon']

    def clonar(self) -> "Produccion":
        return Produccion(self.cabeza, list(self.cuerpo))

    def patron_forma(self) -> str:
        return "".join(tipo_simbolo(s) for s in self.cuerpo)


@dataclass
class Gramatica:
    variables: List[str]
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
        lineas = []
        for v in self.variables:
            cuerpos = [''.join(p.cuerpo) if p.cuerpo else 'ε' for p in self.producciones_de(v)]
            if cuerpos:
                lineas.append(f"{v} -> " + " | ".join(cuerpos))
        return "\n".join(lineas)


def parsear_produccion(texto: str, variables: List[str] = None, terminales: List[str] = None) -> Produccion:
    cabeza, cuerpo_txt = texto.split("->")
    cabeza = cabeza.strip()
    cuerpo_txt = cuerpo_txt.strip()
    cuerpo = tokenizar_cuerpo(cuerpo_txt, variables or [], terminales or [])
    return Produccion(cabeza, cuerpo)


def tokenizar_cuerpo(cuerpo_txt: str, variables: List[str] = None, terminales: List[str] = None) -> List[str]:
    """
    Usa las variables y terminales YA DECLARADOS para decidir dónde corta
    cada símbolo (coincidencia más larga primero). Necesario porque "A2"
    es AMBIGUO sin contexto: podría ser la variable "A2", o la variable
    "A" seguida del terminal "2".
    """
    if cuerpo_txt in ("ε", "epsilon", ""):
        return []
    if variables or terminales:
        return _tokenizar_con_alfabeto(cuerpo_txt, variables or [], terminales or [])
    return _tokenizar_heuristico(cuerpo_txt)


def _tokenizar_con_alfabeto(cuerpo_txt: str, variables: List[str], terminales: List[str]) -> List[str]:
    candidatos = sorted(set(variables) | set(terminales), key=len, reverse=True)
    simbolos = []
    i = 0
    n = len(cuerpo_txt)
    while i < n:
        encontrado = None
        for simbolo in candidatos:
            if simbolo and cuerpo_txt.startswith(simbolo, i):
                encontrado = simbolo
                break
        if encontrado is None:
            resto = cuerpo_txt[i:i + 12]
            raise ValueError(
                f"No se pudo interpretar '{resto}...' dentro de '{cuerpo_txt}': el símbolo en esa "
                f"posición no coincide con ninguna variable ni terminal declarado. Revisa que todos "
                f"los símbolos de las producciones estén en la lista de Variables o de Terminales."
            )
        simbolos.append(encontrado)
        i += len(encontrado)
    return simbolos


def _tokenizar_heuristico(cuerpo_txt: str) -> List[str]:
    """Respaldo sin alfabeto declarado (uso interno del propio algoritmo)."""
    simbolos = []
    i = 0
    n = len(cuerpo_txt)
    while i < n:
        c = cuerpo_txt[i]
        if c.isupper():
            j = i + 1
            while j < n and (cuerpo_txt[j].isdigit() or
                              (cuerpo_txt[j] == '.' and j + 1 < n and cuerpo_txt[j + 1].isdigit())):
                j += 2 if cuerpo_txt[j] == '.' else 1
            simbolos.append(cuerpo_txt[i:j])
            i = j
        else:
            simbolos.append(c)
            i += 1
    return simbolos


def parsear_lineas_gramatica(variables: List[str], terminales: List[str],
                              inicial: str, lineas: List[str]) -> Gramatica:
    g = Gramatica(variables=variables, terminales=terminales, inicial=inicial)
    for linea in lineas:
        cabeza, cuerpos_txt = linea.split("->")
        cabeza = cabeza.strip()
        alternativas = re.split(r'[/|]', cuerpos_txt.strip())
        for alt in alternativas:
            alt = alt.strip()
            g.agregar(cabeza, tokenizar_cuerpo(alt, variables, terminales))
    return g