"""
sustitucion_final.py
Paso 5 (último) del algoritmo de FNG: reemplazar toda producción cuya
cabeza de cuerpo sea una variable, por las producciones de esa variable
que ya empiecen en un símbolo terminal.

Se procesa de la ÚLTIMA variable hacia la PRIMERA (según el orden final
de gramatica.variables, que ya incluye las auxiliares .1 en su posición
correcta). Esto garantiza que, gracias al paso 4 (ya no hay Xi -> Xj α con
i > j), cuando le toca el turno a una variable v, cualquier variable Y que
aparezca al inicio de sus producciones tiene índice mayor y por lo tanto
YA fue completamente resuelta (todas sus producciones ya inician en
terminal) en una iteración anterior de este mismo paso.

Al terminar, la gramática queda en Forma Normal de Greibach: toda
producción tiene la forma A -> a A1 A2 ... An (terminal seguido de cero o
más variables).
"""

from dataclasses import dataclass, field
from typing import List
from models import Gramatica, Produccion, es_no_terminal, ExplosionDeProducciones


@dataclass
class ProduccionMarcada:
    texto: str
    estado: str  # "normal" | "eliminada" | "nueva"


@dataclass
class EventoSustitucionFinal:
    variable: str
    descripcion: str
    producciones_antes: List[ProduccionMarcada] = field(default_factory=list)
    producciones_despues: List[ProduccionMarcada] = field(default_factory=list)


def sustitucion_final(g: Gramatica, max_producciones: int = 1500):
    nueva = g.clonar()
    eventos: List[EventoSustitucionFinal] = []
    orden_proceso = list(reversed(nueva.variables))  # de la última a la primera

    for v in orden_proceso:
        cambio_en_v = False
        while True:
            if len(nueva.producciones) > max_producciones:
                raise ExplosionDeProducciones(
                    f"La sustitución final superó {max_producciones} producciones "
                    f"(explosión combinatoria); se aborta para no agotar memoria."
                )
            prods = nueva.producciones_de(v)
            malas = [p for p in prods if p.cuerpo and es_no_terminal(p.cuerpo[0])]
            if not malas:
                break

            cambio_en_v = True
            antes_marcadas = [
                ProduccionMarcada(str(p), "eliminada" if p in malas else "normal")
                for p in prods
            ]

            nuevas_prods = [p for p in prods if p not in malas]
            despues_marcadas = [ProduccionMarcada(str(p), "normal") for p in nuevas_prods]

            for p in malas:
                y = p.cuerpo[0]
                resto = p.cuerpo[1:]
                # y ya debe estar completamente resuelta (todas sus producciones
                # inician en terminal), porque se procesó antes que v.
                for q in nueva.producciones_de(y):
                    nueva_p = Produccion(v, list(q.cuerpo) + list(resto))
                    nuevas_prods.append(nueva_p)
                    despues_marcadas.append(ProduccionMarcada(str(nueva_p), "nueva"))

            for p in prods:
                nueva.eliminar(p)
            nueva.producciones.extend(nuevas_prods)

            eventos.append(EventoSustitucionFinal(
                variable=v,
                descripcion=(
                    f"{v} tiene producción(es) que inician en una variable no terminal "
                    f"({', '.join(sorted({p.cuerpo[0] for p in malas}))}). Se sustituye esa variable "
                    f"por sus producciones, que ya inician en un símbolo terminal."
                ),
                producciones_antes=antes_marcadas,
                producciones_despues=despues_marcadas,
            ))
            # se vuelve a revisar v por si la sustitución dejó otra cabeza no terminal

        if not cambio_en_v:
            eventos.append(EventoSustitucionFinal(
                variable=v,
                descripcion=f"{v} ya tiene todas sus producciones iniciando en un símbolo terminal. No requiere sustitución."
            ))

    return nueva, eventos


def validar_fng(g: Gramatica) -> List[str]:
    """Verificación final: toda producción debe ser terminal seguido de cero o más variables."""
    from models import es_terminal
    errores = []
    for p in g.producciones:
        if not p.cuerpo:
            errores.append(f"{p} -> producción vacía, no permitida en FNG.")
            continue
        if not es_terminal(p.cuerpo[0]):
            errores.append(f"{p} -> no inicia con un símbolo terminal.")
            continue
        for s in p.cuerpo[1:]:
            if not es_no_terminal(s):
                errores.append(f"{p} -> el símbolo '{s}' después del terminal inicial debe ser una variable.")
    return errores
