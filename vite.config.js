import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
<<<<<<< HEAD
    port: 5173,
    strictPort: true,
=======
    host: true,
    // Allow ngrok tunnel domains for mobile testing.
    allowedHosts: [".ngrok-free.dev", "localhost", "127.0.0.1"],
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
>>>>>>> 08430856d59c2322acb2d319a146251f0b5a370d
  },
});
