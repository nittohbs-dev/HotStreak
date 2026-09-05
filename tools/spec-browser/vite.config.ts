import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Pages: VITE_BASE=/HotStreak/  Local: /
const base = process.env.VITE_BASE || '/'

export default defineConfig({
  plugins: [react()],
  base,
})
