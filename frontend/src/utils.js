export function notacionTupla({ variables = [], terminales = [], inicial = '', prefijo = 'G' }) {
  const V = `{${variables.join(', ')}}`
  const T = `{${terminales.join(', ')}}`
  return `${prefijo} = (${V}, ${inicial}, ${T}, Σ)`}

// Agrupa un texto de gramática "A -> BC | c\nB -> ..." en pares [variable, [alternativas]]
export function agruparPorVariable(texto) {
  if (!texto) return []
  return texto
    .split('\n')
    .map((linea) => linea.split('->'))
    .filter((p) => p.length === 2)
    .map(([cabeza, cuerpo]) => [
      cabeza.trim(),
      cuerpo.split('|').map((s) => s.trim()),
    ])
}