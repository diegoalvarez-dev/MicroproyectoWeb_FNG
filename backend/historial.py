"""
historial.py
Encadena los 5 pasos del algoritmo de conversión FNC -> FNG en un solo
pipeline, y serializa todo el procedimiento (gramáticas intermedias,
producciones tachadas/nuevas, descripciones) en estructuras de datos
simples (dict/list) listas para convertirse a JSON y ser consumidas por
el frontend en React.

Diseño de "modo automático" vs "modo paso a paso":
En vez de mantener estado de sesión en el backend (lo cual complica la
API con manejo de sesiones), el pipeline se ejecuta COMPLETO de una sola
vez y se devuelve la lista total de pasos con sus eventos. El frontend es
quien decide cómo mostrarlo:
- Modo automático: renderiza todos los pasos de una vez.
- Modo paso a paso: renderiza el arreglo de a uno por vez con el botón
  "Siguiente paso", navegando el mismo arreglo que ya tiene completo.
Esto simplifica la API (sin sesiones, sin estado compartido entre
peticiones) y de todas formas cumple el requisito de "avanzar manualmente
y observar cada transformación antes de continuar" (sección 8 del
enunciado), porque el avance ocurre en el cliente, no en el servidor.
"""

from dataclasses import asdict
from typing import List, Optional, Dict, Any

from models import Gramatica
from validador_fnc import validar_fnc
from normalizador import normalizar_fnc_estricta
from renombrador import renombrar_a_greibach
from recursividad import eliminar_recursividad_indirecta, eliminar_recursividad_inmediata
from orden_indices import eliminar_orden_incorrecto
from sustitucion_final import sustitucion_final, validar_fng
from models import ExplosionDeProducciones

# Límite de seguridad: la conversión a FNG puede crecer de forma
# combinatoria (ver ejemplo de la guía: de 14 variables se llega a 248
# producciones). Con gramáticas generadas aleatoriamente con varias
# variables recursivas a la vez, ese crecimiento puede dispararse a miles
# de producciones y agotar la memoria del proceso. En vez de dejar que
# el servidor se caiga, cada módulo del pipeline aborta internamente
# (ExplosionDeProducciones) apenas se supera este umbral, y aquí se
# transforma en una respuesta controlada para el usuario.
MAX_PRODUCCIONES = 1500


def _verificar_limite(g: Gramatica, nombre_paso: str):
    if len(g.producciones) > MAX_PRODUCCIONES:
        raise ExplosionDeProducciones(
            f"La gramática creció a {len(g.producciones)} producciones durante el paso "
            f"'{nombre_paso}', superando el límite de seguridad ({MAX_PRODUCCIONES}). "
            f"Esto ocurre por la explosión combinatoria típica de la conversión a FNG "
            f"cuando hay varias variables con recursividad entrelazada. Prueba con una "
            f"gramática de entrada más pequeña o con menos recursividad cruzada."
        )


def _eventos_a_dict(eventos: List[Any]) -> List[Dict]:
    return [asdict(e) for e in eventos]


def ejecutar_pipeline_completo(g: Gramatica, orden_manual: Optional[List[str]] = None) -> Dict:
    """
    Ejecuta el proceso completo de conversión FNC -> FNG y devuelve un
    diccionario serializable con:
      - validacion_fnc: resultado de validar la gramática de entrada
      - exito: bool general (False si la validación de FNC falla; en ese
        caso no se ejecuta el resto del pipeline)
      - gramatica_original: texto de la gramática tal como se ingresó
      - pasos: lista ordenada de bloques, cada uno con:
            numero, clave, titulo, descripcion_general,
            gramatica_resultante (texto), eventos (lista de sustituciones
            con estado normal/eliminada/nueva)
      - gramatica_final: texto de la gramática resultante
      - validacion_fng: lista de errores (vacía si sí quedó en FNG)
    """
    resultado: Dict[str, Any] = {
        "gramatica_original": g.texto(),
        "pasos": [],
    }

    validacion = validar_fnc(g)
    resultado["validacion_fnc"] = {
        "valido": validacion.valido,
        "errores": [asdict(e) for e in validacion.errores],
    }

    if not validacion.valido:
        resultado["exito"] = False
        resultado["gramatica_final"] = None
        resultado["validacion_fng"] = None
        return resultado

    # Paso 1: normalización a forma estricta (VtVt / VntVt -> VntVnt / VtVnt)
    g0, eventos0 = normalizar_fnc_estricta(g)
    resultado["pasos"].append({
        "numero": 1,
        "clave": "normalizacion",
        "titulo": "Normalización a forma estricta de FNC",
        "descripcion_general": (
            "Se reemplaza todo terminal que no esté en la primera posición de una "
            "producción de 2 símbolos (formas VtVt y VntVt) por una variable auxiliar "
            "que lo genera, dejando solo las formas VntVnt, VtVnt o Vt."
        ),
        "gramatica_resultante": g0.texto(),
        "eventos": _eventos_a_dict(eventos0),
    })

    # Si el usuario dio un orden manual, se completan al final las variables
    # auxiliares que pudo haber creado la normalización (paso 1) y que no
    # existían cuando se definió ese orden.
    if orden_manual is not None:
        faltantes = [v for v in g0.variables if v not in orden_manual]
        orden_manual = list(orden_manual) + faltantes

    # Paso 2: renombrado y ordenamiento
    g1, evento1 = renombrar_a_greibach(g0, orden_manual)
    resultado["pasos"].append({
        "numero": 2,
        "clave": "renombrado",
        "titulo": "Ordenamiento y renombrado de variables",
        "descripcion_general": evento1.descripcion,
        "mapa_equivalencia": evento1.mapa,
        "gramatica_resultante": g1.texto(),
        "eventos": [],
    })

    # Paso 3: recursividad indirecta
    g2, eventos2 = eliminar_recursividad_indirecta(g1)
    _verificar_limite(g2, "recursividad indirecta")
    resultado["pasos"].append({
        "numero": 3,
        "clave": "recursividad_indirecta",
        "titulo": "Eliminación de recursividad a la izquierda (indirecta)",
        "descripcion_general": (
            "Se detectan grupos de variables con recursividad mutua a través del "
            "símbolo inicial de sus producciones y se sustituyen entre sí."
        ),
        "gramatica_resultante": g2.texto(),
        "eventos": _eventos_a_dict(eventos2),
    })

    # Paso 4: recursividad inmediata
    g3, eventos3 = eliminar_recursividad_inmediata(g2)
    _verificar_limite(g3, "recursividad inmediata")
    resultado["pasos"].append({
        "numero": 4,
        "clave": "recursividad_inmediata",
        "titulo": "Eliminación de recursividad inmediata a la izquierda",
        "descripcion_general": (
            "Se revisa cada variable en busca de producciones que inicien en sí misma "
            "y se separan en producciones no recursivas / variable auxiliar '.1'."
        ),
        "gramatica_resultante": g3.texto(),
        "eventos": _eventos_a_dict(eventos3),
    })

    # Paso 5: orden Xi -> Xj alfa con i > j
    g4, eventos4 = eliminar_orden_incorrecto(g3)
    _verificar_limite(g4, "orden de índices")
    resultado["pasos"].append({
        "numero": 5,
        "clave": "orden_indices",
        "titulo": "Eliminación de producciones Xi \u2192 Xj\u03b1 con i > j",
        "descripcion_general": (
            "Se revisa que ninguna producción inicie en una variable de índice menor "
            "al de su propia cabeza; si ocurre, se sustituye por las producciones de esa variable."
        ),
        "gramatica_resultante": g4.texto(),
        "eventos": _eventos_a_dict(eventos4),
    })

    # Paso 6: sustitución final
    g5, eventos5 = sustitucion_final(g4, max_producciones=MAX_PRODUCCIONES)
    resultado["pasos"].append({
        "numero": 6,
        "clave": "sustitucion_final",
        "titulo": "Sustitución final hasta iniciar en terminal",
        "descripcion_general": (
            "Se procesa de la última variable a la primera, sustituyendo toda producción "
            "que inicie en variable, hasta que todas inicien en un símbolo terminal."
        ),
        "gramatica_resultante": g5.texto(),
        "eventos": _eventos_a_dict(eventos5),
    })

    errores_fng = validar_fng(g5)
    resultado["exito"] = len(errores_fng) == 0
    resultado["gramatica_final"] = g5.texto()
    resultado["validacion_fng"] = errores_fng
    resultado["total_variables"] = len(g5.variables)
    resultado["total_producciones"] = len(g5.producciones)

    return resultado
