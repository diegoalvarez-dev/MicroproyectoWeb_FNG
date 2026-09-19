"""
renombrador.py
Paso 1 del algoritmo de FNG: ordenar las variables (símbolo inicial primero)
y renombrarlas como X1, X2, ..., Xn, reescribiendo todas las producciones
con los nuevos nombres.

Diseño de la ordenación:
- Por defecto se usa el orden de declaración del usuario, moviendo el
  símbolo inicial S al frente (S siempre es X1).
- El usuario puede editar manualmente este orden antes de continuar
  (el software se lo debe permitir, tal como se hace en las diapositivas,
  donde la ingeniera reubica una variable para reducir los casos
  Xi -> Xj·α con i > j que habrá que resolver en el paso 4).
- Cualquier violación de orden que quede pendiente después del renombrado
  NO se corrige aquí: la corrige el módulo orden_indices.py (paso 4),
  tal como indica el enunciado y la guía.

Esto hace que el algoritmo sea general (RNF03: no depende de un orden
"mágico" precalculado para casos específicos) y a la vez reproduce el
comportamiento de la profesora, quien reordena manualmente antes de
enumerar.
"""

from dataclasses import dataclass, field
from typing import List, Dict
from models import Gramatica, Produccion


@dataclass
class EventoRenombrado:
    paso: str = "renombrado"
    descripcion: str = ""
    mapa: Dict[str, str] = field(default_factory=dict)
    gramatica_resultante: str = ""


def ordenar_variables(g: Gramatica, orden_manual: List[str] = None) -> List[str]:
    """
    Devuelve el orden final de variables originales, con el símbolo inicial
    siempre de primero.

    orden_manual: si se provee, se usa tal cual (validando que sea una
    permutación de g.variables y que empiece en g.inicial). Si no se
    provee, se usa el orden de declaración con el inicial movido al frente.
    """
    if orden_manual is not None:
        if set(orden_manual) != set(g.variables):
            raise ValueError(
                "El orden manual debe contener exactamente las mismas variables "
                "declaradas en la gramática."
            )
        if orden_manual[0] != g.inicial:
            raise ValueError("El símbolo inicial debe quedar de primero en el orden.")
        return list(orden_manual)

    resto = [v for v in g.variables if v != g.inicial]
    return [g.inicial] + resto


def renombrar_a_greibach(g: Gramatica, orden_manual: List[str] = None):
    """
    Ejecuta el paso 1: ordena y renombra.
    Devuelve (gramatica_nueva, evento_historial).
    """
    orden = ordenar_variables(g, orden_manual)
    mapa = {original: f"X{i+1}" for i, original in enumerate(orden)}

    nueva = Gramatica(
        variables=[mapa[v] for v in orden],
        terminales=list(g.terminales),
        inicial=mapa[g.inicial],
    )

    for p in g.producciones:
        nueva_cabeza = mapa[p.cabeza]
        nuevo_cuerpo = [mapa.get(s, s) for s in p.cuerpo]  # terminales quedan igual
        nueva.agregar(nueva_cabeza, nuevo_cuerpo)

    evento = EventoRenombrado(
        descripcion=(
            "Se ordenan las variables dejando el símbolo inicial de primero, "
            "y se renombra cada una como X1, X2, ..., Xn siguiendo ese orden."
        ),
        mapa=mapa,
        gramatica_resultante=nueva.texto(),
    )
    return nueva, evento
