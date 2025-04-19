/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f5f7ff',
          100: '#ebeefe',
          200: '#d3d8fc',
          300: '#b2b9f9',
          400: '#8a8ef5',
          500: '#6263ef',
          600: '#4d42e3',
          700: '#4336cc',
          800: '#382da5',
          900: '#322c85',
        },
        blue: {
          50: '#edf4ff',
          100: '#dde9fe',
          200: '#c2d5fe',
          300: '#9abafc',
          400: '#7499f9',
          500: '#4c74f5',
          600: '#3252eb',
          700: '#2941d3',
          800: '#2437ab',
          900: '#223189',
        },
        green: {
          50: '#edfcf5',
          100: '#d3f8e6',
          200: '#aaefd0',
          300: '#73e1b1',
          400: '#3eca8c',
          500: '#19ad6f',
          600: '#0e905c',
          700: '#0c744b',
          800: '#0d5c3d',
          900: '#0d4c34',
        },
        purple: {
          50: '#faf5ff',
          100: '#f3e8ff',
          200: '#e9d5ff',
          300: '#d8b4fe',
          400: '#c084fc',
          500: '#a855f7',
          600: '#9333ea',
          700: '#7e22ce',
          800: '#6b21a8',
          900: '#581c87',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      boxShadow: {
        card: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      },
    },
  },
  plugins: [],
} 