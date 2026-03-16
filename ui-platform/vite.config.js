import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "."),
            "@components": path.resolve(__dirname, "./components"),
            "@pages": path.resolve(__dirname, "./pages"),
            "@hooks": path.resolve(__dirname, "./hooks"),
            "@services": path.resolve(__dirname, "./services"),
            "@types": path.resolve(__dirname, "./types"),
            "@utils": path.resolve(__dirname, "./utils"),
        },
    },
    server: {
        port: 3000,
        open: true,
        proxy: {
            "/api": {
                target: "http://localhost:8000",
                changeOrigin: true,
            },
            "/webhooks": {
                target: "http://localhost:8000",
                changeOrigin: true,
            },
            "/health": {
                target: "http://localhost:8000",
                changeOrigin: true,
            },
            "/auth": {
                target: "http://localhost:8000",
                changeOrigin: true,
            },
        },
    },
    build: {
        target: "ES2020",
        sourcemap: true,
        rollupOptions: {
            output: {
                manualChunks: {
                    vendor: ["react", "react-dom", "react-router-dom"],
                },
            },
        },
    },
});
