import { useState } from 'react'
import { generarEjercicio } from '../api'

const NIVELES = [
  { valor: 'facil', etiqueta: 'Fácil', vars: 3 },
  { valor: 'media', etiqueta: 'Media', vars: 4 },
  { valor: 'dificil', etiqueta: 'Difícil', vars: 5 },
]

export default function GeneradorEjercicios({ onGenerado }) {
  const [nivel, setNivel] = useState('media')
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState(null)

  const generar = async () => {
    setCargando(true)
    setError(null)
    try {
      const cfg = NIVELES.find((n) => n.valor === nivel)
      const data = await generarEjercicio({
        num_variables: cfg.vars,
        num_terminales: nivel === 'dificil' ? 3 : 2,
      })
      onGenerado(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="bg-pizarra-800 border border-pizarra-600 rounded-xl p-5 space-y-3">
      <h2 className="font-display font-semibold text-lg text-slate-100">
        Generar ejercicio para practicar
      </h2>
      <p className="text-xs text-slate-400">
        Crea una gramática FNC aleatoria con recursividad (inmediata y/o indirecta) para
        que la resuelvas a mano y luego la compares con el resultado del sistema.
      </p>

      <div className="flex flex-wrap items-center gap-2">
        {NIVELES.map((n) => (
          <button
            key={n.valor}
            onClick={() => setNivel(n.valor)}
            className={`text-xs px-3 py-1.5 rounded-full border transition ${
              nivel === n.valor
                ? 'bg-nueva/20 border-nueva text-nueva'
                : 'border-pizarra-600 text-slate-400 hover:border-slate-400'
            }`}
          >
            {n.etiqueta}
          </button>
        ))}
        <button onClick={generar} disabled={cargando} className="btn-primario ml-auto">
          {cargando ? 'Generando…' : '🎲 Generar ejercicio'}
        </button>
      </div>

      {error && <p className="text-xs text-eliminada">{error}</p>}
    </div>
  )
}
