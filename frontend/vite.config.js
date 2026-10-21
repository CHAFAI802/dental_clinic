import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist-vite',
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://web:8000',
        changeOrigin: true,
        secure: false,
        xfwd: true,
        
      },
      // Fichiers média (modèles .docx) : le backend renvoie des URL
      // absolues construites avec l'hôte de la requête, donc inaccessibles
      // depuis le navigateur via le proxy. Le frontend demande le chemin
      // retourné par l'API (ex. /media/document_templates/…) au serveur de
      // dev, qui le transmet à Django (volume Docker inchangé).
      '/media': {
        target: 'http://web:8000',
        changeOrigin: true,
        secure: false,
        xfwd: true,
      },
    },
  },
})
