"""
orden_indices.py
Paso 4: eliminar producciones Xi -> Xj·alfa donde i > j. Se sustituye Xj
por sus producciones actuales y se repite hasta estabilizar.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from models import Gramatica, Produccion, es_no_terminal, ExplosionDeProducciones

MAX_PRODUCCIONES_INTERNO = 4000
MAX_RONDAS = 60


@dataclass
class ProduccionMarcada:
    texto: str
    estado: str


@dataclass
class EventoOrden:
    variable: str
    descripcion: str
    producciones_antes: List[ProduccionMarcada] = field(default_factory=list)
    producciones_despues: List[ProduccionMarcada] = field(default_factory=list)


def _indice(v: str) -> int:
    num = ""
    for ch in v[1:]:
        if ch.isdigit():
            num += ch
        else:
            break
    return int(num) if num else 0


def eliminar_orden_indices(g: Gramatica) -> Tuple[Gramatica, List[EventoOrden]]:
    nueva = g.clonar()
    eventos: List[EventoOrden] = []
    indices = {v: _indice(v) for v in nueva.variables}

    hubo_alguna = False
    ronda = 0
    while True:
        ronda += 1
        if ronda > MAX_RONDAS:
            raise ExplosionDeProducciones(
                f"La eliminación de Xi -> Xj con i > j no converge tras "
                f"{MAX_RONDAS} rondas; se aborta."
            )
        hubo_cambio = False

        for v in list(nueva.variables):
            prods = nueva.producciones_de(v)
            problematicas = [
                p for p in prods
                if p.cuerpo and es_no_terminal(p.cuerpo[0])
                and p.cuerpo[0] in indices
                and indices[p.cuerpo[0]] < indices.get(v, 0)
                and p.cuerpo[0] != v
            ]
            if not problematicas:
                continue

            hubo_cambio = True
            hubo_alguna = True
            antes_marcadas = [
                ProduccionMarcada(str(p), "eliminada" if p in problematicas else "normal")
                for p in prods
            ]

            nuevas_prods: List[Produccion] = []
            despues_marcadas: List[ProduccionMarcada] = []
            for p in prods:
                if p not in problematicas:
                    nuevas_prods.append(p)
                    despues_marcadas.append(ProduccionMarcada(str(p), "normal"))
                    continue
                j = p.cuerpo[0]
                resto = p.cuerpo[1:]
                for q in nueva.producciones_de(j):
                    nuevo_cuerpo = list(q.cuerpo) + list(resto)
                    nueva_p = Produccion(v, nuevo_cuerpo)
                    nuevas_prods.append(nueva_p)
                    despues_marcadas.append(ProduccionMarcada(str(nueva_p), "nueva"))

            for p in prods:
                nueva.eliminar(p)
            nueva.producciones.extend(nuevas_prods)

            if len(nueva.producciones) > MAX_PRODUCCIONES_INTERNO:
                raise ExplosionDeProducciones(
                    f"La eliminación de Xi -> Xj (i > j) superó "
                    f"{MAX_PRODUCCIONES_INTERNO} producciones; se aborta."
                )

            eventos.append(EventoOrden(
                variable=v,
                descripcion=(
                    f"{v} tiene producción(es) que inician en una variable de "
                    f"índice menor ({', '.join(sorted({p.cuerpo[0] for p in problematicas}))}). "
                    f"Se sustituyen por las producciones actuales de esa variable."
                ),
                producciones_antes=antes_marcadas,
                producciones_despues=despues_marcadas,
            ))

        if not hubo_cambio:
            break

    if not hubo_alguna:
        eventos.append(EventoOrden(
            variable="",
            descripcion="No existen producciones Xi -> Xj·α con índice j menor que i."
        ))

    return nueva, eventos