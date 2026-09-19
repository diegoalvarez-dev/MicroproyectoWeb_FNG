# Conversor FNC → Forma Normal de Greibach

Microproyecto #2 — Teoría de la Computación. Software que recibe una GLC en
Forma Normal de Chomsky y la transforma automáticamente en su equivalente
en Forma Normal de Greibach, mostrando cada paso del procedimiento.

## Estructura

```
backend/     API en Python (Flask) con toda la lógica de conversión
frontend/    Interfaz en React + Tailwind CSS (Vite)
```

## 1. Backend (Python)

Requiere Python 3.9+.

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # en Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 api.py
```

El servidor queda escuchando en `http://localhost:5000`.

Módulos:
- `models.py` — estructuras base (Gramática, Producción)
- `validador_fnc.py` — valida que la entrada cumpla FNC (formas VntVnt, VtVt, VtVnt, VntVt, Vt)
- `normalizador.py` — paso 1: normaliza VtVt/VntVt a forma estricta
- `renombrador.py` — paso 2: ordena y renombra variables a X1..Xn
- `recursividad.py` — pasos 3 y 4: recursividad indirecta e inmediata
- `orden_indices.py` — paso 5: elimina Xi → Xjα con i > j
- `sustitucion_final.py` — paso 6: sustitución final + validación de FNG
- `historial.py` — encadena todo el pipeline y lo serializa
- `generador_ejercicios.py` — generador de gramáticas aleatorias para practicar
- `api.py` — expone todo como API HTTP (Flask)

### Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/validar` | Valida que la gramática esté en FNC |
| POST | `/api/parsear` | Previsualiza cómo se interpretó la gramática ingresada |
| POST | `/api/convertir` | Ejecuta el pipeline completo (FNC → FNG) |
| POST | `/api/generar-ejercicio` | Genera una gramática FNC aleatoria para practicar |
| GET | `/api/salud` | Chequeo de disponibilidad |

## 2. Frontend (React + Tailwind)

Requiere Node.js 18+.

```bash
cd frontend
npm install
npm run dev
```

Se abre en `http://localhost:5173`. Las peticiones a `/api/*` se redirigen
automáticamente al backend en `http://localhost:5000` (configurado en
`vite.config.js`), así que **el backend debe estar corriendo primero**.

Para generar la versión de producción: `npm run build` (queda en `frontend/dist`).

## Convenciones de la gramática

- No terminal (Vnt): letra mayúscula, opcionalmente con dígitos o sufijo
  `.n` (ej: `A`, `X6`, `X6.1`).
- Terminal (Vt): letra minúscula o dígito (ej: `a`, `1`).
- Formas de producción aceptadas como FNC de entrada: `VntVnt`, `VtVt`,
  `VtVnt`, `VntVt`, `Vt` (sin unitarias ni ε, ya depuradas previamente).
- En el textarea de producciones: una variable por línea, alternativas
  separadas por `/`. Ejemplo:
  ```
  S -> AB/a
  A -> SB/a
  B -> b
  ```

## Notas de diseño

- El pipeline se ejecuta completo en una sola llamada a `/api/convertir`;
  el modo "paso a paso" simplemente navega en el cliente el mismo arreglo
  de pasos ya calculado, sin necesidad de manejar sesiones en el backend.
- Cada paso devuelve eventos con estado `normal` / `eliminada` / `nueva`,
  que el frontend pinta como texto tachado o resaltado (igual que se hace
  a mano en las diapositivas de la clase).
- La conversión a FNG puede crecer de forma combinatoria (explicado en el
  código de `historial.py`), por lo que hay límites de seguridad internos
  que abortan con un mensaje claro en vez de agotar memoria.
