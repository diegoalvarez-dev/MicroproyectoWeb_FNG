"""
api.py
API HTTP (Flask) que expone el pipeline de conversión FNC -> FNG para que
el frontend en React lo consuma.

Endpoints:
  POST /api/validar
      body: { "variables": [...], "terminales": [...], "inicial": "S",
               "producciones": ["S -> AB/c", ...] }
      -> { "valido": bool, "errores": [...] }

  POST /api/convertir
      body: igual al anterior, más "orden_manual" opcional (lista de
            variables originales en el orden deseado, empezando por la
            inicial).
      -> resultado completo de historial.ejecutar_pipeline_completo():
         validación FNC, los 5 pasos con sus eventos (tachado/nuevo),
         gramática final y validación de FNG.

  POST /api/parsear
      body: { "variables": [...], "terminales": [...], "inicial": "S",
              "producciones": ["S -> AB/c", ...] }
      -> { "texto": "S -> AB | c\n..." }  (útil para que el front muestre
         una previsualización antes de convertir)

CORS: se habilita manualmente (sin flask_cors, que no está disponible en
este entorno) para permitir peticiones desde el frontend en React
(usualmente en otro puerto durante desarrollo).
"""

from flask import Flask, request, jsonify

from models import parsear_lineas_gramatica, ExplosionDeProducciones
from validador_fnc import validar_fnc
from historial import ejecutar_pipeline_completo
from generador_ejercicios import generar_ejercicio, ParametrosGenerador

app = Flask(__name__)


@app.after_request
def habilitar_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


def _construir_gramatica_desde_json(data):
    variables = data.get("variables", [])
    terminales = data.get("terminales", [])
    inicial = data.get("inicial", "")
    producciones = data.get("producciones", [])
    return parsear_lineas_gramatica(variables, terminales, inicial, producciones)


@app.route("/api/validar", methods=["POST", "OPTIONS"])
def endpoint_validar():
    if request.method == "OPTIONS":
        return "", 204
    data = request.get_json(force=True)
    try:
        g = _construir_gramatica_desde_json(data)
    except Exception as e:
        return jsonify({"valido": False, "errores": [{"codigo": "PARSE", "mensaje": str(e), "produccion": ""}]}), 400

    resultado = validar_fnc(g)
    return jsonify({
        "valido": resultado.valido,
        "errores": [
            {"codigo": e.codigo, "mensaje": e.mensaje, "produccion": e.produccion}
            for e in resultado.errores
        ],
    })


@app.route("/api/parsear", methods=["POST", "OPTIONS"])
def endpoint_parsear():
    if request.method == "OPTIONS":
        return "", 204
    data = request.get_json(force=True)
    try:
        g = _construir_gramatica_desde_json(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"texto": g.texto()})


@app.route("/api/convertir", methods=["POST", "OPTIONS"])
def endpoint_convertir():
    if request.method == "OPTIONS":
        return "", 204
    data = request.get_json(force=True)
    try:
        g = _construir_gramatica_desde_json(data)
    except Exception as e:
        return jsonify({"exito": False, "error": f"Error interpretando la gramática: {e}"}), 400

    orden_manual = data.get("orden_manual")  # opcional

    try:
        resultado = ejecutar_pipeline_completo(g, orden_manual)
    except ExplosionDeProducciones as e:
        return jsonify({"exito": False, "error_tipo": "explosion", "error": str(e)}), 422
    except Exception as e:
        return jsonify({"exito": False, "error_tipo": "interno", "error": f"Error durante la conversión: {e}"}), 500

    return jsonify(resultado)


@app.route("/api/generar-ejercicio", methods=["POST", "OPTIONS"])
def endpoint_generar_ejercicio():
    """
    body opcional: { "num_variables": 4, "num_terminales": 2,
                      "producciones_por_variable_min": 2,
                      "producciones_por_variable_max": 2,
                      "incluir_recursividad_inmediata": true,
                      "incluir_recursividad_indirecta": true,
                      "semilla": 123 }
    Cualquier campo omitido usa el valor por defecto (conservador).
    -> { "variables":[...], "terminales":[...], "inicial":"A",
         "producciones":[...], "enunciado": "...",
         "tiene_recursividad_inmediata": bool,
         "tiene_recursividad_indirecta": bool }
    """
    if request.method == "OPTIONS":
        return "", 204
    data = request.get_json(force=True, silent=True) or {}
    try:
        params = ParametrosGenerador(
            num_variables=data.get("num_variables", 4),
            num_terminales=data.get("num_terminales", 2),
            producciones_por_variable_min=data.get("producciones_por_variable_min", 2),
            producciones_por_variable_max=data.get("producciones_por_variable_max", 2),
            incluir_recursividad_inmediata=data.get("incluir_recursividad_inmediata", True),
            incluir_recursividad_indirecta=data.get("incluir_recursividad_indirecta", True),
            semilla=data.get("semilla"),
        )
        ejercicio = generar_ejercicio(params)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RecursionError:
        return jsonify({
            "error": "No se logró generar un ejercicio seguro con esos parámetros "
                     "tras varios intentos. Prueba con menos variables o producciones."
        }), 422

    return jsonify({
        "variables": ejercicio.variables,
        "terminales": ejercicio.terminales,
        "inicial": ejercicio.inicial,
        "producciones": ejercicio.producciones,
        "enunciado": ejercicio.enunciado,
        "tiene_recursividad_inmediata": ejercicio.tiene_recursividad_inmediata,
        "tiene_recursividad_indirecta": ejercicio.tiene_recursividad_indirecta,
    })


@app.route("/api/salud", methods=["GET"])
def endpoint_salud():
    return jsonify({"estado": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
