import type { CapacitorConfig } from "@capacitor/cli";

const isDev = process.env.NODE_ENV === "development";

const config: CapacitorConfig = {
  appId: "com.anima.travelassistant",
  appName: "出行助手",
  webDir: "dist",
  android: {
    backgroundColor: "#ffffffff",
    allowMixedContent: true,
  },
  plugins: {
    StatusBar: {
      overlaysWebView: true,
    },
  },
  server: isDev
    ? {
        url: "http://10.0.2.2:5187",
        cleartext: true,
        androidScheme: "http",
      }
    : {
        cleartext: true,
        androidScheme: "http",
      },
};

export default config;
