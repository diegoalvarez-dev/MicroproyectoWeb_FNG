import ProduccionLinea from './ProduccionLinea'
import { notacionTupla } from '../utils'

function EventoIndividual({ evento, terminales, variablesInicial, variablesFinal }) {
  const sinCambios = !evento.variable && (!evento.producciones_antes || evento.producciones_antes.length === 0)

  if (sinCambios) {
    return (
      <p className="text-sm text-slate-400 italic border-l-2 border-pizarra-600 pl-3 py-1">
        {evento.descripcion}
      </p>
    )
  }

  return (
    <div className="border border-pizarra-600 rounded-lg overflow-hidden bg-pizarra-900/50">
      <div className="px-4 pt-3 pb-2 border-b border-pizarra-700">
        <p className="text-sm text-slate-300">{evento.descripcion}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-pizarra-700">
        <div className="p-4 space-y-2">
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Antes</p>
          {variablesInicial && (
            <p className="font-mono text-[11px] text-slate-600">
              {notacionTupla({ variables: variablesInicial, terminales, inicial: variablesInicial[0] })}
            </p>
          )}
          <div className="flex flex-wrap gap-1.5">
            {evento.producciones_antes?.map((p, i) => (
              <ProduccionLinea key={i} texto={p.texto} estado={p.estado} />
            ))}
          </div>
        </div>
        <div className="p-4 space-y-2">
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Después</p>
          {variablesFinal && (
            <p className="font-mono text-[11px] text-slate-600">
              {notacionTupla({ variables: variablesFinal, terminales, inicial: variablesFinal[0] })}
            </p>
          )}
          <div className="flex flex-wrap gap-1.5">
            {evento.producciones_despues?.map((p, i) => (
              <ProduccionLinea key={i} texto={p.texto} estado={p.estado} />
            ))}
          </div>
        </div>
      </div>

      {evento.variable_nueva && (
        <div className="px-4 py-3 bg-nueva/5 border-t border-nueva/20">
          <p className="text-[11px] text-nueva mb-1.5">
            ✦ variable auxiliar nueva: <span className="font-mono">{evento.variable_nueva}</span>
          </p>
          <div className="flex flex-wrap gap-1.5">
            {evento.producciones_variable_nueva.map((p, i) => (
              <ProduccionLinea key={i} texto={p.texto} estado={p.estado} />
            ))}
          </div>
        </div>
      )}

      {evento.variable && (
        <div className="px-4 py-2 bg-pizarra-950/60 border-t border-pizarra-700">
          <span className="text-[11px] text-slate-500">Identificado: </span>
          <span className="font-mono text-xs bg-ambar-500/15 text-ambar-400 border border-ambar-500/40 rounded px-2 py-0.5">
            {evento.variable}
          </span>
        </div>
      )}
    </div>
  )
}

export default function HistorialTransformaciones({ pasos, terminales }) {
  return (
    <div className="space-y-6">
      <h2 className="font-display font-semibold text-lg text-slate-100">
        Historial de transformaciones
      </h2>
      {pasos.map((paso, idx) => {
        const variablesPrevias = idx > 0 ? pasos[idx - 1].variables : null
        return (
          <div
            key={paso.numero}
            className="bg-pizarra-800 border border-ambar-500/40 rounded-xl p-5 space-y-4"
          >
            <div className="flex items-center gap-3">
              <span className="flex items-center justify-center w-8 h-8 rounded-full bg-ambar-500 text-pizarra-950 font-bold text-sm shrink-0">
                {paso.numero}
              </span>
              <h3 className="font-display font-semibold text-slate-100">{paso.titulo}</h3>
              <span className="ml-auto font-mono text-[11px] text-slate-500">
                Σ{idx} → Σ{idx + 1}
              </span>
            </div>

            <p className="text-sm text-slate-400">{paso.descripcion_general}</p>

            {paso.mapa_equivalencia && (
              <div className="flex flex-wrap gap-2">
                {Object.entries(paso.mapa_equivalencia).map(([orig, nuevo]) => (
                  <span
                    key={orig}
                    className="font-mono text-xs bg-pizarra-900 border border-pizarra-600 rounded px-2 py-1 text-slate-300"
                  >
                    {orig} <span className="text-ambar-400">→</span> {nuevo}
                  </span>
                ))}
              </div>
            )}

            {paso.eventos?.length > 0 && (
              <div className="space-y-3">
                {paso.eventos.map((ev, i) => (
                  <EventoIndividual
                    key={i}
                    evento={ev}
                    terminales={terminales}
                    variablesInicial={variablesPrevias}
                    variablesFinal={paso.variables}
                  />
                ))}
              </div>
            )}

            <div>
              <p className="text-[11px] text-slate-500 mb-1">gramática resultante de este paso</p>
              {paso.producciones_por_variable ? (
                <div className="font-mono text-xs bg-pizarra-950 border border-pizarra-700 rounded-lg p-3 overflow-x-auto scrollbar-delgada space-y-1.5">
                  {Object.entries(paso.producciones_por_variable).map(([cabeza, alternativas], i) => (
                    <div key={i} className="flex flex-wrap items-baseline gap-1">
                      <span className="font-semibold text-ambar-400">{cabeza}</span>
                      <span className="text-ambar-500/70">→</span>
                      <div className="flex flex-wrap gap-x-1.5 gap-y-1">
                        {alternativas.map((alt, j) => (
                          <span
                            key={j}
                            className={
                              alt.estado === 'nueva'
                                ? 'text-nueva font-semibold'
                                : 'text-slate-300'
                            }
                          >
                            {alt.cuerpo}
                            {j < alternativas.length - 1 && (
                              <span className="text-slate-600"> | </span>
                            )}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <pre className="font-mono text-xs bg-pizarra-950 border border-pizarra-700 rounded-lg p-3 overflow-x-auto scrollbar-delgada text-slate-300 whitespace-pre">
                  {paso.gramatica_resultante}
                </pre>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}