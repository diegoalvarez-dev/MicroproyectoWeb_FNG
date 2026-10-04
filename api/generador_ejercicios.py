"""
generador_ejercicios.py
Generador de ejercicios aleatorios en FNC (modo práctica). Usa variables
con letras mayúsculas (A, B, C...) porque X1, X2... están reservados para
el paso 1 (renombrado a notación Greibach) del conversor. Recibe
directamente num_variables, num_terminales, producciones_por_variable_min
y producciones_por_variable_max (los que manda el frontend según el nivel
elegido: fácil/media/difícil). Los terminales pueden ser letras o
números, se evita repetir la misma alternativa dos veces para una misma
variable, se garantiza que toda variable declarada sea alcanzable desde
la inicial, y se inyecta recursividad inmediata e indirecta de forma
controlada (nunca grupos de más de 2 variables mutuamente recursivas,
para que la conversión no explote combinatoriamente).
"""

import random
import string
from typing import List
from models import Gramatica

ALFABETO_TERMINALES = list(string.ascii_lowercase) + list(string.digits)
ALFABETO_VARIABLES = list(string.ascii_uppercase)

MIN_VARIABLES = 2
MAX_VARIABLES = len(ALFABETO_VARIABLES)
MIN_TERMINALES = 1
MAX_TERMINALES = len(ALFABETO_TERMINALES)
MIN_PRODUCCIONES = 1
MAX_PRODUCCIONES = 4


def _cuerpo_aleatorio(variables: List[str], terminales: List[str]) -> List[str]:
    forma = random.choice(["VntVnt", "VtVt", "VtVnt", "VntVt", "Vt"])
    if forma == "Vt":
        return [random.choice(terminales)]
    if forma == "VntVnt":
        return [random.choice(variables), random.choice(variables)]
    if forma == "VtVt":
        return [random.choice(terminales), random.choice(terminales)]
    if forma == "VtVnt":
        return [random.choice(terminales), random.choice(variables)]
    return [random.choice(variables), random.choice(terminales)]  # VntVt


def _sccs_de(g: Gramatica):
    from recursividad import construir_grafo_cabeza, encontrar_sccs
    return encontrar_sccs(construir_grafo_cabeza(g))


def _variables_alcanzables(g: Gramatica) -> set:
    alcanzables = {g.inicial}
    pendientes = [g.inicial]
    while pendientes:
        actual = pendientes.pop()
        for p in g.producciones_de(actual):
            for simbolo in p.cuerpo:
                if simbolo in g.variables and simbolo not in alcanzables:
                    alcanzables.add(simbolo)
                    pendientes.append(simbolo)
    return alcanzables


def _asegurar_alcanzables(g: Gramatica, terminales: List[str], cuerpos_usados: dict) -> None:
    """Conecta cualquier variable que haya quedado inalcanzable desde el
    símbolo inicial: le agrega una producción nueva a alguna variable ya
    alcanzable que la incluya (forma VntVt o VtVnt), hasta que todas las
    variables declaradas sean alcanzables desde el inicio. Sin esto, el
    generador podía crear gramáticas con variables "sueltas" que el
    validador de FNC marca correctamente como inalcanzables (VAL010)."""
    alcanzables = _variables_alcanzables(g)
    faltantes = [v for v in g.variables if v not in alcanzables]

    for v in faltantes:
        origen = random.choice(list(alcanzables))
        intentos = 0
        agregado = False
        while intentos < 20 and not agregado:
            intentos += 1
            if random.random() < 0.5:
                cuerpo = [v, random.choice(terminales)]       # VntVt
            else:
                cuerpo = [random.choice(terminales), v]        # VtVnt
            if _agregar_sin_repetir(g, origen, cuerpo, cuerpos_usados):
                agregado = True
        if not agregado:
            for t in terminales:
                if _agregar_sin_repetir(g, origen, [v, t], cuerpos_usados):
                    agregado = True
                    break
        alcanzables.add(v)


def _agregar_sin_repetir(g: Gramatica, cabeza: str, cuerpo: List[str], usados: dict) -> bool:
    """Agrega g.agregar(cabeza, cuerpo) solo si esa variable no tiene ya
    exactamente esa misma alternativa (misma cabeza y mismo cuerpo). Evita
    producciones tipo A -> AB/AB. Devuelve True si se agregó."""
    clave = tuple(cuerpo)
    if clave in usados[cabeza]:
        return False
    usados[cabeza].add(clave)
    g.agregar(cabeza, cuerpo)
    return True


def generar_ejercicio(
    num_variables: int = 5,
    num_terminales: int = 3,
    producciones_por_variable_min: int = 2,
    producciones_por_variable_max: int = 3,
) -> dict:
    num_variables = int(num_variables)
    num_terminales = int(num_terminales)
    producciones_por_variable_min = int(producciones_por_variable_min)
    producciones_por_variable_max = int(producciones_por_variable_max)

    if not (MIN_VARIABLES <= num_variables <= MAX_VARIABLES):
        raise ValueError(f"num_variables debe estar entre {MIN_VARIABLES} y {MAX_VARIABLES}.")
    if not (MIN_TERMINALES <= num_terminales <= MAX_TERMINALES):
        raise ValueError(f"num_terminales debe estar entre {MIN_TERMINALES} y {MAX_TERMINALES}.")
    if producciones_por_variable_min < MIN_PRODUCCIONES:
        producciones_por_variable_min = MIN_PRODUCCIONES
    if producciones_por_variable_max > MAX_PRODUCCIONES:
        producciones_por_variable_max = MAX_PRODUCCIONES
    if producciones_por_variable_min > producciones_por_variable_max:
        producciones_por_variable_min = producciones_por_variable_max

    intentos = 0
    while True:
        intentos += 1
        if intentos > 200:
            raise RuntimeError("No se pudo generar un ejercicio válido tras 200 intentos.")

        variables = ALFABETO_VARIABLES[:num_variables]
        terminales = random.sample(ALFABETO_TERMINALES, num_terminales)

        inicial = variables[0]
        g = Gramatica(variables=variables, terminales=terminales, inicial=inicial)
        cuerpos_usados = {v: set() for v in variables}

        for v in variables:
            n_prods = random.randint(producciones_por_variable_min, producciones_por_variable_max)
            intentos_v = 0
            agregadas = 0
            while agregadas < n_prods and intentos_v < 30:
                intentos_v += 1
                if _agregar_sin_repetir(g, v, _cuerpo_aleatorio(variables, terminales), cuerpos_usados):
                    agregadas += 1

        # Inyectar recursividad inmediata controlada
        n_inmediatas = max(1, len(variables) // 3)
        candidatas_inmediata = random.sample(variables, min(n_inmediatas, len(variables)))
        usadas = set(candidatas_inmediata)
        for v in candidatas_inmediata:
            intentos_v = 0
            while intentos_v < 10:
                intentos_v += 1
                if _agregar_sin_repetir(g, v, [v, random.choice(terminales)], cuerpos_usados):
                    break

        # Inyectar recursividad indirecta controlada (parejas, disjuntas de las usadas)
        disponibles = [v for v in variables if v not in usadas]
        n_parejas = max(1, len(variables) // 4)
        for _ in range(n_parejas):
            if len(disponibles) < 2:
                break
            a, b = random.sample(disponibles, 2)
            disponibles = [x for x in disponibles if x not in (a, b)]
            intentos_ab = 0
            while intentos_ab < 10:
                intentos_ab += 1
                if _agregar_sin_repetir(g, a, [b, random.choice(terminales)], cuerpos_usados):
                    break
            intentos_ab = 0
            while intentos_ab < 10:
                intentos_ab += 1
                if _agregar_sin_repetir(g, b, [a, random.choice(terminales)], cuerpos_usados):
                    break
            usadas.add(a)
            usadas.add(b)

        # Garantizar que toda variable declarada sea alcanzable desde la
        # inicial (si no, el validador de FNC la rechaza con VAL010).
        _asegurar_alcanzables(g, terminales, cuerpos_usados)

        # Rechazar si algún grupo mutuamente recursivo quedó con más de 2
        # variables (puede pasar tanto por la generación aleatoria como por
        # las conexiones de alcanzabilidad que se acaban de agregar).
        sccs = _sccs_de(g)
        if any(len(grupo) > 2 for grupo in sccs):
            continue

        return {
            "variables": variables,
            "terminales": terminales,
            "inicial": inicial,
            "gramatica": g.texto(),
            "producciones": [
                f"{v} -> " + "/".join(''.join(p.cuerpo) for p in g.producciones_de(v))
                for v in variables if g.producciones_de(v)
            ],
        }