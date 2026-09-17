# 公考 AI 晨报助手 V0.1 开发规格书

> 文档用途：直接交给开发 Agent 作为唯一需求基线，完成 Android 客户端、后端、知识库、AI 热点评分、闹钟、TTS 和本地唤醒词的第一版开发。
>
> 规格版本：0.1.0  
> 状态：Approved for internal Alpha development  
> 基准日期：2026-09-16  
> 默认语言：简体中文  
> 默认时区：Asia/Shanghai，实际运行时尊重设备时区  
> 暂定产品名：公考晨报  
> 暂定仓库名：`ai-exam-morning-brief`

---

## 0. 交给开发 Agent 的直接指令

将本文件放在仓库根目录，文件名保持为 `DEVELOPMENT_SPEC.md`。给 Agent 的指令如下：

```text
请完整阅读根目录 DEVELOPMENT_SPEC.md，并把它视为当前项目唯一需求基线。

从 M0 开始，严格按 M0→M8 的顺序开发。不要跳过验收测试，不要自行扩展 V0.1 范围。
如果仓库为空，先创建规格要求的 monorepo；如果仓库已有内容，先检查并保留用户现有改动。

执行规则：
1. 每个里程碑先列出待办，再实现，再运行该阶段规定的测试。
2. 每完成一个里程碑，报告：改动文件、实现结果、执行过的命令、测试结果、剩余风险。
3. 所有密钥只允许进入本地环境变量或未提交的 local.properties/.env，绝不写入源码、APK、日志和测试快照。
4. 没有外部 API Key 时必须使用 Mock Provider，让项目仍可启动、测试和演示。
5. Android 依赖选择创建项目时最新的稳定兼容版本，并集中写入 version catalog；不得使用 alpha/canary 依赖，除非本规格明确要求。
6. 数据库变更必须通过 Alembic migration；API 变更必须同步 OpenAPI、契约测试和本规格派生文档。
7. 唤醒词、锁屏闹钟、重启恢复没有在真实 Android 设备上验证前，不得声称“已完成”；只能标记为“代码完成，真机验收待办”。
8. 遇到缺少密钥、新闻源或真机时，不要停止整个项目：使用 Mock/fixture 完成可完成部分，并清楚记录对应验收门禁。
9. 不允许通过后台保活、无障碍服务或绕过系统限制实现息屏监听。
10. 默认连续推进到可执行的干净检查点；只有涉及付费、外部发布、生产数据删除、账号授权或无法替代的用户选择时才暂停询问。
```

### Agent 的完成定义

“完成 V0.1”不是指代码可以编译，而是本文件第 22 节的全部 P0 验收项通过，并生成：

- 可安装的 Debug APK。
- 可通过 Docker Compose 启动的后端和 PostgreSQL/pgvector。
- 一套可重复导入的示例知识库与新闻 fixture。
- 自动化测试报告。
- 真机测试清单及结果。
- 完整的根目录 `README.md` 和 `.env.example`。

---

## 1. 产品目标

V0.1 要完成一个稳定闭环：

```text
本地精确闹钟
  → 闹钟响起
  → 响铃一分钟后播放已提前缓存的AI 公考晨报，条数需要可自定义
  → 用户在 APP 查看热点详情
  → 用户可通过本地唤醒词进入语音对话
  → 本地 Intent 或 RAG+LLM 回答
```

核心价值不是“总结新闻”，而是：

```text
新闻 → 公考价值判断 → 考点映射 → 简洁晨报 → 深入学习
```

### 1.1 V0.1 必须包含

| 能力 | P0 要求 |
|---|---|
| 闹钟 | 创建、编辑、删除、启停、按星期重复、息屏触发、重启恢复 |
| 热点 | RSS/Atom 采集、正文提取、标准化、去重、事件聚合、排序 |
| 知识库 | 大纲、考点、合法来源真题/示例题、政策材料的导入和 RAG 检索 |
| AI 判断 | 固定维度评分、固定 JSON Schema、服务端校验、失败降级 |
| AI 内容 | TTS brief、首页摘要、详情分析三层内容 |
| 晨报 | 每日 3～5 条、提前生成、提前同步、本地离线可播、支持用户手动关闭 |
| TTS | Android 系统 TTS，中文可用性检测、语速设置、播放控制 |
| 唤醒词 | 本地检测、检测前音频不上云、默认 Assistant 模式、按住说话回退 |
| 语音命令 | 闹钟和热点类 Intent 本地路由；知识问答才调用后端 |
| 可观测性 | 结构化日志、AI 调用记录、任务运行记录，不记录原始语音 |

### 1.2 V0.1 明确不做

- 社区、私信、排行榜、课程商城、付费订阅。
- iOS、Wear OS、小米手环端应用。
- 控制手机任意功能。
- 自训练大语言模型。
- 生产级多租户和复杂账号体系。
- 云端自然音色 TTS、数字人、情绪语音。
- 自动绕过网站反爬、登录墙或付费墙。
- 未经许可复制或重新分发受版权保护的真题全文和新闻全文。

V0.1 是内部 Alpha。公开测试前必须完成第 18 节的发布门禁。

---

## 2. 产品原则与强制约束

以下约束优先级高于具体实现偏好：

1. **闹钟可靠性不得依赖网络、后端、LLM 或推送。**
2. **晨报必须提前生成并缓存到手机。** 到点时不得临时请求 LLM。
3. **唤醒前的连续音频只在本地内存中处理，不保存、不上传。**
4. **所有 AI 输出先通过结构化 Schema 校验，服务端自行计算总分。**
5. **一条新闻内容相同且 AI 版本未改变时只分析一次。**
6. **所有热点保留原始来源链接、发布时间和处理版本。**
7. **客户端永远不持有 LLM、Embedding、新闻服务的私密 API Key。**
8. **V0.1 不用普通后台 Service 永久录音。** 息屏唤醒仅在用户将应用选择为当前语音交互服务后启用。
9. **没有证据的内容不得由 AI 补全。** 不确定时返回 `insufficient_evidence=true`。
10. **模型、Wake Word、STT 均通过 Adapter 接口接入，业务层不依赖某个供应商。**

---

## 3. 用户与核心场景

### 3.1 目标用户

- 正在准备国考、省考、事业单位考试的中文用户。
- 希望每天快速知道“什么值得关注、为什么可能考”的用户。
- 早晨可用于收听的时间只有 1～5 分钟。

### 3.2 主流程 A：设置闹钟

1. 用户打开“闹钟”页并创建 时间节点、或者周期的闹钟。
2. 闹钟响起后设定的分钟后开启“停止闹钟后播放晨报”。
3. 应用检查并解释通知、精确闹钟、全屏通知所需权限。
4. 保存 Room 后立即计算下一次触发时间并注册一个单次系统闹钟。
5. UI 显示“将在 X 小时 Y 分钟后响铃”。

### 3.3 主流程 B：起床与晨报

1. 到点后，即使设备锁屏且 APP 进程不存在，闹钟仍响。
2. 锁屏显示闹钟界面，提供“停止”和“稍后提醒”。
3. 用户停止后，若晨报已缓存且开启播放，则询问或按用户设置自动播放。
4. TTS 播放 3～5 条，每条只包含标题、发生了什么、考公关注点。
5. 用户可暂停、继续、上一条、下一条、停止。
6. 没网时使用缓存；没有今日缓存时可使用最近 24 小时内有效缓存，并明确播报“以下为最近缓存内容”；仍无缓存则只完成闹钟，不伪造晨报。

### 3.4 主流程 C：查看热点

首页按“今日重点”和“其他值得关注”分组。点击后展示：

- 标题、来源、发布时间、原文链接。
- 30 秒了解。
- 背景与变化。
- 为什么值得公考关注。
- 关联考点、适用考试模块、可能考法。
- 证据与知识库引用。
- 听讲解、生成一道练习题、收藏（收藏可 P1）。

### 3.5 主流程 D：语音助手

1. 用户在设置中启用语音助手，并按引导将本应用选择为当前语音交互服务。
2. 本地引擎检测测试唤醒词；自定义中文模型文件可配置替换。
3. 检测成功后播放短提示音，才开始正式录音并进入 STT。
4. 识别文本先进入本地 Intent Router。
5. 闹钟命令本地执行；热点查询优先读本地缓存；解释类问题调用后端 RAG+LLM。
6. 结果通过 TTS 播放，并在语音会话 UI 中显示文字。

---

## 4. 信息架构与页面

底部导航固定为四项：

| 页面 | P0 内容 |
|---|---|
| 首页 | 今日晨报卡片、今日重点、其他热点、缓存状态 |
| 闹钟 | 闹钟列表、新建/编辑、晨报播放设置 |
| 学习 | 热点历史、考点分类；收藏和错题允许先显示“即将支持”但不得做假交互 |
| 我的 | 考试方向、TTS、语速、语音助手状态、权限状态、隐私说明、诊断信息 |

额外页面：

- 首次启动与权限引导。
- 热点详情。
- 全屏闹钟。
- 晨报播放器。
- 语音会话。
- 知识库/模型版本诊断页（Debug 构建可见）。

UI 必须支持深色模式、系统字体缩放和基础无障碍语义。所有空状态、加载态、错误态、离线态均必须有明确文案。

---

## 5. 总体架构

```text
┌──────────────── Android ────────────────┐
│ Compose UI                              │
│ Alarm / Briefing / Hotspot / Voice      │
│ Room cache + WorkManager                │
│ AlarmManager + System TTS               │
│ VoiceInteractionService + WakeWord      │
└───────────────────┬─────────────────────┘
                    │ HTTPS JSON
┌───────────────────▼─────────────────────┐
│ FastAPI                                 │
│ Hotspot API / Briefing API / Chat API   │
│ News pipeline / AI pipeline / RAG       │
│ Dedicated scheduler-worker              │
└───────────────────┬─────────────────────┘
                    │
┌───────────────────▼─────────────────────┐
│ PostgreSQL + pgvector                   │
│ News / Events / KB / Analysis / Runs    │
└─────────────────────────────────────────┘
```

### 5.1 进程边界

- `android`: 用户界面、本地闹钟、本地缓存、TTS、Wake Word 和 Intent。
- `backend-api`: 无状态 HTTP API，不运行定时任务。
- `backend-worker`: 采集、清洗、向量化、评分、摘要、晨报生成。
- `postgres`: 唯一主数据库，同时承担向量检索。
- V0.1 不引入 Redis、Kafka、Kubernetes、Elasticsearch。

---

## 6. 技术栈冻结

### 6.1 Android

| 项目 | 选择 |
|---|---|
| 语言/UI | Kotlin + Jetpack Compose + Material 3 |
| SDK | `minSdk 29`，`targetSdk 36`，`compileSdk 36` |
| 架构 | 单 Activity、Navigation Compose、MVVM、Repository |
| 依赖注入 | Hilt |
| 本地数据库 | Room |
| 网络 | Retrofit + OkHttp + Kotlinx Serialization |
| 后台同步 | WorkManager |
| 闹钟 | AlarmManager + BroadcastReceiver + Alarm foreground service/activity |
| 音频 | 系统 AudioManager/Media APIs；铃声使用 `USAGE_ALARM` |
| TTS | Android `TextToSpeech` + `UtteranceProgressListener` |
| 唤醒服务 | `VoiceInteractionService` + `VoiceInteractionSessionService` |
| Wake Word | `WakeWordEngine` 接口；Alpha 默认接 Picovoice Porcupine Android Adapter，本地运行 |
| STT | `SpeechToTextEngine` 接口；默认 Android SpeechRecognizer，必须有按住说话回退 |
| 测试 | JUnit、Turbine、MockWebServer、Room in-memory、Compose UI test |

说明：Porcupine 需要 AccessKey，自定义唤醒词需要 Android `.ppn` 模型。没有密钥时，Debug 构建使用 `FakeWakeWordEngine` 和按钮模拟检测事件，以便其余语音链路可测试；这不算真机唤醒词验收通过。若项目决定使用另一款本地引擎，只能替换 Adapter，不得改变上层状态机。

### 6.2 后端

| 项目 | 选择 |
|---|---|
| 语言 | Python 3.12+ |
| API | FastAPI + Pydantic v2 |
| ORM/迁移 | SQLAlchemy 2 async + Alembic |
| 数据库 | PostgreSQL 16+ + pgvector |
| HTTP | HTTPX |
| Feed | feedparser |
| 正文提取 | trafilatura；失败时保留 feed 摘要并标记质量 |
| 调度 | 独立 worker + APScheduler；PostgreSQL advisory lock 防止重复运行 |
| AI | `AIProvider`、`EmbeddingProvider` Adapter；支持 `mock` 与至少一个真实 Provider |
| 测试 | pytest、pytest-asyncio、HTTPX TestClient、Testcontainers 或 Compose 测试库 |
| 代码质量 | Ruff + MyPy；所有公共边界有类型 |

### 6.3 版本策略

- 创建工程时选择彼此兼容的最新稳定版本，并在 Android version catalog、Python lockfile 固定。
- 不在本规格里硬编码易过时的具体库小版本。
- 禁止无原因使用 `latest.release`、动态版本或未锁定依赖。

---

## 7. 仓库结构

```text
ai-exam-morning-brief/
├── DEVELOPMENT_SPEC.md
├── README.md
├── .gitignore
├── docker-compose.yml
├── android/
│   ├── app/
│   ├── core/
│   │   ├── common/
│   │   ├── database/
│   │   ├── model/
│   │   ├── network/
│   │   └── testing/
│   ├── feature/
│   │   ├── alarm/
│   │   ├── briefing/
│   │   ├── hotspot/
│   │   ├── onboarding/
│   │   ├── settings/
│   │   └── voice/
│   ├── gradle/libs.versions.toml
│   ├── gradlew
│   └── gradlew.bat
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── news/
│   │   ├── knowledge/
│   │   ├── rag/
│   │   ├── ai/
│   │   ├── briefing/
│   │   └── jobs/
│   ├── alembic/
│   ├── tests/
│   ├── fixtures/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── Dockerfile
│   └── .env.example
├── contracts/
│   ├── openapi.json
│   ├── examples/
│   └── schemas/
├── knowledge/
│   ├── README.md
│   ├── seed/
│   └── manifests/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── AI_RULES.md
│   ├── DATABASE.md
│   ├── PRIVACY.md
│   └── TEST_PLAN.md
└── scripts/
    ├── bootstrap.sh
    ├── check.sh
    └── seed_demo.sh
```

开发 Agent 可由本规格派生 `docs/` 下的专题文档，但不得改变本规格的产品范围；冲突时以本文件为准。

---

## 8. 后端数据模型

所有主键使用 UUID，时间使用 `timestamptz` 并以 UTC 保存。所有可审计表包含 `created_at`、`updated_at`。原始 AI/抓取大文本应按保留策略清理。

### 8.1 `news_sources`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | uuid | 主键 |
| name | text | 来源名 |
| source_type | enum | `rss`、`atom`、`manual` |
| feed_url | text nullable | Feed 地址 |
| base_url | text | 来源站点 |
| reliability_score | smallint | 0～10，由管理员配置 |
| enabled | bool | 是否采集 |
| fetch_interval_minutes | int | 最低 30 |
| terms_note | text | 授权/使用说明 |
| last_success_at | timestamptz | 最近成功时间 |

### 8.2 `news_articles`

核心字段：

```text
id, source_id, canonical_url, source_guid, title,
published_at, fetched_at, author, language,
feed_summary, extracted_text, extraction_quality,
content_hash, normalized_title, status,
raw_metadata(jsonb), processing_version
```

约束：

- `canonical_url` 唯一；URL 不可靠时使用 `(source_id, source_guid)` 唯一。
- `content_hash` 对规范化正文计算，用于精确去重。
- `status`：`new | cleaned | duplicate | rejected | analyzed | failed`。
- API 不向客户端返回完整 `extracted_text`。

### 8.3 `hotspot_events` 与 `hotspot_event_articles`

事件把多篇谈论同一事情的新闻合并为一个热点。

```text
hotspot_events:
id, canonical_title, category, subcategories(jsonb),
first_seen_at, last_seen_at, status,
representative_article_id, cluster_version

hotspot_event_articles:
event_id, article_id, similarity, is_primary
```

### 8.4 `knowledge_documents` 与 `knowledge_chunks`

```text
knowledge_documents:
id, external_id, title, document_type,
exam_scope, source_url, license_note,
effective_from, effective_to, content_hash,
version, status, metadata(jsonb)

knowledge_chunks:
id, document_id, chunk_index, text,
token_count, tags(jsonb),
embedding vector(1536), embedding_model,
metadata(jsonb)
```

默认 Embedding 维度为 1536。更换维度必须新增迁移并重建索引，不能静默混存。

`document_type`：

- `exam_outline`
- `exam_point`
- `official_question`
- `policy_material`
- `editorial_rule`
- `example_material`

### 8.5 `hotspot_analyses`

```text
id, event_id, analysis_version, model_provider, model_name,
exam_relevance, clear_test_point, public_affairs,
timeliness, source_reliability, trend_linkage,
essay_interview_value, total_score,
include_in_hotlist, include_in_briefing,
category, subcategories(jsonb), exam_types(jsonb),
reason, brief, summary, deep_analysis,
key_points(jsonb), possible_questions(jsonb),
knowledge_refs(jsonb), evidence_refs(jsonb),
insufficient_evidence, moderation_status,
prompt_hash, input_hash, raw_response(jsonb),
created_at
```

唯一约束：`(event_id, analysis_version, input_hash)`。

### 8.6 `briefings` 与 `briefing_items`

```text
briefings:
id, briefing_date, timezone, locale, version,
status, intro_text, outro_text,
estimated_seconds, generated_at, expires_at

briefing_items:
briefing_id, hotspot_analysis_id, position,
tts_text, estimated_seconds
```

唯一约束：`(briefing_date, timezone, locale, version)`。

### 8.7 运行与反馈表

- `job_runs`: job 名、开始/结束、状态、计数、错误摘要。
- `ai_runs`: task、provider、model、latency、token/usage、cost_estimate、状态、重试次数；不保存密钥。
- `human_labels`: event、人工分级/分类、标注人、备注。
- `user_feedback`: 匿名 install id 哈希、event、click/read/collect/hide 等事件。

---

## 9. Android 本地数据模型

### 9.1 `AlarmEntity`

```kotlin
data class AlarmEntity(
    val id: String,
    val hour: Int,
    val minute: Int,
    val repeatDaysMask: Int,
    val enabled: Boolean,
    val label: String,
    val soundUri: String?,
    val vibrate: Boolean,
    val snoozeMinutes: Int,
    val morningBriefEnabled: Boolean,
    val autoPlayBrief: Boolean,
    val nextTriggerAtEpochMillis: Long?,
    val createdAtEpochMillis: Long,
    val updatedAtEpochMillis: Long
)
```

`repeatDaysMask` 使用 7 位 bitmask，周一为最低位；领域层必须提供可读转换函数，不允许 UI 直接操作位运算。

### 9.2 缓存实体

- `CachedHotspotEntity`: 列表所需字段、ETag、内容版本、缓存时间。
- `CachedHotspotDetailEntity`: 完整详情 JSON、版本、缓存时间。
- `CachedBriefingEntity`: 日期、时区、版本、完整 TTS 文本、条目、过期时间。
- `SyncStateEntity`: resource、cursor、etag、last_success、last_error。
- `VoiceSettingsEntity`: enabled、engine、wake model id、STT provider、privacy acknowledgement。

服务端删除或版本变化时，客户端按稳定 ID upsert。Room migration 必须有自动化测试。

---

## 10. 新闻处理流水线

### 10.1 固定步骤

```text
读取启用来源
→ 抓取 RSS/Atom
→ 规范化 URL、标题、时间、语言
→ 在允许条件下提取正文
→ 精确去重（URL/GUID/content hash）
→ 近似去重（标题 + 时间窗 + 内容指纹）
→ 基础规则过滤
→ 事件聚类
→ RAG 检索
→ LLM 分项判断
→ Schema 校验和服务端重算总分
→ 生成三级内容
→ 选择晨报条目
```

### 10.2 来源规范

- Alpha 至少配置 3 个公开、合法、稳定的 RSS/Atom 或人工导入来源。
- 来源 URL 通过环境配置或数据库管理，不散落在代码中。
- 尊重 robots、站点条款和访问频率；不绕过验证码、反爬或登录。
- 客户端只展示必要摘要与原文链接，不重新发布新闻全文。
- fixture 必须是自写示例或许可材料，不能把抓取全文提交进 Git。

### 10.3 去重规则

按顺序执行：

1. 相同 canonical URL：同一文章。
2. 相同 source GUID：同一文章。
3. 相同正文 hash：同一内容。
4. 48 小时内标题规范化后高度相似且正文 SimHash/embedding 相似：候选重复。
5. 多来源讲述同一事实：不删除，聚合到同一 `hotspot_event`。

近似规则的阈值写入配置并记录版本，不硬编码在业务函数中。

### 10.4 定时任务

默认时间：

| 任务 | 频率 |
|---|---|
| feed collection | 每 30 分钟，来源间加入抖动 |
| cleaning/dedup | 每次采集后 |
| event clustering | 每小时 |
| AI analysis | 每小时处理新事件；失败指数退避 |
| briefing generation | 每日 05:00，按时区 |
| retention cleanup | 每日 03:30 |

所有任务必须幂等，并通过 PostgreSQL advisory lock 防止多个 worker 重复执行。

---

## 11. 知识库与 RAG 规范

### 11.1 四类内容

1. 考试规则：国考/省考大纲、模块定义。
2. 历年题型：仅导入官方公开、获授权或自写示例内容。
3. 考点体系：公共管理、经济、科技、社会、生态等层级标签。
4. 动态热点：已经聚合的事件及其时间线。

### 11.2 导入格式

`knowledge/manifests/*.yaml`：

```yaml
external_id: KB-GOV-001
title: 基层治理示例考点
document_type: exam_point
exam_scope: [国考, 省考]
source_url: null
license_note: internally-authored-example
effective_from: 2026-01-01
tags: [公共管理, 基层治理, 公共服务]
file: ../seed/kb-gov-001.md
```

导入必须验证 external id、hash、授权说明和文件存在性。相同 hash 不重复向量化。

### 11.3 切块与检索

- 每块目标 500～800 个中文字符，重叠 100～150 字；不在标题和列表中间盲目截断。
- 保存文档、章节、标签、有效期、来源元数据。
- 首轮向量召回 20 条；按考试范围、有效期和文档类型过滤后重排，最终向 LLM 提供最多 8 条。
- 检索结果必须把 `knowledge_chunk_id` 带入 AI 输出的证据映射。
- 无足够知识证据时允许热点仍进入列表，但不得生成确定性的“可能考法”。

### 11.4 RAG 质量基线

建立至少 30 个查询的黄金集，覆盖：基层治理、就业、财政、科技创新、生态、公共服务等。指标：

- Recall@8 ≥ 0.80。
- 返回已过期内容时必须明确标记，不得当作现行规则。
- 每个回答的关键判断能回指至少一个知识块或原始新闻证据。

---

## 12. AI 评分与生成规范

### 12.1 分项评分

| 字段 | 范围 | 含义 |
|---|---:|---|
| exam_relevance | 0～30 | 与考试知识体系相关度 |
| clear_test_point | 0～20 | 能否形成明确考点 |
| public_affairs | 0～15 | 公共治理、经济社会等议题价值 |
| timeliness | 0～10 | 时效性 |
| source_reliability | 0～10 | 来源与证据可靠度 |
| trend_linkage | 0～5 | 与近期持续热点的关联 |
| essay_interview_value | 0～10 | 申论/面试素材价值 |

总分由后端相加，LLM 返回的总分即使存在也必须忽略。

| 总分 | 处理 |
|---:|---|
| 0～49 | 不进入热点 |
| 50～64 | APP“其他值得关注” |
| 65～79 | APP“今日重点”候选 |
| 80～100 | 晨报候选 |

晨报还必须满足：`source_reliability >= 7`、证据完整、非重复事件、无未解决安全标记。每天选择 3～5 条，同一一级分类最多 2 条。

### 12.2 AI 必须返回的 JSON

```json
{
  "scores": {
    "exam_relevance": 26,
    "clear_test_point": 17,
    "public_affairs": 13,
    "timeliness": 8,
    "source_reliability": 9,
    "trend_linkage": 3,
    "essay_interview_value": 9
  },
  "category": "公共管理",
  "subcategories": ["基层治理", "数字政府"],
  "exam_types": ["申论", "面试"],
  "reason": "事件与基层治理和公共服务优化直接相关。",
  "brief": "某项公共服务政策发布。考公可关注基层治理和数字政务两个方向。",
  "summary": "……",
  "deep_analysis": {
    "background": "……",
    "what_changed": "……",
    "why_it_matters": "……",
    "exam_relevance": "……",
    "possible_angles": ["……"]
  },
  "key_points": ["……", "……"],
  "knowledge_refs": ["knowledge-chunk-uuid"],
  "evidence_refs": ["article-uuid"],
  "insufficient_evidence": false,
  "safety_flags": []
}
```

Pydantic Schema 要求：

- 禁止额外字段。
- 分值必须为整数且在各自范围内。
- `category` 必须来自受控枚举。
- `exam_types` 仅允许 `行测常识 | 申论 | 面试`。
- `knowledge_refs` 与 `evidence_refs` 必须属于本次输入集合，防止伪造引用。
- 校验失败最多做一次结构修复调用；仍失败则任务失败并进入重试队列。

### 12.3 三层内容长度

| 层级 | 长度 | 用途 |
|---|---:|---|
| TTS Brief | 30～80 个中文字符/条 | 闹钟后播报 |
| Quick Summary | 150～300 个中文字符 | 首页与列表 |
| Deep Analysis | 500～1200 个中文字符 | 详情页 |

晨报禁止长篇背景、完整题目、未经证据支持的预测和 AI 个人立场。TTS 文本不得播报 URL、Markdown、星号或生硬字段名。

### 12.4 Prompt 版本

Prompt 由代码外模板管理，并包含：

- `system-rules-v1`
- `hotspot-score-v1`
- `hotspot-content-v1`
- `chat-rag-v1`

每次运行保存 prompt 版本和 hash。修改 Prompt 必须使 `analysis_version` 递增，并跑第 19 节的评测集。

### 12.5 Provider 降级

```text
cache hit
→ primary provider
→ 同 provider 一次短重试
→ fallback provider（如配置）
→ 标记失败，保留上一版有效内容
```

不得因为 AI 失败删除上一版晨报；不得把未校验的 fallback 文本直接交给客户端。

---

## 13. HTTP API 契约

所有接口前缀 `/v1`，UTF-8 JSON，错误使用统一结构，OpenAPI 为机器可读契约。Alpha 使用环境配置的 `X-Client-Token` 保护非 health 接口；这只是内部测试方案，不是公开发布认证方案。

### 13.1 通用错误

```json
{
  "error": {
    "code": "BRIEFING_NOT_FOUND",
    "message": "今日晨报尚未生成",
    "request_id": "uuid",
    "retryable": true
  }
}
```

### 13.2 端点

#### `GET /health`

返回 API 和数据库状态。不得泄露环境变量、连接串或 Provider 密钥。

#### `GET /v1/hotspots`

查询参数：`date`、`timezone`、`category`、`cursor`、`limit`（1～50，默认 20）。

返回：

```json
{
  "date": "2026-09-16",
  "items": [
    {
      "id": "uuid",
      "title": "示例政策发布",
      "summary": "……",
      "category": "公共管理",
      "subcategories": ["基层治理"],
      "exam_types": ["申论", "面试"],
      "importance": "core",
      "published_at": "2026-09-16T01:00:00Z",
      "source_names": ["示例来源"],
      "content_version": 1
    }
  ],
  "next_cursor": null
}
```

#### `GET /v1/hotspots/{id}`

返回完整详情、来源列表、知识引用和内容版本，不返回抓取的新闻全文。

#### `GET /v1/briefings/today`

查询参数：`date`、`timezone`、`locale=zh-CN`。支持 `ETag`/`If-None-Match`。

```json
{
  "id": "uuid",
  "date": "2026-09-16",
  "timezone": "Asia/Shanghai",
  "version": 1,
  "generated_at": "2026-09-15T21:00:00Z",
  "expires_at": "2026-09-17T00:00:00Z",
  "intro_text": "早上好，今天为你筛选了三条值得关注的热点。",
  "items": [
    {
      "position": 1,
      "hotspot_id": "uuid",
      "title": "示例政策发布",
      "tts_text": "第一条，示例政策发布……",
      "estimated_seconds": 22
    }
  ],
  "outro_text": "详细内容可以在公考晨报中查看。"
}
```

#### `POST /v1/ai/chat`

```json
{
  "question": "第一条为什么可能会考？",
  "hotspot_id": "uuid",
  "conversation_id": "client-generated-uuid",
  "locale": "zh-CN"
}
```

返回答案、引用和可选本地动作建议。服务端不得直接创建手机闹钟。

#### `POST /v1/feedback/events`

批量提交最小化匿名事件。用户关闭统计后不发送。

### 13.3 缓存与兼容性

- 列表、详情、晨报返回 `ETag` 和 `Cache-Control`。
- 新增可选字段允许兼容；删除/改名字段必须升 API 主版本。
- Android 对未知枚举使用 `UNKNOWN`，不得崩溃。
- `contracts/examples` 中每个端点至少有一个成功和一个错误样例。

---

## 14. Android 闹钟实现规范

### 14.1 调度算法

- 使用墙上时钟语义，按用户设备时区计算下一次。
- 每个闹钟只注册“下一次”单次精确 alarm；触发或设备时间变化后再计算后续一次。
- 面向用户的闹钟优先使用 `AlarmManager.setAlarmClock()`。
- 调用前检查精确闹钟能力；Alpha 默认声明 `SCHEDULE_EXACT_ALARM` 并在 UI 中引导用户授权。
- 正式上架前根据 Google Play 的 alarm app 资格决定是否改用 `USE_EXACT_ALARM`，不得同时滥用两者。
- 使用稳定、唯一的 `PendingIntent` 标识；更新闹钟时先取消旧标识再注册新触发。

### 14.2 必须处理的系统事件

- `BOOT_COMPLETED`
- `TIME_SET`
- `TIMEZONE_CHANGED`
- 应用升级/替换后首次启动
- 精确闹钟权限状态变化

收到后从 Room 读取全部启用闹钟并重算，而不是依赖内存状态。设备重启后系统会清除原 alarm，因此重建是 P0。

### 14.3 响铃路径

```text
AlarmManager
→ AlarmReceiver（只做极短工作）
→ AlarmRingingService
→ 高优先级 CATEGORY_ALARM 通知
→ Full-screen AlarmActivity / heads-up fallback
→ 铃声 + 震动
```

要求：

- Notification channel 使用高重要性、`USAGE_ALARM`。
- 声音使用正确 AudioAttributes，不受媒体音量误控制。
- AlarmActivity 使用系统支持的锁屏显示/点亮方式，不使用废弃 window flag。
- Android 14+ 检查全屏 Intent 能力；不可用时显示持久 heads-up 与清晰修复入口。
- “停止”和“稍后提醒”同时存在于 Activity 与通知操作中。
- 停止操作必须幂等，并释放播放器、震动、wake lock 和 service。
- snooze 创建一个单次 alarm，不改变原重复规则。

### 14.4 权限

按功能需要声明并在运行时逐项解释：

- `POST_NOTIFICATIONS`
- `SCHEDULE_EXACT_ALARM`（Alpha）
- `USE_FULL_SCREEN_INTENT`
- `RECEIVE_BOOT_COMPLETED`
- `VIBRATE`
- 前台服务及媒体播放对应权限
- `RECORD_AUDIO` 只在语音功能启用时请求

拒绝语音权限不能影响闹钟和热点功能。拒绝通知/全屏权限时 UI 必须说明降级行为。

---

## 15. 晨报缓存与 TTS

### 15.1 同步策略

- 用户启用晨报后，WorkManager 每天在闹钟前预留足够时间执行约束式同步。
- 应用启动、网络恢复、闹钟设置变化时触发一次去重后的即时同步。
- 周期任务不是精确执行保障；同步失败不影响闹钟。
- 成功响应完整写入 Room 事务后才替换当前缓存，防止半写入。

### 15.2 缓存选择

触发时按以下顺序：

1. 当前设备日期、当前时区的有效晨报。
2. 最近 24 小时内且内容版本完整的缓存，播报缓存提示。
3. 无内容：不播报新闻，只提示“今日晨报暂未准备好”。

### 15.3 TTS 状态机

```text
Idle → Initializing → Ready → Speaking ↔ Paused → Completed
                         └→ Error
```

- 等待 `OnInitListener` 成功后才调用 speak。
- 检查 `Locale.SIMPLIFIED_CHINESE` 可用性；不可用时引导安装语音数据。
- 每条使用唯一 utterance id，通过 `UtteranceProgressListener` 更新进度。
- 默认语速 1.0，允许 0.8～1.3。
- 音频焦点被通话等高优先级事件抢占时暂停或停止。
- Activity/Service 销毁时正确 `stop()` 与 `shutdown()`。

---

## 16. 唤醒词、STT 与 Intent

### 16.1 先做技术验证

M1 即完成一个独立 Wake Word Spike，必须在目标真机上验证：

- 用户可在系统设置选择本应用为当前语音交互服务。
- 锁屏、息屏时服务是否按系统规则存活。
- 唤醒词在安静和轻噪声环境的成功率。
- 30 分钟耗电、温升、误唤醒次数。
- 与通话、录音、音乐播放冲突时的行为。
- 小米/HyperOS 的额外限制与用户设置步骤。

如果目标 OEM 阻止稳定运行，不能使用保活黑科技；保留按住说话入口，并把息屏唤醒标成实验功能。

### 16.2 服务结构

```text
VoiceInteractionService（轻量、系统保持）
  → WakeWordEngine（本地）
  → 检测事件
  → VoiceInteractionSessionService（单独进程）
  → STT
  → IntentRouter
  → Local executor 或 Backend chat
  → TTS
```

`VoiceInteractionService` 中禁止网络、数据库大查询和复杂 UI。重工作放到 session/service/repository。

### 16.3 隐私

- Wake Word 阶段音频只保留引擎所需的短环形缓冲区。
- 不写文件、不进入日志、不上传。
- 检测成功后明确提示，用户取消即停止 STT。
- 设置页显示当前状态：关闭、本地监听、正式录音、上传识别。
- V0.1 不保存原始语音；只在用户同意后保存转写文本用于会话。

### 16.4 Intent Schema

```kotlin
sealed interface VoiceIntent {
    data class CreateAlarm(val localDateTime: LocalDateTime, val repeat: Set<DayOfWeek>) : VoiceIntent
    data class DisableAlarm(val alarmId: String?) : VoiceIntent
    data object ListTodayHotspots : VoiceIntent
    data class ExplainHotspot(val hotspotId: String?) : VoiceIntent
    data class GenerateQuestion(val hotspotId: String?) : VoiceIntent
    data class AskAI(val text: String, val hotspotId: String?) : VoiceIntent
    data class NeedClarification(val prompt: String) : VoiceIntent
    data object Unsupported : VoiceIntent
}
```

### 16.5 第一版支持的表达

- “明天早上七点叫我。”
- “每周一到周五七点半叫我。”
- “关闭明天的闹钟。”
- “今天有什么热点？”
- “第一条讲详细一点。”
- “这个为什么可能会考？”
- “给我出一道题。”

涉及日期和时间歧义时必须复述确认。例如“七点”在语境不明确时询问早上还是晚上。所有创建/删除闹钟的执行结果都必须语音与 UI 双重反馈。

---

## 17. 安全、隐私与内容规范

### 17.1 密钥和网络

- 后端密钥仅来自环境变量或秘密管理服务。
- Android 只配置 API base URL 和内部 Alpha token；Release 构建不得包含共享静态密钥。
- 生产环境只允许 HTTPS，Debug 本地地址通过单独 network security config 管理。
- 日志自动清理 Authorization、Cookie、API Key、原始正文和用户语音/转写中的敏感内容。

### 17.2 数据最小化

- 不要求通讯录、位置、短信、相册权限。
- install id 使用随机 UUID，服务端仅保存带盐哈希。
- 用户可清除本地缓存、会话文字和匿名统计标识。
- 匿名分析默认关闭或在首次使用时清晰选择，不使用暗示性勾选。

### 17.3 内容

- AI 输出是备考信息整理，不是官方考试预测。
- 对政策、法律、考试规则标注来源和日期。
- 原始新闻与知识材料不得伪造引用。
- 对高风险内容按 Provider 和产品规则进行安全处理，但不得用安全过滤替代事实核查。

---

## 18. Alpha 与正式发布门禁

Alpha 可以使用：

- `X-Client-Token`。
- 手动配置的少量测试来源。
- Mock AI、Fake Wake Word。
- Debug 签名和局域网后端。

公开 Beta 前必须完成：

- 正式用户认证和限流，移除 APK 中共享 token。
- 新闻来源授权/条款审查与隐私政策。
- Google Play 精确闹钟、全屏 Intent、麦克风和数据安全表审核。
- Release 签名、密钥管理、崩溃上报同意机制。
- API 滥用防护、费用上限和告警。
- 真机矩阵测试，至少 Google/AOSP、Xiaomi/HyperOS、Samsung 三类设备。
- 删除 Debug 菜单、fixture 和测试后门。

---

## 19. 测试与评测

### 19.1 后端自动化

- 数据模型和 migration 从空库升级测试。
- RSS 解析、正文缺失、时间格式异常、重复 GUID 测试。
- 精确/近似去重与事件聚类测试。
- AI Schema 边界、伪造引用、超范围分值、修复失败测试。
- 总分服务端计算与阈值测试。
- 晨报 3～5 条、分类多样性、无候选降级测试。
- ETag、分页、统一错误、认证和限流测试。
- Job 幂等和并发锁测试。

### 19.2 AI 黄金集

首版至少 100 条人工标注事件，分为“核心、重点、普通、无关”，并记录分类和理由。不得使用该集合做 Prompt 人工挑例后又宣称为独立测试。

最低基线：

- “核心/重点”与“无关”二分类 F1 ≥ 0.80。
- 无关新闻进入晨报的比例 ≤ 5%。
- Schema 成功率（含一次修复）≥ 99%。
- 引用有效率 100%。
- 人工抽检事实性严重错误率 ≤ 2%。

### 19.3 Android 自动化

- 下一次闹钟时间：跨日、跨周、夏令时/时区变更、过去时间。
- Room migration、缓存替换、断网选择旧缓存。
- Intent parsing 与歧义确认。
- API 成功、304、超时、5xx、Schema 前向兼容。
- TTS 状态机与生命周期。
- Compose 关键页面 loading/empty/error/offline 测试。

### 19.4 真机测试

每项记录机型、系统版本、时间、结果和日志 ID：

1. 锁屏 10 分钟后响铃。
2. Doze 情况下响铃。
3. 强制停止与普通划掉任务的差异有明确说明；用户主动“强制停止”后系统限制不承诺绕过。
4. 重启后闹钟恢复。
5. 修改时区/系统时间后重算。
6. 通知权限拒绝、精确 alarm 权限撤销、全屏权限不可用的降级。
7. 断网响铃和播放缓存晨报。
8. TTS 引擎缺失或中文数据缺失。
9. 息屏唤醒、误唤醒、耗电和麦克风占用冲突。

---

## 20. 开发里程碑与任务顺序

### M0：工程骨架

实现：

- Monorepo、Android 工程、FastAPI、PostgreSQL/pgvector、Compose。
- 环境样例、Docker Compose、format/lint/test 命令。
- `/health`，Android Debug 页请求 `/health`。
- Mock AI 和 fixture 框架。

验收：后端一条命令启动；Android 编译；客户端能显示 health 成功/失败；CI 或本地检查脚本全绿。

### M1：高风险技术 Spike

实现两个最小闭环：

- 精确闹钟 → 锁屏通知/Activity → 停止。
- Assistant service → 本地测试唤醒事件 → STT/模拟 STT → TTS。

验收：真机记录结果。若无真机，输出明确待测步骤，继续 M2，但不得把 M1 标记完成。

### M2：新闻采集与数据库

实现来源、采集、清洗、精确去重、fixture、job run。此阶段不调用真实 AI。

验收：重复执行不产生重复行；错误来源不阻断其他来源；可查询规范化候选数据。

### M3：知识库和 RAG

实现 manifest 校验、切块、向量化、检索 API/CLI、30 查询黄金集。

验收：Mock embedding 可跑测试；真实 embedding 配置后 Recall@8 达到基线。

### M4：AI 热点评分与内容

实现事件聚类、RAG 上下文、Provider Adapter、JSON Schema、分数计算、缓存、评测脚本。

验收：100 条测试集可生成报告；引用有效率 100%；阈值和内容长度通过。

### M5：热点与晨报 API

实现列表、详情、晨报、ETag、错误契约、Alpha 认证、定时生成。

验收：契约测试通过；同一天重复生成幂等；3～5 条和多样性规则生效。

### M6：Android 热点与离线缓存

实现首页、详情、导航、Room、同步、离线态。

验收：在线同步后断网仍可浏览缓存；Schema 未知枚举不崩溃。

### M7：完整闹钟与 TTS

实现重复规则、重启恢复、权限引导、snooze、晨报缓存、播放器。

验收：第 19.4 节除 Wake Word 外全部相关项通过。

### M8：完整语音、加固与 Alpha 交付

实现真实 Wake Word Adapter、STT、Intent Router、RAG 问答、隐私 UI、诊断与发布清单。

验收：六类语音命令通过；唤醒前音频不上云；真机 Wake Word 指标有记录；生成 APK 和完整报告。

---

## 21. 本地启动与检查命令规范

Agent 最终必须让以下工作流成立，并在 README 中根据实际生成结果补充版本和故障排查。

### 21.1 后端

```bash
cp backend/.env.example backend/.env
docker compose up -d db
cd backend
uv sync
uv run alembic upgrade head
uv run python -m app.cli.seed_demo
uv run uvicorn app.main:app --reload
```

含义：

- `cp`：从不含密钥的模板创建本地配置；真实 `.env` 必须被 Git 忽略。
- `docker compose up -d db`：只在后台启动 PostgreSQL/pgvector。
- `uv sync`：按 lockfile 安装可复现的 Python 环境。
- `alembic upgrade head`：把数据库升级到最新 migration。
- `seed_demo`：导入可合法提交的自写示例知识和新闻。
- `uvicorn ... --reload`：开发模式启动 API，源码变化时重载；不得用于生产。

### 21.2 Worker

```bash
cd backend
uv run python -m app.worker
```

含义：启动独立任务进程。API 进程不得同时偷偷运行 scheduler，否则多 worker 部署会重复任务。

### 21.3 Android

WSL 中可运行代码检查；模拟器、USB 真机和 Android Studio 推荐由 Windows 侧负责。仓库在 WSL 时用 VS Code/Android Studio 的 WSL 支持打开，避免在 Windows 与 Linux 两套 Gradle 缓存间混用。

```bash
cd android
./gradlew testDebugUnitTest lintDebug assembleDebug
```

含义：依次运行 JVM 单元测试、Android Lint，并生成 Debug APK。Windows 原生终端使用 `gradlew.bat`；Linux/WSL 使用 `./gradlew`。

### 21.4 总检查

```bash
./scripts/check.sh
```

该脚本必须只做可重复、非破坏性检查：后端格式/类型/测试、契约一致性、Android 单测/lint/build。失败时返回非零退出码。

---

## 22. V0.1 最终验收清单

### 22.1 P0 功能

- [ ] 可创建、修改、删除、启停、重复和 snooze 闹钟。
- [ ] 息屏且进程不存在时闹钟能响。
- [ ] 重启、时区和系统时间变化后正确恢复。
- [ ] 每日自动采集至少 3 个合法测试来源。
- [ ] 精确和近似去重有效，多来源事件可聚合。
- [ ] 知识库可导入、更新和检索。
- [ ] AI 返回固定 Schema，后端计算总分。
- [ ] 热点列表、详情和原始来源可查看。
- [ ] 生成三级摘要与 3～5 条晨报。
- [ ] 晨报提前缓存；断网仍能响铃并播放缓存。
- [ ] 系统 TTS 中文可播，可暂停/继续/停止。
- [ ] 本地 Wake Word 在目标真机通过或明确标为实验并保留按住说话。
- [ ] Wake Word 之前的音频不上传、不落盘。
- [ ] STT 后先走 Intent Router。
- [ ] 创建/关闭闹钟不调用 LLM。
- [ ] AI 问答走 RAG 并返回有效引用。

### 22.2 质量

- [ ] 所有自动化检查通过。
- [ ] 没有硬编码密钥、动态依赖和提交的真实新闻全文。
- [ ] API、数据库、AI 和隐私文档与实现一致。
- [ ] 关键错误有可理解的用户提示和结构化日志。
- [ ] AI 黄金集达到第 19.2 节基线。
- [ ] 真机测试报告包含目标 Xiaomi/HyperOS 设备结果。
- [ ] APK、后端启动说明、示例数据和已知限制齐全。

---

## 23. 决策记录与待用户提供项

以下项目不阻止 Agent 使用 Mock 完成开发，但接入真实能力前需要用户提供：

| 项目 | 缺失时行为 |
|---|---|
| 最终 application id 与产品名 | Alpha 使用 `com.example.exambrief` / “公考晨报” |
| LLM API Key、Provider、模型 | 使用 Mock；真实模型由环境变量配置 |
| Embedding Provider | 使用确定性测试 embedding；真实库不得混入测试向量 |
| Porcupine AccessKey 和 Android `.ppn` | Fake engine + 按住说话；不算真机唤醒完成 |
| 自定义唤醒词 | Alpha 使用供应商内置测试词，中文词后换模型文件 |
| 合法新闻源清单 | 使用本地 fixture 和经确认的公开 feed |
| 合法知识材料 | 使用自写示例，禁止 Agent 自行下载盗版题库 |
| 目标 Xiaomi 机型与 Android/HyperOS 版本 | 其他真机先测，并保留 Xiaomi 门禁 |

默认决策可由用户后续通过 ADR 修改。Agent 不得因这些待提供项把密钥、版权材料或虚假实现塞入仓库。

---

## 24. 官方平台依据

开发和验收时优先以最新官方文档为准。本规格建立时核对了以下页面：

- [Android：Schedule alarms](https://developer.android.com/develop/background-work/services/alarms)
- [Android：VoiceInteractionService](https://developer.android.com/reference/android/service/voice/VoiceInteractionService)
- [Android：后台启动前台服务限制](https://developer.android.com/develop/background-work/services/fgs/restrictions-bg-start)
- [Android：前台服务类型要求](https://developer.android.com/about/versions/14/changes/fgs-types-required)
- [Android：创建通知与 full-screen intent](https://developer.android.com/develop/ui/compose/notifications/create-notification)
- [Android：TextToSpeech](https://developer.android.com/reference/android/speech/tts/TextToSpeech)
- [Google Play：Target API level requirements](https://support.google.com/googleplay/android-developer/answer/11926878)

截至 2026-09-16，Google Play 新手机应用和更新要求面向 Android 16/API 36；平台政策可能继续变化，因此准备上架时必须重新核对。Android 官方说明：用户选择的当前 `VoiceInteractionService` 会由系统保持运行以支持后台 hotword，但服务本身应保持轻量；这不等于所有 OEM 都保证第三方自定义唤醒词具有相同的硬件 DSP、耗电和锁屏体验，所以 M1 真机 Spike 是发布门禁。

---

## 25. 变更控制

任何需求变更先新增 `docs/adr/NNNN-title.md`，说明：

- 问题与背景。
- 原方案。
- 新方案。
- 数据/API/权限/成本/隐私影响。
- 迁移与回滚方法。

以下改动必须由用户明确确认后才能进入 V0.1：新增付费服务、增加敏感权限、上传唤醒前音频、公开发布、采集需要登录或禁止抓取的数据、引入新的基础设施服务、扩大到非公考领域。

本规格至此结束。
