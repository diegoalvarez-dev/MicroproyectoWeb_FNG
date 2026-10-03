const PASOS_NOMBRES = [
  'Renombrado de variables',
  'Recursividad indirecta',
  'Recursividad inmediata',
  'Orden de índices',
  'Sustitución final',
]

export default function BarraAcciones({
  onValidar,
  onIrAPaso,
  onEjecutarCompleto,
  onNuevaGramatica,
  cargando,
  pasoActualVisible,
}) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <button onClick={onValidar} disabled={cargando} className="btn-secundario">
          Validar
        </button>

        {PASOS_NOMBRES.map((nombre, i) => {
          const yaRevelado = pasoActualVisible > i
          return (
            <button
              key={nombre}
              onClick={() => onIrAPaso(i)}
              disabled={cargando}
              title={`Ejecutar / mostrar solo hasta el paso ${i + 1}`}
              className={`text-xs px-3 py-2 rounded-lg border transition disabled:opacity-50 ${
                yaRevelado
                  ? 'border-ambar-500/60 bg-ambar-500/10 text-ambar-400'
                  : 'border-pizarra-600 text-slate-300 hover:border-ambar-500/60 hover:text-ambar-400'
              }`}
            >
              {i + 1}. {nombre}
            </button>
          )
        })}

        <button
          onClick={onNuevaGramatica}
          className="ml-auto text-xs px-3 py-2 rounded-lg border border-eliminada/50 text-eliminada
                     hover:bg-eliminada/10 transition"
        >
          Nueva gramática
        </button>
      </div>

      <button
        onClick={onEjecutarCompleto}
        disabled={cargando}
        className="w-full sm:w-auto btn-primario text-sm px-6 py-2.5"
      >
        {cargando ? 'Ejecutando…' : '▶ Ejecutar proceso completo'}
      </button>
    </div>
  )
}