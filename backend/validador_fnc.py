"""
validador_fnc.py
Valida que una gramática esté en Forma Normal de Chomsky (FNC) usando
EXACTAMENTE las 5 formas de cuerpo de producción aceptadas:

    Vnt Vnt   (dos no terminales)
    Vt  Vt    (dos terminales)
    Vt  Vnt   (terminal + no terminal)
    Vnt Vt    (no terminal + terminal)
    Vt        (un solo terminal)

No se acepta: producciones unitarias (Vnt -> Vnt), producciones vacías
(epsilon) ni cuerpos de 3 o más símbolos. Se asume que esas ya fueron
eliminadas en la fase previa de normalización a Chomsky. También se
valida que no haya producciones repetidas ni variables inalcanzables
desde el símbolo inicial.
"""

from dataclasses import dataclass
from typing import List
from models import Gramatica, Produccion, es_terminal, es_no_terminal


@dataclass
class ErrorValidacion:
    codigo: str
    mensaje: str


def _forma_de(p: Produccion) -> str:
    cuerpo = p.cuerpo
    if len(cuerpo) == 1:
        return "Vt" if es_terminal(cuerpo[0]) else "Vnt"
    if len(cuerpo) == 2:
        a, b = cuerpo
        ta = "Vnt" if es_no_terminal(a) else ("Vt" if es_terminal(a) else "?")
        tb = "Vnt" if es_no_terminal(b) else ("Vt" if es_terminal(b) else "?")
        return f"{ta}{tb}"
    return f"{len(cuerpo)}simbolos"


FORMAS_VALIDAS = {"VntVnt", "VtVt", "VtVnt", "VntVt", "Vt"}


def validar_fnc(g: Gramatica) -> List[ErrorValidacion]:
    errores: List[ErrorValidacion] = []

    for v in g.variables:
        if not g.producciones_de(v):
            errores.append(ErrorValidacion(
                "VAL001",
                f"La variable '{v}' está declarada pero no tiene ninguna producción."
            ))

    for p in g.producciones:
        cuerpo = p.cuerpo
        texto = str(p)

        if len(cuerpo) == 0:
            errores.append(ErrorValidacion(
                "VAL002",
                f"La producción '{texto}' es una producción vacía (ε). "
                f"En FNC no se permiten producciones epsilon; deben haberse "
                f"eliminado en la fase de normalización previa."
            ))
            continue

        if len(cuerpo) == 1:
            simbolo = cuerpo[0]
            if es_terminal(simbolo):
                continue  # forma Vt, válida
            if es_no_terminal(simbolo):
                errores.append(ErrorValidacion(
                    "VAL003",
                    f"La producción '{texto}' es una producción unitaria "
                    f"(no terminal -> no terminal). En FNC no se permiten "
                    f"producciones unitarias; deben haberse eliminado en la "
                    f"fase de normalización previa."
                ))
                continue
            errores.append(ErrorValidacion(
                "VAL004",
                f"La producción '{texto}' tiene el símbolo '{simbolo}', que no "
                f"corresponde a ningún terminal ni variable declarada."
            ))
            continue

        if len(cuerpo) == 2:
            a, b = cuerpo
            a_term, a_var = es_terminal(a), es_no_terminal(a)
            b_term, b_var = es_terminal(b), es_no_terminal(b)

            if not (a_term or a_var):
                errores.append(ErrorValidacion(
                    "VAL005",
                    f"En la producción '{texto}', el símbolo '{a}' no está "
                    f"declarado como terminal ni como variable."
                ))
                continue
            if not (b_term or b_var):
                errores.append(ErrorValidacion(
                    "VAL006",
                    f"En la producción '{texto}', el símbolo '{b}' no está "
                    f"declarado como terminal ni como variable."
                ))
                continue

            forma = _forma_de(p)
            if forma not in FORMAS_VALIDAS:
                errores.append(ErrorValidacion(
                    "VAL007",
                    f"La producción '{texto}' tiene forma '{forma}', que no "
                    f"es una de las formas permitidas en FNC (VntVnt, VtVt, "
                    f"VtVnt, VntVt, Vt)."
                ))
            continue

        # 3 o más símbolos
        errores.append(ErrorValidacion(
            "VAL008",
            f"La producción '{texto}' tiene {len(cuerpo)} símbolos en el "
            f"cuerpo. En FNC el cuerpo no puede superar 2 símbolos."
        ))

    # Producciones repetidas: aunque matemáticamente no invalida la FNC,
    # no tiene sentido declarar la misma alternativa dos veces para la
    # misma variable (ej. A -> AB/AB/CD/1/1). Se avisa para que el
    # estudiante corrija el enunciado.
    vistos_por_variable = {}
    for p in g.producciones:
        clave = (p.cabeza, tuple(p.cuerpo))
        vistos_por_variable[clave] = vistos_por_variable.get(clave, 0) + 1

    ya_reportados = set()
    for (cabeza, cuerpo_tupla), veces in vistos_por_variable.items():
        if veces > 1 and (cabeza, cuerpo_tupla) not in ya_reportados:
            ya_reportados.add((cabeza, cuerpo_tupla))
            cuerpo_txt = ''.join(cuerpo_tupla) if cuerpo_tupla else 'ε'
            errores.append(ErrorValidacion(
                "VAL009",
                f"La variable '{cabeza}' tiene la producción '{cabeza} -> {cuerpo_txt}' "
                f"repetida {veces} veces. Elimina las repeticiones, cada alternativa "
                f"debe aparecer una sola vez."
            ))

    # Variables inalcanzables: toda variable declarada debe poder
    # derivarse desde el símbolo inicial siguiendo producciones (directa
    # o transitivamente). Si no, es una variable "muerta" que no aporta
    # nada a ninguna cadena generada por la gramática.
    if g.inicial in g.variables:
        alcanzables = {g.inicial}
        pendientes = [g.inicial]
        while pendientes:
            actual = pendientes.pop()
            for p in g.producciones_de(actual):
                for simbolo in p.cuerpo:
                    if es_no_terminal(simbolo) and simbolo not in alcanzables:
                        alcanzables.add(simbolo)
                        pendientes.append(simbolo)

        for v in g.variables:
            if v not in alcanzables:
                errores.append(ErrorValidacion(
                    "VAL010",
                    f"La variable '{v}' es inalcanzable desde el símbolo inicial "
                    f"'{g.inicial}': no aparece en el cuerpo de ninguna producción "
                    f"derivable desde '{g.inicial}'. Elimínala o conéctala a la "
                    f"gramática desde alguna producción alcanzable."
                ))

    return errores