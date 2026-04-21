# SkyEye Web

SkyEye 的 React 单页前端，负责视频上传、检索范围选择、语义搜索与结果展示。

## 开发启动

1. 在项目根目录启动 FastAPI 后端。
2. 进入 web 目录安装依赖并启动前端。

PowerShell 示例：

```powershell
cd web
bun install
bun run dev
```

默认前端地址：

- http://localhost:5173

## 环境变量

可复制示例文件并按需修改：

```powershell
Copy-Item .env.example .env.local
```

当前支持：

- VITE_API_BASE_URL: API 基础地址，默认建议使用 /api/。

说明：

- 开发模式下已配置 Vite 代理，将 /api 转发到 http://localhost:8000。
- 如果你要直连后端地址，可在 .env.local 中设置为 http://localhost:8000/api/。

## 打包

```powershell
bun run build
```

构建产物位于 dist 目录。
