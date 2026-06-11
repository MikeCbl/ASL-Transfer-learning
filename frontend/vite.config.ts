import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import tailwindcss from '@tailwindcss/vite';

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte(), tailwindcss()],
  server: {
    proxy: {
      // Wszystkie zapytania z frontendu do /api/... trafią do Twojego kontenera FastAPI
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // Ucinamy '/api', więc wywołanie fetch('/api/predict') na froncie
        // trafi dokładnie w 'http://127.0.0.1:8000/predict' w backendzie
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
});
