import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// En desarrollo, Vite (5173) reenvía /api a la API de FastAPI (8000). En producción la API sirve dist/.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { "/api": "http://localhost:8000" } },
  build: { chunkSizeWarningLimit: 2500 },
});
