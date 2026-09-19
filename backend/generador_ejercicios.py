"""
generador_ejercicios.py
Genera gramáticas aleatorias, válidas en Forma Normal de Chomsky según las
5 formas acordadas para este proyecto (VntVnt, VtVt, VtVnt, VntVt, Vt),
pensadas para que el usuario practique el proceso de conversión a FNG a
mano y luego lo compare contra el resultado automático del sistema
(mismo enfoque que se usó en el proyecto de Chomsky).

Un ejercicio "interesante" para este tema DEBE contener recursividad a la
izquierda (inmediata y/o indirecta), porque si no, los pasos 2 y 3 del
algoritmo de Greibach no tendrían nada que hacer y el ejercicio perdería
su propósito pedagógico. Por eso el generador, a diferencia de uno
puramente aleatorio, INYECTA deliberadamente al menos un caso de
recursividad (configurable) antes de completar el resto de la gramática
al azar.
"""

import random
import string
from dataclasses import dataclass, field
from typing import List, Optional

from models import Gramatica, Produccion
from validador_fnc import validar_fnc

FORMAS = ["VntVnt", "VtVt", "VtVnt", "VntVt", "Vt"]


@dataclass
class ParametrosGenerador:
    # Valores conservadores por defecto: el propósito de estos ejercicios
    # es que el usuario los resuelva A MANO y compare contra el sistema, no
    # generar la gramática más grande posible. La conversión a FNG crece de
    # forma combinatoria (ver ejemplo real de la guía: 14 variables -> 248
    # producciones), así que con más de 5 variables o más de 2 producciones
    # por variable ya es fácil pasarse de lo que una persona puede resolver
    # a mano en una sesión de estudio, y con más recursividad simultánea
    # cruzada el conteo final puede dispararse a miles de producciones.
    num_variables: int = 4          # recomendado entre 3 y 5
    num_terminales: int = 2         # recomendado entre 2 y 3
    producciones_por_variable_min: int = 2
    producciones_por_variable_max: int = 2
    incluir_recursividad_inmediata: bool = True
    incluir_recursividad_indirecta: bool = True
    semilla: Optional[int] = None

    def __post_init__(self):
        if self.num_variables > 6:
            raise ValueError(
                "num_variables no debería superar 6: la conversión a FNG crece de forma "
                "combinatoria y una gramática más grande puede volverse impráctica de resolver "
                "a mano o incluso agotar memoria durante la conversión automática."
            )
        if self.producciones_por_variable_max > 3:
            raise ValueError(
                "producciones_por_variable_max no debería superar 3, por la misma razón: "
                "el crecimiento combinatorio de la conversión a Greibach."
            )


@dataclass
class Ejercicio:
    variables: List[str]
    terminales: List[str]
    inicial: str
    producciones: List[str]     # en formato "A -> BC/d/..." listo para la API
    gramatica: Gramatica
    tiene_recursividad_inmediata: bool
    tiene_recursividad_indirecta: bool
    enunciado: str


def _nombres_variables(n: int) -> List[str]:
    letras = list(string.ascii_uppercase)
    if n <= len(letras):
        return letras[:n]
    # si se piden más de 26, se agregan sufijos numéricos (A1, B1, ...)
    extra = []
    i = 1
    while len(letras) + len(extra) < n:
        extra.append(f"{letras[len(extra) % len(letras)]}{i}")
        i += 1
    return (letras + extra)[:n]


def _nombres_terminales(n: int) -> List[str]:
    letras = list(string.ascii_lowercase)
    digitos = list(string.digits)
    disponibles = letras + digitos
    if n > len(disponibles):
        n = len(disponibles)
    return disponibles[:n]


def _cuerpo_aleatorio(forma: str, variables: List[str], terminales: List[str],
                       cabeza: Optional[str] = None) -> List[str]:
    if forma == "VntVnt":
        return [random.choice(variables), random.choice(variables)]
    if forma == "VtVt":
        return [random.choice(terminales), random.choice(terminales)]
    if forma == "VtVnt":
        return [random.choice(terminales), random.choice(variables)]
    if forma == "VntVt":
        return [random.choice(variables), random.choice(terminales)]
    if forma == "Vt":
        return [random.choice(terminales)]
    raise ValueError(f"Forma desconocida: {forma}")


def generar_ejercicio(params: ParametrosGenerador = None) -> Ejercicio:
    if params is None:
        params = ParametrosGenerador()
    if params.semilla is not None:
        random.seed(params.semilla)

    variables = _nombres_variables(params.num_variables)
    terminales = _nombres_terminales(params.num_terminales)
    inicial = variables[0]

    g = Gramatica(variables=variables, terminales=terminales, inicial=inicial)

    tiene_inmediata = False
    tiene_indirecta = False

    # 1. Inyectar recursividad inmediata en una variable aleatoria
    if params.incluir_recursividad_inmediata and len(variables) >= 1:
        v = random.choice(variables)
        forma = random.choice(["VntVnt", "VntVt"])
        if forma == "VntVnt":
            cuerpo = [v, random.choice(variables)]
        else:
            cuerpo = [v, random.choice(terminales)]
        g.agregar(v, cuerpo)
        tiene_inmediata = True

    # 2. Inyectar recursividad indirecta entre dos variables distintas
    if params.incluir_recursividad_indirecta and len(variables) >= 2:
        x, y = random.sample(variables, 2)
        g.agregar(x, [y, random.choice(terminales)])
        g.agregar(y, [x, random.choice(terminales)])
        tiene_indirecta = True

    # 3. Completar con producciones aleatorias válidas para cada variable.
    #    IMPORTANTE: se limita fuertemente la probabilidad de que una
    #    producción "de relleno" inicie en variable (formas VntVnt/VntVt),
    #    porque cada una de esas es una arista más en el grafo de "primera
    #    variable" que usa el paso de recursividad indirecta. Si demasiadas
    #    variables terminan conectadas entre sí, se forma un solo grupo de
    #    recursividad mutua gigante (en vez de parejas pequeñas como en el
    #    ejemplo de la guía) y la conversión a FNG explota combinatoriamente.
    PROB_RELLENO_INICIA_EN_VARIABLE = 0.15

    for v in variables:
        objetivo = random.randint(params.producciones_por_variable_min,
                                   params.producciones_por_variable_max)
        intentos = 0
        while len(g.producciones_de(v)) < max(objetivo, 1) and intentos < 20:
            intentos += 1
            if random.random() < PROB_RELLENO_INICIA_EN_VARIABLE:
                forma = random.choice(["VntVnt", "VntVt"])
            else:
                forma = random.choice(["VtVt", "VtVnt", "Vt"])
            cuerpo = _cuerpo_aleatorio(forma, variables, terminales)
            # evitar producciones duplicadas exactas
            if any(p.cabeza == v and p.cuerpo == cuerpo for p in g.producciones):
                continue
            g.agregar(v, cuerpo)

    # 4. Verificación de seguridad #1: la gramática SIEMPRE debe ser FNC
    #    válida por construcción (defensa extra antes de entregarla).
    resultado = validar_fnc(g)
    if not resultado.valido:
        return generar_ejercicio(ParametrosGenerador(
            num_variables=params.num_variables,
            num_terminales=params.num_terminales,
            incluir_recursividad_inmediata=False,
            incluir_recursividad_indirecta=False,
        ))

    # 5. Verificación de seguridad #2: ningún grupo de recursividad mutua
    #    (componente fuertemente conexa en el grafo de "primera variable")
    #    puede tener más de 2 variables, o la conversión a FNG corre
    #    riesgo real de explotar combinatoriamente y agotar memoria. Si
    #    ocurre, se reintenta la generación completa (con la misma
    #    dificultad) hasta un máximo de intentos; si aun así no se logra,
    #    se cae a una versión sin recursividad indirecta inyectada.
    from recursividad import construir_grafo_cabeza, encontrar_sccs
    grafo = construir_grafo_cabeza(g)
    sccs = encontrar_sccs(grafo)
    if any(len(scc) > 2 for scc in sccs):
        if params.semilla is not None:
            # con semilla fija no tiene sentido reintentar (daría lo mismo);
            # se cae directo a una versión más simple y determinista.
            return generar_ejercicio(ParametrosGenerador(
                num_variables=params.num_variables,
                num_terminales=params.num_terminales,
                producciones_por_variable_min=params.producciones_por_variable_min,
                producciones_por_variable_max=params.producciones_por_variable_max,
                incluir_recursividad_indirecta=False,
                semilla=params.semilla,
            ))
        return generar_ejercicio(params)

    lineas = []
    for v in variables:
        cuerpos = ["".join(p.cuerpo) for p in g.producciones_de(v)]
        lineas.append(f"{v} -> " + "/".join(cuerpos))

    enunciado = (
        f"Dada la siguiente gramática en Forma Normal de Chomsky "
        f"(variables: {', '.join(variables)}; terminales: {', '.join(terminales)}; "
        f"símbolo inicial: {inicial}), obtenga su Forma Normal de Greibach:\n\n"
        + "\n".join(lineas)
    )

    return Ejercicio(
        variables=variables,
        terminales=terminales,
        inicial=inicial,
        producciones=lineas,
        gramatica=g,
        tiene_recursividad_inmediata=tiene_inmediata,
        tiene_recursividad_indirecta=tiene_indirecta,
        enunciado=enunciado,
    )
