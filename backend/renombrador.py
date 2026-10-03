"""
renombrador.py
Paso 1: renombrado de variables a notación Greibach (X1..Xn), con el
símbolo inicial siempre como X1. NO se transforma el cuerpo de ninguna
producción más allá de sustituir los nombres de variable: las formas
VntVnt / VtVt / VtVnt / VntVt / Vt se conservan tal cual, solo cambian
los nombres.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from models import Gramatica, Produccion, es_no_terminal


@dataclass
class EventoRenombrado:
    descripcion: str
    mapa: Dict[str, str] = field(default_factory=dict)


def renombrar_a_greibach(g: Gramatica, orden_manual: Optional[List[str]] = None):
    if orden_manual:
        orden = list(orden_manual)
    else:
        resto = [v for v in g.variables if v != g.inicial]
        orden = [g.inicial] + resto

    mapa = {v: f"X{i+1}" for i, v in enumerate(orden)}

    nuevas_variables = [mapa[v] for v in orden]
    nuevas_producciones: List[Produccion] = []
    for p in g.producciones:
        nueva_cabeza = mapa[p.cabeza]
        nuevo_cuerpo = [mapa[s] if es_no_terminal(s) else s for s in p.cuerpo]
        nuevas_producciones.append(Produccion(nueva_cabeza, nuevo_cuerpo))

    g2 = Gramatica(
        variables=nuevas_variables,
        terminales=list(g.terminales),
        inicial=mapa[g.inicial],
        producciones=nuevas_producciones,
    )

    descripcion_partes = [f"{v} -> {mapa[v]}" for v in orden]
    evento = EventoRenombrado(
        descripcion=(
            "Se renombran las variables a notación Greibach (X1..Xn), dejando "
            "el símbolo inicial como X1: " + ", ".join(descripcion_partes) + ". "
            "El cuerpo de las producciones no se modifica, solo se sustituyen "
            "los nombres de las variables."
        ),
        mapa=mapa,
    )
    return g2, evento