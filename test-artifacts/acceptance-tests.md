# Acceptance Tests for 洪涝灾害 AI 协同辅助决策系统

**Purpose:** ATDD acceptance tests for all core user stories, following the Given-When-Then format.

**Date:** 2026-04-01
**Status:** Draft

---

## Epic 0: 基础框架与交互底座

### Story 0.1: Monorepo 与 Docker WSL2 环境初始化

**As a** 开发者
**I want** 配置 Monorepo 结构与 Docker Compose 编排环境
**So that** 前端、后端与仿真 Sidecar 能在单机 WSL2 环境下通过容器网络互通

#### Acceptance Test AT0.1-01: Docker Compose 服务启动

```gherkin
Scenario: 启动 Docker Compose 后所有服务正常运行
  Given 一个空的 Git 仓库与 Windows 11 环境
  And 已安装 Docker Desktop with WSL2 backend
  When 运行 `docker-compose up -d`
  Then 系统应自动启动四个服务：frontend, backend, physics-sidecar, redis-stack
  And 所有容器状态应为 "healthy"
  And 容器日志中无 ERROR 级别错误
```

#### Acceptance Test AT0.1-02: WSL2 Ext4 卷挂载验证

```gherkin
Scenario: 容器挂载至 WSL2 Ext4 原生卷
  Given Docker Compose 已配置 WSL2 volume mounts
  When 运行 `docker-compose up -d`
  Then 各容器必须挂载至 WSL2 的 Ext4 原生卷
  And 严禁出现 Windows 文件权限冲突
  And 文件 IO 性能测试应达到 100MB/s 以上
```

#### Acceptance Test AT0.1-03: 容器间网络互通

```gherkin
Scenario: 容器间网络通信正常
  Given 所有容器已启动
  When backend 容器尝试连接 redis-stack
  And frontend 容器尝试连接 backend
  Then 所有连接应成功建立
  And 网络延迟应低于 10ms
```

---

### Story 0.2: 前端框架与 GIS 骨架搭建

**As a** 前端开发者
**I want** 搭建基于 Next.js 的基础页面与 Mapbox 地图层
**So that** 后续的物理仿真切片有可展示的"家"

#### Acceptance Test AT0.2-01: 地图渲染验证

```gherkin
Scenario: 页面加载时正确渲染地图
  Given 用户访问应用首页
  When 页面完成加载
  Then 地图应正确渲染目标流域（如永定河）的 3D 地形与 L1 底板
  And 地图加载时间应低于 3 秒
  And 缩放/平移操作应流畅无卡顿
```

#### Acceptance Test AT0.2-02: TailwindCSS 响应式布局

```gherkin
Scenario: UI 响应式布局适配不同设备
  Given 页面已加载
  When 用户调整浏览器窗口大小
  Then UI 应自动适配桌面端、平板、笔记本等不同分辨率
  And 指挥官在笔记本上的操作应完全支持
  And 所有交互元素最小点击区域应≥44x44 像素
```

---

### Story 0.3: 实时证据总线实现

**As a** 系统架构师
**I want** 实现基于 Socket.io 的双向通讯总线
**So that** 决策大脑能将"边算边推"的物理证据实时发送至前端

#### Acceptance Test AT0.3-01: Socket.io 连接建立

```gherkin
Scenario: 前端与后端建立 Socket.io 连接
  Given 后端服务已启动
  When 前端页面加载并初始化 Socket.io 客户端
  Then 应成功建立 WebSocket 连接
  And 连接状态应显示为"connected"
```

#### Acceptance Test AT0.3-02: 物理证据实时推送

```gherkin
Scenario: 物理 Worker 推送仿真切片就绪信号
  Given Socket.io 连接已建立
  When 物理 Worker 发送 PHYSICS:TILE_READY 信号
  Then 前端 useEvidenceStream Hook 应能瞬间捕捉信号
  And 通过 Socket.io 二进制流接收数据
  And 通讯延迟必须稳定在 200ms 以内（单机环境测试）
```

---

## Epic 1: 地域大脑极速活化中心

### Story 1.1: 战术级活化协议实现

**As a** 系统管理员
**I want** 上传 Activation-Pack 并触发 15 分钟极速活化
**So that** 系统能瞬间适配北京或新疆等特定地域的地理与知识底座

#### Acceptance Test AT1.1-01: Activation-Pack 上传

```gherkin
Scenario: 上传标准 Activation-Pack
  Given 一个标准的.zip 数据包（含 L1 地理数据、L2 历史 RAG 包）
  When 管理员调用 `/api/v1/activation/tactical` 接口并上传该包
  Then 接口应返回 200 OK
  And 返回 status: "pending" 表示准备活化
```

#### Acceptance Test AT1.1-02: 15 分钟战术活化完成

```gherkin
Scenario: 系统在 15 分钟内完成战术活化
  Given Activation-Pack 已上传
  When 战术活化流程启动
  Then 系统应在 15 分钟内完成 RAG 并行灌装与物理网格映射
  And 必须通过 DEMS v1.0 标准校验
  And 返回 status: "ACTIVE_TACTICAL" 信号
```

#### Acceptance Test AT1.1-03: DEMS v1.0 级联逻辑校验

```gherkin
Scenario: DEMS v1.0 级联逻辑正确加载
  Given 已上传的 Activation-Pack
  When 活化流程执行
  Then ontology_mapping.json 中的级联逻辑应正确加载
  And 所有实体映射应无冲突
  And 所有 cascade_rules 应语法正确
```

---

### Story 1.2: 战略级深度蒸馏

**As a** 系统管理员
**I want** 在战术活化后启动 72 小时的全量知识蒸馏与红蓝预演
**So that** 大脑能达到"地域精算"级别，具备极高的决策精度

#### Acceptance Test AT1.2-01: 战略蒸馏启动

```gherkin
Scenario: 启动 72 小时战略级深度活化
  Given 系统已处于战术活化状态
  When 触发后台战略任务流程
  Then 系统应开始百万次红蓝对抗预演
  And 战术级功能应保持可用
```

#### Acceptance Test AT1.2-02: 前台实时预警不阻塞

```gherkin
Scenario: 战略蒸馏期间前台预警正常运作
  Given 战略蒸馏任务正在运行
  When 收到实时预警信号
  Then 系统应正常响应预警
  And 战略蒸馏任务不应阻塞前台逻辑
```

---

### Story 1.3: 增量知识注入

**As a** 技术审计员
**I want** 在不重置系统的前提下注入新的经验案例
**So that** 系统能针对特定失误进行自我修正

#### Acceptance Test AT1.3-01: 增量知识注入

```gherkin
Scenario: 注入新的经验案例
  Given 一个已活化的系统
  When 提供一个包含新案例的 Markdown 片段
  Then RAG 引擎应完成增量索引更新
  And 系统不应重置或重启
```

#### Acceptance Test AT1.3-02: 新案例在辩论中被引用

```gherkin
Scenario: AI 专家引用新注入的案例
  Given 增量知识已成功注入
  When 启动 MAD 辩论流程
  Then AI 专家 Agent 在辩论中应能引用此新案例
  And 引用格式应符合 MACP v1.0 协议
```

---

## Epic 2: 专业数据生成与双轨激发引擎

### Story 2.1: 矢量化影像分析数据生成

**As a** DGM 模拟器
**I want** 生成 GeoJSON 格式的受淹边界与风险点位矢量表
**So that** AI 专家 Agent 能直接读取结构化数据而非处理原始图像

#### Acceptance Test AT2.1-01: GeoJSON 输出格式验证

```gherkin
Scenario: 生成符合 DEMS v1.0 的 GeoJSON
  Given 一个模拟灾害场景配置
  When 激发仿真流程
  Then 系统应产出符合 DEMS v1.0 规范的结构化 GeoJSON
  And 要素 UID 必须与 Activation-Pack 字典完全对齐
```

#### Acceptance Test AT2.1-02: 物理引擎签名

```gherkin
Scenario: 数据包附带物理引擎签名
  Given GeoJSON 数据已生成
  When 输出数据包
  Then 必须包含物理引擎的 SHA-256 签名 Header
  And 签名应与数据内容一致
```

---

### Story 2.2: 基础设施存活率实时计算

**As a** 态势感知引擎
**I want** 根据实时水位矢量表动态计算基站存活率
**So that** 指挥官能预判通信盲区

#### Acceptance Test AT2.2-01: 基站存活率计算

```gherkin
Scenario: 根据水位计算基站存活率
  Given 实时的水位分布 GeoJSON 文本
  When 物理计算节点接收到该表
  Then 系统应输出所有基站的 [ID, 状态 (Alive/Offline), 信号衰减度] 列表
  And 计算应基于水位与基站位置的几何关系
```

#### Acceptance Test AT2.2-02: 60 秒刷新推送

```gherkin
Scenario: 基站状态每 60 秒刷新推送
  Given Socket.io 连接已建立
  When 系统运行
  Then 基站存活率列表必须每 60 秒刷新一次
  And 刷新后的数据应推送至 WebSocket 总线
```

---

### Story 2.3: 双轨激发总线逻辑

**As a** 消息总线
**I want** 统一接收真实预警信号与模拟数据包
**So that** 下游推理引擎无需感知数据源类型

#### Acceptance Test AT2.3-01: 真实预警信号接入

```gherkin
Scenario: 接入真实预警信号
  Given 真实气象预警数据源可用
  When 气象部门发布预警信号
  Then 系统应能接收并解析预警数据
  And 数据应转换为统一的内部格式
```

#### Acceptance Test AT2.3-02: 模拟数据包接入

```gherkin
Scenario: 接入 DGM 模拟数据包
  Given DGM 模拟器已配置
  When 触发模拟演练
  Then 系统应能接收模拟数据包
  And 数据格式应与真实数据一致
```

#### Acceptance Test AT2.3-03: 下游引擎无感知切换

```gherkin
Scenario: 下游引擎不感知数据源类型
  Given 消息总线已接收数据
  When 数据传递给推理引擎
  Then 推理引擎应使用统一接口处理数据
  And 不应区分数据来源于真实或模拟
```

---

## Epic 3: 咨询级多目标决策分析

### Story 3.1: Plan A/B/C 三路方案并发生成

**As a** 指挥中枢 Agent
**I want** 并发调用 DeepSeek-R1 针对三个不同的权重目标产出方案
**So that** 指挥官能从多维度进行策略比选

#### Acceptance Test AT3.1-01: 三方案并发生成

```gherkin
Scenario: 并发生成 Plan A/B/C 三套方案
  Given 活化后的底图数据与实时预警信息
  When 触发方案生成指令
  Then 系统应在 120 秒内输出三份独立的 Markdown 方案草案
  And Plan A 应聚焦安全优先
  And Plan B 应聚焦平衡策略
  And Plan C 应聚焦最小干预
```

#### Acceptance Test AT3.1-02: 方案章节完整性

```gherkin
Scenario: 每份草案包含必要章节
  Given 方案已生成
  Then 每份草案必须包含核心研判章节
  And 每份草案必须包含 ROI 评分章节
  And 每份草案必须包含依据章节
  And 每份草案必须包含资源表章节
```

---

### Story 3.2: 循证推理与"证据桥"校验

**As a** 审计节点
**I want** 强制校验 Plan 中每一条建议的物理依据
**So that** 杜绝任何无根据的"幻觉"建议

#### Acceptance Test AT3.2-01: 数值描述证据匹配

```gherkin
Scenario: 校验方案中的数值描述
  Given AI 生成的方案文本
  When 包含数值描述（如"预计水位 4.2m"）时
  Then 系统必须在后台成功匹配对应的物理指纹或历史 RAG ID
  And 匹配结果应记录在证据桥中
```

#### Acceptance Test AT3.2-02: 无证据标识

```gherkin
Scenario: 无证据建议被标记
  Given 方案中的某条建议无法匹配证据
  When 执行证据桥校验
  Then 该建议条目必须被标注"EVIDENCE_VOID"标识
  And 用户界面应显示该标识警告指挥官
```

---

## Epic 4: 专家智能体虚拟会商与 MAD 辩论

### Story 4.1: MACP v1.0 通信协议实现

**As a** MAS 框架
**I want** 强制所有 Agent 的输入输出均符合 SDP/DCP/VIAP 模式
**So that** 智能体之间能够进行无歧义的"语义对话"

#### Acceptance Test AT4.1-01: MACP Header 验证

```gherkin
Scenario: Agent 辩论消息符合 MACP Header 要求
  Given 专家 Agent 发出的辩论消息
  When 消息进入系统总线时
  Then 系统应校验 Header 是否包含有效 trace_id
  And Header 应包含物理指纹
  And 无效的 Header 应被拒绝
```

#### Acceptance Test AT4.1-02: MACP Body 验证

```gherkin
Scenario: Agent 辩论消息符合 MACP Body 要求
  Given 专家 Agent 发出的辩论消息
  When 消息进行 Body 验证
  Then Body 必须包含量化的倾向性评分 (inclination)
  And inclination 值必须在 0-1 之间
  And 无效的 Body 应被拒绝
```

---

### Story 4.2: 多轮对抗博弈逻辑

**As a** 专家 Agent
**I want** 对他人的方案进行不少于三轮的漏洞挖掘与成本质疑
**So that** 最终方案经过多维度的极限压力测试

#### Acceptance Test AT4.2-01: 三轮对抗辩论

```gherkin
Scenario: 执行不少于三轮的对抗辩论
  Given 第一轮生成的方案草案
  When 启动 MAD 会商流
  Then 水文专家应发表质疑
  And 应急专家应发表质疑
  And 经济专家应发表质疑
  And 质疑点需引用对方的具体数据路径
```

#### Acceptance Test AT4.2-02: 对抗过程审计日志

```gherkin
Scenario: 对抗过程全量记录
  Given MAD 辩论正在进行
  When Agent 发表观点
  Then 所有消息应记录到 LangSmith 审计日志
  And 日志应包含完整的 trace_id 链路
```

---

### Story 4.3: Watchdog 强制收敛仲裁

**As a** Command Agent
**I want** 在第 8 分钟自动截断辩论并提取最大共识
**So that** 稳稳守住 10 分钟决策极限

#### Acceptance Test AT4.3-01: 480 秒自动截断

```gherkin
Scenario: Watchdog 在第 8 分钟截断辩论
  Given 一个正在进行的 MAD 辩论会话
  When Watchdog 检测到会话计时达到 480 秒
  Then Command Agent 必须立即停止所有输入
  And 基于当前的 inclination 向量产出最终仲裁报告
```

#### Acceptance Test AT4.3-02: 10 分钟决策极限

```gherkin
Scenario: 整个辩论在 10 分钟内完成
  Given MAD 辩论已启动
  When 辩论流程执行
  Then 从启动到最终报告输出应在 600 秒内完成
  And 超时应触发紧急仲裁机制
```

---

## Epic 5: 物理 - 逻辑实时耦合与交互看板

### Story 5.1: 亚秒级 What-if 仿真反馈

**As a** 指挥官
**I want** 在看板上拖动降雨参数滑块并瞬间看到水位变化预测
**So that** 我能直观建立物理防线的安全感

#### Acceptance Test AT5.1-01: 30 秒仿真反馈

```gherkin
Scenario: 参数调整后 30 秒内完成仿真
  Given 一个已加载的地理底座
  When 指挥官调整前端参数滑块
  Then 系统应在 30 秒内完成局部网格的 Godunov 重算
  And 结果应通过 WebSocket 推送至前端
```

#### Acceptance Test AT5.1-02: Mapbox 覆盖层更新

```gherkin
Scenario: 前端地图覆盖层实时更新
  Given 仿真结果已推送
  When 前端接收到结果切片
  Then Mapbox 覆盖层应立即更新显示
  And 更新过程应流畅无闪烁
```

---

### Story 5.2: 物理敏感型 ROI 动态修正

**As a** 决策引擎
**I want** 根据最新的流速与淹没历时参数自动重算各 Plan 的 ROI 得分
**So that** 建议方案能随着物理态势的恶化而自动降级或优化

#### Acceptance Test AT5.2-01: 流速超阈值权重调整

```gherkin
Scenario: 流速超阈值时自动调整 AHP 权重
  Given 最新的物理仿真输出流
  When 流速超过 1.5m/s
  Then 系统应自动调整 AHP 权重
  And 降低 Plan B (平衡型) 的评分
  And 提升 Plan A (安全型) 的优先级
```

#### Acceptance Test AT5.2-02: 淹没历时超阈值权重调整

```gherkin
Scenario: 淹没历时超阈值时自动调整权重
  Given 最新的物理仿真输出流
  When 淹没历时预估超过 24 小时
  Then 系统应自动调整 AHP 权重
  And Plan 评分应实时更新
```

---

## Epic 6: 权威 SOP 落地与防御性阻断

### Story 6.1: 原子级 SOP 自动生成

**As a** 系统
**I want** 将已选定的策略翻译为具体的救灾调派指令集
**So that** 执行人员能收到无歧义的行动指南

#### Acceptance Test AT6.1-01: 结构化指令表生成

```gherkin
Scenario: 生成原子级 SOP 指令表
  Given 一个已选定的最终策略结果
  When 触发"一键生成 SOP"
  Then 系统应产出结构化指令表
  And 每条指令必须包含 [执行主体，时空坐标，动作动词，数量参数]
```

#### Acceptance Test AT6.1-02: 指令术语规范

```gherkin
Scenario: SOP 指令术语符合国家规范
  Given SOP 已生成
  Then 指令术语必须严格符合国家防汛应急预案规范
  And 不应使用模糊或歧义表述
```

---

### Story 6.2: 防御性签名与黑匣子记录

**As a** 安全合规官
**I want** 强制拦截高危指令并要求双重签名
**So that** 关键决策过程具备不可消除的可追溯性

#### Acceptance Test AT6.2-01: 高危指令双重签名

```gherkin
Scenario: 高危指令需要双重签名
  Given 一条涉及"开闸泄洪"或"牺牲部分资产"的指令
  When 系统执行下发前
  Then 必须弹出双重数字签名窗口
  And 要求录入决策依据密码
```

#### Acceptance Test AT6.2-02: 黑匣子审计日志

```gherkin
Scenario: 决策过程自动写入黑匣子
  Given 高危指令处理流程
  When 决策完成
  Then 全过程数据应自动写入审计黑匣子日志
  And 日志应不可篡改
  And 日志应支持后续审计追溯
```

---

## Epic 7: 智能体全生命周期管理系统

### Story 7.1: 智能体快速创建模板

**As a** 管理员
**I want** 利用模板快速创建新的专家智能体
**So that** 系统能灵活扩展专家领域

#### Acceptance Test AT7.1-01: 模板创建智能体

```gherkin
Scenario: 使用模板创建智能体
  Given 系统提供智能体创建模板
  When 管理员填写必要信息并提交
  Then 系统应创建新的专家智能体
  And 智能体应符合 MACP v1.0 协议规范
```

---

### Story 7.2: 智能体即插即用激活

**As a** 管理员
**I want** 支持新智能体的"即插即用"与自动激活
**So that** 系统能快速响应新的专业需求

#### Acceptance Test AT7.2-01: 即插即用激活

```gherkin
Scenario: 新智能体即插即用
  Given 新智能体已创建
  When 智能体注册到系统
  Then 系统应自动完成激活流程
  And 智能体应能参与 MAD 辩论
```

---

### Story 7.3: 智能体状态可视化

**As a** 管理员
**I want** 可视化展示智能体运行状态与决策历史
**So that** 我能了解智能体的工作情况

#### Acceptance Test AT7.3-01: 状态可视化

```gherkin
Scenario: 展示智能体运行状态
  Given 智能体正在运行
  When 管理员访问状态页面
  Then 应显示智能体的在线状态
  And 应显示智能体的健康评分
  And 应显示智能体的最近活动时间
```

---

## Cross-Cutting Acceptance Tests

### AT-CROSS-01: 10 分钟决策全链路 SLA

```gherkin
Scenario: 完整决策流程在 10 分钟内完成
  Given 预警信号已触发
  When 启动完整决策流程 (包括数据接入、风险研判、Plan 生成、MAD 辩论、SOP 生成)
  Then 从预警到最终 SOP 输出应在 600 秒内完成
  And 每个子流程的计时应记录在审计日志
```

### AT-CROSS-02: 90 秒物理反馈 SLA

```gherkin
Scenario: 物理仿真反馈在 90 秒内完成
  Given 物理仿真请求已提交
  When 仿真流程启动
  Then 仿真结果应在 90 秒内返回
  And 结果应包含 SHA-256 物理指纹
```

### AT-CROSS-03: 全链路逻辑溯源

```gherkin
Scenario: CoT 摘要与 RAG 引用 ID 强制挂载
  Given AI 生成的任何建议或决策
  When 追溯决策链路
  Then 必须能追溯到 CoT 摘要
  And 必须能追溯到 RAG 引用 ID
  And 溯源链路应完整无断裂
```

### AT-CROSS-04: 物理 - 逻辑双向验证锁

```gherkin
Scenario: 物理偏差超阈值自动触发风险标记
  Given AI 决策与物理仿真结果
  When 物理偏差 > 15%
  Then 系统应自动触发风险标记
  And 用户界面应显示风险警告
```

### AT-CROSS-05: 证据权威性评分

```gherkin
Scenario: 自动计算展示"循证得分"
  Given 一个生成的 Plan
  When 查看 Plan 详情
  Then 应显示该 Plan 的"循证得分"
  And 得分应基于证据桥中的引用质量计算
```

---

## Acceptance Test Execution Status

| Test ID | Story | Status | Executed Date | Notes |
|---------|-------|--------|---------------|-------|
| AT0.1-01 | Story 0.1 | ⏳ Pending | - | - |
| AT0.1-02 | Story 0.1 | ⏳ Pending | - | - |
| AT0.2-01 | Story 0.2 | ⏳ Pending | - | - |
| AT0.3-01 | Story 0.3 | ⏳ Pending | - | - |
| AT1.1-01 | Story 1.1 | ⏳ Pending | - | - |
| AT1.1-02 | Story 1.1 | ⏳ Pending | - | - |
| AT2.1-01 | Story 2.1 | ⏳ Pending | - | - |
| AT3.1-01 | Story 3.1 | ⏳ Pending | - | - |
| AT4.1-01 | Story 4.1 | ⏳ Pending | - | - |
| AT4.3-01 | Story 4.3 | ⏳ Pending | - | - |
| AT5.1-01 | Story 5.1 | ⏳ Pending | - | - |
| AT6.1-01 | Story 6.1 | ⏳ Pending | - | - |
| AT6.2-01 | Story 6.2 | ⏳ Pending | - | - |
| AT7.2-01 | Story 7.2 | ⏳ Pending | - | - |
| AT-CROSS-01 | Cross-Cutting | ⏳ Pending | - | - |
| AT-CROSS-02 | Cross-Cutting | ⏳ Pending | - | - |

---

**Document generated by bmad-testarch-atdd workflow**
