/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#1976D2',
        'primary-dark': '#1565C0',
        secondary: '#757575',
        success: '#4CAF50',
        danger: '#F44336',
        background: '#FAFAFA',
        surface: '#FFFFFF',
        line: '#E0E0E0',
        ink: '#212121',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
