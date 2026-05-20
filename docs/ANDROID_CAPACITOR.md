# 打包为 Android（Capacitor）

本项目是 **Vite + React** 前端；安卓端为 **Capacitor WebView** 外壳，界面逻辑仍在当前仓库，每次发版：`build` → 把 `dist` 拷贝进原生工程。

## 组员环境要装什么

1. **Node.js**（与现在开发一致）
2. **Android Studio**（含 Android SDK、至少一个模拟器镜像）
3. **JDK**：Android Studio 一般会带；若 Gradle 报错再按报错装对应 JDK。

## 日常命令（在项目根目录）

```bash
# 安装依赖（含 Capacitor）
npm install

# 打完前端并把静态资源同步到 android 工程（发版必做）
npm run build:android
```

等价于：`npm run build` + `npm run cap:sync`。

## 用 Android Studio 跑起来

1. 确保已执行过至少一次：`npm run build:android`
2. 打开 Android Studio → **Open** → 选中本仓库里的 **`android`** 文件夹（不要选错成仓库根）。
3. 等待 Gradle Sync 完成后，选一个 **虚拟机或真机**，点绿色 **Run**。

## 只打开 Android 工程（不自动 build）

若你刚改过前端且已手动 `npm run build`：

```bash
npm run cap:sync      # 或完整走 npm run build:android
npm run cap:android   # 会执行 cap open android
```

## App 信息与包名

- 配置文件：`capacitor.config.ts`  
- **`appId`**：应用 ID（上架用），可按团队改成你们正式域名反向如 `com.xxx.product`。  
- **`appName`**：桌面显示名称。

修改后执行：`npm run build:android`，再在 Android Studio 里 **Rebuild**。

## 开发时真机连着电脑预览（可选）

不打包，让 App 打开你电脑的 Vite：

1. 电脑上：`npm run dev -- --host`（记终端里的局域网 IP + 端口）。
2. 在 `capacitor.config.ts` 里临时打开：

   ```ts
   server: { url: "http://你的局域网IP:5187", cleartext: true },
   ```

3. `npm run cap:sync`，Android Studio **Run**。  
调试完删掉 `server`，再 `npm run build:android` 走正式离线包。

## 路由说明

当前使用 **`BrowserRouter`**；Capacitor 8 默认 WebView 资源加载方式多数情况下可直接用。若遇 **刷新或直接打开子路径白屏**，再考虑改为 **`HashRouter`**（可单独开一个 issue）。

## 常见问题

| 现象 | 处理 |
|------|------|
| `cap: command not found` | 用 `npx cap sync`，或已通过 `npm run cap:sync` 调用脚本 |
| Gradle / SDK 报错 | Android Studio → SDK Manager 装缺失组件；或使用 Studio 自带的 JDK |
| `dist` 不存在 | 先执行 `npm run build` |
| Figma CDN 图为空 | manifest 已有 `INTERNET`；离线包仍会联网拉外链图，离线演示需本地化资源 |

更完整流程见官方文档：**[Capacitor — Development Workflow](https://capacitorjs.com/docs/basics/workflow)**。
