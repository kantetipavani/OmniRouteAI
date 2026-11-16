import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const BACKEND_PORT = process.env.VITE_BACKEND_PORT || 8001;

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: `http://127.0.0.1:${BACKEND_PORT}`,
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, res) => {
            console.warn(`[vite proxy] Backend not reachable at http://127.0.0.1:${BACKEND_PORT}. Please start the backend server via 'python run_app.py'.`);
            if (res && !res.headersSent && typeof res.writeHead === 'function') {
              res.writeHead(503, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({
                error: 'Backend service unavailable',
                detail: `Could not connect to OmniRoute backend at http://127.0.0.1:${BACKEND_PORT}. Ensure the backend is running with 'python run_app.py'.`
              }));
            }
          });
        }
      }
    }
  }
})
