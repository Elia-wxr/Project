# Tarot JupyterLab 六人 Agentic Coding 分工与交付计划

本轮从已经可安装、前后端已连通的开发版继续推进，不再重新搭建项目骨架。六人均按至少拥有一个基于 Qwen3.8 的 Deepseek Harness 的条件安排任务，重点交付 JupyterLab 原生风格界面、侧栏图标、通用 OpenAI-compatible AI 模块和配置页面，以及与课程一分钟演示逐段对应的课程系统 Wiki 展示页；A、B、C、D、F 的代码通过个人分支与 Pull Request 协作，E 统一负责课程 Wiki、配套演示和人工验收，不需要创建分支或提交 PR。

修订日期为 2026-11-08，源码核对基线为 `main@9c643c6ebc0438287f0fde4e4917baa06cba2c7c`。本次修改的是计划文档；下文的 CSS、SVG、页面及新增接口是待实施规范，不代表这些功能已经写入产品代码。

## 合并说明

本版合并了原项目根目录 `Plan.md` 的有效技术内容和小组最新确认的六人分工，不是把两份计划直接拼接。原计划中的数据字段、已有接口、模块行为、验收方法和发布操作继续作为约束；与当前进度或最新要求冲突的人员安排、课程专用 AI 配置和从零搭建任务已替换。

| 原计划内容 | 合并后的处理 |
| --- | --- |
| 两周交付、英文侧栏、单牌与最近记录、正式 PyPI | 保留目标与功能边界；以现有可安装开发版为起点。 |
| 目录、模块说明、完整数据模型和 HTTP 样例 | 保留在“文件归属与接口先行”“数据模型、主流程与已有接口”，按实际 `sidebar.ts`、`TarotClient`、`TarotService` 更新名称和负责人。 |
| 前端和 AI 的旧范围 | 增补 JupyterLab 原生 CSS、侧栏图标、自定义 OpenAI-compatible 服务及配置页，不恢复学校平台绑定。 |
| 旧人力假设、分工和排期 | 以本版六人分工为唯一执行表；全员具备 harness，E 不建分支、不提交 PR，F 负责审核协调与发布。 |
| 测试、试发、正式发布和交接 | 保留详细步骤、命令与记录模板；F 构建/发布，E 独立人工试装，D 为经授权的发布备份。 |
| 课程展示 | 新增课程系统 Wiki 与逐段对应的 60 秒演示，由 E 统一交付，不进入 GitHub Wiki 或代码 PR 流程。 |

## 当前进度与本轮范围

### 已完成的部分继续复用

本计划参考《项目进度与后续安排》《抽牌请求代码讲解与浏览器验证》，并核对了当前仓库源码。两份旧说明与本计划冲突时，以本计划的新分工和验收要求为准，历史演示记录不自动等同于新版验收结果。

| 部分 | 当前基线 | 本轮处理 |
| --- | --- | --- |
| 侧栏和通信 | `frontend/src/sidebar.ts`、`api.ts` 已支持抽牌、解读、保存和查看最近记录。 | 增量美化、图标、配置入口及状态反馈，不重写主流程。 |
| 后端接口 | `app.py` 已提供五个 HTTP 操作，`service.py` 协调活动会话。 | 保留原接口，新增配置与连接测试接口。 |
| 牌库和抽牌 | 已有 78 张牌、单牌抽取、正逆位、关键词及会话 ID。 | 不重新分配“实现牌库”任务，补回归测试和必要修复。 |
| AI | 已有同步 provider、提示词、输出解析器和 `FakeAIProvider`。 | 泛化真实 provider，去除课程平台耦合，保留模拟测试能力。 |
| 本地保存 | 已有最近一条记录的保存、读取、覆盖和写入失败保护。 | 保持 `schema_version=1`，防止新配置功能破坏旧记录。 |
| 构建和测试 | 已有 Python/wheel 和前端构建配置；本次在上述基线重新运行，60 项 Python 测试通过。 | 加入新功能测试、CI、独立试装和发布检查。 |
| 浏览器与真实服务 | 附件记录了开发版模拟流程及重启查看验证。 | 新版界面、真实通用服务和正式发布仍须重新验收，不能用旧截图代替。 |

当前前端是 TypeScript、Lumino Widget 和 DOM 实现，不是已经完成的 React 前端。本轮不为了美化强制迁移 React，也不因为成员使用同一种 coding harness，就把产品运行时 AI 绑定到该 harness 或某个模型。

### 必做与延后

| 优先级 | 本轮交付 | 完成条件 |
| --- | --- | --- |
| P0 | 原生风格 UI 与侧栏图标 | 默认浅色、深色主题均协调；图标可见；键盘可用；窄侧栏无横向溢出。 |
| P0 | 通用 AI provider | OpenAI Chat Completions 协议、自定义 Base URL/模型/密钥，源码和用户文案不再绑定课程平台。 |
| P0 | AI 配置页 | 可编辑配置、保存非敏感项、管理临时密钥、主动测试连接，清楚区分模拟与真实模式。 |
| P0 | 稳定性和安全回归 | 无配置、错误密钥、超时、异常输出、连续点击后仍可恢复；旧历史可读，密钥不泄漏。 |
| P0 | 代码 PR 协作与独立展示交付 | A、B、C、D、F 各自建分支并提交 PR，由 F 协调审核；F 自己的 PR 由其他成员审核。E 无需分支或 PR，以课程 Wiki、演示和人工验收记录交付。 |
| P0 | 课程系统 Wiki 与一分钟演示 | 在课程系统发布，不走 GitHub 或 PR；一页串起实际功能和证据，60 秒脚本与页面分区、实际版本逐段对应。 |
| P0 | 独立试装与正式 PyPI | 候选包由非构建者试装；正式发布后再次按包名和版本安装验收。 |
| 延后 | 三牌阵、多条历史、导入导出、牌面图库、多语言、流式输出、多 provider 档案 | 不挤占本轮；只维护一套有效 AI 配置和最近一条历史。 |

原计划的首版边界继续有效：只支持单用户 Jupyter Server、一个活动会话、`single` 牌阵和 `focus` 位置。牌库浏览/搜索、按位置重抽、多用户账号与同步、完整 JSON Schema、自动发布和多平台测试矩阵均不在本轮必做范围；课程若要求源码包 `sdist`，D1 单独加入交付清单。

## 六人分工

A-F 是成员代号，不代表能力、资历或可用工时。D1 将其替换为姓名并确认实际可用时间；取消旧计划中“只有两人有 agent”“半量交接”“E/F 机动”的假设，按工程开发、审核发布和课程展示分配六人的独立责任，E 不承担代码提交要求。

| 成员 | 主责 | 主分支示例 | 交付重点 | 核验 / 工作备份 |
| --- | --- | --- | --- | --- |
| A | 主侧栏视觉、主题、图标及入口集成 | `feat/a-sidebar-theme-icon` | CSS、SVG、主界面状态、配置页挂载、主流程 E2E | F 主审，B 核对界面 / B |
| B | AI 配置页面和前端请求契约 | `feat/b-ai-settings-ui` | 表单、校验、保存/测试反馈、类型和配置页测试 | F 主审，接口由 D 加审 / A |
| C | 通用 AI provider 与兼容性 | `feat/c-openai-compatible-provider` | 去耦、请求/响应适配、网络异常测试 | F 主审，D 核对后端契约 / D |
| D | 配置后端、安全边界和运行时接入 | `feat/d-ai-settings-api` | 配置存储、认证接口、热更新、后端回归测试 | F 主审，C 核对安全与 provider / C |
| E | 课程 Wiki、配套演示与人工验收 | 不需要分支或 PR | 页面编辑发布、60 秒脚本与计时、独立试装和问题记录 | A 核对展示，C/D 核对技术描述 / B |
| F | PR 审核、CI、打包与发布 | `chore/f-ci-release` | 审核记录、CI 门禁、依赖、干净构建、README、发布证据 | 自己的 PR 由 A 或 D 审核 / D |

### A：原生风格主界面与图标

- **A-01，D3 前**：按本文 CSS 规范改造主侧栏，加入塔罗 SVG 和 `LabIcon`，替换竖排纯文字标签。提交浅色与深色截图，原有抽牌、解读和保存按钮继续工作。
- **A-02，D5 前**：统一输入框、按钮、分区标题、牌面摘要、历史记录、空状态和错误状态。补 `focus-visible`、禁用、加载及窄宽度处理，保留英文默认界面。
- **A-03，D7 前**：接入 B 的配置面板，显示 AI 状态和配置入口。配置保存失败不得清空当前牌面，主侧栏不得自行持有或回显 API key。
- **A-04，D3 骨架、D8 完整回归**：维护 `tests/e2e/` 主流程测试骨架，覆盖两种主题、窄侧栏、键盘、重复点击及解读/保存反馈。B 在同一骨架补配置页场景，F 接入 CI。
- **展示素材，D8 前**：向 E 提供最终风格的主侧栏、抽牌和历史截图，标注对应提交及实际状态，不另做与产品不一致的宣传界面。
- **验收证据**：主题对比截图、320/480 px 侧栏截图、键盘走查及前端构建结果。A 审查 B 的界面 PR，不承担其他五人的全部集成修复。

### B：AI 配置页面

- **B-01，D3 前**：新建 `settings.ts`，使用约定的 mock 响应完成配置页。与 D 冻结字段、错误码、密钥操作语义；不等待真实账号才能开发。
- **B-02，D6 前**：在 `api.ts` 和 `types.ts` 接入读取、保存、连接测试，保留原有五个操作。请求封装须支持 PUT、嵌套 JSON、数字和布尔值，不能沿用仅接收字符串字段的限制；结构化保留 HTTP 状态和 `error.code`，再处理草稿、环境变量锁定及测试反馈。
- **B-03，D7 前**：补前端表单/状态测试，处理服务重启后的“密钥未设置”，以及更换服务器后必须重新提供密钥的提示。向 A 提供小型挂载接口，而不是改写整份 `sidebar.ts`。
- **展示素材，D8 前**：向 E 提供不含密钥的配置页截图及一句“自定义服务器和模型”的演示说明，供 Wiki 与口播使用。
- **验收证据**：从未配置到真实模式可用的完整操作记录；测试失败仍保留草稿和当前牌面。B 审查 A 的主题和可访问性。

### C：通用 AI provider

- **C-01，D3 前**：实现 `OpenAICompatibleProvider`，删除旧 provider 类名、导出、课程模型默认值和专用环境变量读取。保留 `AIProvider.generate(prompt)` 的同步契约和 `FakeAIProvider`。
- **C-02，D5 前**：覆盖自定义地址、子路径、尾斜杠、Bearer/无认证、模型透传、超时、401/403、404、429、5xx、空内容及异常 JSON。请求不自动重试，不偷偷切换服务或模拟结果。
- **C-03，D7 前**：与 E 用获授权的真实自定义兼容服务完成一次侧栏解读，核对总结、单牌解释和建议。另一类端点至少完成传输契约模拟测试，并明确标注模拟与真实的区别。
- **展示素材，D8 前**：向 E 提供合成问题对应的真实解读样例及 provider 机制的简短解释，注明哪些结果来自真实服务、哪些来自模拟测试。
- **验收证据**：provider 单元测试、请求契约样例及脱敏真实验收记录。若服务或账号不可用，记录具体阻塞，不把 mock 通过写成真实通过。

### D：配置 API 与安全接入

- **D-01，D2 前**：提交配置接口样例和 Python 数据约定，与 B/C 确认依赖。新增 `ai/config.py`，统一配置来源，provider 本身不再到处读取环境变量。
- **D-02，D5 前**：实现配置读取、保存及测试 handler，认证、XSRF、校验和脱敏错误处理沿用 Jupyter 请求边界。实现非敏感配置原子保存，密钥仅保存在进程内存或由环境变量提供。
- **D-03，D7 前**：在 `service.py` 接入有效配置快照、忙碌保护和超时恢复。配置变更不影响旧历史，进行中的解读不被换 provider，失败时不部分写入新配置。
- **D-04，D3 骨架、D8 完整回归**：维护后端 `tests/integration/` 和共享 fixture，补抽牌/历史回归、写入失败、配置冲突、迟到结果、重定向与地址边界测试。接收 E 的人工复现后，由对应代码作者修复，E 不改源码。
- **展示素材，D8 前**：向 E 提供“前端 → Python 后端 → 配置的 AI 服务”的实际链路说明，核对 Wiki 上的安全和存储描述没有夸大。
- **验收证据**：配置优先级、并发冲突、磁盘失败、密钥清除、重启、日志脱敏及未认证请求测试。D 审查 C 的请求和错误处理。

### E：课程 Wiki、配套演示与人工验收

E 不需要创建 Git 分支或提交 PR，也不承担自动化测试代码和源码修复。交付直接保存在课程系统或小组共享文档；发现问题时提供操作步骤、预期/实际结果和脱敏截图，由 A-D 的模块作者补测试和修复。

- **E-01，D2 前**：确认课程 Wiki 的页面位置、编辑/阅卷权限、语言及现场/录屏要求，整理页面框架和人工验收清单。记录实际页面 URL，不需要 GitHub Wiki 或代码仓库权限。
- **E-02，D8 初稿、D10 展示候选版、D12 最终版**：汇总 A-D 的功能素材和 F 的版本/安装/审核证据，在课程系统统一编辑和发布 Wiki。保证页面与已验收版本一致，A 核对展示，C/D 核对技术描述，不走 PR。
- **E-03，D8-D12**：按清单人工走查主流程、配置、两种主题和错误恢复；D11/D12 在干净环境独立安装候选包与正式包。至少 E 和另一位成员各跑一次完整流程，记录问题、复验结果和环境，不要求 E 编写测试脚本。
- **E-04，D9 初稿、D10 计时**：编写与 Wiki 分区一一对应的 60 秒演示脚本和操作表，组织至少两次完整计时排练。检查页面、操作、真实/模拟标识与候选版本一致，指定主讲及备份，D12 随最终页面复排。
- **验收证据**：课程页面编辑/发布记录、素材清单、脚本、实际计时、人工缺陷复现及安装记录。E 的贡献不以提交数量或 PR 数量衡量，也不替代代码作者的自动化测试责任。

### F：PR 审核、工程化与发布

- **F-01，D2 前**：统一维护依赖声明和锁文件，提前加入图标所需依赖，建立 Python 测试、前端构建及文档检查的 PR 流水线。新增门禁先在基线上确认可运行，不把未确认的旧问题全部塞入本轮。
- **F-02，D8 前**：补配置说明、跨终端安装步骤、故障排查和包内容检查脚本。更新 README 和两份进度/讲解文档，删除其中会误导用户的旧平台专属设置。
- **F-03，D11-D14**：从冻结提交构建、检查并交付候选包，经 E 独立验收和组内确认后发布正式 PyPI。记录版本、源码 SHA、制品 SHA-256、安装命令及发布后的验收。
- **F-04，D2 建立清单、D3-D10 持续审核**：负责 A-D 的 PR 首轮审核和合并前检查，核对改动范围、公共契约、相关测试、CI、异常处理、密钥及说明文档。给出具体 review 意见并跟踪修复，跨模块改动邀请对应成员加审，不用“agent 说通过”代替核验。
- **展示支持，D8/D12**：向 E 提供安装命令、源码/包版本、正式发布链接和代码 PR/review 清单。F 不再负责 Wiki 编辑、发布或演示脚本。
- **验收证据**：PR 审核记录、待修问题清单、CI、构建/包检查脚本、文档和发布清单。F 自己的 PR 由 A 或 D 审核，禁止自审自批；审核职责不等于获得自动合并或发布权限。

## 文件归属与接口先行

下面是主要写入权，不是禁止别人阅读。跨代码模块改动先在 PR 中说明，由文件负责人确认；尤其不能让多个 agent 同时改入口、依赖和锁文件，再把冲突全部留到最后；课程 Wiki 和配套展示材料则按表中负责人直接协作，不走代码 PR。

| 文件或目录 | 主写人 | 协作规则 |
| --- | --- | --- |
| `frontend/src/sidebar.ts`、`index.ts` | A | B 提供配置面板 API，挂载由 A 完成。 |
| `frontend/style/index.css`、`base.css`、`sidebar.css`、`icons/tarot.svg` | A | A 维护 CSS 汇总入口；基础规范全员复用。 |
| `frontend/src/icons.ts`、`svg.d.ts` | A | 图标源码和类型声明随同提交，不手改构建产物。 |
| `frontend/src/settings.ts`、`frontend/style/settings.css` | B | 只负责配置面板；A 将其样式加入汇总入口。 |
| `frontend/src/api.ts`、`types.ts` | B | D 确认 HTTP 字段；扩展方法不得破坏既有调用。 |
| `src/tarot_jupyterlab/ai/provider.py`、`ai/__init__.py`、`prompts.py`、`interpreter.py` | C | 保留解析契约；不要引入无关的多轮聊天重构。 |
| `src/tarot_jupyterlab/ai/config.py`、`app.py`、`service.py`、`errors.py` | D | C 通过构造参数接收配置；D 清理服务层残留名称。 |
| `cards.py`、`history.py`、`tests/integration/`、共享 fixture | D | C 补 AI 场景；业务代码只做有测试支持的缺陷修复，不扩展牌阵或历史条数。 |
| `tests/e2e/` | A 主维护、B 写配置页场景 | A/B 协调文件边界，F 接入 CI；不再由 E 编写自动化测试。 |
| 演示脚本、逐秒操作表、计时记录（课程系统附件或小组共享文档） | E | A 核对展示，主讲及备份参加计时；无需分支或 PR。 |
| 课程系统 Wiki 展示页、脱敏截图/录屏和素材清单 | E 汇总 | A-D 提供功能素材、F 提供版本和审核证据；E 统一编辑发布，A/C/D 核对内容，无需 PR。 |
| `pyproject.toml`、`frontend/package.json`、`yarn.lock`、CI、发布脚本、README、docs | F | 依赖需求在 D1 汇总；后续用小 PR 单独修改，禁止多种锁文件并存。 |
| `card_set.json` | D 维护数据校验，F 维护打包映射 | 根目录文件继续作为唯一牌库源；安装后按包资源读取，不另手工维护一份生成副本。 |
| `src/tarot_jupyterlab/__init__.py`、`_version.py`、`jupyter-config/` | F | 扩展发现和启用配置由 D 协同核对；版本和安装映射纳入 F 的发布 PR，由 A 或 D 审核。 |
| `src/tarot_jupyterlab/labextension/` 等前端生成产物 | 构建流程生成 | A/B 改前端源码，F 验证生成和打包结果；不直接手改编译后的 JS/CSS 来修问题。 |
| `models.py`、现有 JSON 字段、`Plan.md` | 共享契约 | D 负责接口变更协调，F 维护合并后的计划；改变契约须通知使用方。 |
| 模块单元测试 | 对应模块作者 | A/B 写前端测试，C 写 provider 测试，D 写配置/存储测试，F 写构建检查；E 只做人工验收和问题记录。 |

建议 B 导出 `TarotSettingsPanel extends Widget`，构造参数为 `TarotClient` 和保存成功回调。D1 先确定这个接口与 JSON fixture，A 可接 stub、B 可接 mock、C 可接假 HTTP transport，三条工作线都不需要等待真实服务或完整后端。

## 数据模型、主流程与已有接口

本节恢复原计划中仍有效的详细契约，供代码成员和 harness 做回归检查，不表示需要重新实现这些已有功能。Python 模型、HTTP 响应与磁盘记录必须保持一致；新增 AI 配置使用独立的数据结构，不能混入塔罗历史。

### 会话与记录

| 对象 | 字段与首版约定 |
| --- | --- |
| `Card` | 保留牌名、类别、花色、牌号、等级、元素和两组关键词；正逆位属于抽牌结果，不改变牌库本体。 |
| `DrawnCard` | `card` 为实际抽到的牌，`position="focus"`，`orientation` 只能是 `upright` 或 `reversed`。 |
| `Session` | 服务端生成 UUID；`spread_name="single"`、`cards` 长度为 1、`revision=1`、`allow_repeats=false`；时间为带时区的 UTC 时间。 |
| `Reading` | `session_id`、`session_revision` 匹配当前会话；包含 `summary`、长度为 1 的 `card_interpretations`、`advice`、`provider` 和 `created_at`。 |
| `SessionRecord` | 顶层固定为 `schema_version=1`、`session`、`reading`；尚未解读时 `reading=null`。 |
| 运行状态 | 活动记录、生成请求标记和按钮状态只在运行时维护；成功解读可以更新时间，保存与查看保留快照值。 |

一次成功抽牌同时新建会话和选牌，对外首次可见的会话版本为 1。两个独立会话可以抽到同一张牌，`allow_repeats=false` 不代表禁止跨会话抽到相同牌；首版没有会话内重复抽牌设置。

### 五个已有 HTTP 操作

所有路径相对于 Jupyter Server 的 `base_url`，前端沿用 `TarotClient`、`ServerConnection.makeRequest` 和服务器设置，不硬编码根路径或端口。写请求采用 JSON；服务端校验请求类型和字段，牌面、会话版本、时间及保存路径均由服务端决定，不信任浏览器提交的替代值。

| 方法与路径 | 请求 | 成功响应 | 保持的行为 |
| --- | --- | --- | --- |
| `GET /tarot/api/health` | 无 | `200 {"status":"ok"}` | 仅验证插件后端可用，不代表 AI 连通。 |
| `POST /tarot/api/draw` | `{"question":"What should I reflect on?"}` | `200 {"record": SessionRecordJSON}` | 问题 trim 后为 1–2000 字符；成功替换活动记录，初始 `reading=null`，失败不清掉旧记录。 |
| `POST /tarot/api/reading` | `{"session_id":"…","language":"en"}` | `200 {"record": SessionRecordJSON}` | 只处理当前 ID；首版接受 `en` 或省略语言。已有解读时返回当前记录，失败后可重试。 |
| `POST /tarot/api/history/latest` | `{"session_id":"…"}` | `200 {"record": SessionRecordJSON}` | 保存服务端的完整活动记录，磁盘替换成功后才回复成功。 |
| `GET /tarot/api/history/latest` | 无 | `200 {"record": SessionRecordJSON 或 null}` | 文件不存在返回 `{"record":null}`，损坏返回存储错误；只读，不创建活动会话。 |

磁盘 JSON 对应 `record` 字段的内容，不包含 HTTP 的外层 `{"record": ...}` 包装。时间序列化为 ISO 8601 带时区字符串，Python tuple 对应 JSON 数组，`None` 对应 `null`；无可用 AI 时仍能健康检查、抽牌、保存牌面和读取历史。

### 完整字段与共享样例

以下 `*JSON` 类型用于完整描述传输格式，不要求把现有前端的 `SessionRecord`、`DrawnCard` 等类型全部重命名。B 维护 `frontend/src/types.ts`，D 维护共享 fixture，C 复用 AI 样例；D1 对齐 `draw-ok.json`、`reading-ok.json`、`history-empty.json`、`reading-timeout.json`，再增加配置读取、保存冲突和连接测试样例。

```typescript
export interface CardJSON {
  name: string;
  arcana: "Major" | "Minor";
  suit: "Wands" | "Cups" | "Swords" | "Pentacles" | null;
  number: number | null;
  rank: string | null;
  element: string;
  upright: string[];
  reversed: string[];
}

export interface DrawnCardJSON {
  card: CardJSON;
  position: "focus";
  orientation: "upright" | "reversed";
}

export interface SessionJSON {
  session_id: string;
  question: string;
  spread_name: "single";
  cards: [DrawnCardJSON];
  revision: 1;
  allow_repeats: false;
  created_at: string;
  updated_at: string;
}

export interface ReadingJSON {
  session_id: string;
  session_revision: 1;
  summary: string;
  card_interpretations: [string];
  advice: string;
  provider: string;
  created_at: string;
}

export interface SessionRecordJSON {
  schema_version: 1;
  session: SessionJSON;
  reading: ReadingJSON | null;
}

export interface ErrorJSON {
  error: { code: string; message: string };
}
```

下面保留原计划的一条合成记录，用于解读、保存和读取测试，不是已完成的真实 AI 验收证据。抽牌成功样例采用相同结构，将 `reading` 改为 `null`，并令 `updated_at` 等于 `created_at`；模拟数据和真实调用结果必须分别标识。

```json
{
  "record": {
    "schema_version": 1,
    "session": {
      "session_id": "e3338dca-3a88-4a5f-8bb7-5b2dc96f1398",
      "question": "What should I reflect on?",
      "spread_name": "single",
      "cards": [
        {
          "position": "focus",
          "orientation": "upright",
          "card": {
            "name": "The Fool",
            "arcana": "Major",
            "suit": null,
            "number": 0,
            "rank": null,
            "element": "Air",
            "upright": ["beginnings", "freedom"],
            "reversed": ["recklessness", "hesitation"]
          }
        }
      ],
      "revision": 1,
      "allow_repeats": false,
      "created_at": "2026-01-01T08:00:00+00:00",
      "updated_at": "2026-01-01T08:00:02+00:00"
    },
    "reading": {
      "session_id": "e3338dca-3a88-4a5f-8bb7-5b2dc96f1398",
      "session_revision": 1,
      "summary": "Consider approaching the question with curiosity.",
      "card_interpretations": ["The Fool suggests openness to a new start."],
      "advice": "Pick one small step you can reflect on today.",
      "provider": "FakeAIProvider",
      "created_at": "2026-01-01T08:00:02+00:00"
    }
  }
}
```

错误继续使用统一外壳，前端按 `error.code` 选择英文提示，同时保留 HTTP 状态。未知错误显示通用重试提示，不把原始服务端堆栈或上游响应直接展示给用户。

```json
{
  "error": {
    "code": "AI_TIMEOUT",
    "message": "The reading took too long. Try again or save the card without a reading."
  }
}
```

### 统一错误映射

| HTTP | `error.code` | 何时返回 | 界面处理 |
| --- | --- | --- | --- |
| 400 | `INVALID_REQUEST` | JSON、字段类型、问题长度或配置字段非法。 | 指出可纠正项，保留非敏感输入。 |
| 404 | `SESSION_NOT_FOUND` | 请求需要活动会话，但服务端没有。 | 提示重新抽牌。 |
| 409 | `SESSION_CONFLICT` | 客户端 ID 与活动 ID 不同。 | 提示会话已变化，清理过期操作状态。 |
| 409 | `READING_IN_PROGRESS` | 生成期间再次生成、抽牌或保存。 | 提示等待，仍可只读查看历史。 |
| 409 | `CONFIG_CONFLICT` | 保存或测试使用了旧 `config_revision`。 | 保留草稿，提示重新读取有效配置。 |
| 503 | `AI_UNAVAILABLE` | 缺配置、鉴权失败或无法连接配置的服务。 | 提示检查配置，允许保存牌面。 |
| 503 | `AI_RATE_LIMITED` | 上游返回 429。 | 提示稍后手动重试，不自动连续请求。 |
| 504 | `AI_TIMEOUT` | provider 或整体等待超时。 | 恢复按钮，允许重试或只保存牌面。 |
| 502 | `AI_BAD_RESPONSE` | 上游服务错误、空内容或响应无法解析。 | 保留牌面，显示脱敏生成失败提示。 |
| 500 | `STORAGE_ERROR` | 历史/配置读取损坏或写盘失败。 | 不显示保存成功，旧文件和有效状态保持不变。 |
| 500 | `INTERNAL_ERROR` | 牌库或其他服务端异常。 | 显示通用错误，仅记录必要脱敏诊断。 |

Jupyter 自身的认证拒绝或会话过期可能返回非 JSON，B 要在请求封装中处理并提示重新连接，而不是只尝试解析 JSON。应用响应、普通日志、测试附件和演示素材都不得包含真实密钥、认证头、完整模型原文或私人问题。

### 牌库、会话协调与历史存储

下面保留已有 Python 函数签名，作为 D 的回归边界，而不是新的开发任务。C 负责 provider，D 负责牌库/历史必要修复和服务协调；原计划中由 A 新建服务端、C 新建牌库的任务不再重复安排。

```python
from datetime import datetime
from pathlib import Path
from random import Random
from typing import Any

from tarot_jupyterlab.models import Card, Session, SessionRecord


def load_card_set(path: Path | None = None) -> tuple[Card, ...]:
    """Load the packaged deck or an explicit test file."""
    ...


def create_single_session(
    question: str,
    cards: tuple[Card, ...],
    *,
    rng: Random | None = None,
    now: datetime | None = None,
) -> Session:
    """Validate the question and draw one card and orientation."""
    ...


def record_to_dict(record: SessionRecord) -> dict[str, Any]:
    """Serialize the shared record shape for HTTP and disk."""
    ...


def save_latest(record: SessionRecord, path: Path) -> None:
    """Atomically replace the latest saved record."""
    ...


def load_latest(path: Path) -> dict[str, Any] | None:
    """Return a validated snapshot, or None for a missing file."""
    ...
```

- **牌库校验**：UTF-8 JSON 应有 78 张牌，其中 22 张 Major、56 张 Minor，牌名唯一、必要字段与正逆位关键词有效；无效数据抛 `InvalidCardSetError`。启动时加载一次，安装环境通过 `importlib.resources` 读包内资源，测试可传临时路径。
- **问题与随机性**：问题 trim 后须为 1–2000 字符，无效输入抛 `InvalidSessionError`。抽牌和正逆位使用同一个可注入随机源；固定种子测试对比牌与朝向，UUID 和时间可独立变化。
- **职责分层**：`app.py` 负责认证、请求校验、路由和错误响应，`TarotService` 负责活动记录与调用顺序，工作线程只返回候选解读。不能把业务状态散落到多个 handler 或让 provider 直接改活动记录。
- **生成隔离**：生成前校验 ID、忙碌状态并取快照，服务层在线程中调用同步解读函数；按本版 `timeout_seconds + 5` 设置整体等待上限，不恢复原计划中固定 45 秒的旧值。仅在请求标记和活动 ID 仍匹配时接收结果，超时/取消后的迟到结果不得写回。
- **服务生命周期**：刷新浏览器后可只读打开最近保存记录；服务重启会清除未保存的活动会话。查看历史不能覆盖当前表单、重抽牌、自动调用 AI 或生成新的活动会话。
- **存储路径**：最近记录默认位于用户 Jupyter 数据目录的 `tarot-jupyterlab/latest.json`；客户端仅传会话 ID，测试注入临时路径。AI 非敏感配置另存于配置目录，不能共用历史文件。
- **原子保存**：先校验版本、单牌及解读关联，在目标目录写完整临时文件，关闭后原子替换；失败抛 `StorageError` 并清理临时文件，旧记录仍可读。磁盘成功后前端才能显示 `Saved`。
- **只读加载**：缺失文件返回空，无法解码、关键字段缺失或解读关联错位返回 `StorageError`。覆盖有/无解读往返、空目录、损坏、覆盖、替换失败和重启后内容一致的回归用例。

扩展发现入口和启用 JSON 是现有安装链路的一部分，本轮只验证不回退；F/D 核对 `_jupyter_server_extension_points()`、`_load_jupyter_server_extension()` 与安装映射，沿用 [Jupyter Server 扩展发现与启用规范](https://jupyter-server.readthedocs.io/en/latest/developers/extensions.html#making-an-extension-discoverable)。AI 配置新增三个 HTTP 操作后，也必须保持原来的五个操作可用，而不是替换现有路由。

### 主侧栏状态和现有客户端

主界面继续包含 `Your question`、`Draw a card`、`Drawn card`、`Generate reading`、`Save as latest` 和 `Latest saved reading`，并显示 `For entertainment and self-reflection only.`。A 负责主界面状态，B 扩展请求封装和配置面板；问题、解读和错误按纯文本渲染。

| 状态 | 页面行为 |
| --- | --- |
| 初始或未配置 AI | 可抽牌、查看历史和打开配置页；无活动记录时禁用生成和保存。 |
| 抽牌成功 | 显示牌名、正逆位与对应关键词，标为 `Unsaved`；允许生成或直接保存。 |
| 正在生成 | 显示 `Generating reading…`，禁用抽牌、重复生成、保存和修改有效 AI 配置；历史仍可只读查看。 |
| 生成成功 | 显示总结、单牌解释和建议；模拟模式必须有可见的模拟标识。 |
| 生成失败或超时 | 保留牌面，恢复按钮，提供重试、配置检查和只保存牌面的路径。 |
| 保存 | 提示 `This replaces any previously saved reading.`，确认后发送 ID；成功响应到达后才显示 `Saved`。 |
| 历史 | 区分空状态、只读记录和读取错误；不覆盖当前问题、牌面和配置草稿。 |

实际前端已使用 `TarotClient` 类，下列是需要保持的现有方法，不再采用原计划中尚未实现的自由函数命名。B 在同一客户端增加配置方法，并确保请求层支持 PUT、嵌套 JSON、数字和布尔值。

```typescript
// Existing TarotClient contract; SessionRecord is the current frontend type.
interface TarotClientContract {
  health(): Promise<{ status: 'ok' }>;
  draw(question: string): Promise<SessionRecord>;
  reading(sessionId: string): Promise<SessionRecord>;
  saveLatest(sessionId: string): Promise<SessionRecord>;
  latest(): Promise<SessionRecord | null>;
}
```

## 前端 CSS 与交互规范

### 视觉原则

插件应像 JupyterLab 自带侧栏，而不是嵌入另一套网站主题。JupyterLab 官方要求扩展优先复用公共主题变量，避免依赖 `--jp-private-*`，样式放在 `style/` 并由入口汇总，见 [JupyterLab CSS Patterns](https://jupyterlab.readthedocs.io/en/stable/developer/css.html)。

- **整体风格**：紧凑、清晰、低装饰；不使用渐变、玻璃效果、大面积阴影、外链字体或另一个 UI 框架的全局 reset。
- **作用域**：主根节点使用 `.jp-TarotSidebar`，配置面板使用 `.jp-TarotSettingsPanel`；组件子类名表达语义。禁止无作用域的 `button`、`input`、`h2`、`body` 或 JupyterLab 全局选择器。
- **颜色**：产品 CSS 不写死白色/黑色，不读取主题名称后自行切换色表；通过公共变量自动适配主题。不得覆盖宿主现有的 `--jp-*` 变量，不用 `!important` 修补层叠。
- **间距与尺寸**：采用 4/8/12/16 px 间距，侧栏内边距 12 px，控件最小高度 28 px。宽度跟随容器，测试 320 px 与 480 px；200% 缩放下允许换行，不出现横向滚动或按钮遮挡。
- **内容层级**：标题、问题输入、牌面、解读、操作、最近历史清晰分组。保持 `Unsaved`、`Saved`、`Demo reading (simulated)` 等可见文本，不仅靠颜色区分状态。
- **可访问性**：每个输入有可关联的英文 label；Tab 顺序合理；保留焦点样式；加载状态使用 `aria-busy`，状态区使用 `role="status"` 和 `aria-live="polite"`。
- **安全渲染**：用户问题、模型输出和服务器错误使用 `textContent` 等纯文本方式。固定模板可以使用静态 HTML，禁止把上述动态字符串插入 `innerHTML`。

以下 token 对应 JupyterLab 公共主题变量，具体定义可在 [JupyterLab 主题变量文件](https://github.com/jupyterlab/jupyterlab/blob/main/packages/theme-light-extension/style/variables.css) 核对。表中使用方式是本项目约定，不另建一套独立配色。

| 用途 | CSS token |
| --- | --- |
| 主背景 / 次级区域 | `--jp-layout-color1` / `--jp-layout-color2` |
| 主要 / 次要文字 | `--jp-ui-font-color1` / `--jp-ui-font-color2` |
| 字体 / 正文 / 辅助字 | `--jp-ui-font-family` / `--jp-ui-font-size1` / `--jp-ui-font-size0` |
| 边框 / 圆角 | `--jp-border-color2` / `--jp-border-radius` |
| 输入背景 / 边框 / 焦点边框 | `--jp-input-background` / `--jp-input-border-color` / `--jp-input-active-border-color` |
| 主按钮 / 反色文字 | `--jp-brand-color1` / `--jp-ui-inverse-font-color1` |
| 错误 / 成功 / 提醒 | `--jp-error-color1` / `--jp-success-color1` / `--jp-warn-color1` |

### CSS 起步模板

下面的片段供 A 落到 `frontend/style/sidebar.css`，不是要求只完成这些样式。B 的配置页沿用同一规范，A 在 `style/index.css` 中统一引入本地 `base.css`、`sidebar.css` 和 `settings.css`。

```css
.jp-TarotSidebar {
  box-sizing: border-box;
  min-width: 0;
  padding: 12px;
  overflow: auto;
  color: var(--jp-ui-font-color1);
  background: var(--jp-layout-color1);
  font-family: var(--jp-ui-font-family);
  font-size: var(--jp-ui-font-size1);
}

.jp-TarotSidebar .jp-TarotSidebar-section {
  display: grid;
  min-width: 0;
  gap: 8px;
  margin-block-end: 16px;
}

.jp-TarotSidebar .jp-TarotSidebar-input {
  box-sizing: border-box;
  width: 100%;
  min-height: 28px;
  padding: 6px 8px;
  border: 1px solid var(--jp-input-border-color);
  border-radius: var(--jp-border-radius);
  background: var(--jp-input-background);
  color: var(--jp-ui-font-color1);
  font: inherit;
}

.jp-TarotSidebar .jp-TarotSidebar-button {
  min-height: 28px;
  padding: 4px 12px;
  border: 1px solid var(--jp-border-color2);
  border-radius: var(--jp-border-radius);
  background: var(--jp-layout-color2);
  color: var(--jp-ui-font-color1);
  font: inherit;
  cursor: pointer;
}

.jp-TarotSidebar .jp-TarotSidebar-button.jp-mod-primary {
  border-color: var(--jp-brand-color1);
  background: var(--jp-brand-color1);
  color: var(--jp-ui-inverse-font-color1);
}

.jp-TarotSidebar .jp-TarotSidebar-button:disabled {
  opacity: 0.5;
  cursor: default;
}

.jp-TarotSidebar .jp-TarotSidebar-input:focus-visible,
.jp-TarotSidebar .jp-TarotSidebar-button:focus-visible {
  outline: 2px solid var(--jp-brand-color1);
  outline-offset: 2px;
}

.jp-TarotSidebar .jp-TarotSidebar-message {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.jp-TarotSidebar .jp-TarotSidebar-message.jp-mod-error {
  color: var(--jp-error-color1);
}
```

### 侧栏图标

左侧活动栏使用“一张卡片加中心菱形”的单色图标，面板内部继续显示 `Tarot` 标题。自定义图标用 `@jupyterlab/ui-components` 的 `LabIcon` 和主题 class 注解，SVG 独立存放；这是 [JupyterLab UI 复用指南](https://jupyterlab.readthedocs.io/en/4.6.x/extension/ui_components.html) 推荐的接入方式。

图标草案保存为 `frontend/style/icons/tarot.svg`，采用 `24 × 24` viewBox。A 可以微调轮廓，但不得替换成 emoji、远程图片或固定浅色背景图片。

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path class="jp-icon3" fill="currentColor" fill-rule="evenodd"
    d="M7 2h10a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Zm0 2v16h10V4H7Z"/>
  <path class="jp-icon3" fill="currentColor"
    d="m12 7 3 5-3 5-3-5 3-5Z"/>
</svg>
```

```typescript
// frontend/src/icons.ts
import { LabIcon } from '@jupyterlab/ui-components';
import tarotSvg from '../style/icons/tarot.svg';

export const tarotIcon = new LabIcon({
  name: 'tarot-jupyterlab:tarot',
  svgstr: tarotSvg
});
```

```typescript
// frontend/src/svg.d.ts
declare module '*.svg' {
  const value: string;
  export default value;
}
```

```typescript
// frontend/src/sidebar.ts: import 后，在现有构造函数内设置
this.title.icon = tarotIcon;
this.title.label = '';
this.title.caption = 'Tarot';
this.addClass('jp-TarotSidebar');
```

- **依赖**：F 在 D2 前把与现有 JupyterLab 4 依赖系列一致的 `@jupyterlab/ui-components` 加入 `frontend/package.json`，同步 `yarn.lock`；A 补 `tarotIcon` import。
- **布局**：保持现有 `app.shell.add(sidebar, 'left', { rank: 900 })`，不另造活动栏，也不覆盖其他扩展图标。
- **可访问性**：实际检查活动栏 tab 的可访问名称为 `Tarot`，不能把空 label 当成验收完成；若宿主未从 caption 提供名称，按宿主 tab 接口补全。
- **验收**：浅色/深色下分别检查正常、hover、选中及缩放状态；侧栏内另提供有英文标签的 `AI settings` 入口。

## 通用 AI 模块规范

### 兼容目标与请求边界

本轮把“OpenAI-compatible”明确限定为非流式 Chat Completions 文本请求，不等同于支持所有厂商的所有 API。官方协议使用 `POST /chat/completions`，必要字段为 `model` 和 `messages`，响应从 `choices[].message.content` 读取，参数支持也会随模型不同而变化，见 [OpenAI Chat Completions API](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)。

```text
浏览器配置页 / Tarot 主侧栏
  -> 已认证的 Jupyter Server /tarot/api/...
  -> 配置解析与 TarotService
  -> OpenAICompatibleProvider
  -> 用户配置的 Base URL + /chat/completions
```

- **实现选择**：优先复用现有标准库 HTTP 实现，不为了“兼容”强制引入 SDK。若 C 提议使用官方 SDK，须由 F 固定依赖并显式设置超时及 `max_retries=0`，因为 SDK 支持自定义 `base_url` 且带可配置重试机制，见 [OpenAI Python 库说明](https://developers.openai.com/api/reference/python)。
- **保留边界**：继续提供同步 `generate(prompt: str) -> str`，由服务层在线程中调用。保留现有提示词和结构化解读解析，不把 HTTP provider 与塔罗输出格式混在一起。
- **构造参数**：`base_url`、`model`、`api_key`、`auth_mode`、`timeout_seconds` 显式传入。模型名由用户填写并原样发送，不能写死课程模型或 coding harness 的模型。
- **最小请求**：发送 `model`、`messages` 和 `stream: false`；默认不发送 `temperature`、工具调用、强制 JSON 输出或厂商特有参数。后续要支持高级参数时另开任务，不用静默降级隐藏不兼容。
- **地址处理**：去除尾斜杠后只附加一次 `/chat/completions`，保留用户提供的 `/v1` 或网关子路径。输入完整 `/chat/completions` 地址时提示改填 Base URL，不重复拼接，也不猜测补上 `/v1`。
- **认证方式**：`bearer` 发送 `Authorization: Bearer ...`；`none` 完全不发送认证头，供明确配置的无密钥本地服务使用。不得把“密钥留空”偷偷解释为所有远程服务都无需认证。
- **错误处理**：空 `choices`、空/null 内容、非 JSON、鉴权、限流及网络错误统一转换为脱敏的项目错误。浏览器不能收到上游原始响应、认证头或异常堆栈。
- **超时与模式**：默认网络超时 30 秒，可配置 5-120 秒；服务层整体等待上限设为 `timeout_seconds + 5` 秒，而不是继续写死另一个不一致的值。失败不自动重试或切成模拟模式，`FakeAIProvider` 只在显式 Demo 模式启用。
- **兼容验收**：至少一套真实自定义兼容服务通过完整解读；官方路径和另一种网关/本地路径均有契约测试。每项标为“真实通过 / mock 通过 / 未验证”，不声称无限兼容。

### 旧名称清理

清理是一个跨模块任务，不是只把一个类重命名。C、D、A 和 F 分别处理自己负责的代码、文案和说明，删除旧名称后仍须保留同等测试覆盖。

| 旧项 | 新约定 | 负责人 |
| --- | --- | --- |
| `SocratesProvider`、相关导出和显示名 | `OpenAICompatibleProvider`，中性显示名 `OpenAI-compatible` | C |
| `SOCRATES_API_BASE` / `SOCRATES_API_KEY` / `SOCRATES_MODEL` | `TAROT_AI_BASE_URL` / `TAROT_AI_API_KEY` / `TAROT_AI_MODEL` | D；C 移除 provider 内读取 |
| 写死的课程模型、错误消息、测试函数名和示例域名 | 用户模型名、通用错误、通用测试命名及合成域名 | C、D |
| 侧栏隐私提示和 README/教学说明中的平台限定 | “configured AI server” 及通用配置说明 | A、F |

不保留旧类或旧环境变量兼容别名，避免模块继续带着旧名称。用户已经保存的历史属于用户数据，不批量改写；旧记录仍应能读出，UI 可把旧 provider 标签展示为通用历史标签，而不在新源码增加旧名称映射常量。

F 在 PR 审核和发布检查中对本轮维护的源码、前端、测试及用户文档执行以下扫描，预期没有匹配；`git grep` 无匹配返回 1，扫描执行错误不得当成通过。本计划保留上面的迁移对照和这条审计命令，因此不把 `Plan.md` 本身列入扫描范围，Git 历史也不重写。

```bash
git grep -n -i 'socrates' -- src frontend tests README.md docs pyproject.toml
```

## AI 配置页面设计

### 页面布局与字段

设置页放在现有 Tarot 面板中，用 `Reading` 和 `AI settings` 切换，不新建外部网页或要求用户编辑源码。B 使用同一套主题变量，A 负责顶部入口；离开设置页不清空已抽牌记录，未保存草稿在离开前询问是否放弃。

```text
Tarot                                      [AI settings]
Reading | AI settings

AI connection
Status: Not configured / Configured (not tested) / Demo

Mode
( ) Real API       ( ) Demo (simulated)

Base URL *
[https://api.openai.com/v1                         ]
Use the server's API base URL, not /chat/completions.

Model *
[Enter a model ID                                 ]

Authentication
[Bearer API key / No authentication               ]

API key
[Password input                                  ] [Show]
Key: Not set / Set for this server / From environment
Entered keys remain in server memory until it restarts.
[Clear runtime key]

Timeout (seconds)
[30]

[Test connection]     [Save configuration]     [Cancel]

Your question and card details are sent to the configured
AI server only when you request a real reading.
Testing sends a short synthetic prompt and may incur API charges.
```

| 字段 | 规则 | 保存/来源 |
| --- | --- | --- |
| `mode` | `real` 或 `demo`，默认 `real`；Demo 必须显示模拟标识。 | 可持久化；保留 `TAROT_DEMO_MODE=1/0` 的显式启动覆盖。 |
| `base_url` | 默认示例为官方 Base URL；允许用户改为兼容服务器，拒绝 URL 用户信息、query、fragment 和完整补全路径。 | 非敏感配置；`TAROT_AI_BASE_URL` 可覆盖。 |
| `model` | Real API 时必填，trim 后非空；可手输，不依赖 `/models` 才能使用。 | 非敏感配置；`TAROT_AI_MODEL` 可覆盖。 |
| `auth_mode` | `bearer` / `none`，默认 `bearer`；真实请求时 Bearer 必须有密钥。 | 非敏感配置；`TAROT_AI_AUTH_MODE` 可覆盖。 |
| `api_key` | password 输入，不回填已有 key；Show 只显示用户本次刚输入的值。 | 不写磁盘；`TAROT_AI_API_KEY` 或后端运行时内存。 |
| `timeout_seconds` | 有限数值，5-120 秒，默认 30；拒绝 NaN、字符串冒充数值及越界值。 | 非敏感配置；`TAROT_AI_TIMEOUT_SECONDS` 可覆盖。 |

Base URL 指向的是运行 Python 后端的服务器所能访问的地址，`127.0.0.1` 指后端所在机器，不一定是打开浏览器的电脑。配置页须说明这一点，避免远程 JupyterLab 用户误把浏览器电脑上的模型地址当成服务器本地地址。

### 操作和状态语义

- **Save configuration**：只保存并应用配置，不发送模型请求。结构合法但缺少 Bearer key 时可保存为 `Not configured`；下次生成前再明确提示补齐，不能显示“连接成功”。
- **Test connection**：使用当前草稿及匹配服务器的凭证发送固定短测试文本，不发送用户问题，不保存草稿，不改变牌面或历史。按钮旁明确提示可能产生 API 费用，禁止打开页面或输入时自动测试。
- **测试结果**：显示成功/失败、耗时和可操作的脱敏提示，不展示原始返回体。测试通过仅说明该草稿的连通性，不代替完整塔罗解读验收；任意字段修改后清除旧的通过标记。
- **Cancel**：放弃未保存草稿、清空本次输入的 key，恢复已生效配置。关闭/销毁设置面板或保存成功后也清除瞬时密钥字段；测试后尚未保存的新 key 只暂留在当前表单供保存使用，禁止写入浏览器持久存储。
- **Demo**：显示明确的模拟状态，禁用真实连接测试；不产生网络请求，不把模拟成功显示为服务器连接成功。切换模式不隐式删除已保存的非敏感真实配置。
- **忙碌状态**：保存和测试期间防止重复提交；解读中禁止修改有效 AI 配置，后端仍须做冲突检查，不能只依赖前端禁用。失败后恢复控件，保留非敏感草稿。
- **重启状态**：Base URL、模型等恢复，页面输入的运行时 key 不恢复，重新显示 `Not set`。环境变量提供的 key 仍显示 `From environment`，不透露值、前缀或末四位。
- **隐私说明**：真实解读只发当前问题和必要牌面；保存历史是独立的本地操作。保留 `For entertainment and self-reflection only.`，不把 AI 结果描述成确定预测。

## 配置后端契约与安全边界

### 保持既有接口

“数据模型、主流程与已有接口”中的五个 HTTP 操作和完整字段是唯一的既有业务契约，本节只补充配置能力。`SessionRecord`、`schema_version=1`、单牌 `revision=1` 及 `session_id` 关联规则不变；配置功能不能迫使抽牌、保存或历史读取先有可用 AI。

新路径同样相对 Jupyter Server 的 `base_url`，不得硬编码根路径或端口。前端继续通过 `TarotClient` 和 `ServerConnection.makeRequest` 发给 Jupyter 后端，不从浏览器直连 AI 服务器。

### 新增接口

`config_revision` 只用于配置并发控制，与塔罗会话的 `revision` 完全不同。D1 由 B/D 确认字段并提交同一组 JSON fixture；后续变更必须同步类型、handler、mock 和测试。

| 方法与路径 | 请求 | 响应/行为 |
| --- | --- | --- |
| `GET /tarot/api/ai/settings` | 无 | 返回有效非敏感配置、来源/锁定字段、是否有 key 和配置版本；不返回密钥。 |
| `PUT /tarot/api/ai/settings` | `config_revision`、`settings`，可选 `api_key` 或 `clear_api_key` | 校验并原子保存/应用；成功返回新的脱敏配置快照。 |
| `POST /tarot/api/ai/test` | `config_revision`、当前草稿 `settings`，可选新 `api_key` | 不持久化，成功返回 `ok`、`latency_ms` 和脱敏消息。 |

读取成功的建议结构如下，示例中的值不是真实服务配置。`locked_fields` 必须与服务端实际拒绝修改的字段一致，前端不能通过移除 disabled 绕过约束。

```json
{
  "config_revision": 1,
  "settings": {
    "mode": "real",
    "base_url": "https://api.openai.com/v1",
    "model": "",
    "auth_mode": "bearer",
    "timeout_seconds": 30
  },
  "key_present": false,
  "key_source": "none",
  "locked_fields": [],
  "status": "not_configured"
}
```

- **配置优先级**：环境变量覆盖已保存的用户非敏感配置，再使用默认值；被环境覆盖的字段标为只读。测试草稿不能绕过被锁定字段，成功保存只更新可编辑字段。
- **版本冲突**：旧 `config_revision` 的保存或测试返回 `409 CONFIG_CONFLICT`，保留用户草稿并提示重新读取。当前有解读/配置测试时，另一项会改变或使用 AI 配置的冲突操作返回明确 busy 错误。
- **密钥更新**：不传 `api_key` 表示尝试保留原 key；传非空值表示替换；`clear_api_key:true` 表示清除运行时 key。空字符串或同时“替换+清除”视为非法，清除操作不能删除服务进程的环境变量。
- **服务器绑定**：key 与规范化后的 Base URL 绑定；更换 Base URL 不得自动沿用原 key，须重新输入或显式选择无认证。环境 key 必须与显式环境 Base URL 配对，并锁定该 Base URL，防止把凭证发往新服务器。
- **持久化位置**：非敏感配置写入服务端确定的 Jupyter 用户配置目录下 `tarot-jupyterlab/ai-config.json`，不接受前端传入文件路径。密钥、测试回复、用户问题均不进入该文件。
- **原子性**：先验证并完成安全写盘，再替换内存有效配置及运行时 key；磁盘失败时旧配置、旧 key 和活动会话保持不变。返回读取结果的 HTTP 响应加 `Cache-Control: no-store`。
- **解读隔离**：解读开始时取 provider/配置快照；运行中保存配置被拒绝。超时或取消后的迟到结果不能覆盖新会话，查看历史不触发联网或更换 provider；已有解读不因改设置自动重生成，新配置用于后续新解读。

### 安全要求和错误反馈

- **Jupyter 认证**：全部新 handler 要认证，写请求保留 XSRF 检查，不修改全局 CORS，不允许未认证用户通过测试接口调用任意服务器。
- **地址边界**：默认允许公网 HTTPS，保持 TLS 证书校验；本地 HTTP 仅允许显式选择的回环地址。拒绝云元数据、link-local 和其他未授权私网目的地，私网网关只能通过服务端管理员白名单开放。
- **重定向**：不自动跟随上游重定向，尤其不能把认证头转发到另一地址。URL 校验须覆盖解析出的目标地址，不能只检查 URL 字符串前缀；D/C 补重定向与地址边界测试，F 核查覆盖。
- **部署边界**：本轮面向单用户 Jupyter Server，不宣称支持共享账户或多租户密钥隔离。远程部署的自定义 URL 编辑应由管理员白名单约束，不能把配置接口当作公共代理。
- **日志和浏览器**：不记录 key、Authorization、配置请求体、完整 prompt 或模型原文；不把 key 放在 localStorage、sessionStorage、Jupyter Settings、历史 JSON、截图或 PR。API key 仅为输入到已认证 Jupyter 后端的短暂表单值。
- **配置错误**：非法字段返回 `400 INVALID_REQUEST`，并指出可纠正的字段；错误内容不包含密钥或上游响应体。
- **AI 错误**：沿用 `503 AI_UNAVAILABLE`、`504 AI_TIMEOUT`、`502 AI_BAD_RESPONSE`；新增 `503 AI_RATE_LIMITED` 供 429 使用。鉴权失败应提示检查 key，404 应提示核对 Base URL/模型，不能把所有失败都说成“网络断开”。
- **失败恢复**：无配置、测试失败或真实解读失败后仍可抽牌和保存无解读记录；只有显式 Demo 选择才能生成模拟结果。保存配置不等于真实调用通过。

## 课程系统 Wiki 展示页面与一分钟演示

Wiki 展示页位于课程系统，不在 GitHub，由 E 统一负责，E 无需创建分支或提交 PR。课程的一分钟展示必须与该页面配套，按“单页 Wiki + 60 秒讲解/操作”安排；页面和口播默认采用与产品一致的英文，D1 由 E 核对课程页面位置、编辑/阅卷权限、语言以及现场/录屏要求。

### 页面内容与分工

E 同时负责页面、脚本和演示组织，A-D 从自己的已验收功能提供素材，F 提供版本、安装和代码审核证据。页面不重复整份 README，也不宣传尚未实现的功能；展示顺序和演示操作保持一致，A/C/D 分别核对涉及自己模块的事实，不为页面另开 PR。

| 页面区块 | 必须展示的内容 | 素材提供 / 汇总 |
| --- | --- | --- |
| `What it does` | 项目名、用一句话解释用途、JupyterLab 中的实际界面，以及娱乐/自我反思定位。 | A / E |
| `Draw a card` | 合成问题、一次单牌抽取、正逆位及关键词，使用本版本截图或演示。 | A / E |
| `Configure your AI` | Base URL、模型、自定义服务器能力和脱敏配置页，不出现真实 key。 | B、C / E |
| `Read and save` | 真实解读样例、保存最近一条、重启后的只读查看；模拟素材必须显著标识。 | A、C、D / E |
| `How it works` | 简短的前端 → Python 后端 → OpenAI-compatible 服务链路，以及本地历史存储。 | C、D / E |
| `Try it / Evidence` | 安装命令、PyPI 版本、源码与验收记录；代码成员提供 PR/review，E 提供课程页面、排练与人工验收贡献记录。 | F 提供版本/代码证据 / E |

课程系统中的 Wiki 页面是正式展示入口，由 E 直接编辑和发布，A 核对展示效果，C/D 核对技术描述，F 只核对其提供的版本和发布信息。小组可以在共享文档保存 Markdown 草稿、素材清单和匹配的口播/操作稿作为备份，但不要求提交到代码仓库，也不设置 PR 前置条件。

E 在 D2 前确认课程系统页面的实际位置、编辑权限和教师/阅卷者的访问方式，并记录页面 URL。若权限或系统暂不可用，先保留共享草稿并向课程方反馈，不能把“草稿已完成”当作“课程 Wiki 已发布”；不因此改用 GitHub Wiki 或改变代码仓库可见性。

### 60 秒逐段演示表

下面是排练目标时间，不是声称未经计时已经符合一分钟要求。E 应使用最终稿至少完整排练两次，将总时长控制在 60 秒内，并保留实际耗时；需要删减时先删背景介绍，不删核心操作和真实/模拟说明。

| 时间 | Wiki 对应区块 | 屏幕动作与讲解重点 |
| --- | --- | --- |
| 0-8 秒 | `What it does` | 从 Wiki 标题和实际界面图开始，一句话说明这是 JupyterLab 内的抽牌与 AI 反思插件。 |
| 8-18 秒 | `Draw a card` | 对照该区块，在插件现场抽一张牌或播放明确标记的操作片段，指出正逆位和关键词。 |
| 18-30 秒 | `Configure your AI` | 展示无密钥值的设置页，说明 Base URL 和模型可自定义，产品不绑定学校平台。 |
| 30-45 秒 | `Read and save` | 展示已取得的解读及保存/重启查看结果，说明只保留最近一条。 |
| 45-54 秒 | `How it works` | 指向简单链路，解释浏览器请求 Python 后端，再由后端访问配置的 AI 服务。 |
| 54-60 秒 | `Try it / Evidence` | 回到 Wiki 的安装与证据区，指出最终包链接、代码和团队贡献，结束展示。 |

真实模型延迟不能决定整段展示能否完成，因此不把现场等待联网回复作为默认脚本中的必经步骤。若课程允许录屏，可使用来自同一最终版本的真实录制片段，明确标为 recorded；若要求现场演示，由 E 在 D1 核对规则后协调 A-D 调整操作顺序，不能假装录像或模拟结果是现场真实调用。

### Wiki 与演示完成条件

- **同一版本**：页面、截图、演示脚本、安装命令和最终包对应同一已验收版本；若发补丁，F 通知 E 版本变化，由 E 收集更新素材并同步页面和脚本。
- **逐段对应**：脚本每个时间段都能指向 Wiki 的相应分区，不在一分钟内临时翻找长 README、旧截图或另一套演示材料。
- **可访问**：E 请 A 或 B 用课程账号和指定的阅卷权限独立检查页面、图片、视频及链接，不能只在作者编辑状态下自测。无需强行公开到互联网，访问范围遵循课程系统的要求。
- **真实和脱敏**：不泄露 API key、Jupyter token、私人问题、内部服务器信息或成员私人资料；已验证功能、模拟演示和未来计划清楚分开。
- **计时与备份**：主讲与备份至少各走通一次，保存实际时长和卡点；提供本地页面/截图作为网络故障备份，但备份不取代应发布的 Wiki。
- **最终交付**：课程 Wiki 实际 URL、页面最后更新时间或系统内版本记录、60 秒脚本、计时记录，以及课程要求时的录屏链接/文件一并列入课程提交清单。

## Agentic Coding 与分支 / PR 流程

### 代码成员独立分支，E 无需分支

以下分支和 PR 规则只适用于 A、B、C、D、F 的代码、测试、构建和仓库文档修改，E 不需要分支或 PR。代码成员从最新 `main` 建自己的功能分支，不共享开发分支，不直接向 `main` 提交或 force-push；同一成员的多个 agent 使用不同 worktree/分支，下列 `<changed-files>` 需替换为实际核对过的文件路径。

```bash
# 开始前确认工作区干净；若有未提交工作，先处理，不直接覆盖
git status
git switch main
git pull --ff-only origin main
git switch -c feat/a-sidebar-theme-icon

# 实现与本地测试后，只暂存自己核对过的文件
git add <changed-files>
git commit -m "feat(ui): add theme-aware tarot sidebar icon"
git push -u origin feat/a-sidebar-theme-icon

# 在 GitHub 创建 PR，base 为 main，head 为自己的分支
gh pr create --base main --head feat/a-sidebar-theme-icon
```

- **尽早开 Draft PR**：说明任务、范围和依赖，方便发现文件冲突。依赖尚未合并时可用 mock 开发；若采用 stacked PR，须清楚标注依赖并在合并前重设正确 base。
- **小步合并**：先合并契约/依赖，再合并 provider、配置 API、配置页及主题改造，最后合并跨模块测试和发布变更。基础设施和测试骨架不必等所有功能结束才合并。
- **同步方式**：需要更新分支时先 `git fetch origin`，再按团队约定 merge 最新 `origin/main`；不对别人的分支重写历史。合并冲突由作者和文件负责人一起解决。
- **审核分配**：A-D 的 PR 默认由 F 主审，涉及跨模块接口、安全或数据兼容时邀请相应使用方加审。F 自己的 PR 由 A 或 D 主审，不能自己批准，也不能把自己的 agent 当独立 reviewer。
- **合并门槛**：非作者 reviewer 通过、相关测试/构建通过、跨模块接口由使用方确认、未解决评论清零。F 完成审核清单后交团队指定维护者合并，不因为负责审核就绕过权限或自动合并。
- **仓库设置**：请有管理员权限的成员为 `main` 启用 PR review 和必需 CI 检查；未配置前执行人工同等门禁，不宣称保护已生效。合并由团队指定维护者执行，不自动合并、不自动发布。

### F 的 PR 审核清单

F 负责审核节奏和工程门禁，不替作者完成所有修复，也不接管 E 的 Wiki 发布。审核意见应指出具体文件、问题和验证方式，作者补充提交后再复核，目标是在下一次每日验收点前给出首轮反馈。

- **范围与归属**：任务目标清楚，改动只覆盖必要文件；没有夹带无关重构、生成产物或越过共享文件边界。
- **接口与兼容**：请求/响应、错误码和 TypeScript/Python 类型一致；原有五个操作、历史格式及离线抽牌/保存没有回退。
- **测试与 CI**：相应单元、集成或浏览器用例已补，提交了实际命令和结果；不能通过删测试、弱化断言或忽略失败换绿灯。
- **安全与体验**：检查密钥、日志、配置来源、错误恢复及必要的主题/键盘证据；Wiki 页面本身不纳入代码 PR。
- **处理结果**：明确记录可合并、需修改或阻塞的原因；保存有效 review 记录，发布前整理未解决问题。
- **回避与备份**：F 自己提交或共同编写的改动由 A 或 D 独立审核。F 不可用时 D 临时协调，但 D 不能审自己的 PR，相关 PR 改由 A 或其他非作者模块负责人审核。

### Coding harness 工作约束

A、B、C、D、F 可把下面模板交给各自的 harness，再填入具体任务编号和允许路径。模型负责生成、运行和修正，代码成员负责确认需求、核对 diff、复跑测试、解释实现及提交 PR；E 可用 harness 整理页面、脚本和验收记录，不执行建分支或提交代码的步骤。

```text
先阅读 Plan.md、README.md、目标模块和相关测试。
任务：<例如 B-02：AI 配置页接入>
当前基线：<commit SHA>
允许修改：<本成员负责的文件>
不得修改：他人入口文件、依赖/锁文件、生成产物及任何凭证文件。
必须保持：现有五个接口、SessionRecord 格式、英文界面和离线抽牌/保存。
必须交付：最小改动、对应测试、运行命令、实际结果和已知限制。
不要编造测试通过；不要读取或输出 .env、真实 key、Jupyter token、私人历史。
需要改共享契约时先停下说明，由负责人协调后再继续。
```

A、B、C、D、F 的 PR 都要有可执行或可验证交付，测试和 CI 脚本同样属于有效工程贡献。E 以课程 Wiki、演示与人工验收记录证明贡献，不要求为了“每人一个 PR”创建空分支或无意义提交；全组贡献不按 agent 生成行数衡量。

### PR 描述与验收模板

```markdown
## 目的
- 任务编号：
- 实现内容：
- 不在本 PR 范围内的内容：

## 影响
- 修改文件和公共接口：
- 依赖的 PR：
- 数据/配置兼容影响：

## 验证
- 环境、命令及实际结果：
- 新增/更新的自动化测试：
- UI 改动：浅色/深色、窄侧栏、键盘证据：
- AI 改动：mock/真实分别列出，证据脱敏：
- 尚未运行的检查及原因：

## Review
- 指定 reviewer：
- 密钥与私人数据检查：
- 已知风险及回滚方式：
```

## 两周推进顺序

D1 是小组约定的新一轮开工日，不强行等于本文修订日，D1-D14 为日历天。默认每天香港时间 20:00 更新状态；D1 确认姓名、可用时间、课程截止日及发布材料，若期限更短先压缩延后项，不取消安全和独立验收。

| 时间 | 各线并行推进 | 到点验收 |
| --- | --- | --- |
| D1-D2 | D/B/C 冻结配置契约和 fixture；A 准备 CSS/图标；A/D 建浏览器/后端测试骨架；E 确认课程 Wiki/一分钟展示要求；F 建审核清单、CI 并确认发布权限。 | A、B、C、D、F 建分支/Draft PR，E 不建分支；课程 Wiki 的页面位置/权限有结论；基线可复现；未引入真实凭证。 |
| D3-D5 | A 交主题/图标；B 交表单；C 交 provider 和错误测试；D 交配置 API 与集成测试；E 建课程页面框架；F 持续审核 PR。 | 各模块有独立可运行交付和审核意见；E 的页面结构清楚；无真实服务也能通过 mock 验证。 |
| D6-D7 | B/D 接口联调，A 挂载设置页，C 与 E 分别实施/人工见证真实服务验证，E 整理 Wiki 素材，F 审核集成改动并更新工程文档。 | “配置 → 测试 → 抽牌 → 真实解读 → 保存 → 重启查看”闭环；无 key 路径同样可用；错误由对应代码作者处理。 |
| D8-D10 | A-D 补自动化回归并交素材；E 完成人工走查、Wiki 候选页和脚本，组织两次计时；F 复审 PR 和构建检查。D10 冻结候选提交。 | 功能 P0 通过，Wiki 与演示逐段匹配且不超过 60 秒；关键 PR 审核、旧名称/凭证检查和构建通过。 |
| D11 | F 构建候选包并安排 TestPyPI 或同制品本地预发布试装；E 和另一位成员独立验证。 | 记录 wheel 名称、版本、源码 SHA、制品哈希与试装结果；失败不进入正式发布。 |
| D12 | 组内确认后由 F 正式发布并交版本信息，E 从正式 PyPI 锁定版本重新安装、更新课程 Wiki 最终链接并复排。 | 正式版本页、Wiki 实际 URL、安装命令、用户侧安装及最终演示证据。 |
| D13-D14 | A-D 修复必要补丁，F 完成审核与发布复验协调；E 完成页面访问检查、最终计时和展示贡献整理。 | 最终版本、源码、README、Wiki、脚本、代码成员 PR/review 与 E 的页面/验收记录一致。 |

关键依赖是“字段/样例冻结 → provider 与配置后端 → 前端接线 → 跨模块验收 → 候选包 → 正式包”。主题、图标、配置页 mock、测试骨架、CI 和课程页面框架可以从 D1 并行；测试代码归对应模块作者，F 审核，E 做页面与人工验收，不把所有联调或测试集中给一个人。

## 测试与完成标准

### 最低验收矩阵

自动化测试由对应代码作者编写，F 核对覆盖和 CI，F 自己的改动由 A 或 D 复核。E 参与下表中的真实操作、安装、页面和演示验收，不承担测试脚本提交或技术 PR 审批。

| 编号 | 场景 | 通过条件 | 执行 / 复核 |
| --- | --- | --- | --- |
| T01 | 基线回归 | 原有 60 项测试的业务覆盖不减少，新增测试全部通过；不以删除断言换绿灯。 | 各代码作者 / F；F 的改动由 A/D 审 |
| T02 | 主题和图标 | 浅色/深色、选中/hover、320/480 px、200% 缩放可用，图标有名称。 | A / B、E |
| T03 | 配置表单 | 必填、URL、超时、锁定字段、草稿取消、清除 key 和忙碌状态正确。 | B / F；E 人工走查 |
| T04 | 配置存储 | 非敏感项重启保留，运行时 key 重启消失；原子写失败不损坏旧配置。 | D / C、F |
| T05 | 密钥隔离 | GET/错误/日志/历史/构建包不包含测试 key；换服务器不沿用旧 key，环境 key 不可清除。 | D / C、F |
| T06 | 通用 HTTP 契约 | 官方路径、自定义子路径、Bearer/none、模型透传、尾斜杠及响应校验通过。 | C / D |
| T07 | AI 故障 | 缺配置、401/403、404、429、5xx、超时、非 JSON/空输出有脱敏提示并恢复可操作状态。 | C、D / F；E 人工走查 |
| T08 | 真实解读 | 至少一个获授权的自定义兼容服务生成完整英文解读；与 mock 证据分开。 | C / E |
| T09 | 并发和迟到结果 | 重复生成、生成中改配置、旧配置版本保存有冲突保护；迟到结果不覆盖新会话。 | D / F |
| T10 | 历史与离线 | 有/无解读均可保存；覆盖须确认；写入失败保留旧记录；重启只读查看一致。 | D 自动化、E 手工 / F |
| T11 | 认证与地址安全 | 未认证、无效 XSRF、非根 Jupyter base URL、恶意重定向/非法目标地址均按边界处理。 | D、B / C、F |
| T12 | 去耦扫描 | 约定扫描路径中旧平台名称为零，通用错误和配置文档一致。 | F 执行扫描 / A、C、D |
| T13 | wheel 试装 | 从冻结提交干净构建，制品包含最新前端/图标/牌库/后端及启用配置，不含 key 和个人历史。 | F / D、E |
| T14 | 正式发布复验 | 非发布者从正式 PyPI 按版本安装，无源码目录和手工前端编译，主流程通过。 | E / 另一成员 |
| T15 | 课程系统 Wiki | E 完成页面并发布，按阅卷权限可访问；素材/链接可用，与最终版本一致且无敏感信息，E 无需分支或 PR。 | E / A、C、D |
| T16 | 一分钟配套演示 | 脚本六段与 Wiki 分区一一对应，至少两次完整计时不超过 60 秒，主讲和备份均能完成。 | E / A、全组 |
| T17 | PR 审核 | A-D 的 PR 经 F 或已指定的非作者备份审核；F 自己的 PR 经 A/D 审核；CI、接口和未解决评论满足合并门槛。 | F 协调 / A、D |

CI 中的 AI 测试全部使用 mock/合成密钥，不能要求每位 reviewer 有真实账户。真实调用是额外人工验收项，需用户明确点击或成员主动执行；截图和 Network 记录遮住 key、Authorization、Jupyter token 及私人问题。

现有检查入口为 `python -m pytest`，前端在 `frontend/` 执行 `jlpm install --immutable` 与 `jlpm build:prod`。F 将新增检查加入实际可运行的 CI 和 README；文档中尚未创建的脚本不能提前记成已通过门禁。

### 人工验收顺序与记录

E 按以下顺序操作，A-D 提供可控失败场景并负责自动化测试和修复；E 不因此承担脚本或代码 PR。候选版和正式版均使用隔离的历史目录或测试用户，不能把之前留存的数据误认为本次安装、保存和重启成功。

1. 在干净环境按指定来源和版本安装，记录 OS、Python、JupyterLab 版本，检查前后端扩展及侧栏图标；新历史显示空状态。
2. 提交空白和超长问题，再提交合成问题；核对返回的牌名、正逆位和对应关键词，并检查浅色/深色、窄侧栏和键盘操作。
3. 不配置真实 AI 时验证抽牌、直接保存和查看历史；显式 Demo 模式下验证模拟标识。用模块作者提供的测试场景复现失败/超时，确认按钮恢复。
4. 填写获授权的自定义服务，先区分“保存配置”和“测试连接”，再实际生成完整英文解读；检查隐私提示和娱乐提示，记录真实与 mock 的不同证据。
5. 保存有解读的记录，退出并重启 JupyterLab，核对同一条问题、牌面、正逆位、关键词与解读；运行时 key 不应随重启恢复。
6. 再保存一条无解读记录，检查替换确认与只保留最近一条；写盘失败和迟到结果由对应自动化用例补充验证。
7. 按最终课程 Wiki 完整走一次配套演示，核对版本、素材和链接，再记录主讲与备份的实际计时。

所有检查采用同一记录格式，失败、阻塞和未运行必须与通过区分。E 的记录存于课程系统或共享文档，代码成员的测试证据放入对应 PR，F 汇总发布门禁所需结果。

```text
检查项 / 日期 / 验收人：
环境（OS、Python、JupyterLab）：
源码提交 / 包名 / 版本 / 安装来源：
执行命令与主要步骤：
模式与证据类型（真实 API / Demo / mock / 未验证）：
结果（通过 / 失败 / 阻塞 / 未运行）：
脱敏证据（测试输出、截图、课程页面或公开版本 URL）：
问题复现 / 模块负责人 / 复验时间：
```

## 构建、试发和正式发布

以下恢复原计划的发布操作细节，并按新分工由 F 主持、E 独立试装、D 作授权备份。命令是待执行模板，尖括号内替换为实际值；这份计划不表示已经上传任何包，也不授权 agent 自动发布。

### 发布准备与现有骨架复验

F 在 D2 前确认正式 PyPI/TestPyPI 权限、候选包名、版本方案及课程是否要求源码包，任务记录只保存状态，不共享 token。D 作为发布备份必须通过自己的授权获得权限，不能复制 F 的上传凭证；E 保持非发布者身份，负责独立试装和课程页面同步。

- **课程材料**：D1 核对分发名、版本、作者字段、许可证、源码包、截图和提交渠道；保留原项目候选分发名 `tarot-jupyterlab`，由 F 确认实际可用名称和带组名的备选名。公开页面不存在并不能保证名称可用，按 [PyPI 项目命名规则](https://docs.pypi.org/project-management/choosing-a-name/) 核对。
- **账号与备份**：F/D 各自准备邮箱验证、双重认证和授权状态；上传凭证只留在发布者本机，按 [PyPI 发布说明](https://docs.pypi.org/publishing/publishing-to-pypi/) 准备。已有项目的备份发布权限由 Owner 邀请并由受邀者接受，不能共享主发布者账号，见 [PyPI 协作者管理](https://docs.pypi.org/project-management/managing-collaborators/)。
- **构建环境**：F 与 A/B 固定开发端 Node、前端包管理器、锁文件和构建命令；复验现有骨架，不重新搭模板。使用者只安装 Python 包和预构建 wheel，不应为了安装插件手工编译前端。
- **名称与映射**：分别核对 PyPI 分发名、Python 导入名、Jupyter 扩展目录名和前端插件注册名；不得因为分发名变化就无必要地一起改动全部内部名称。F/D 核对扩展发现、启用 JSON 和运行时依赖。
- **制品内容**：wheel 必须包含 Python 模块、唯一牌库源对应的包资源、最新前端 JS/CSS、塔罗 SVG、启用配置和元数据；不得包含 `.env`、私人 `latest.json`、用户 AI 配置、真实凭证和缓存。
- **构建配置**：`pyproject.toml` 的 hook、前端脚本、产物目录和安装映射必须一致；从干净源码重建，不能沿用旧前端。若独立 Schema 仍延期，不保留指向不存在文件的强制打包项。

### 候选包与预发布验收

F 从 D10 冻结提交在干净构建环境重跑测试，D11 交付候选 wheel、版本、源码 SHA、制品 SHA-256、文件清单和检查结果。A-D 负责各自失败项修复，F 的构建/发布代码仍由 A 或 D 审核，不因临近交付免审。

```bash
# 在已安装开发依赖的干净源码根目录执行
python -m pytest
(cd frontend && jlpm install --immutable && jlpm build:prod)
python -m build --wheel --outdir dist/release
python -m twine check "<wheel-path>"
```

课程如要求 `sdist`，F 将其加入构建、`twine check`、文件清单与独立安装验证，不能只生成后直接上传。F/D 复核 README、LICENSE、元数据和包内文件，E 收到明确版本与哈希后在非源码目录独立试装。

组内批准预发布后，由 F 上传这一份候选制品；E 先从正式 PyPI 安装锁定的 JupyterLab 及 F 列出的全部运行时依赖，再从 TestPyPI 只安装明确版本的项目包，步骤参照 [Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)。下面依赖示例只列 JupyterLab，F 必须补齐实际制品的其他运行时依赖，`pip check` 不通过就不能继续验收。

```bash
# F：在获得上传授权后执行
python -m twine upload --repository testpypi "<wheel-path>"

# E：在新建并激活的干净 Python 环境中执行
python -m pip install --index-url https://pypi.org/simple/ "jupyterlab==<lab-version>"
# 如有其他运行时依赖，按 F 提供的已验证列表从正式 PyPI 安装
python -m pip install --index-url https://test.pypi.org/simple/ --no-deps "<package>==<version>"
python -m pip check
jupyter labextension list
jupyter server extension list
jupyter lab
```

TestPyPI 暂不可用时，E 对同一个候选 wheel 做独立本地安装，记录原因、哈希和完整结果；这只代替预发布验证，不代替正式 PyPI 交付。正式发布前必须有 E 的通过记录和另一位成员的复核，任何代码、依赖、包名、版本或制品变化都要重建和复验。

### 正式发布与干净环境复验

F 在 D12 上传前核对 E 的验收、组内确认、包名、版本、源码 SHA 和制品哈希，只上传已经独立试装的同一份文件；课程要求源码包时按已验收清单一并上传，发布步骤参照 [Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)。上传成功后记录实际版本页 URL、时间和结果，不用候选包页面或本地安装成功代替。

```bash
# F：仅在组内确认与独立验收通过后执行
python -m twine upload --repository pypi "<wheel-path>"
```

E 另建干净环境，按正式索引、实际包名和精确版本安装，再走完整人工验收；不能继续使用预发布环境或源码目录中的可编辑安装。F 保持发布者角色，E 保持非发布者身份，并将最终版本、安装命令和脱敏证据同步到课程 Wiki。

```bash
# E：激活另一个干净环境后执行
python -m pip install --index-url https://pypi.org/simple/ --no-cache-dir "jupyterlab==<lab-version>" "<package>==<version>"
python -m pip check
jupyter labextension list
jupyter server extension list
jupyter lab
```

### 补丁与最终材料

- **补丁处理**：D13-D14 的代码修复仍归 A-D 对应作者，F 审核协调并提升补丁版本、重建制品，E 重跑独立试装和受影响的展示段落。PyPI 制品文件名不能重复使用，即使旧文件已删除也不行，参照 [PyPI 上传故障排查](https://docs.pypi.org/publishing/troubleshooting/)。
- **最终一致性**：README、课程 Wiki、演示截图、脚本和验收记录全部使用最后通过的实际版本，F 向 E 提供版本变化和新证据。旧失败记录可以留作追踪，但不能混作最终通过证据。
- **课程提交**：D14 汇总正式 PyPI 版本页、准确安装命令、对应源码提交或标签、README、验收表、Wiki URL、60 秒脚本/计时记录和六人贡献。未完成的真实服务验证、发布或课程页面权限必须明确列为阻塞，不以计划条目冒充完成。

## 阻塞、接手与贡献记录

- **模块延期**：代码成员在验收点没有可运行结果时，当天提交当前分支、失败命令和下一步；E 则交课程草稿、操作记录和具体阻塞，不要求补建分支。由分工表中的备份接手明确子任务，不把全部工作自动转给 A。
- **接口冲突**：B/D/C 先统一 fixture 和字段，再修改实现；其他人继续跑 mock。不得各写一套配置类型后在最后一天互相适配。
- **真实服务不可用**：C/E 记录脱敏错误，换另一套获授权的兼容服务或继续离线回归；真实验收仍标为阻塞，不能把 Demo 改名为真实结果。
- **审核阻塞**：F 在下一次每日验收点说明待审清单和卡点；必要时由 D 协调非作者 reviewer 接手，作者不能自行批准。不能为了赶展示跳过关键测试或安全检查。
- **发布权限问题**：F 负责尽早协调，D 只在授权后接手；E 继续独立验收，不接管上传凭证。不能因发布困难声称已完成正式 PyPI 交付。
- **安装或包名阻塞**：侧栏缺失、服务端未启用或 API 失败时，先查制品内容，再查扩展发现/启用，最后查 `base_url` 与认证，由相关作者修复、E 复验。分发名不可用时由 F 确认备选名并同步元数据/README，重新构建和试装，不跳过验证。
- **Wiki 或演示阻塞**：E 在 D2 前处理课程系统页面位置与权限，在 D10 前暴露超时或操作卡点；必要时由 B 协助展示工作，不需要为 E 建分支。优先删减旁支介绍，不能省掉配套 Wiki 或用未发布草稿冒充最终页面。
- **连续延期**：成员连续错过两个验收点或明确无法继续时，当天更新可用人力、接手人和复验时间，先关闭延后项。若正式 PyPI、核心功能或课程展示仍会延期，应尽早向老师说明具体受影响项，不能把 E 的 Wiki 或 F 的审核当作可取消的机动任务。
- **贡献归属**：A、B、C、D、F 保留代码提交、PR 和审核记录，E 以课程系统编辑记录、内容复核、演示计时及人工验收证明贡献。六人均提供可讲解、可核对的成果，不要求 E 补 PR，不用 agent 对话量或代码行数代替成果。

```text
任务编号 / 成员：
代码任务（A/B/C/D/F）：分支 / PR / reviewer
展示验收任务（E）：课程页面 URL / 编辑、计时或人工验收记录
状态：进行中 / 待审核或复核 / 已合并或已发布 / 已验收 / 阻塞
已完成的可运行结果：
执行命令、环境与结果：
依赖和当前阻塞：
下一步、验收人和复验时间：
AI 辅助范围及本人已核对的内容：
```

## 最终完成标准

最终交付是一个可以独立安装、配置、运行和展示的版本，不以六个人都建分支作为标准。A、B、C、D、F 完成工程交付，E 完成课程页面、配套演示与人工验收；以下条件全部满足后才结束本轮，未完成项须明确保留。

- [ ] A、B、C、D、F 有独立分支、有效 PR 和非作者审核，F 完成审核协调，自己的 PR 未自审自批。
- [ ] E 完成课程 Wiki、演示和人工验收记录，不需要创建分支或提交 PR。
- [ ] 主侧栏符合公共 CSS 规范，塔罗图标在浅色/深色主题中正常。
- [ ] AI 模块和用户文档不再依赖旧课程平台，自定义 OpenAI-compatible 服务有真实验收。
- [ ] 配置页、密钥生命周期、服务器绑定、连接测试及错误恢复均通过。
- [ ] 原有单牌、解读、最近记录和重启查看功能未回退。
- [ ] CI、包内容检查、候选包独立试装和正式包复验通过。
- [ ] Wiki 展示页已在课程系统发布，无需 PR；60 秒脚本逐段对应，主讲/备份计时和阅卷访问检查通过。
- [ ] 最终 PyPI 版本、源码提交、README、Wiki、演示脚本和贡献记录相互对应。
