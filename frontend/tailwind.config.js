/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
        display: ['"Space Grotesk"', 'sans-serif'],
      },
      colors: {
        // Paleta propia del proyecto: tema "gramática / derivación",
        // fondo oscuro tipo pizarra con acentos ámbar (símbolo terminal
        // inicial de toda producción en Greibach) y verde/rosa para
        // marcar sustituciones nuevas / eliminadas.
        pizarra: {
          950: '#0b0f14',
          900: '#0f1620',
          800: '#161f2c',
          700: '#1f2b3a',
          600: '#2b3a4d',
        },
        ambar: {
          400: '#f2b84b',
          500: '#e2a53a',
        },
        nueva: {
          DEFAULT: '#34d399',
          bg: 'rgba(52,211,153,0.12)',
        },
        eliminada: {
          DEFAULT: '#fb7185',
          bg: 'rgba(251,113,133,0.10)',
        },
      },
    },
  },
  plugins: [],
}
