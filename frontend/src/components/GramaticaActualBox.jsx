import { notacionTupla, agruparPorVariable } from '../utils'

export default function GramaticaActualBox({ variables, terminales, inicial, texto, indiceSigma }) {
  if (!texto) return null
  const grupos = agruparPorVariable(texto)

  return (
    <div className="bg-pizarra-800 border border-pizarra-600 rounded-xl p-5">
      <div className="flex items-start justify-between gap-3 flex-wrap mb-3">
        <div className="flex items-center gap-2">
          <h2 className="font-display font-semibold text-slate-100">Gramática actual</h2>
          <span className="font-mono text-xs bg-ambar-500/15 text-ambar-400 border border-ambar-500/40 rounded px-2 py-0.5">
            Σ{indiceSigma}
          </span>
        </div>
        <p className="font-mono text-xs text-slate-500">
          {notacionTupla({ variables, terminales, inicial })}
        </p>
      </div>

      <div className="space-y-1.5">
        {grupos.map(([cabeza, alternativas], i) => (
          <div key={i} className="flex flex-wrap items-baseline gap-1">
            <span className="font-mono text-sm font-semibold text-ambar-400">{cabeza}</span>
            <span className="text-ambar-500/70">→</span>
            <div className="flex flex-wrap gap-x-2 gap-y-1">
              {alternativas.map((alt, j) => (
                <span key={j} className="font-mono text-sm text-slate-300">
                  {alt}
                  {j < alternativas.length - 1 && <span className="text-slate-600"> | </span>}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
