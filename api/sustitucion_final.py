"""
sustitucion_final.py
Paso 5: sustitución final hasta que toda producción inicie en un símbolo
terminal (Forma Normal de Greibach).
"""

from dataclasses import dataclass, field
from typing import List, Tuple
from models import Gramatica, Produccion, es_terminal, es_no_terminal, ExplosionDeProducciones

MAX_PRODUCCIONES_INTERNO = 4000
MAX_RONDAS = 60


@dataclass
class ProduccionMarcada:
    texto: str
    estado: str


@dataclass
class EventoSustitucion:
    variable: str
    descripcion: str
    producciones_antes: List[ProduccionMarcada] = field(default_factory=list)
    producciones_despues: List[ProduccionMarcada] = field(default_factory=list)


def sustitucion_final(g: Gramatica) -> Tuple[Gramatica, List[EventoSustitucion]]:
    nueva = g.clonar()
    eventos: List[EventoSustitucion] = []
    hubo_alguna = False

    orden_descendente = list(reversed(nueva.variables))

    for v in orden_descendente:
        ronda = 0
        while True:
            ronda += 1
            if ronda > MAX_RONDAS:
                raise ExplosionDeProducciones(
                    f"La sustitución final no converge para {v} tras "
                    f"{MAX_RONDAS} rondas; se aborta."
                )
            prods = nueva.producciones_de(v)
            problematicas = [
                p for p in prods
                if p.cuerpo and es_no_terminal(p.cuerpo[0])
            ]
            if not problematicas:
                break

            hubo_alguna = True
            antes_marcadas = [
                ProduccionMarcada(str(p), "eliminada" if p in problematicas else "normal")
                for p in prods
            ]

            nuevas_prods: List[Produccion] = []
            despues_marcadas: List[ProduccionMarcada] = []
            variables_sustituidas = set()
            for p in prods:
                if p not in problematicas:
                    nuevas_prods.append(p)
                    despues_marcadas.append(ProduccionMarcada(str(p), "normal"))
                    continue
                j = p.cuerpo[0]
                resto = p.cuerpo[1:]
                variables_sustituidas.add(j)
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
                    f"La sustitución final en {v} superó "
                    f"{MAX_PRODUCCIONES_INTERNO} producciones; se aborta."
                )

            eventos.append(EventoSustitucion(
                variable=v,
                descripcion=(
                    f"{v} tiene producción(es) que inician en variable "
                    f"({', '.join(sorted(variables_sustituidas))}). Se sustituyen por "
                    f"las producciones ya resueltas de esa variable, que ya inician "
                    f"en terminal."
                ),
                producciones_antes=antes_marcadas,
                producciones_despues=despues_marcadas,
            ))

    if not hubo_alguna:
        eventos.append(EventoSustitucion(
            variable="",
            descripcion="Todas las producciones ya iniciaban en un símbolo terminal."
        ))

    return nueva, eventos


def validar_fng(g: Gramatica) -> List[str]:
    errores = []
    for p in g.producciones:
        if not p.cuerpo:
            errores.append(f"{p} -> producción vacía, no permitida en FNG.")
            continue
        if not es_terminal(p.cuerpo[0]):
            errores.append(f"{p} -> no inicia con un símbolo terminal.")
    return errores