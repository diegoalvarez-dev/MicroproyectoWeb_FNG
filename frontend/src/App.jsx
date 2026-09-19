import { useState } from 'react'
import GramaticaForm from './components/GramaticaForm'
import GeneradorEjercicios from './components/GeneradorEjercicios'
import ValidacionPanel from './components/ValidacionPanel'
import PasoCard from './components/PasoCard'
import NavegacionPasos from './components/NavegacionPasos'
import ResultadoFinal from './components/ResultadoFinal'
import { validarGramatica, convertirGramatica } from './api'

export default function App() {
  const [gramaticaTexto, setGramaticaTexto] = useState(null)
  const [validacion, setValidacion] = useState(null)
  const [resultado, setResultado] = useState(null)
  const [modo, setModo] = useState('automatico')
  const [pasoActual, setPasoActual] = useState(0)
  const [cargando, setCargando] = useState(false)
  const [errorGeneral, setErrorGeneral] = useState(null)

  const manejarValidar = async (payload) => {
    setCargando(true)
    setErrorGeneral(null)
    try {
      const data = await validarGramatica(payload)
      setValidacion(data)
      setResultado(null)
    } catch (e) {
      setErrorGeneral(e.message)
    } finally {
      setCargando(false)
    }
  }

  const manejarConvertir = async (payload, modoSolicitado) => {
    setCargando(true)
    setErrorGeneral(null)
    setModo(modoSolicitado)
    setPasoActual(0)
    try {
      const data = await convertirGramatica(payload)
      setResultado(data)
      setValidacion(data.validacion_fnc)
    } catch (e) {
      setErrorGeneral(e.data?.error || e.message)
      setResultado(null)
    } finally {
      setCargando(false)
    }
  }

  const manejarEjercicioGenerado = (ejercicio) => {
    setGramaticaTexto({
      variables: ejercicio.variables.join(', '),
      terminales: ejercicio.terminales.join(', '),
      inicial: ejercicio.inicial,
      producciones: ejercicio.producciones.join('\n'),
    })
    setValidacion(null)
    setResultado(null)
  }

  return (
    <div className="min-h-screen pb-16">
      <header className="border-b border-pizarra-700 bg-pizarra-900/70 backdrop-blur sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-ambar-500 flex items-center justify-center font-display font-bold text-pizarra-950">
            Λ
          </div>
          <div>
            <h1 className="font-display font-semibold text-slate-100 leading-tight">
              FNC → FNG
            </h1>
            <p className="text-[11px] text-slate-500 leading-tight">
              Conversor paso a paso a Forma Normal de Greibach · Teoría de la Computación
            </p>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 mt-6 space-y-6">
        <GeneradorEjercicios onGenerado={manejarEjercicioGenerado} />

        <GramaticaForm
          valor={gramaticaTexto}
          onCambiar={setGramaticaTexto}
          onValidar={manejarValidar}
          onConvertir={manejarConvertir}
          cargando={cargando}
        />

        {errorGeneral && (
          <div className="border border-eliminada/40 bg-eliminada/10 text-eliminada rounded-lg px-4 py-3 text-sm">
            {errorGeneral}
          </div>
        )}

        <ValidacionPanel validacion={validacion} />

        {cargando && (
          <div className="text-center text-sm text-slate-400 py-6">
            Procesando conversión…
          </div>
        )}

        {resultado?.exito && (
          <>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setModo('automatico')}
                className={`text-xs px-3 py-1.5 rounded-full border transition ${
                  modo === 'automatico'
                    ? 'bg-ambar-500 text-pizarra-950 border-ambar-500 font-semibold'
                    : 'border-pizarra-600 text-slate-400 hover:border-slate-400'
                }`}
              >
                Ver todo el proceso
              </button>
              <button
                onClick={() => setModo('pasoapaso')}
                className={`text-xs px-3 py-1.5 rounded-full border transition ${
                  modo === 'pasoapaso'
                    ? 'bg-ambar-500 text-pizarra-950 border-ambar-500 font-semibold'
                    : 'border-pizarra-600 text-slate-400 hover:border-slate-400'
                }`}
              >
                Paso a paso
              </button>
            </div>

            {modo === 'automatico' ? (
              <div className="space-y-6">
                {resultado.pasos.map((paso) => (
                  <PasoCard key={paso.numero} paso={paso} />
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                <NavegacionPasos
                  actual={pasoActual}
                  total={resultado.pasos.length}
                  onCambiar={setPasoActual}
                />
                <PasoCard paso={resultado.pasos[pasoActual]} />
              </div>
            )}

            <ResultadoFinal resultado={resultado} />
          </>
        )}

        {resultado && !resultado.exito && resultado.validacion_fnc?.valido === false && (
          <p className="text-sm text-slate-400">
            Corrige los errores de validación de arriba para poder convertir la gramática.
          </p>
        )}
      </main>
    </div>
  )
}
