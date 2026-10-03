"""
api.py
Servidor Flask con los endpoints del conversor FNC -> FNG.
"""

from flask import Flask, request, jsonify

from models import parsear_lineas_gramatica, ExplosionDeProducciones
from validador_fnc import validar_fnc
from historial import convertir_a_fng
from generador_ejercicios import generar_ejercicio

app = Flask(__name__)


@app.after_request
def agregar_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def _construir_gramatica_desde_payload(data):
    variables = [v.strip() for v in data.get("variables", []) if v.strip()]
    terminales = [t.strip() for t in data.get("terminales", []) if t.strip()]
    inicial = data.get("inicial", "").strip()
    # Sidebar.jsx (construirPayload) manda el campo "producciones", con
    # líneas tipo "A -> AB/CD/a". Se acepta también "lineas" por si algún
    # otro cliente lo manda con ese nombre.
    lineas = [
        l.strip()
        for l in (data.get("producciones") or data.get("lineas") or [])
        if l.strip()
    ]
    if not variables:
        raise ValueError("Debe declarar al menos una variable.")
    if not inicial:
        inicial = variables[0]
    return parsear_lineas_gramatica(variables, terminales, inicial, lineas)


@app.route("/api/salud", methods=["GET"])
def salud():
    return jsonify({"estado": "ok"})


@app.route("/api/validar", methods=["POST", "OPTIONS"])
def validar():
    if request.method == "OPTIONS":
        return "", 204
    data = request.get_json(force=True)
    try:
        g = _construir_gramatica_desde_payload(data)
    except Exception as e:
        return jsonify({"exito": False, "error": str(e)}), 400

    errores = validar_fnc(g)
    es_valida = len(errores) == 0
    return jsonify({
        # ValidacionPanel.jsx lee "valido"; se deja también "exito" por
        # consistencia con el resto de endpoints.
        "valido": es_valida,
        "exito": es_valida,
        "errores": [{"codigo": e.codigo, "mensaje": e.mensaje} for e in errores],
        "gramatica": g.texto(),
    })
    
@app.route("/api/parsear", methods=["POST", "OPTIONS"])
def parsear():
    if request.method == "OPTIONS":
        return "", 204
    data = request.get_json(force=True)
    try:
        g = _construir_gramatica_desde_payload(data)
    except Exception as e:
        return jsonify({"exito": False, "error": str(e)}), 400
    return jsonify({"exito": True, "gramatica": g.texto()})


@app.route("/api/convertir", methods=["POST", "OPTIONS"])
def convertir():
    if request.method == "OPTIONS":
        return "", 204
    data = request.get_json(force=True)
    try:
        g = _construir_gramatica_desde_payload(data)
    except Exception as e:
        return jsonify({"exito": False, "error_tipo": "parseo", "error": str(e)}), 400

    errores_fnc = validar_fnc(g)
    if errores_fnc:
        return jsonify({
            "exito": False,
            "error_tipo": "validacion_fnc",
            "error": "La gramática no cumple la Forma Normal de Chomsky (FNC).",
            "errores_fnc": [{"codigo": e.codigo, "mensaje": e.mensaje} for e in errores_fnc],
        }), 422

    orden_manual = data.get("orden_manual") or None

    try:
        resultado = convertir_a_fng(g, orden_manual)
    except ExplosionDeProducciones as e:
        return jsonify({"exito": False, "error_tipo": "explosion", "error": str(e)}), 422

    return jsonify(resultado)


@app.route("/api/generar-ejercicio", methods=["POST", "OPTIONS"])
def generar_ejercicio_endpoint():
    if request.method == "OPTIONS":
        return "", 204
    data = request.get_json(force=True) or {}
    try:
        ejercicio = generar_ejercicio(
            num_variables=data.get("num_variables", 5),
            num_terminales=data.get("num_terminales", 3),
            producciones_por_variable_min=data.get("producciones_por_variable_min", 2),
            producciones_por_variable_max=data.get("producciones_por_variable_max", 3),
        )
    except Exception as e:
        return jsonify({"exito": False, "error": str(e)}), 400
    return jsonify({"exito": True, **ejercicio})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)