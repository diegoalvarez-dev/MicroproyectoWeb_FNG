export default function ResultadoFinal({ resultado }) {
  if (!resultado || !resultado.exito) return null

  return (
    <div className="bg-gradient-to-br from-pizarra-800 to-pizarra-900 border border-nueva/40 rounded-xl p-5 space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-nueva text-xl">✓</span>
        <h2 className="font-display font-semibold text-lg text-slate-100">
          Gramática en Forma Normal de Greibach
        </h2>
      </div>
      <p className="text-xs text-slate-400">
        {resultado.total_variables} variables · {resultado.total_producciones} producciones ·
        validación automática de FNG superada
      </p>
      <pre className="font-mono text-xs bg-pizarra-950 border border-pizarra-700 rounded-lg p-4 overflow-x-auto scrollbar-delgada text-nueva/90 whitespace-pre">
        {resultado.gramatica_final}
      </pre>
    </div>
  )
}
