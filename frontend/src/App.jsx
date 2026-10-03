import { useState } from 'react'
import Encabezado from './components/Encabezado'
import Sidebar from './components/Sidebar'
import BarraAcciones from './components/BarraAcciones'
import ValidacionPanel from './components/ValidacionPanel'
import GramaticaActualBox from './components/GramaticaActualBox'
import HistorialTransformaciones from './components/HistorialTransformaciones'
import ResultadoFinal from './components/ResultadoFinal'
import { validarGramatica, convertirGramatica } from './api'

export default function App() {
  const [gramaticaTexto, setGramaticaTexto] = useState(null)
  const [gramaticaRegistrada, setGramaticaRegistrada] = useState(null) // payload ya parseado
  const [validacion, setValidacion] = useState(null)
  const [resultado, setResultado] = useState(null)
  // Cuántos pasos del historial se muestran. 0 = ninguno todavía.
  // Esto es lo que hace que el "modo paso a paso" sea real: aunque el
  // backend calcula el pipeline completo en una sola llamada, el frontend
  // solo REVELA los pasos hasta este número, nunca todos de una vez.
  const [pasoMaximoVisible, setPasoMaximoVisible] = useState(0)
  const [cargando, setCargando] = useState(false)
  const [errorGeneral, setErrorGeneral] = useState(null)

  const registrar = (payload) => {
    setGramaticaRegistrada(payload)
    setValidacion(null)
    setResultado(null)
    setErrorGeneral(null)
    setPasoMaximoVisible(0)
  }

  const limpiarTodo = () => {
    setGramaticaTexto(null)
    setGramaticaRegistrada(null)
    setValidacion(null)
    setResultado(null)
    setErrorGeneral(null)
    setPasoMaximoVisible(0)
  }

  const validar = async () => {
    if (!gramaticaRegistrada) {
      setErrorGeneral('Primero registra una gramática.')
      return
    }
    setCargando(true)
    setErrorGeneral(null)
    try {
      const data = await validarGramatica(gramaticaRegistrada)
      setValidacion(data)
    } catch (e) {
      setErrorGeneral(e.message)
    } finally {
      setCargando(false)
    }
  }

  // Asegura que el resultado completo esté calculado (una sola llamada al
  // backend), sin revelar nada todavía. Devuelve el resultado.
  const asegurarResultado = async () => {
    if (resultado) return resultado
    if (!gramaticaRegistrada) {
      setErrorGeneral('Primero registra una gramática con "Registrar gramática".')
      return null
    }
    setCargando(true)
    setErrorGeneral(null)
    try {
      const data = await convertirGramatica(gramaticaRegistrada)
      setResultado(data)
      setValidacion(data.validacion_fnc)
      return data
    } catch (e) {
      setErrorGeneral(e.data?.error || e.message)
      setResultado(null)
      return null
    } finally {
      setCargando(false)
    }
  }

  // Click en "Ejecutar proceso completo": calcula (si hace falta) y
  // revela TODOS los pasos de una vez.
  const ejecutarCompleto = async () => {
    const data = await asegurarResultado()
    if (data?.exito) setPasoMaximoVisible(data.pasos.length)
  }

  // Click en el botón de un paso puntual (ej. "2. Recursividad indirecta"):
  // calcula (si hace falta) y revela SOLO hasta ese paso, ni uno más.
  const irAPaso = async (indice) => {
    const data = await asegurarResultado()
    if (data?.exito) setPasoMaximoVisible(indice + 1)
  }

  const pasosVisibles = resultado ? resultado.pasos.slice(0, pasoMaximoVisible) : []
  const ultimoPasoVisible = pasosVisibles[pasosVisibles.length - 1]
  const procesoCompletoVisible = resultado && pasoMaximoVisible >= resultado.pasos.length

  const cajaGramaticaActual = ultimoPasoVisible
    ? {
        variables: ultimoPasoVisible.variables,
        terminales: resultado.terminales,
        inicial: ultimoPasoVisible.variables[0],
        texto: ultimoPasoVisible.gramatica_resultante,
      }
    : gramaticaRegistrada
    ? {
        variables: gramaticaRegistrada.variables,
        terminales: gramaticaRegistrada.terminales,
        inicial: gramaticaRegistrada.inicial,
        texto: gramaticaRegistrada.producciones.map((l) => l.replaceAll('/', ' | ')).join('\n'),
      }
    : null

  return (
    <div className="min-h-screen pb-16">
      <Encabezado />

      <main className="max-w-7xl mx-auto px-5 mt-6 grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-6">
        <Sidebar
          valor={gramaticaTexto}
          onCambiar={setGramaticaTexto}
          onRegistrar={registrar}
          onLimpiar={limpiarTodo}
          cargando={cargando}
        />

        <div className="space-y-6 min-w-0">
          <BarraAcciones
            onValidar={validar}
            onIrAPaso={irAPaso}
            onEjecutarCompleto={ejecutarCompleto}
            onNuevaGramatica={limpiarTodo}
            cargando={cargando}
            pasoActualVisible={pasoMaximoVisible}
          />

          {errorGeneral && (
            <div className="border border-eliminada/40 bg-eliminada/10 text-eliminada rounded-lg px-4 py-3 text-sm">
              {errorGeneral}
            </div>
          )}

          <ValidacionPanel validacion={validacion} />

          {cargando && (
            <div className="text-center text-sm text-slate-400 py-4">Procesando…</div>
          )}

          {cajaGramaticaActual && (
            <GramaticaActualBox {...cajaGramaticaActual} indiceSigma={pasoMaximoVisible} />
          )}

          {pasosVisibles.length > 0 && (
            <HistorialTransformaciones pasos={pasosVisibles} terminales={resultado.terminales} />
          )}

          {procesoCompletoVisible && <ResultadoFinal resultado={resultado} />}
        </div>
      </main>
    </div>
  )
}