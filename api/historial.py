"""
historial.py
Orquesta el proceso completo FNC -> FNG en 5 pasos y serializa cada paso
(con su gramática resultante y sus eventos) a un dict listo para JSON.
"""

from dataclasses import asdict
from typing import List, Optional, Set, Tuple, Dict

from models import Gramatica, ExplosionDeProducciones
from renombrador import renombrar_a_greibach
from recursividad import eliminar_recursividad_indirecta, eliminar_recursividad_inmediata
from orden_indices import eliminar_orden_indices
from sustitucion_final import sustitucion_final, validar_fng

MAX_PRODUCCIONES = 6000

def _verificar_limite(g: Gramatica, nombre_paso: str) -> None:
    if len(g.producciones) > MAX_PRODUCCIONES:
        raise ExplosionDeProducciones(
            f"Tras el paso '{nombre_paso}' la gramática superó "
            f"{MAX_PRODUCCIONES} producciones; se aborta la conversión "
            f"para no agotar memoria. Esto puede pasar con gramáticas que "
            f"tienen demasiadas variables mutuamente recursivas a la vez."
        )


def _tuplas(g: Gramatica) -> Set[Tuple[str, tuple]]:
    return {(p.cabeza, tuple(p.cuerpo)) for p in g.producciones}


def _marcar_por_variable(g: Gramatica, anteriores: Set[Tuple[str, tuple]]) -> Dict[str, list]:
    """Agrupa las producciones de g por variable (en el orden de g.variables)
    y marca cada alternativa como 'nueva' (si esa combinación exacta
    cabeza+cuerpo no existía en la gramática anterior) o 'normal'."""
    resultado: Dict[str, list] = {}
    for v in g.variables:
        alternativas = []
        for p in g.producciones_de(v):
            clave = (p.cabeza, tuple(p.cuerpo))
            estado = "normal" if clave in anteriores else "nueva"
            alternativas.append({
                "cuerpo": ''.join(p.cuerpo) if p.cuerpo else 'ε',
                "estado": estado,
            })
        if alternativas:
            resultado[v] = alternativas
    return resultado


def convertir_a_fng(g: Gramatica, orden_manual: Optional[List[str]] = None) -> dict:
    resultado = {"exito": True, "error_tipo": None, "error": None, "pasos": []}

    # Paso 1: renombrado (solo nombres, no se tocan los cuerpos). No hay
    # producciones "nuevas" de verdad aquí, solo variables renombradas,
    # así que todas se marcan como "normal".
    g1, evento1 = renombrar_a_greibach(g, orden_manual)
    _verificar_limite(g1, "renombrado")
    tuplas_g1 = _tuplas(g1)
    resultado["pasos"].append({
        "numero": 1,
        "clave": "renombrado",
        "titulo": "Renombrado de variables a notación Greibach",
        "descripcion_general": evento1.descripcion,
        "mapa_equivalencia": evento1.mapa,
        "variables": g1.variables,
        "inicial": g1.inicial,
        "terminales": g1.terminales,
        "gramatica_resultante": g1.texto(),
        "producciones_por_variable": _marcar_por_variable(g1, tuplas_g1),
        "eventos": [],
    })

    # Paso 2: recursividad indirecta (a la izquierda, entre 2+ variables)
    g2, eventos2 = eliminar_recursividad_indirecta(g1)
    _verificar_limite(g2, "recursividad indirecta")
    tuplas_g2 = _tuplas(g2)
    resultado["pasos"].append({
        "numero": 2,
        "clave": "recursividad_indirecta",
        "titulo": "Eliminación de recursividad a la izquierda (indirecta)",
        "descripcion_general": (
            "Se eliminan los ciclos de recursividad mutua entre dos o más "
            "variables (Xi depende de Xj y Xj depende de Xi, directa o "
            "transitivamente), sustituyendo simultáneamente por rondas."
        ),
        "variables": g2.variables,
        "inicial": g2.inicial,
        "terminales": g2.terminales,
        "gramatica_resultante": g2.texto(),
        "producciones_por_variable": _marcar_por_variable(g2, tuplas_g1),
        "eventos": [asdict(e) for e in eventos2],
    })

    # Paso 3: recursividad inmediata (X -> Xalfa), paso separado y posterior
    g3, eventos3 = eliminar_recursividad_inmediata(g2)
    _verificar_limite(g3, "recursividad inmediata")
    tuplas_g3 = _tuplas(g3)
    resultado["pasos"].append({
        "numero": 3,
        "clave": "recursividad_inmediata",
        "titulo": "Eliminación de recursividad inmediata a la izquierda",
        "descripcion_general": (
            "Se eliminan las producciones X -> Xα que quedaron (o que ya "
            "existían), separando las no recursivas de las recursivas y "
            "creando la variable auxiliar X.1 correspondiente."
        ),
        "variables": g3.variables,
        "inicial": g3.inicial,
        "terminales": g3.terminales,
        "gramatica_resultante": g3.texto(),
        "producciones_por_variable": _marcar_por_variable(g3, tuplas_g2),
        "eventos": [asdict(e) for e in eventos3],
    })

    # Paso 4: orden de índices (Xi -> Xjα con i > j)
    g4, eventos4 = eliminar_orden_indices(g3)
    _verificar_limite(g4, "orden de índices")
    tuplas_g4 = _tuplas(g4)
    resultado["pasos"].append({
        "numero": 4,
        "clave": "orden_indices",
        "titulo": "Eliminación de producciones Xi -> Xjα con i > j",
        "descripcion_general": (
            "Se sustituyen las producciones que inician en una variable de "
            "índice menor al de la cabeza, usando las producciones actuales "
            "de esa variable, hasta que todas respeten el orden Xi -> Xjα "
            "con j > i (o inicien ya en terminal)."
        ),
        "variables": g4.variables,
        "inicial": g4.inicial,
        "terminales": g4.terminales,
        "gramatica_resultante": g4.texto(),
        "producciones_por_variable": _marcar_por_variable(g4, tuplas_g3),
        "eventos": [asdict(e) for e in eventos4],
    })

    # Paso 5: sustitución final hasta Forma Normal de Greibach
    g5, eventos5 = sustitucion_final(g4)
    _verificar_limite(g5, "sustitución final")
    errores_fng = validar_fng(g5)
    resultado["pasos"].append({
        "numero": 5,
        "clave": "sustitucion_final",
        "titulo": "Sustitución final a Forma Normal de Greibach",
        "descripcion_general": (
            "Se procesan las variables de la última a la primera, "
            "sustituyendo cualquier producción que aún inicie en variable "
            "por las producciones ya resueltas de esa variable, hasta que "
            "toda producción inicie en un símbolo terminal."
        ),
        "variables": g5.variables,
        "inicial": g5.inicial,
        "terminales": g5.terminales,
        "gramatica_resultante": g5.texto(),
        "producciones_por_variable": _marcar_por_variable(g5, tuplas_g4),
        "eventos": [asdict(e) for e in eventos5],
    })

    resultado["gramatica_final"] = g5.texto()
    resultado["validacion_fng"] = errores_fng
    resultado["exito"] = len(errores_fng) == 0

    return resultado