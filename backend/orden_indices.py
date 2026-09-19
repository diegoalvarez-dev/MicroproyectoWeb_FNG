"""
orden_indices.py
Paso 4 del algoritmo de FNG: eliminar todas las producciones de la forma
Xi -> Xj α donde el índice de Xi es MAYOR al índice de Xj (viola el orden
que se fijó en el paso 1 de renombrado/ordenamiento).

Se reemplaza Xj por todas sus producciones ACTUALES (no hace falta usar
"originales" como en la recursividad indirecta, porque aquí no hay
mutualidad: el orden garantiza que Xj, al tener índice menor, ya fue
tratado o no depende de Xi, así que no hay ciclos que resolver de forma
simultánea). Se repite hasta que ya ninguna producción de ninguna variable
viole el orden.

El "índice" de cada variable se toma de su posición en la lista
gramatica.variables (que ya incluye, en el orden correcto, las variables
auxiliares tipo X6.1 insertadas justo después de su variable base en el
paso de recursividad inmediata).
"""

from dataclasses import dataclass, field
from typing import List
from models import Gramatica, Produccion, es_no_terminal, ExplosionDeProducciones

MAX_PRODUCCIONES_INTERNO = 1500


@dataclass
class ProduccionMarcada:
    texto: str
    estado: str  # "normal" | "eliminada" | "nueva"


@dataclass
class EventoOrden:
    variable: str
    descripcion: str
    producciones_antes: List[ProduccionMarcada] = field(default_factory=list)
    producciones_despues: List[ProduccionMarcada] = field(default_factory=list)


def eliminar_orden_incorrecto(g: Gramatica):
    nueva = g.clonar()
    eventos: List[EventoOrden] = []
    orden_variables = list(nueva.variables)

    def idx(v: str) -> int:
        return orden_variables.index(v)

    hubo_alguna = False
    cambiado = True
    while cambiado:
        cambiado = False
        for v in orden_variables:
            prods = nueva.producciones_de(v)
            malas = [
                p for p in prods
                if p.cuerpo and es_no_terminal(p.cuerpo[0]) and idx(p.cuerpo[0]) < idx(v)
            ]
            if not malas:
                continue

            hubo_alguna = True
            cambiado = True

            antes_marcadas = [
                ProduccionMarcada(str(p), "eliminada" if p in malas else "normal")
                for p in prods
            ]

            nuevas_prods = [p for p in prods if p not in malas]
            despues_marcadas = [ProduccionMarcada(str(p), "normal") for p in nuevas_prods]

            for p in malas:
                y = p.cuerpo[0]
                resto = p.cuerpo[1:]
                for q in nueva.producciones_de(y):
                    nueva_p = Produccion(v, list(q.cuerpo) + list(resto))
                    nuevas_prods.append(nueva_p)
                    despues_marcadas.append(ProduccionMarcada(str(nueva_p), "nueva"))

            for p in prods:
                nueva.eliminar(p)
            nueva.producciones.extend(nuevas_prods)

            if len(nueva.producciones) > MAX_PRODUCCIONES_INTERNO:
                raise ExplosionDeProducciones(
                    f"La eliminación de orden incorrecto (Xi->Xj\u03b1, i>j) superó "
                    f"{MAX_PRODUCCIONES_INTERNO} producciones al procesar {v}; se aborta."
                )

            eventos.append(EventoOrden(
                variable=v,
                descripcion=(
                    f"{v} tiene producción(es) que inician con una variable de índice menor "
                    f"({', '.join(sorted({p.cuerpo[0] for p in malas}))}), lo cual viola el orden "
                    f"establecido. Se sustituye esa variable por todas sus producciones actuales."
                ),
                producciones_antes=antes_marcadas,
                producciones_despues=despues_marcadas,
            ))
            # se reinicia el recorrido de variables tras cada cambio para
            # volver a evaluar por si el cambio introdujo nuevas violaciones
            break

    if not hubo_alguna:
        eventos.append(EventoOrden(
            variable="",
            descripcion="No existen producciones de la forma Xi -> Xj α con i > j; el orden ya es correcto."
        ))

    return nueva, eventos
