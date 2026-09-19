import { useState, useEffect } from 'react'

const EJEMPLO = {
  variables: 'S, A, B',
  terminales: 'a, b',
  inicial: 'S',
  producciones: 'S -> AB/a\nA -> SB/a\nB -> b',
}

export default function GramaticaForm({ valor, onCambiar, onValidar, onConvertir, cargando }) {
  const [local, setLocal] = useState(valor || EJEMPLO)

  useEffect(() => {
    if (valor) setLocal(valor)
  }, [valor])

  useEffect(() => {
    try {
      localStorage.setItem('fng_ultima_gramatica', JSON.stringify(local))
    } catch (e) { /* almacenamiento no disponible, se ignora */ }
  }, [local])

  const actualizar = (campo, val) => {
    const nuevo = { ...local, [campo]: val }
    setLocal(nuevo)
    onCambiar?.(nuevo)
  }

  const construirPayload = () => ({
    variables: local.variables.split(',').map((s) => s.trim()).filter(Boolean),
    terminales: local.terminales.split(',').map((s) => s.trim()).filter(Boolean),
    inicial: local.inicial.trim(),
    producciones: local.producciones.split('\n').map((s) => s.trim()).filter(Boolean),
  })

  return (
    <div className="bg-pizarra-800 border border-pizarra-600 rounded-xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-display font-semibold text-lg text-slate-100">
          Gramática en FNC
        </h2>
        <button
          onClick={() => { setLocal(EJEMPLO); onCambiar?.(EJEMPLO) }}
          className="text-xs text-slate-400 hover:text-ambar-400 transition"
        >
          cargar ejemplo
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <Campo label="Variables (Vnt)" placeholder="S, A, B">
          <input
            className="input"
            value={local.variables}
            onChange={(e) => actualizar('variables', e.target.value)}
          />
        </Campo>
        <Campo label="Terminales (Vt)" placeholder="a, b">
          <input
            className="input"
            value={local.terminales}
            onChange={(e) => actualizar('terminales', e.target.value)}
          />
        </Campo>
        <Campo label="Símbolo inicial" placeholder="S">
          <input
            className="input"
            value={local.inicial}
            onChange={(e) => actualizar('inicial', e.target.value)}
          />
        </Campo>
      </div>

      <Campo label="Producciones (una variable por línea, alternativas separadas por / )">
        <textarea
          className="input font-mono h-32 resize-y"
          placeholder={'S -> AB/a\nA -> SB/a\nB -> b'}
          value={local.producciones}
          onChange={(e) => actualizar('producciones', e.target.value)}
        />
      </Campo>

      <div className="flex flex-wrap gap-3 pt-1">
        <button
          disabled={cargando}
          onClick={() => onValidar(construirPayload())}
          className="btn-secundario"
        >
          Validar FNC
        </button>
        <button
          disabled={cargando}
          onClick={() => onConvertir(construirPayload(), 'automatico')}
          className="btn-primario"
        >
          Conversión automática
        </button>
        <button
          disabled={cargando}
          onClick={() => onConvertir(construirPayload(), 'pasoapaso')}
          className="btn-primario-outline"
        >
          Modo paso a paso
        </button>
      </div>
    </div>
  )
}

function Campo({ label, children }) {
  return (
    <label className="block text-xs text-slate-400 space-y-1">
      <span>{label}</span>
      {children}
    </label>
  )
}
