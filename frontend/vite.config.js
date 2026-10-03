import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During development, any request starting with /api is forwarded to the Python server.
// That means the browser only ever talks to ONE origin, and no keys or backend URLs
// are needed in the React code.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
