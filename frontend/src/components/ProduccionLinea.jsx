export default function ProduccionLinea({ texto, estado }) {
  const base = 'font-mono text-sm px-2 py-1 rounded whitespace-nowrap'
  if (estado === 'eliminada') {
    return <span className={`${base} tachado`}>{texto}</span>
  }
  if (estado === 'nueva') {
    return <span className={`${base} resaltado-nueva`}>{texto}</span>
  }
  return <span className={`${base} text-slate-300`}>{texto}</span>
}
