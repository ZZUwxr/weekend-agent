import react from "@vitejs/plugin-react";
import tailwind from "tailwindcss";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: "./",
  server: {
    // 固定 5187，占线时不要悄悄换端口，避免看错本地其他 Vite 进程
    port: 5187,
    strictPort: true,
  },
  css: {
    postcss: {
      plugins: [tailwind()],
    },
  },
});
