"""
historial.py
Orquesta el proceso completo FNC -> FNG en 5 pasos y serializa cada paso
a un dict listo para JSON.
"""

from dataclasses import asdict
from typing import List, Optional

from models import Gramatica, ExplosionDeProducciones
from renombrador import renombrar_a_greibach
from recursividad import eliminar_recursividad_indirecta, eliminar_recursividad_inmediata
from orden_indices import eliminar_orden_indices
from sustitucion_final import sustitucion_final, validar_fng

MAX_PRODUCCIONES = 1500


def _verificar_limite(g: Gramatica, nombre_paso: str) -> None:
    if len(g.producciones) > MAX_PRODUCCIONES:
        raise ExplosionDeProducciones(
            f"Tras el paso '{nombre_paso}' la gramática superó "
            f"{MAX_PRODUCCIONES} producciones; se aborta la conversión "
            f"para no agotar memoria. Esto puede pasar con gramáticas que "
            f"tienen demasiadas variables mutuamente recursivas a la vez."
        )


def convertir_a_fng(g: Gramatica, orden_manual: Optional[List[str]] = None) -> dict:
    resultado = {"exito": True, "error_tipo": None, "error": None, "pasos": []}

    # Paso 1: renombrado (solo nombres, no se tocan los cuerpos)
    g1, evento1 = renombrar_a_greibach(g, orden_manual)
    _verificar_limite(g1, "renombrado")
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
        "eventos": [],
    })

    # Paso 2: recursividad indirecta (a la izquierda, entre 2+ variables)
    g2, eventos2 = eliminar_recursividad_indirecta(g1)
    _verificar_limite(g2, "recursividad indirecta")
    resultado["pasos"].append({
        "numero": 2,
        "clave": "recursividad_indirecta",
        "titulo": "Eliminación de recursividad a la izquierda (indirecta)",
        "descripcion_general": (
            "Se eliminan los ciclos de recursividad mutua entre dos o más "
            "variables, sustituyendo simultáneamente por rondas."
        ),
        "variables": g2.variables,
        "inicial": g2.inicial,
        "terminales": g2.terminales,
        "gramatica_resultante": g2.texto(),
        "eventos": [asdict(e) for e in eventos2],
    })

    # Paso 3: recursividad inmediata (X -> Xalfa), paso separado y posterior
    g3, eventos3 = eliminar_recursividad_inmediata(g2)
    _verificar_limite(g3, "recursividad inmediata")
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
        "eventos": [asdict(e) for e in eventos3],
    })

    # Paso 4: orden de índices (Xi -> Xjα con i > j)
    g4, eventos4 = eliminar_orden_indices(g3)
    _verificar_limite(g4, "orden de índices")
    resultado["pasos"].append({
        "numero": 4,
        "clave": "orden_indices",
        "titulo": "Eliminación de producciones Xi -> Xjα con i > j",
        "descripcion_general": (
            "Se sustituyen las producciones que inician en una variable de "
            "índice menor al de la cabeza, usando las producciones actuales "
            "de esa variable, hasta respetar el orden Xi -> Xjα con j > i."
        ),
        "variables": g4.variables,
        "inicial": g4.inicial,
        "terminales": g4.terminales,
        "gramatica_resultante": g4.texto(),
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
        "eventos": [asdict(e) for e in eventos5],
    })

    resultado["gramatica_final"] = g5.texto()
    resultado["validacion_fng"] = errores_fng
    resultado["exito"] = len(errores_fng) == 0

    return resultado