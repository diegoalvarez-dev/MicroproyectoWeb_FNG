export default function NavegacionPasos({ actual, total, onCambiar }) {
  return (
    <div className="flex items-center justify-between bg-pizarra-800 border border-pizarra-600 rounded-xl px-4 py-3">
      <button
        onClick={() => onCambiar(Math.max(0, actual - 1))}
        disabled={actual === 0}
        className="btn-secundario"
      >
        ← Anterior
      </button>

      <div className="flex items-center gap-1.5">
        {Array.from({ length: total }).map((_, i) => (
          <button
            key={i}
            onClick={() => onCambiar(i)}
            className={`w-2.5 h-2.5 rounded-full transition ${
              i === actual ? 'bg-ambar-500 w-6' : 'bg-pizarra-600 hover:bg-pizarra-600/70'
            }`}
            aria-label={`Ir al paso ${i + 1}`}
          />
        ))}
        <span className="ml-2 text-xs text-slate-400 font-mono">
          paso {actual + 1} / {total}
        </span>
      </div>

      <button
        onClick={() => onCambiar(Math.min(total - 1, actual + 1))}
        disabled={actual === total - 1}
        className="btn-primario"
      >
        Siguiente paso →
      </button>
    </div>
  )
}
