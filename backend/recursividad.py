"""
recursividad.py
Paso 2: eliminar recursividad indirecta a la izquierda (mutua entre 2+ variables).
Paso 3: eliminar recursividad inmediata a la izquierda (X -> Xα).

Diseño general (no hardcodeado a un ejemplo):

1. Se construye un grafo dirigido "de cabeza": hay una arista Xi -> Xj si
   existe una producción Xi -> Xj α (Xj es no terminal y aparece de primero).
2. Se buscan las componentes fuertemente conexas (SCC) de tamaño > 1 de ese
   grafo: cada una representa un grupo de variables con recursividad
   indirecta mutua entre sí (Xi depende de Xj y Xj depende de Xi, directa
   o transitivamente).
3. Para cada grupo, se hace una sustitución simultánea: cada producción de
   una variable V que empiece con otra variable Y del mismo grupo (Y != V)
   se reemplaza por las producciones ORIGINALES de Y (las que tenía ANTES
   de esta ronda), EXCLUYENDO las que a su vez empiecen con Y (para no
   reintroducir la recursividad que se busca eliminar). Se usa el estado
   "antes de la ronda" para todas las variables del grupo a la vez -tal
   como se explicó-, y se repite el proceso hasta que ninguna producción
   de ninguna variable del grupo empiece con OTRA variable del mismo grupo
   (las que empiezan con la propia variable se dejan, pues son
   recursividad inmediata y se resuelven en el paso siguiente).
4. Ya sin recursividad indirecta, se recorre cada variable de la gramática
   y se le aplica la eliminación estándar de recursividad inmediata a la
   izquierda (creación de la variable auxiliar V.1).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set
from models import Gramatica, Produccion, es_no_terminal, ExplosionDeProducciones

# Límite de seguridad interno: si en algún momento intermedio la gramática
# supera este número de producciones, se aborta la conversión en vez de
# seguir multiplicando producciones hasta agotar la memoria del proceso.
MAX_PRODUCCIONES_INTERNO = 1500


@dataclass
class ProduccionMarcada:
    texto: str
    estado: str  # "normal" | "eliminada" | "nueva"


@dataclass
class EventoRecursividad:
    paso: str                      # "recursividad_indirecta" | "recursividad_inmediata"
    variable: str
    descripcion: str
    producciones_antes: List[ProduccionMarcada] = field(default_factory=list)
    producciones_despues: List[ProduccionMarcada] = field(default_factory=list)
    variable_nueva: str = ""
    producciones_variable_nueva: List[ProduccionMarcada] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Grafo de cabeza y búsqueda de componentes fuertemente conexas (Kosaraju)
# ---------------------------------------------------------------------------

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
    """Kosaraju. Devuelve solo las SCC con más de una variable (recursividad indirecta real)."""
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


# ---------------------------------------------------------------------------
# Paso 2: recursividad indirecta
# ---------------------------------------------------------------------------

def eliminar_recursividad_indirecta(g: Gramatica):
    nueva = g.clonar()
    eventos: List[EventoRecursividad] = []

    grafo = construir_grafo_cabeza(nueva)
    sccs = encontrar_sccs(grafo)

    if not sccs:
        eventos.append(EventoRecursividad(
            paso="recursividad_indirecta",
            variable="",
            descripcion="No existe recursividad indirecta (a la izquierda) entre variables en esta gramática."
        ))
        return nueva, eventos

    for grupo in sccs:
        estable = False
        ronda = 0
        while not estable:
            ronda += 1
            snapshot = {v: list(nueva.producciones_de(v)) for v in grupo}
            cambios_por_variable: Dict[str, List[Produccion]] = {}
            hubo_cambio = False

            for v in grupo:
                nuevas_prods = []
                antes_marcadas = []
                despues_marcadas = []
                cambio_en_v = False
                for p in snapshot[v]:
                    cabeza_cuerpo0 = p.cuerpo[0] if p.cuerpo else None
                    if cabeza_cuerpo0 in grupo and cabeza_cuerpo0 != v:
                        # Sustituir por las producciones ORIGINALES (snapshot) de esa variable,
                        # excluyendo las que a su vez inician en sí misma.
                        y = cabeza_cuerpo0
                        resto = p.cuerpo[1:]
                        antes_marcadas.append(ProduccionMarcada(str(p), "eliminada"))
                        cambio_en_v = True
                        for q in snapshot[y]:
                            if q.cuerpo and q.cuerpo[0] == y:
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
                    hubo_cambio = True
                    eventos.append(EventoRecursividad(
                        paso="recursividad_indirecta",
                        variable=v,
                        descripcion=(
                            f"{v} tiene recursividad indirecta a la izquierda con otra(s) variable(s) "
                            f"del grupo {sorted(grupo)}. Se sustituyen las producciones de {v} que "
                            f"inician en esas variables, usando las producciones originales de la ronda "
                            f"(excluyendo las que a su vez inician en sí mismas)."
                        ),
                        producciones_antes=antes_marcadas,
                        producciones_despues=despues_marcadas,
                    ))

            # commit simultáneo
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
            if ronda > 50:
                raise ExplosionDeProducciones(
                    f"La eliminación de recursividad indirecta no converge tras 50 rondas "
                    f"para el grupo {sorted(grupo)}; se aborta."
                )

            estable = not hubo_cambio

    return nueva, eventos


# ---------------------------------------------------------------------------
# Paso 3: recursividad inmediata a la izquierda
# ---------------------------------------------------------------------------

def eliminar_recursividad_inmediata(g: Gramatica):
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

        antes_marcadas = []
        for p in prods:
            estado = "eliminada" if p in recursivas else "normal"
            antes_marcadas.append(ProduccionMarcada(str(p), estado))

        # quitar producciones viejas de v
        for p in prods:
            nueva.eliminar(p)

        despues_marcadas = []
        nuevas_v = []
        for p in no_recursivas:
            nuevas_v.append(Produccion(v, list(p.cuerpo)))
            despues_marcadas.append(ProduccionMarcada(f"{v} -> {''.join(p.cuerpo)}", "normal"))
        for p in no_recursivas:
            nuevo_cuerpo = list(p.cuerpo) + [v_aux]
            nuevas_v.append(Produccion(v, nuevo_cuerpo))
            despues_marcadas.append(ProduccionMarcada(f"{v} -> {''.join(nuevo_cuerpo)}", "nueva"))

        prods_aux = []
        aux_marcadas = []
        for p in recursivas:
            alfa = p.cuerpo[1:]  # se quita la v inicial
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
        # se inserta la variable auxiliar justo después de v en el orden de variables
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
