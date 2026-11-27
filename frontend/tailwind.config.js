/** @type {import('tailwindcss').Config} */
const honey = {
  50: '#fff8e9',
  100: '#fef0d2',
  200: '#f9dfa9',
  300: '#f4d18e',
  400: '#f0c986',
  500: '#e2b76e',
  600: '#c8954e',
  700: '#a8753c',
  800: '#80572f',
  900: '#5b3e28',
  950: '#35231a',
};

const plum = {
  50: '#f9eef7',
  100: '#f0d7eb',
  200: '#e3b4d7',
  300: '#d396be',
  400: '#b76ba2',
  500: '#8e4d7f',
  600: '#713b65',
  700: '#592d50',
  800: '#3b163a',
  900: '#281027',
  950: '#170a18',
};

export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      colors: {
        honey,
        plum,
        void: {
          950: '#09070a',
          900: '#100b12',
          850: '#1a101c',
          800: '#26152a',
        },
        blue: honey,
        sky: honey,
        cyan: honey,
        indigo: plum,
        purple: plum,
        violet: plum,
        wing: {
          blue: '#f0c986',
          cyan: '#e2b76e',
          indigo: '#713b65',
          purple: '#8e4d7f',
          violet: '#b76ba2',
        },
      },
      boxShadow: {
        glass: '0 14px 42px 0 rgba(0, 0, 0, 0.58), inset 0 1px 0 0 rgba(255, 255, 255, 0.07)',
        'glass-lg': '0 24px 70px 0 rgba(0, 0, 0, 0.72), inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
        'glow-blue': '0 0 28px -4px rgba(240, 201, 134, 0.35)',
        'glow-purple': '0 0 28px -4px rgba(142, 77, 127, 0.45)',
        'glow-cyan': '0 0 24px -4px rgba(226, 183, 110, 0.35)',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        'pulse-glow': {
          '0%, 100%': { opacity: '0.45', transform: 'scale(1)' },
          '50%': { opacity: '0.75', transform: 'scale(1.06)' },
        },
        'fade-in-up': {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        float: 'float 6s ease-in-out infinite',
        'pulse-glow': 'pulse-glow 8s ease-in-out infinite',
        'fade-in-up': 'fade-in-up 0.45s ease-out forwards',
      },
    },
  },
  plugins: [],
};
