# 开发进度与验收记录

更新于 2026-09-17。需求基线为根目录 `DEVELOPMENT_SPEC.md`。本文件记录代码状态；没有真机或真实数据库的检查不标记通过。

| 里程碑 | 当前结果 | 待验收 |
|---|---|---|
| M0 工程骨架 | Android Compose 工程、FastAPI `/health`、Compose/pgvector 配置、Mock Provider、锁文件、检查脚本已写入；Android Debug APK 构建通过 | 本机无 Docker，数据库启动和端到端 health 未验证 |
| M1 高风险 Spike | 尚未实现锁屏闹钟与 Assistant service 闭环 | 目标真机与系统权限验证 |
| M2 新闻采集 | RSS/Atom 解析、规范化、精确去重、正文提取、独立 worker、advisory lock、job run、自写 fixture 已写入 | 真实 PostgreSQL 幂等测试、近似去重阈值评测、合法来源清单 |
| M3 知识库 | manifest 校验、切块、Mock embedding、pgvector 检索已写入 | 真实 embedding、30 查询黄金集与 Recall@8 |
| M4 AI 热点 | 事件聚合、评分 Schema、引用校验、服务端总分及 Mock 演示分析已写入 | 真实 Provider、人工标注 100 条黄金集、质量指标 |
| M5 API/晨报 | 列表、详情、晨报读取、ETag、Alpha token、候选选择、Mock/真实模型问答适配与引用校验、反馈事件接口和 OpenAPI 已写入 | 真实数据库契约测试、真实模型调用与质量验收、定时生成实跑 |
| M6 Android 热点 | Compose 热点列表与详情、Room 缓存、WorkManager 同步、离线详情和开发健康检查页已写入，Debug APK 构建通过 | 模拟器与真机交互验收 |
| M7 闹钟与 TTS | Room 闹钟模型、无损 1→2 迁移及按设备时区计算下一次触发的领域函数已写入，3 个时间计算测试通过 | AlarmManager 注册、系统事件恢复、响铃、TTS 及真机验收 |
| M8 语音与交付 | 未开始 | Wake Word、STT、Intent、隐私、APK 与发布门禁 |

已执行的可重复检查：

```text
uv lock / uv sync --frozen：通过
ruff check / ruff format --check：通过
mypy app：通过
pytest -q：44 passed
alembic upgrade head --sql：通过（只生成 SQL，未连接 PostgreSQL）
scripts/export_openapi.py --check：通过
Gradle testDebugUnitTest：通过（3 个测试）
Gradle lintDebug：通过（报告无 issue）
Gradle assembleDebug：通过（生成 Debug APK）
```

运行端到端验收还需要 Docker 和至少一台目标 Android 真机；JDK 17 与 Android SDK 36 已在本地工具目录中。真实新闻源、合法知识材料、模型密钥和 Porcupine 资源尚未提供，当前演示运行使用自写 fixture 与 Mock；真实模型适配器仅通过模拟 HTTP 响应验证。
