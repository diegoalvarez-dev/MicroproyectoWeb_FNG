export default function ValidacionPanel({ validacion }) {
  if (!validacion) return null

  if (validacion.valido) {
    return (
      <div className="border border-nueva/40 bg-nueva/10 text-nueva rounded-lg px-4 py-3 text-sm">
        ✓ La gramática ingresada cumple con la Forma Normal de Chomsky.
      </div>
    )
  }

  return (
    <div className="border border-eliminada/40 bg-eliminada/10 rounded-lg px-4 py-3 space-y-2">
      <p className="text-sm text-eliminada font-semibold">
        ✕ La gramática no cumple con la Forma Normal de Chomsky:
      </p>
      <ul className="space-y-1">
        {validacion.errores.map((e, i) => (
          <li key={i} className="text-xs text-slate-300">
            <span className="font-mono text-eliminada">[{e.codigo}]</span> {e.mensaje}
            {e.produccion && (
              <span className="font-mono text-slate-500"> ({e.produccion})</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
