# 公考晨报

Android 客户端与 Python 后端的单仓库项目。唯一需求基线见 [开发规格](DEVELOPMENT_SPEC.md)。

## 当前进度

工程处于开发中。后端已具备新闻采集与事件聚合、知识材料导入、AI 分析校验、热点与晨报生成及读取、带引用校验的问答适配和反馈 API。Android 已有热点列表、详情、Room 缓存、后台同步、闹钟数据模型与时间计算和开发用健康检查页；Debug APK 已构建，但尚未经过模拟器或真机交互验收。完整进度与未通过的验收项见 [开发进度](docs/PROGRESS.md)。

## 后端本地启动

需要 Docker、Python 3.12+ 和 uv：

```bash
cp backend/.env.example backend/.env
docker compose up -d db
cd backend
uv sync --frozen
uv run alembic upgrade head
uv run python -m app.cli.seed_demo
uv run uvicorn app.main:app --reload
```

访问 `http://127.0.0.1:8000/health`。示例新闻由本项目自写；不包含第三方新闻全文。

热点接口使用 Alpha 测试凭据：

```bash
curl -H 'X-Client-Token: local-debug-token-change-me' 'http://127.0.0.1:8000/v1/hotspots?date=2026-09-16&timezone=Asia/Shanghai'
```

演示数据日期固定为 2026-09-16，不代表当天真实新闻。机器可读 API 见 `contracts/openapi.json`。

## Android

需 JDK 17 和 Android SDK 36。当前环境已将两者安装在忽略提交的 `.tools/` 中；`android/local.properties` 指向本地 SDK。执行 `testDebugUnitTest lintDebug assembleDebug` 已通过，APK 位于 `android/app/build/outputs/apk/debug/`。Debug 版允许模拟器通过 `10.0.2.2:8000` 访问宿主机的 HTTP 后端；Release 版需配置 HTTPS 地址与凭据。真机需要配置独立的开发服务地址。

## 检查

在工具链齐全的环境运行 `./scripts/check.sh`。该脚本会检查后端格式、类型、测试、OpenAPI 一致性和 Android 构建；缺少工具时明确失败。
