import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'


// Add this at the top of your index.js or App.js file
if (typeof globalThis === 'undefined') {
  (window as any).globalThis = window;
}


createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
