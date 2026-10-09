import { useState, useEffect } from 'react'
import { generarEjercicio } from '../api'

const VACIO = { variables: '', terminales: '', inicial: '', producciones: '' }

const NIVELES = [
  { valor: 'facil', etiqueta: 'Fácil', vars: 4, term: 2, prodMin: 2, prodMax: 3 },
  { valor: 'media', etiqueta: 'Media', vars: 6, term: 3, prodMin: 2, prodMax: 3 },
  { valor: 'dificil', etiqueta: 'Difícil', vars: 8, term: 4, prodMin: 3, prodMax: 4 },
]

// Vnt: solo letras mayúsculas (sin dígitos, sin minúsculas, sin símbolos).
const TOKEN_VNT_VALIDO = /^[A-Z]+$/
// Vt: solo dígitos o letras minúsculas.
const TOKEN_VT_VALIDO = /^[a-z0-9]+$/

// "A -> AB/a\nB -> b" -> { A: 'AB/a', B: 'b' }
function lineasAMapa(producciones) {
  const mapa = {}
  ;(producciones || '')
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean)
    .forEach((linea) => {
      const [cabeza, cuerpo] = linea.split('->')
      if (cabeza && cuerpo !== undefined) {
        mapa[cabeza.trim()] = cuerpo.trim()
      }
    })
  return mapa
}

function listaDeVariables(texto) {
  return (texto || '')
    .split(/[, ]+/)
    .map((s) => s.trim())
    .filter(Boolean)
}

// Verdadero si la lista está vacía (todavía no se terminó de escribir) o si
// TODOS los tokens cumplen la regex dada. Solo se considera "inválido" (rojo)
// cuando hay contenido que no cumple.
function todosCumplen(tokens, regex) {
  return tokens.every((t) => regex.test(t))
}

export default function Sidebar({ valor, onCambiar, onRegistrar, onLimpiar, cargando }) {
  const [local, setLocal] = useState(valor || VACIO)
  const [produccionesMapa, setProduccionesMapa] = useState(() => lineasAMapa((valor || VACIO).producciones))
  const [nivel, setNivel] = useState('media')
  const [generando, setGenerando] = useState(false)
  const [errorGenerador, setErrorGenerador] = useState(null)
  // Snapshot de la gramática tal como quedó la última vez que se registró.
  // A diferencia de "local" (que sigue cambiando mientras el usuario edita),
  // esto NO se actualiza con cada tecla: solo cambia al registrar de nuevo
  // o al limpiar campos. Sirve para ver cómo era la gramática original
  // mientras se navega por los pasos de la conversión.
  const [gramaticaOriginal, setGramaticaOriginal] = useState(null)

  // Si viene una gramática nueva desde afuera (ej. el generador de
  // ejercicios), se recarga tanto el texto plano como el mapa por variable.
  useEffect(() => {
    if (valor) {
      setLocal(valor)
      setProduccionesMapa(lineasAMapa(valor.producciones))
    }
  }, [valor])

  const variablesActuales = listaDeVariables(local.variables)
  const terminalesActuales = listaDeVariables(local.terminales.replaceAll(',', ' '))

  const vntValido = todosCumplen(variablesActuales, TOKEN_VNT_VALIDO)
  const vtValido = todosCumplen(terminalesActuales, TOKEN_VT_VALIDO)
  const inicialTexto = local.inicial.trim()
  const inicialValido = inicialTexto === '' || variablesActuales.includes(inicialTexto)

  const formularioValido =
    vntValido &&
    vtValido &&
    inicialValido &&
    variablesActuales.length > 0 &&
    inicialTexto !== ''

  // Cada vez que cambia la lista de variables (VNT), se sincroniza el mapa
  // de producciones: se agregan campos vacíos para variables nuevas y se
  // quitan los de variables que ya no existen, sin perder lo que el
  // usuario ya había escrito para las que se mantienen.
  useEffect(() => {
    setProduccionesMapa((anterior) => {
      const nuevo = {}
      variablesActuales.forEach((v) => {
        nuevo[v] = anterior[v] ?? ''
      })
      return nuevo
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [local.variables])

  const actualizar = (campo, val) => {
    setLocal((prev) => ({ ...prev, [campo]: val }))
  }

  const actualizarProduccion = (variable, val) => {
    setProduccionesMapa((prev) => ({ ...prev, [variable]: val }))
  }

  const construirPayload = () => {
    const producciones = variablesActuales
      .filter((v) => produccionesMapa[v]?.trim())
      .map((v) => `${v} -> ${produccionesMapa[v].trim()}`)

    return {
      variables: variablesActuales,
      terminales: local.terminales.split(',').map((s) => s.trim()).filter(Boolean),
      inicial: local.inicial.trim(),
      producciones,
    }
  }

  const generar = async () => {
    setGenerando(true)
    setErrorGenerador(null)
    try {
      const cfg = NIVELES.find((n) => n.valor === nivel)
      const data = await generarEjercicio({
        num_variables: cfg.vars,
        num_terminales: cfg.term,
        producciones_por_variable_min: cfg.prodMin,
        producciones_por_variable_max: cfg.prodMax,
      })
      const nuevo = {
        variables: data.variables.join(', '),
        terminales: data.terminales.join(', '),
        inicial: data.inicial,
        producciones: data.producciones.join('\n'),
      }
      setLocal(nuevo)
      setProduccionesMapa(lineasAMapa(nuevo.producciones))
      onCambiar?.(nuevo)
    } catch (e) {
      setErrorGenerador(e.message)
    } finally {
      setGenerando(false)
    }
  }

  const registrar = () => {
    if (!formularioValido) return
    const payload = construirPayload()
    // Guarda una foto fija de cómo quedó la gramática en el momento de
    // registrar, para el panel "Gramática original" de abajo.
    setGramaticaOriginal({
      variables: variablesActuales,
      terminales: payload.terminales,
      inicial: payload.inicial,
      produccionesPorVariable: Object.fromEntries(
        variablesActuales.map((v) => [
          v,
          (produccionesMapa[v] || '')
            .split('/')
            .map((s) => s.trim())
            .filter(Boolean),
        ])
      ),
    })
    onRegistrar(payload)
  }

  const limpiar = () => {
    setLocal(VACIO)
    setProduccionesMapa({})
    setGramaticaOriginal(null)
    onLimpiar?.()
  }

  return (
    <aside className="space-y-5">
      {/* MODO PRÁCTICA */}
      <div className="border border-dashed border-ambar-500/50 bg-ambar-500/5 rounded-xl p-4 space-y-3">
        <p className="text-[11px] tracking-widest text-ambar-400 font-mono uppercase font-semibold">
          Modo práctica
        </p>
        <p className="text-xs text-slate-400 leading-relaxed">
          Genera una gramática aleatoria en FNC, resuélvela a mano y compara tu respuesta
          con el resultado de "Ejecutar proceso completo".
        </p>

        <div className="flex flex-wrap gap-1.5">
          {NIVELES.map((n) => (
            <button
              key={n.valor}
              onClick={() => setNivel(n.valor)}
              className={`text-[11px] px-2.5 py-1 rounded-full border transition ${
                nivel === n.valor
                  ? 'bg-ambar-500/20 border-ambar-500 text-ambar-400'
                  : 'border-pizarra-600 text-slate-400 hover:border-slate-400'
              }`}
            >
              {n.etiqueta}
            </button>
          ))}
        </div>

        <button
          onClick={generar}
          disabled={generando}
          className="w-full btn-primario text-sm"
        >
          {generando ? 'Generando…' : 'Generar ejercicio aleatorio'}
        </button>
        {errorGenerador && <p className="text-xs text-eliminada">{errorGenerador}</p>}
      </div>

      {/* FORMULARIO DE REGISTRO */}
      <div className="bg-pizarra-800 border border-pizarra-600 rounded-xl p-4 space-y-4">
        <div>
          <p className="font-mono text-sm text-slate-300">G = (V, T, S, P)</p>
          <p className="text-xs text-slate-500 mt-0.5">
            Registra los componentes de tu Gramática Libre de Contexto en FNC.
          </p>
        </div>

        <Campo label="Variables (Vnt)" ejemplo="ej. S, A, B">
          <input
            className={`input ${!vntValido ? 'border-eliminada focus:border-eliminada ring-2 ring-eliminada/30' : ''}`}
            placeholder="S, A, B"
            value={local.variables}
            onChange={(e) => actualizar('variables', e.target.value)}
          />
          {!vntValido && (
            <span className="block text-[10px] text-eliminada mt-1">
              Solo se permiten letras mayúsculas (sin números ni símbolos).
            </span>
          )}
        </Campo>

        <Campo label="Terminales (Vt)" ejemplo="ej. a, b, 1, 2">
          <input
            className={`input ${!vtValido ? 'border-eliminada focus:border-eliminada ring-2 ring-eliminada/30' : ''}`}
            placeholder="a, b"
            value={local.terminales}
            onChange={(e) => actualizar('terminales', e.target.value)}
          />
          {!vtValido && (
            <span className="block text-[10px] text-eliminada mt-1">
              Solo se permiten letras minúsculas o números.
            </span>
          )}
        </Campo>

        <Campo label="Símbolo inicial">
          <input
            className={`input ${!inicialValido ? 'border-eliminada focus:border-eliminada ring-2 ring-eliminada/30' : ''}`}
            placeholder="S"
            value={local.inicial}
            onChange={(e) => actualizar('inicial', e.target.value)}
          />
          {!inicialValido && (
            <span className="block text-[10px] text-eliminada mt-1">
              Debe ser una de las variables (Vnt) declaradas arriba.
            </span>
          )}
        </Campo>

        {variablesActuales.length > 0 && vntValido ? (
          <div className="space-y-2 pt-1 border-t border-pizarra-700">
            <p className="text-[11px] uppercase tracking-widest text-slate-500 font-mono pt-2">
              Producciones
            </p>
            <div className="space-y-2">
              {variablesActuales.map((v) => (
                <div key={v} className="flex items-center gap-2">
                  <div className="flex flex-col items-center w-5 shrink-0">
                    <span className="font-mono text-sm font-bold text-ambar-400">{v}</span>
                    <span className="text-ambar-500/70 text-xs leading-none">→</span>
                  </div>
                  <input
                    className="input font-mono text-xs py-2"
                    placeholder="ej: AB/CD/a/1"
                    value={produccionesMapa[v] ?? ''}
                    onChange={(e) => actualizarProduccion(v, e.target.value)}
                  />
                </div>
              ))}
            </div>
            <p className="text-[10px] text-slate-600">
              alternativas separadas por / (ej: AB/CD/a/1)
            </p>
          </div>
        ) : (
          variablesActuales.length > 0 && (
            <p className="text-[11px] text-eliminada/80 pt-1 border-t border-pizarra-700 pt-2">
              Corrige las variables (Vnt) para poder escribir las producciones.
            </p>
          )
        )}

        <button
          onClick={registrar}
          disabled={cargando || !formularioValido}
          className="w-full bg-pizarra-600 hover:bg-pizarra-600/70 border border-ambar-500/30
                     text-slate-100 font-semibold text-sm px-4 py-2.5 rounded-lg transition
                     disabled:opacity-50"
        >
          Registrar gramática
        </button>
        <button
          onClick={limpiar}
          className="w-full border border-pizarra-600 text-slate-400 hover:text-white hover:border-slate-400
                     text-sm px-4 py-2 rounded-lg transition"
        >
          Limpiar campos
        </button>
      </div>

      {/* GRAMÁTICA ORIGINAL: foto fija de lo registrado, no se actualiza
          mientras se navega por los pasos de la conversión. */}
      {gramaticaOriginal && <GramaticaOriginalBox gramatica={gramaticaOriginal} />}
    </aside>
  )
}

function GramaticaOriginalBox({ gramatica }) {
  const { variables, terminales, inicial, produccionesPorVariable } = gramatica
  return (
    <div className="bg-pizarra-800 border border-pizarra-600 rounded-xl p-4 space-y-3">
      <div className="flex items-start justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <p className="text-[11px] uppercase tracking-widest text-ambar-400 font-mono font-semibold">
            Gramática original
          </p>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded border border-ambar-500/50 text-ambar-400 bg-ambar-500/10">
            Σ0
          </span>
        </div>
        <p className="font-mono text-[11px] text-slate-500 text-right">
          G = ({'{'}{variables.join(', ')}{'}'}, {inicial}, {'{'}{terminales.join(', ')}{'}'}, Σ)
        </p>
      </div>

      <div className="space-y-1.5">
        {variables.map((v) => (
          <div key={v} className="flex items-baseline gap-2 font-mono text-xs">
            <span className="font-bold text-ambar-400 w-4 shrink-0">{v}</span>
            <span className="text-ambar-500/70">→</span>
            {produccionesPorVariable[v]?.length ? (
              <span className="text-slate-300 break-all">
                {produccionesPorVariable[v].join(' / ')}
              </span>
            ) : (
              <span className="text-slate-600 italic">(sin producciones)</span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function Campo({ label, ejemplo, children }) {
  return (
    <label className="block text-xs text-slate-400 space-y-1">
      <span>{label}</span>
      {children}
      {ejemplo && <span className="block text-[10px] text-slate-600">{ejemplo}</span>}
    </label>
  )
}