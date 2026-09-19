"""
validador_fnc.py
Valida que una gramática de entrada esté en Forma Normal de Chomsky (FNC),
según las combinaciones de cuerpo aceptadas para este proyecto:

    VntVnt, VtVt, VtVnt, VntVt, Vt

(No se aceptan producciones unitarias tipo A->B, ni producción vacía A->ε,
porque se asume que la gramática ya fue depurada previamente).

Devuelve un resultado estructurado (válido/inválido + lista de errores
detallados) pensado para mostrarse directamente en el front como parte
de RNF11 (mensajes de error comprensibles).
"""

from dataclasses import dataclass, field
from typing import List
from models import Gramatica, Produccion, es_terminal, es_no_terminal

FORMAS_VALIDAS = {"VntVnt", "VtVt", "VtVnt", "VntVt", "Vt"}


@dataclass
class ErrorValidacion:
    codigo: str
    mensaje: str
    produccion: str = ""


@dataclass
class ResultadoValidacion:
    valido: bool
    errores: List[ErrorValidacion] = field(default_factory=list)

    def agregar(self, codigo: str, mensaje: str, produccion: str = ""):
        self.valido = False
        self.errores.append(ErrorValidacion(codigo, mensaje, produccion))


def validar_fnc(g: Gramatica) -> ResultadoValidacion:
    resultado = ResultadoValidacion(valido=True)

    # 1. Debe existir al menos una variable
    if not g.variables:
        resultado.agregar("VAL001", "La gramática debe declarar al menos una variable (no terminal).")

    # 2. Debe existir al menos un terminal
    if not g.terminales:
        resultado.agregar("VAL002", "La gramática debe declarar al menos un símbolo terminal.")

    # 3. Debe existir símbolo inicial
    if not g.inicial:
        resultado.agregar("VAL003", "Debe indicarse un símbolo inicial.")
    elif g.inicial not in g.variables:
        resultado.agregar(
            "VAL004",
            f"El símbolo inicial '{g.inicial}' no pertenece al conjunto de variables declaradas."
        )

    # 4. Todo símbolo usado en las producciones debe haber sido declarado
    declarados = set(g.variables) | set(g.terminales)
    for p in g.producciones:
        if p.cabeza not in g.variables:
            resultado.agregar(
                "VAL005",
                f"La variable '{p.cabeza}' aparece como cabeza de producción pero no fue declarada.",
                str(p)
            )
        for simbolo in p.cuerpo:
            if simbolo not in declarados:
                resultado.agregar(
                    "VAL006",
                    f"El símbolo '{simbolo}' usado en '{p}' no fue declarado ni como variable ni como terminal.",
                    str(p)
                )

    # 5. Cada producción debe cumplir con una de las 5 formas válidas de FNC
    for p in g.producciones:
        if p.es_vacia():
            resultado.agregar(
                "VAL007",
                f"La producción '{p.cabeza} -> ε' no está permitida: la gramática de entrada "
                f"no debe tener producciones vacías (se asume ya depurada).",
                str(p)
            )
            continue

        if len(p.cuerpo) > 2:
            resultado.agregar(
                "VAL008",
                f"La producción '{p}' tiene {len(p.cuerpo)} símbolos en el cuerpo. "
                f"En FNC el cuerpo no puede superar 2 símbolos.",
                str(p)
            )
            continue

        if len(p.cuerpo) == 1:
            simbolo = p.cuerpo[0]
            if es_no_terminal(simbolo):
                resultado.agregar(
                    "VAL009",
                    f"La producción '{p}' es una producción unitaria (variable -> variable). "
                    f"No está permitida: debe eliminarse en la fase de depuración de FNC.",
                    str(p)
                )
                continue
            if not es_terminal(simbolo):
                resultado.agregar(
                    "VAL010",
                    f"El símbolo '{simbolo}' en '{p}' no es reconocible como terminal ni no terminal.",
                    str(p)
                )
                continue

        patron = p.patron_forma()
        if patron not in FORMAS_VALIDAS:
            resultado.agregar(
                "VAL011",
                f"La producción '{p}' tiene la forma '{patron}', que no está permitida en FNC "
                f"para este proyecto. Formas válidas: {', '.join(sorted(FORMAS_VALIDAS))}.",
                str(p)
            )

    return resultado
