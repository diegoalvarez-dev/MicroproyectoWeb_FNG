"""
recursividad.py
Paso 2: eliminar recursividad A LA IZQUIERDA (indirecta/mutua entre 2+ variables).
Paso 3: eliminar recursividad INMEDIATA a la izquierda (X -> Xalfa).

Son dos pasos DISTINTOS y SEPARADOS (nunca se entrelazan variable por
variable): primero se resuelve TODA la recursividad indirecta de la
gramática completa (iterando hasta que no quede ninguna), y solo cuando
ya no hay ninguna, se pasa al paso 3 para resolver la recursividad
inmediata que haya quedado o que ya existiera desde el principio.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple
from models import Gramatica, Produccion, es_no_terminal, ExplosionDeProducciones

MAX_PRODUCCIONES_INTERNO = 4000
MAX_RONDAS_POR_GRUPO = 60


@dataclass
class ProduccionMarcada:
    texto: str
    estado: str  # "normal" | "eliminada" | "nueva"


@dataclass
class ProduccionExcluida:
    texto: str
    motivo: str


@dataclass
class EventoRecursividad:
    paso: str  # "recursividad_indirecta" | "recursividad_inmediata"
    variable: str
    descripcion: str
    producciones_antes: List[ProduccionMarcada] = field(default_factory=list)
    producciones_despues: List[ProduccionMarcada] = field(default_factory=list)
    producciones_excluidas: List[ProduccionExcluida] = field(default_factory=list)
    variable_nueva: str = ""
    producciones_variable_nueva: List[ProduccionMarcada] = field(default_factory=list)


def construir_grafo_cabeza(g: Gramatica) -> Dict[str, Set[str]]:
    grafo = {v: set() for v in g.variables}
    for p in g.producciones:
        if p.cuerpo and es_no_terminal(p.cuerpo[0]) and p.cuerpo[0] != p.cabeza:
            grafo[p.cabeza].add(p.cuerpo[0])
    return grafo


def _grafo_inverso(grafo: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    inv = {v: set() for v in grafo}
    for v, vecinos in grafo.items():
        for u in vecinos:
            inv.setdefault(u, set()).add(v)
    return inv


def encontrar_sccs(grafo: Dict[str, Set[str]]) -> List[Set[str]]:
    visitados = set()
    orden = []

    def dfs1(nodo):
        pila = [(nodo, iter(grafo.get(nodo, ())))]
        visitados.add(nodo)
        while pila:
            actual, it = pila[-1]
            avanzo = False
            for vecino in it:
                if vecino not in visitados:
                    visitados.add(vecino)
                    pila.append((vecino, iter(grafo.get(vecino, ()))))
                    avanzo = True
                    break
            if not avanzo:
                orden.append(actual)
                pila.pop()

    for nodo in grafo:
        if nodo not in visitados:
            dfs1(nodo)

    inv = _grafo_inverso(grafo)
    visitados2 = set()
    sccs = []
    for nodo in reversed(orden):
        if nodo in visitados2:
            continue
        componente = set()
        pila = [nodo]
        visitados2.add(nodo)
        while pila:
            actual = pila.pop()
            componente.add(actual)
            for vecino in inv.get(actual, ()):
                if vecino not in visitados2:
                    visitados2.add(vecino)
                    pila.append(vecino)
        sccs.append(componente)

    return [scc for scc in sccs if len(scc) > 1]


def eliminar_recursividad_indirecta(g: Gramatica) -> Tuple[Gramatica, List[EventoRecursividad]]:
    nueva = g.clonar()
    eventos: List[EventoRecursividad] = []
    hubo_algo_en_total = False

    pasada = 0
    while True:
        pasada += 1
        grafo = construir_grafo_cabeza(nueva)
        sccs = encontrar_sccs(grafo)
        if not sccs:
            break
        if pasada > MAX_RONDAS_POR_GRUPO:
            raise ExplosionDeProducciones(
                "La eliminación de recursividad indirecta no converge tras "
                f"{MAX_RONDAS_POR_GRUPO} pasadas; se aborta."
            )

        hubo_cambio_en_pasada = False

        for grupo in sccs:
            ronda = 0
            while True:
                ronda += 1
                if ronda > MAX_RONDAS_POR_GRUPO:
                    raise ExplosionDeProducciones(
                        f"La eliminación de recursividad indirecta no converge para "
                        f"el grupo {sorted(grupo)} tras {MAX_RONDAS_POR_GRUPO} rondas; "
                        f"se aborta."
                    )

                snapshot = {v: list(nueva.producciones_de(v)) for v in grupo}
                cambios_por_variable: Dict[str, List[Produccion]] = {}
                hubo_cambio_ronda = False

                for v in grupo:
                    nuevas_prods: List[Produccion] = []
                    antes_marcadas: List[ProduccionMarcada] = []
                    despues_marcadas: List[ProduccionMarcada] = []
                    excluidas: List[ProduccionExcluida] = []
                    cambio_en_v = False
                    variables_sustituidas: Set[str] = set()

                    for p in snapshot[v]:
                        cabeza_cuerpo0 = p.cuerpo[0] if p.cuerpo else None
                        if cabeza_cuerpo0 in grupo and cabeza_cuerpo0 != v:
                            y = cabeza_cuerpo0
                            resto = p.cuerpo[1:]
                            antes_marcadas.append(ProduccionMarcada(str(p), "eliminada"))
                            cambio_en_v = True
                            variables_sustituidas.add(y)
                            for q in snapshot[y]:
                                if q.cuerpo and q.cuerpo[0] == y:
                                    excluidas.append(ProduccionExcluida(
                                        texto=str(q),
                                        motivo=(
                                            f"no se incluye porque empieza por {y}, la misma "
                                            f"variable que se está sustituyendo: si se incluyera, "
                                            f"se volvería a introducir la recursividad que se "
                                            f"busca eliminar."
                                        ),
                                    ))
                                    continue
                                nueva_p = Produccion(v, list(q.cuerpo) + list(resto))
                                nuevas_prods.append(nueva_p)
                                despues_marcadas.append(ProduccionMarcada(str(nueva_p), "nueva"))
                        else:
                            nuevas_prods.append(p)
                            antes_marcadas.append(ProduccionMarcada(str(p), "normal"))
                            despues_marcadas.append(ProduccionMarcada(str(p), "normal"))

                    cambios_por_variable[v] = nuevas_prods
                    if cambio_en_v:
                        hubo_cambio_ronda = True
                        eventos.append(EventoRecursividad(
                            paso="recursividad_indirecta",
                            variable=v,
                            descripcion=(
                                f"{v} tiene recursividad a la izquierda con "
                                f"{', '.join(sorted(variables_sustituidas))} (grupo mutuo "
                                f"{sorted(grupo)}). Se sustituye esa variable por sus "
                                f"producciones actuales, usando las que tenía antes de esta "
                                f"ronda."
                            ),
                            producciones_antes=antes_marcadas,
                            producciones_despues=despues_marcadas,
                            producciones_excluidas=excluidas,
                        ))

                for v in grupo:
                    for p in list(nueva.producciones_de(v)):
                        nueva.eliminar(p)
                    for p in cambios_por_variable[v]:
                        nueva.producciones.append(p)

                if len(nueva.producciones) > MAX_PRODUCCIONES_INTERNO:
                    raise ExplosionDeProducciones(
                        f"La eliminación de recursividad indirecta superó "
                        f"{MAX_PRODUCCIONES_INTERNO} producciones (ronda {ronda} del grupo "
                        f"{sorted(grupo)}); se aborta para no agotar memoria."
                    )

                if hubo_cambio_ronda:
                    hubo_algo_en_total = True
                    hubo_cambio_en_pasada = True
                if not hubo_cambio_ronda:
                    break

        if not hubo_cambio_en_pasada:
            break

    if not hubo_algo_en_total:
        eventos.append(EventoRecursividad(
            paso="recursividad_indirecta",
            variable="",
            descripcion="No existe recursividad a la izquierda (indirecta) entre variables en esta gramática."
        ))

    return nueva, eventos


def eliminar_recursividad_inmediata(g: Gramatica) -> Tuple[Gramatica, List[EventoRecursividad]]:
    nueva = g.clonar()
    eventos: List[EventoRecursividad] = []
    variables_originales = list(nueva.variables)
    hubo_alguna = False

    for v in variables_originales:
        prods = nueva.producciones_de(v)
        recursivas = [p for p in prods if p.cuerpo and p.cuerpo[0] == v]
        no_recursivas = [p for p in prods if not (p.cuerpo and p.cuerpo[0] == v)]

        if not recursivas:
            continue

        hubo_alguna = True
        v_aux = f"{v}.1"
        while v_aux in nueva.variables:
            v_aux += ".1"

        antes_marcadas = [
            ProduccionMarcada(str(p), "eliminada" if p in recursivas else "normal")
            for p in prods
        ]

        for p in prods:
            nueva.eliminar(p)

        despues_marcadas: List[ProduccionMarcada] = []
        nuevas_v: List[Produccion] = []
        for p in no_recursivas:
            nuevas_v.append(Produccion(v, list(p.cuerpo)))
            despues_marcadas.append(ProduccionMarcada(f"{v} -> {''.join(p.cuerpo)}", "normal"))
        for p in no_recursivas:
            nuevo_cuerpo = list(p.cuerpo) + [v_aux]
            nuevas_v.append(Produccion(v, nuevo_cuerpo))
            despues_marcadas.append(ProduccionMarcada(f"{v} -> {''.join(nuevo_cuerpo)}", "nueva"))

        prods_aux: List[Produccion] = []
        aux_marcadas: List[ProduccionMarcada] = []
        for p in recursivas:
            alfa = p.cuerpo[1:]
            prods_aux.append(Produccion(v_aux, list(alfa)))
            aux_marcadas.append(ProduccionMarcada(f"{v_aux} -> {''.join(alfa)}", "nueva"))
        for p in recursivas:
            alfa = p.cuerpo[1:]
            nuevo_cuerpo = list(alfa) + [v_aux]
            prods_aux.append(Produccion(v_aux, nuevo_cuerpo))
            aux_marcadas.append(ProduccionMarcada(f"{v_aux} -> {''.join(nuevo_cuerpo)}", "nueva"))

        nueva.producciones.extend(nuevas_v)
        nueva.producciones.extend(prods_aux)
        if len(nueva.producciones) > MAX_PRODUCCIONES_INTERNO:
            raise ExplosionDeProducciones(
                f"La eliminación de recursividad inmediata en {v} superó "
                f"{MAX_PRODUCCIONES_INTERNO} producciones; se aborta para no agotar memoria."
            )

        idx = nueva.variables.index(v)
        nueva.variables.insert(idx + 1, v_aux)

        eventos.append(EventoRecursividad(
            paso="recursividad_inmediata",
            variable=v,
            descripcion=(
                f"{v} tiene recursividad inmediata a la izquierda ({v} -> {v}α). "
                f"Se separan las producciones recursivas de las no recursivas y se crea "
                f"la variable auxiliar {v_aux}."
            ),
            producciones_antes=antes_marcadas,
            producciones_despues=despues_marcadas,
            variable_nueva=v_aux,
            producciones_variable_nueva=aux_marcadas,
        ))

    if not hubo_alguna:
        eventos.append(EventoRecursividad(
            paso="recursividad_inmediata",
            variable="",
            descripcion="No existe recursividad inmediata a la izquierda en esta gramática."
        ))

    return nueva, eventos