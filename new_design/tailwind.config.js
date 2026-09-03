/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
        serif: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        // Tailwind's palette steps in hundreds, so half-steps like `zinc-150`
        // or `zinc-650` -- used in ~78 places across the pages -- matched no
        // class and emitted no CSS at all. The colour then fell through to
        // whatever was inherited: the Analytics chart legend, for one, was
        // rendering at 1.22:1, and several "borders" had no colour of their
        // own. These are the midpoints the markup was already asking for, so
        // every existing class now resolves to the shade it names.
        zinc: {
          150: '#ececee',
          250: '#dcdcdf',
          350: '#bbbbc1',
          450: '#898992',
          550: '#62626b',
          650: '#494950',
          750: '#333338',
          850: '#1f1f22',
        },
        emerald: { 450: '#22c58b' },
        amber: { 450: '#f8ae17' },
        purple: { 650: '#8a2bdc' },
        blue: { 650: '#2158e2', 750: '#1d47c4' },
        pulse: {
          // The brand terracotta is unchanged (#D56426 / #B8521C); it moved
          // behind CSS variables only so it lives in one place and can be
          // tuned per theme later if wanted. Every existing
          // `text-pulse-orange` / `bg-pulse-orange` class works unchanged.
          orange: 'rgb(var(--pulse-orange) / <alpha-value>)',
          'orange-hover': 'rgb(var(--pulse-orange-hover) / <alpha-value>)',
          'orange-50': '#FAF3ED',
          cream: '#FAF5EF',
          'cream-border': '#E8CBB3',
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive) / <alpha-value>)",
          foreground: "hsl(var(--destructive-foreground) / <alpha-value>)",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        sidebar: {
          DEFAULT: "hsl(var(--sidebar-background))",
          foreground: "hsl(var(--sidebar-foreground))",
          primary: "hsl(var(--sidebar-primary))",
          "primary-foreground": "hsl(var(--sidebar-primary-foreground))",
          accent: "hsl(var(--sidebar-accent))",
          "accent-foreground": "hsl(var(--sidebar-accent-foreground))",
          border: "hsl(var(--sidebar-border))",
          ring: "hsl(var(--sidebar-ring))",
        },
      },
      borderRadius: {
        xl: "calc(var(--radius) + 4px)",
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        xs: "calc(var(--radius) - 6px)",
      },
      boxShadow: {
        xs: "0 1px 2px 0 rgb(0 0 0 / 0.04)",
        'soft-sm': '0 2px 8px -2px rgba(15, 23, 42, 0.04), 0 1px 4px -1px rgba(15, 23, 42, 0.02)',
        'soft-md': '0 4px 20px -4px rgba(15, 23, 42, 0.06), 0 2px 8px -2px rgba(15, 23, 42, 0.03)',
        'soft-lg': '0 10px 30px -6px rgba(15, 23, 42, 0.08), 0 4px 12px -3px rgba(15, 23, 42, 0.04)',
        'soft-glow': '0 0 20px -3px rgba(213, 100, 38, 0.2)',
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "caret-blink": {
          "0%,70%,100%": { opacity: "1" },
          "20%,50%": { opacity: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "caret-blink": "caret-blink 1.25s ease-out infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}