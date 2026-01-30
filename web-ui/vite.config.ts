import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const analyzerTarget = env.VITE_ANALYZER_URL || "http://localhost:5002";
  const anonymizerTarget = env.VITE_ANONYMIZER_URL || "http://localhost:5001";
  const sitTarget = env.VITE_SIT_API_URL || "http://localhost:8000";

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        "/api/scan": {
          target: sitTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/scan/, "/scan"),
        },
        "/api/analyzer": {
          target: analyzerTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/analyzer/, ""),
        },
        "/api/anonymizer": {
          target: anonymizerTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/anonymizer/, ""),
        },
        "/api/sit": {
          target: sitTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/sit/, ""),
        },
        "/api/presidio": {
          target: sitTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/presidio/, "/presidio"),
        },
      },
    },
    test: {
      globals: true,
      environment: "jsdom",
      setupFiles: "./src/test/setup.ts",
    },
  };
});
