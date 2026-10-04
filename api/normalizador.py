"""
normalizador.py
Paso 1 (nuevo) del pipeline: normaliza la gramática de entrada, que puede
venir en cualquiera de las 5 formas acordadas (VntVnt, VtVt, VtVnt, VntVt,
Vt), a la forma que el algoritmo clásico de Greibach necesita para
funcionar correctamente: producciones de un solo terminal (Vt), de dos
variables (VntVnt), o de un terminal seguido de UNA variable (VtVnt).

Por qué es necesario:
- Vt (A -> a): ya es compatible, no requiere cambio.
- VtVnt (A -> aB): ya es compatible (terminal al inicio, variable
  después); el resto del algoritmo nunca toca el símbolo inicial cuando
  ya es terminal, así que no hace falta tocarlo.
- VntVnt (A -> BC): es el caso "normal" para el que está diseñado el
  resto del algoritmo (pasos de recursividad, orden e índices).
- VtVt (A -> ab): PROBLEMÁTICO. El segundo símbolo es un terminal que
  quedaría "suelto" en medio de futuras sustituciones, violando la FNG.
- VntVt (A -> Ba): PROBLEMÁTICO por la misma razón: el terminal final
  puede terminar en medio de una producción más larga cuando B se
  sustituye en el paso 5.

Para los dos casos problemáticos, se reemplaza el terminal que NO está en
la primera posición por una variable auxiliar Ta (con Ta -> a), igual que
se hace en la guía antes de construir la FNC estricta. Se reutiliza la
misma variable auxiliar cada vez que se necesite el mismo terminal, para
no inflar la gramática innecesariamente (RNF07).
"""

from dataclasses import dataclass, field
from typing import List, Dict
from models import Gramatica, Produccion, es_terminal, es_no_terminal


@dataclass
class ProduccionMarcada:
    texto: str
    estado: str  # "normal" | "eliminada" | "nueva"


@dataclass
class EventoNormalizacion:
    variable: str
    descripcion: str
    producciones_antes: List[ProduccionMarcada] = field(default_factory=list)
    producciones_despues: List[ProduccionMarcada] = field(default_factory=list)


def _nombre_variable_para_terminal(terminal: str, ocupados: set) -> str:
    base = f"T{terminal.upper()}"
    nombre = base
    sufijo = 1
    while nombre in ocupados:
        sufijo += 1
        nombre = f"{base}{sufijo}"
    return nombre


def normalizar_fnc_estricta(g: Gramatica):
    """
    Devuelve (gramatica_normalizada, eventos). No modifica g.
    """
    nueva = g.clonar()
    eventos: List[EventoNormalizacion] = []
    terminal_a_variable: Dict[str, str] = {}
    ocupados = set(nueva.variables)
    variables_auxiliares_creadas: List[str] = []

    def obtener_variable(t: str) -> str:
        if t in terminal_a_variable:
            return terminal_a_variable[t]
        nombre = _nombre_variable_para_terminal(t, ocupados)
        ocupados.add(nombre)
        terminal_a_variable[t] = nombre
        variables_auxiliares_creadas.append(nombre)
        nueva.agregar(nombre, [t])
        return nombre

    hubo_cambios = False

    for v in list(g.variables):  # se recorre la gramática original para no verse afectado por inserciones
        prods = nueva.producciones_de(v)
        antes_marcadas = []
        despues_marcadas = []
        cambio_en_v = False

        for p in list(prods):
            if len(p.cuerpo) != 2:
                antes_marcadas.append(ProduccionMarcada(str(p), "normal"))
                despues_marcadas.append(ProduccionMarcada(str(p), "normal"))
                continue

            s0, s1 = p.cuerpo
            necesita_cambio = (
                (es_terminal(s0) and es_terminal(s1)) or          # VtVt
                (es_no_terminal(s0) and es_terminal(s1))           # VntVt
            )

            if not necesita_cambio:
                antes_marcadas.append(ProduccionMarcada(str(p), "normal"))
                despues_marcadas.append(ProduccionMarcada(str(p), "normal"))
                continue

            hubo_cambios = True
            cambio_en_v = True
            antes_marcadas.append(ProduccionMarcada(str(p), "eliminada"))

            var_aux = obtener_variable(s1)
            nuevo_cuerpo = [s0, var_aux]
            nueva.eliminar(p)
            nueva.agregar(v, nuevo_cuerpo)
            despues_marcadas.append(ProduccionMarcada(f"{v} -> {''.join(nuevo_cuerpo)}", "nueva"))

        if cambio_en_v:
            eventos.append(EventoNormalizacion(
                variable=v,
                descripcion=(
                    f"{v} tiene producción(es) con un terminal que no está al inicio del cuerpo "
                    f"(forma VtVt o VntVt). Se reemplaza ese terminal por una variable auxiliar "
                    f"que lo genera, para dejar la producción en forma VntVnt o VtVnt."
                ),
                producciones_antes=antes_marcadas,
                producciones_despues=despues_marcadas,
            ))

    for nombre in variables_auxiliares_creadas:
        if nombre not in nueva.variables:
            nueva.variables.append(nombre)

    if not hubo_cambios:
        eventos.append(EventoNormalizacion(
            variable="",
            descripcion="Todas las producciones ya cumplen con la forma estricta (VntVnt, VtVnt o Vt); no se requiere normalización."
        ))

    return nueva, eventos
