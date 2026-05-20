import type { CapacitorConfig } from "@capacitor/cli";

/** 原生壳配置：web 资源来自 Vite 的 `npm run build` 输出目录 */
const config: CapacitorConfig = {
  appId: "com.anima.travelassistant",
  appName: "出行助手",
  webDir: "dist",
  /** 若要真机在开发时直连电脑上的 Vite，可改成你的局域网 IP（仅调试用）
   * server: { url: "http://192.168.1.xx:5187", cleartext: true },
   */
};

export default config;
