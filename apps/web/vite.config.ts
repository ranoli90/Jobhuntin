import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { VitePWA } from 'vite-plugin-pwa';
import { readFileSync } from "fs";

const pkg = JSON.parse(readFileSync(path.join(__dirname, "package.json"), "utf-8"));
const version = pkg.version ?? "0.0.2";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  return {
    define: {
      "import.meta.env.VITE_APP_VERSION": JSON.stringify(version),
    },
    plugins: [react(), VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'],
      manifest: {
        name: 'JobHuntin',
        short_name: 'JobHuntin',
        description: 'AI Job Search Automation & Auto-Apply',
        theme_color: '#ffffff',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    })],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: env.API_URL || "http://localhost:8000",
          changeOrigin: true,
        },
      },
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ["react", "react-dom", "react-router-dom", "framer-motion"],
            ui: ["lucide-react", "canvas-confetti", "clsx", "tailwind-merge"],
          },
        },
      },
    },
    // Only strip console/debugger in production builds.
    // In development, keep them for debugging auth flows, API calls, etc.
    esbuild: mode === "production"
      ? { drop: ["console", "debugger"] }
      : {},
  };
});
