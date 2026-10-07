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
        // Paleta "gramática / derivación", fondo oscuro tipo pizarra.
        // Acento principal (clave "ambar", por compatibilidad con las
        // clases ya usadas en los componentes) ahora es violeta digital.
        // "nueva"/"eliminada" son colores semánticos del historial
        // (producciones nuevas / eliminadas) y no cambian.
        pizarra: {
          950: '#0b0f14',
          900: '#0f1620',
          800: '#161f2c',
          700: '#1f2b3a',
          600: '#2b3a4d',
        },
        ambar: {
          400: '#a78bfa',
          500: '#8b5cf6',
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