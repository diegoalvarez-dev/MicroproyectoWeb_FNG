const BASE = '/api'

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const err = new Error(data.error || data.mensaje || 'Error en la petición')
    err.data = data
    throw err
  }
  return data
}

export function validarGramatica(gramatica) {
  return post('/validar', gramatica)
}

export function convertirGramatica(gramatica, ordenManual) {
  return post('/convertir', { ...gramatica, orden_manual: ordenManual || null })
}

export function generarEjercicio(params) {
  return post('/generar-ejercicio', params || {})
}
