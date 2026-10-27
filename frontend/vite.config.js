import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// npm run dev -> http://localhost:5173, /api/* is forwarded to the Python server
// (python src/main.py serve, port 8000)
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
