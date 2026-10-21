import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Khi chạy dev (npm run dev), mọi request /api được chuyển tới backend.
// Cổng backend publish trong docker-compose mặc định là 18000.
const backend = process.env.VITE_PROXY_TARGET || "http://localhost:18000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 15173,
    proxy: {
      "/api": { target: backend, changeOrigin: true },
    },
  },
});
