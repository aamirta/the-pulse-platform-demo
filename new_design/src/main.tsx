import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
// --- Visual Enhancement Layer (additive; disable via VITE_VISUAL_ENHANCEMENTS=false or ?ve=off) ---
import '@/enhancements/enhancements.css'
import { initEnhancements } from '@/enhancements/flags'
import App from './App.tsx'

initEnhancements()
import { ThemeProvider } from '@/hooks/useTheme'
import { LanguageProvider } from '@/context/LanguageContext'
import { AuthProvider } from '@/context/AuthContext'
import { Toaster } from '@/components/ui/sonner'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <LanguageProvider>
        <AuthProvider>
          <App />
          <Toaster position="bottom-right" richColors closeButton />
        </AuthProvider>
      </LanguageProvider>
    </ThemeProvider>
  </StrictMode>,
)
