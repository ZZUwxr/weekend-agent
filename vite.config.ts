import react from "@vitejs/plugin-react";
import tailwind from "tailwindcss";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: "./",
  server: {
    // 避免与占用 5173 的其他本地项目（例如另一个 Vite 应用）冲突，导致改代码却看不到效果
    port: 5180,
    strictPort: false,
  },
  css: {
    postcss: {
      plugins: [tailwind()],
    },
  },
});
