export default function Encabezado() {
  return (
    <header className="border-b border-pizarra-700 bg-pizarra-900/70 backdrop-blur">
      <div className="max-w-7xl mx-auto px-5 py-4">
        <p className="text-[11px] tracking-widest text-ambar-400 font-mono uppercase">
          Teoría de la Computación · By Diego Alvarez, Diego Marquez y Juan Quintero
        </p>
        <h1 className="font-display font-semibold text-2xl text-slate-100 mt-0.5">
          Conversor de Gramáticas <span className="text-ambar-400">FNC → FNG</span>
        </h1>
      </div>
    </header>
  )
}
