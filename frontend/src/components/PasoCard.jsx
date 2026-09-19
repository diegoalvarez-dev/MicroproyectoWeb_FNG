import ProduccionLinea from './ProduccionLinea'

function BloqueEvento({ evento }) {
  const sinCambios =
    !evento.variable &&
    (!evento.producciones_antes || evento.producciones_antes.length === 0)

  if (sinCambios) {
    return (
      <p className="text-sm text-slate-400 italic border-l-2 border-pizarra-600 pl-3">
        {evento.descripcion}
      </p>
    )
  }

  return (
    <div className="border border-pizarra-600 rounded-lg p-4 space-y-3 bg-pizarra-900/60">
      {evento.variable && (
        <p className="text-xs uppercase tracking-wide text-ambar-400 font-semibold">
          Variable {evento.variable}
        </p>
      )}
      <p className="text-sm text-slate-300">{evento.descripcion}</p>

      {evento.producciones_antes?.length > 0 && (
        <div>
          <p className="text-[11px] text-slate-500 mb-1">antes</p>
          <div className="flex flex-wrap gap-1.5 scrollbar-delgada overflow-x-auto pb-1">
            {evento.producciones_antes.map((p, i) => (
              <ProduccionLinea key={i} texto={p.texto} estado={p.estado} />
            ))}
          </div>
        </div>
      )}

      {evento.producciones_despues?.length > 0 && (
        <div>
          <p className="text-[11px] text-slate-500 mb-1">después</p>
          <div className="flex flex-wrap gap-1.5 scrollbar-delgada overflow-x-auto pb-1">
            {evento.producciones_despues.map((p, i) => (
              <ProduccionLinea key={i} texto={p.texto} estado={p.estado} />
            ))}
          </div>
        </div>
      )}

      {evento.variable_nueva && (
        <div className="pt-1 border-t border-pizarra-700">
          <p className="text-[11px] text-nueva mb-1">
            ✦ nueva variable auxiliar: {evento.variable_nueva}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {evento.producciones_variable_nueva.map((p, i) => (
              <ProduccionLinea key={i} texto={p.texto} estado={p.estado} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default function PasoCard({ paso }) {
  return (
    <div className="bg-pizarra-800 border border-pizarra-600 rounded-xl p-5 space-y-4">
      <div className="flex items-center gap-3">
        <span className="flex items-center justify-center w-8 h-8 rounded-full bg-ambar-500 text-pizarra-950 font-bold text-sm shrink-0">
          {paso.numero}
        </span>
        <h3 className="font-display font-semibold text-slate-100">{paso.titulo}</h3>
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
            <BloqueEvento key={i} evento={ev} />
          ))}
        </div>
      )}

      <div>
        <p className="text-[11px] text-slate-500 mb-1">gramática resultante</p>
        <pre className="font-mono text-xs bg-pizarra-950 border border-pizarra-700 rounded-lg p-3 overflow-x-auto scrollbar-delgada text-slate-300 whitespace-pre">
          {paso.gramatica_resultante}
        </pre>
      </div>
    </div>
  )
}
