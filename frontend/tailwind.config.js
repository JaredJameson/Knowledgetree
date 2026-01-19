/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Enable dark mode with class strategy
  theme: {
    extend: {
      // Color system - Pastel palette with semantic tokens
      colors: {
        // Primary (Pastel Blue)
        primary: {
          50: '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#3B82F6', // Default primary
          600: '#2563EB',
          700: '#1D4ED8',
          800: '#1E40AF',
          900: '#1E3A8A',
        },
        // Success (Pastel Green)
        success: {
          50: '#F0FDF4',
          100: '#DCFCE7',
          200: '#BBF7D0',
          300: '#86EFAC',
          400: '#4ADE80',
          500: '#22C55E', // Default success
          600: '#16A34A',
          700: '#15803D',
          800: '#166534',
          900: '#14532D',
        },
        // Warning (Pastel Amber)
        warning: {
          50: '#FFFBEB',
          100: '#FEF3C7',
          200: '#FDE68A',
          300: '#FCD34D',
          400: '#FBBF24',
          500: '#F59E0B', // Default warning
          600: '#D97706',
          700: '#B45309',
          800: '#92400E',
          900: '#78350F',
        },
        // Error (Pastel Red)
        error: {
          50: '#FEF2F2',
          100: '#FEE2E2',
          200: '#FECACA',
          300: '#FCA5A5',
          400: '#F87171',
          500: '#EF4444', // Default error
          600: '#DC2626',
          700: '#B91C1C',
          800: '#991B1B',
          900: '#7F1D1D',
        },
        // Neutrals (Grayscale)
        neutral: {
          50: '#FAFAFA',
          100: '#F5F5F5',
          200: '#E5E5E5',
          300: '#D4D4D4',
          400: '#A3A3A3',
          500: '#737373',
          600: '#525252',
          700: '#404040',
          800: '#262626',
          900: '#171717',
        },
        // Category colors (8 pastels for category tree)
        category: {
          lavender: '#E6E6FA',
          mint: '#E0F8F1',
          peach: '#FFE5D9',
          sky: '#E0F4FF',
          rose: '#FFE5E5',
          lemon: '#FFFACD',
          sage: '#E8F5E9',
          lilac: '#F3E5F5',
        },
      },
      // Typography - Inter font family
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
      // Font sizes (type scale)
      fontSize: {
        'display-lg': ['3rem', { lineHeight: '1.2', fontWeight: '700' }],       // 48px
        'display': ['2.5rem', { lineHeight: '1.2', fontWeight: '700' }],         // 40px
        'heading-lg': ['2rem', { lineHeight: '1.25', fontWeight: '600' }],       // 32px
        'heading': ['1.5rem', { lineHeight: '1.25', fontWeight: '600' }],        // 24px
        'heading-sm': ['1.25rem', { lineHeight: '1.25', fontWeight: '600' }],    // 20px
        'xl': ['1.25rem', { lineHeight: '1.5' }],                                // 20px
        'lg': ['1.125rem', { lineHeight: '1.5' }],                               // 18px
        'base': ['1rem', { lineHeight: '1.5' }],                                 // 16px
        'sm': ['0.875rem', { lineHeight: '1.5' }],                               // 14px
        'xs': ['0.75rem', { lineHeight: '1.5' }],                                // 12px
      },
      // Spacing (8px base scale)
      spacing: {
        '1': '0.25rem',  // 4px
        '2': '0.5rem',   // 8px (base unit)
        '3': '0.75rem',  // 12px
        '4': '1rem',     // 16px (default gap)
        '5': '1.25rem',  // 20px
        '6': '1.5rem',   // 24px (large gap)
        '8': '2rem',     // 32px (section gap)
        '10': '2.5rem',  // 40px
        '12': '3rem',    // 48px
        '16': '4rem',    // 64px
        '20': '5rem',    // 80px
        '24': '6rem',    // 96px
      },
      // Border radius
      borderRadius: {
        'none': '0',
        'sm': '0.25rem',   // 4px
        'md': '0.5rem',    // 8px (default)
        'lg': '0.75rem',   // 12px
        'xl': '1rem',      // 16px
        'full': '9999px',  // pills
      },
      // Box shadow (5 elevation levels)
      boxShadow: {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
      },
      // Animation durations
      transitionDuration: {
        '100': '100ms',
        '150': '150ms',
        '200': '200ms',
        '300': '300ms',
      },
    },
  },
  plugins: [],
}
