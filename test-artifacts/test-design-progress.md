---
stepsCompleted: ['step-01-detect-mode', 'step-02-load-context', 'step-03-risk-and-testability', 'step-04-coverage-plan']
lastStep: 'step-04-coverage-plan'
lastSaved: '2026-03-31T00:00:00Z'
inputDocuments: [
  '_bmad-output/planning-artifacts/prd.md',
  '_bmad-output/planning-artifacts/architecture.md',
  '_bmad-output/planning-artifacts/epics.md',
  '_bmad-output/project-context.md',
  'src-frontend/playwright.config.ts',
  'src-backend/requirements.txt'
]
---

# Test Design Progress - 洪涝灾害 AI 协同辅助决策系统

## Step 01: Detect Mode & Prerequisites ✅ COMPLETED
## Step 02: Load Context & Knowledge Base ✅ COMPLETED

*(Previous steps retained - see prior content for mode determination and context loading)*

---

## Step 03: Testability & Risk Assessment ✅ COMPLETED

### 1. Testability Review (System-Level)

#### 🚨 Testability Concerns (Actionable Issues)

| ID | Concern | Impact | Mitigation | Priority |
|----|---------|--------|------------|----------|
| **T-01** | **LLM Non-Determinism**: DeepSeek API responses vary between runs, making assertion-based testing challenging | High | Use mock LLM responses for unit/integration tests; reserve real LLM tests for E2E validation with tolerant assertions | P0 |
| **T-02** | **Physics Simulation Coupling**: Godunov solver requires specific WSL2/Docker environment, hard to test in CI | High | Abstract physics interface with dependency injection; use recorded simulation snapshots for replay testing | P0 |
| **T-03** | **MACP Protocol Complexity**: Multi-field validation (SDP/DCP/VIAP) creates combinatorial test explosion | Medium | Implement schema-based property testing; use contract testing for protocol boundaries | P1 |
| **T-04** | **Real-Time Socket Events**: Socket.io bidirectional events difficult to sequence deterministically | Medium | Use socket.io-mock library; record/replay event sequences for regression testing | P1 |
| **T-05** | **Multi-Agent Concurrency**: MAD debate timing and turn-taking non-deterministic | Medium | Implement test harness with deterministic round-robin scheduling; use logical clocks for ordering | P1 |
| **T-06** | **Evidence Trace ID Propagation**: Decision_Trace_ID must flow through all layers for traceability | Medium | Implement trace ID validation middleware; add trace completeness checks to all tests | P1 |
| **T-07** | **Resource Contention**: Dynamic Priority Scheduling (DQS) requires multi-process coordination | Low | Use Docker Compose profiles for isolated test environments; implement resource budget testing | P2 |

#### ✅ Testability Strengths (Existing Advantages)

| Strength | Description | Test Benefit |
|----------|-------------|--------------|
| **MACP Explicit State** | All agent state encoded explicitly in MACP SDP field | Easy state seeding and verification |
| **Semantic Gateway** | Single translation layer between physical data and AI consumption | Clear boundary for integration tests |
| **Evidence Bridge** | Physical fingerprints (SHA-256) provide objective correctness criteria | Deterministic validation of simulation outputs |
| **Idempotent Nodes** | LangGraph nodes designed stateless/idempotent | Repeatable tests without complex cleanup |
| **Redis Pub/Sub Bus** | Centralized event bus with explicit message format | Easy to record/replay for testing |
| **Existing CI/CD** | GitHub Actions with parallel sharding | Fast feedback loop for test execution |

#### ASRs (Architecturally Significant Requirements) - Test Implications

| ASR | Status | Test Strategy |
|-----|--------|---------------|
| **MACP v1.0 Protocol Compliance** | ACTIONABLE | Contract tests for SDP/DCP/VIAP structure; VIAP validator unit tests |
| **DEMS Schema Enforcement** | ACTIONABLE | Schema validation tests for all data elements |
| **10-Minute Decision Limit** | ACTIONABLE | Performance tests with timing assertions; watchdog timer tests |
| **90-Second Physics Feedback** | ACTIONABLE | Simulation performance benchmarks; timeout handling tests |
| **99% Agent Availability** | ACTIONABLE | Chaos testing with agent failures; recovery tests |
| **Evidence Traceability (100%)** | ACTIONABLE | Trace completeness assertions in all integration tests |
| **Defensive Blocking** | ACTIONABLE | Security tests for high-risk command interception |
| **Physical Law Firewall** | ACTIONABLE | Property-based tests for conservation law validation |

---

### 2. Risk Assessment Matrix

#### Risk Scoring Methodology
- **Probability (P)**: 1 (Low) / 2 (Medium) / 3 (High)
- **Impact (I)**: 1 (Low) / 2 (Medium) / 3 (High)
- **Risk Score**: P × I (range 1-9)
- **Priority Threshold**: Score ≥ 6 = High Priority

#### Risk Register

| ID | Risk Description | Category | P | I | Score | Priority | Mitigation Strategy | Owner | Timeline |
|----|------------------|----------|---|---|-------|----------|---------------------|-------|----------|
| **R-01** | **LLM API Unavailable**: DeepSeek API outages block all decision-making | TECH | 2 | 3 | 6 | 🔴 HIGH | Implement RAG fallback mode with historical evidence; add circuit breaker pattern | Backend Team | Sprint 1 |
| **R-02** | **Physics Simulation Timeout**: Godunov solver exceeds 90-second SLA | PERF | 2 | 3 | 6 | 🔴 HIGH | Implement progressive mesh coarsening; add early termination with degraded fidelity | Physics Team | Sprint 2 |
| **R-03** | **MACP Protocol Violation**: Agent sends malformed messages, breaking debate flow | TECH | 2 | 2 | 4 | 🟡 MEDIUM | VIAP validator middleware; schema-first code generation | Backend Team | Sprint 1 |
| **R-04** | **Memory Exhaustion**: 16GB RAM insufficient for concurrent AI+Simulation | PERF | 2 | 2 | 4 | 🟡 MEDIUM | Enforce Docker memory limits; implement memory monitoring and alerting | DevOps Team | Sprint 1 |
| **R-05** | **Cascading Data Conflict**: DGM signal conflicts with physical simulation state | DATA | 2 | 3 | 6 | 🔴 HIGH | Implement event生效缓冲区 (event buffering); cascade operator validation | Architecture Team | Sprint 3 |
| **R-06** | **Socket.io Connection Loss**: Real-time evidence stream interrupted | TECH | 2 | 2 | 4 | 🟡 MEDIUM | Implement reconnection logic with backpressure; cache last-known-good state | Frontend Team | Sprint 1 |
| **R-07** | **Evidence Trace ID Loss**: Traceability broken mid-pipeline | DATA | 2 | 2 | 4 | 🟡 MEDIUM | Middleware-level trace injection; trace completeness assertions | Backend Team | Sprint 2 |
| **R-08** | **SOP Execution Without Confirmation**: Remonstrance lock bypassed | SEC | 1 | 3 | 3 | 🟢 LOW | UI-level confirmation dialogs; backend-level confirmation tokens | Fullstack Team | Sprint 4 |
| **R-09** | **Rescue Team "Ghost Resource"**: SOP agents disappear in social simulation | DATA | 2 | 2 | 4 | 🟡 MEDIUM | Resource exclusivity bus; dynamic obstacle injection | Simulation Team | Sprint 3 |
| **R-10** | **Precision Mismatch**: Sub-meter DGM vs 30m grid simulation | DATA | 2 | 2 | 4 | 🟡 MEDIUM | Precision degradation operator; semantic smoothing | Architecture Team | Sprint 2 |
| **R-11** | **Cognitive Dissonance**: RAG history conflicts with real-time physics | BUS | 2 | 2 | 4 | 🟡 MEDIUM | Evidence weighting model; physics-dominant decision rules | AI Team | Sprint 3 |
| **R-12** | **Physical Conservation Violation**: Red team injects impossible parameters | SEC | 2 | 3 | 6 | 🔴 HIGH | Dimensional analysis firewall; physics常识校验 middleware | Security Team | Sprint 4 |

#### Risk Summary

| Priority | Count | Risk IDs |
|----------|-------|----------|
| 🔴 High (≥6) | 4 | R-01, R-02, R-05, R-12 |
| 🟡 Medium (4-5) | 7 | R-03, R-04, R-06, R-07, R-09, R-10, R-11 |
| 🟢 Low (≤3) | 1 | R-08 |

**Total Identified Risks**: 12

---

### 3. Risk-Based Test Priorities

Based on risk assessment, prioritize test development:

| Priority | Test Focus | Linked Risks | Epic Coverage |
|----------|------------|--------------|---------------|
| **P0** | LLM Fallback & Circuit Breaker | R-01 | Epic 1, Epic 7 |
| **P0** | Physics Performance Benchmarks | R-02 | Epic 5 |
| **P0** | Cascade Conflict Validation | R-05, R-12 | Epic 2, Epic 6 |
| **P1** | MACP Protocol Validation | R-03 | Epic 4 |
| **P1** | Resource Monitoring & Limits | R-04 | Epic 0 |
| **P1** | Trace ID Completeness | R-07 | Epic 3, Epic 4 |
| **P1** | Socket Reconnection & Caching | R-06 | Epic 0 |
| **P2** | Remonstrance Lock Verification | R-08 | Epic 5 |
| **P2** | Resource Exclusivity Testing | R-09 | Epic 2 |
| **P2** | Evidence Weighting Tests | R-11 | Epic 3 |

---

## Next Steps

Proceed to **Step 04: Coverage Plan** to define comprehensive test coverage strategy and test case specifications.

---

**Progress**: Step 03 Complete → Proceeding to Step 04

---

## Step 04: Coverage Plan & Execution Strategy ✅ COMPLETED

### 1. Test Coverage Matrix

#### Epic 0: 基础框架与交互底座

| Test ID | Requirement/Scenario | Test Level | Priority | Test Type | Location |
|---------|---------------------|------------|----------|-----------|----------|
| **E0-T01** | Monorepo Docker 环境初始化 | Integration | P0 | Functional | `src-backend/test/` |
| **E0-T02** | WSL2 Ext4 卷挂载验证 | Integration | P0 | Configuration | `deploy/` |
| **E0-T03** | React/Mapbox 前端骨架加载 | Component | P0 | Functional | `src-frontend/tests/` |
| **E0-T04** | Socket.io 双向事件总线 | Integration | P0 | Functional | `src-backend/test/` |
| **E0-T05** | MACP 协议消息格式验证 | Unit | P0 | Schema | `src-backend/test/test_macp_*.py` |
| **E0-T06** | X-Decision-Trace-ID 传播 | Integration | P1 | Traceability | `src-backend/test/` |
| **E0-T07** | Redis Pub/Sub 消息路由 | Unit | P1 | Functional | `src-backend/test/` |

#### Epic 1: 地域大脑极速活化中心

| Test ID | Requirement/Scenario | Test Level | Priority | Test Type | Location |
|---------|---------------------|------------|----------|-----------|----------|
| **E1-T01** | Activation-Pack 注入与验证 | Integration | P0 | Functional | `src-backend/test/` |
| **E1-T02** | 15 分钟战术活化计时 | Performance | P0 | Timing | `src-backend/test/` |
| **E1-T03** | RAG 知识灌装完整性 | Integration | P1 | Validation | `src-backend/test/` |
| **E1-T04** | 增量知识注入 (热更新) | Integration | P1 | Functional | `src-backend/test/` |
| **E1-T05** | 活化状态机转换 | Unit | P2 | State Machine | `src-backend/test/` |

#### Epic 2: 专业数据生成与双轨激发引擎

| Test ID | Requirement/Scenario | Test Level | Priority | Test Type | Location |
|---------|---------------------|------------|----------|-----------|----------|
| **E2-T01** | DGM 激发模拟预警 | Integration | P0 | Functional | `src-backend/test/` |
| **E2-T02** | 真实监测数据流接入 | Integration | P0 | Integration | `src-backend/test/` |
| **E2-T03** | GIS 矢量数据表生成 | Unit | P0 | Data Quality | `src-data-generator/test/` |
| **E2-T04** | 水文传感器时序数据 | Unit | P1 | Data Quality | `src-data-generator/test/` |
| **E2-T05** | 基础设施存活状态表 | Unit | P1 | Data Quality | `src-data-generator/test/` |
| **E2-T06** | 社会域动态模拟 | Unit | P2 | Simulation | `src-data-generator/test/` |
| **E2-T07** | 干扰指令级联激发 | Integration | P1 | Chaos | `src-backend/test/` |
| **E2-T08** | 精度降级对齐算子 | Unit | P2 | Validation | `src-data-generator/test/` |

#### Epic 3: 咨询级多目标决策分析

| Test ID | Requirement/Scenario | Test Level | Priority | Test Type | Location |
|---------|---------------------|------------|----------|-----------|----------|
| **E3-T01** | 多维风险研判报告生成 | Integration | P0 | Functional | `src-backend/test/` |
| **E3-T02** | Plan A/B/C 并行生成 | Integration | P0 | Functional | `src-backend/test/` |
| **E3-T03** | 证据桥强制引用 | Integration | P0 | Traceability | `src-backend/test/` |
| **E3-T04** | 咨询级文档自动生成 | Integration | P1 | Functional | `src-backend/test/` |
| **E3-T05** | ROI 动态修正 | Integration | P2 | Functional | `src-backend/test/` |
| **E3-T06** | 证据权重模型验证 | Unit | P1 | Validation | `src-backend/test/` |

#### Epic 4: 专家智能体虚拟会商与 MAD 辩论

| Test ID | Requirement/Scenario | Test Level | Priority | Test Type | Location |
|---------|---------------------|------------|----------|-----------|----------|
| **E4-T01** | 虚拟会商室召集 | Integration | P0 | Functional | `src-backend/test/test_debate_*.py` |
| **E4-T02** | 不少于三轮对抗辩论 | Integration | P0 | Functional | `src-backend/test/test_debate_*.py` |
| **E4-T03** | Command Agent 强制仲裁 | Integration | P0 | Functional | `src-backend/test/` |
| **E4-T04** | 辩论流实时穿透展示 | E2E | P1 | UI | `src-frontend/tests/` |
| **E4-T05** | Watchdog 仲裁机制 | Integration | P0 | Timeout | `src-backend/test/` |
| **E4-T06** | TTL 监控 (10 分钟极限) | Performance | P0 | Timing | `src-backend/test/` |
| **E4-T07** | 辩论证据快照持久化 | Integration | P1 | Redis | `src-backend/test/` |
| **E4-T08** | 智能体推理逻辑热更新 | Integration | P2 | Functional | `src-backend/test/` |

#### Epic 5: 物理 - 逻辑实时耦合与交互看板

| Test ID | Requirement/Scenario | Test Level | Priority | Test Type | Location |
|---------|---------------------|------------|----------|-----------|----------|
| **E5-T01** | What-if 干预仿真 (30 秒反馈) | Performance | P0 | Timing | `src-physics-sidecar/test/` |
| **E5-T02** | 物理后果预演 (90 秒/60 分钟) | Performance | P0 | Timing | `src-physics-sidecar/test/` |
| **E5-T03** | 参数化因果图渲染 | E2E | P1 | UI | `src-frontend/tests/` |
| **E5-T04** | 防线崩溃概率观察 | E2E | P1 | UI | `src-frontend/tests/` |
| **E5-T05** | Remonstrance Lock 验证 | Integration | P0 | Safety | `src-backend/test/` |
| **E5-T06** | 增量关键帧推送 | Integration | P1 | Streaming | `src-frontend/tests/` |
| **E5-T07** | 动态优先级调度 (DQS) | Performance | P2 | Resource | `src-backend/test/` |

#### Epic 6: 权威 SOP 落地与防御性阻断

| Test ID | Requirement/Scenario | Test Level | Priority | Test Type | Location |
|---------|---------------------|------------|----------|-----------|----------|
| **E6-T01** | 原子级 SOP 自动生成 | Integration | P0 | Functional | `src-backend/test/` |
| **E6-T02** | 任务分流 (冷静指挥/人文关怀) | Integration | P1 | Functional | `src-backend/test/` |
| **E6-T03** | 红蓝对抗引擎拦截 | Security | P0 | Validation | `src-backend/test/` |
| **E6-T04** | 违反水利标准拦截 | Security | P0 | Compliance | `src-backend/test/` |
| **E6-T05** | 防御性指令阻断协议 | Security | P0 | Safety | `src-backend/test/` |
| **E6-T06** | 双重签名验证 | Security | P0 | Auth | `src-backend/test/` |
| **E6-T07** | 黑匣子记录完整性 | Integration | P1 | Audit | `src-backend/test/` |
| **E6-T08** | SOP 导出格式验证 | Unit | P1 | Validation | `src-backend/test/` |

#### Epic 7: 智能体全生命周期管理系统

| Test ID | Requirement/Scenario | Test Level | Priority | Test Type | Location |
|---------|---------------------|------------|----------|-----------|----------|
| **E7-T01** | 智能体快速创建模板 | Integration | P1 | Functional | `src-backend/test/` |
| **E7-T02** | 智能体即插即用激活 | Integration | P0 | Functional | `src-backend/test/` |
| **E7-T03** | 智能体在线率监控 (>99%) | Performance | P0 | Reliability | `src-backend/test/` |
| **E7-T04** | 智能体状态可视化 | E2E | P1 | UI | `src-frontend/tests/` |
| **E7-T05** | 智能体手动下线/静默 | Integration | P2 | Functional | `src-backend/test/` |
| **E7-T06** | 智能体决策历史追溯 | E2E | P1 | Traceability | `src-frontend/tests/` |
| **E7-T07** | 资源预算监控 | Performance | P2 | Resource | `src-backend/test/` |

---

### 2. Cross-Cutting Tests

| Category | Test ID | Description | Priority |
|----------|---------|-------------|----------|
| **Performance** | PERF-01 | 10 分钟决策全链路计时 | P0 |
| **Performance** | PERF-02 | 90 秒物理反馈 SLA 验证 | P0 |
| **Performance** | PERF-03 | 并发 Agent 压力测试 (100+ 同时连接) | P1 |
| **Performance** | PERF-04 | 内存限制验证 (16GB 上限) | P1 |
| **Security** | SEC-01 | 物理定律防火墙验证 | P0 |
| **Security** | SEC-02 | 高风险命令预演拦截 | P0 |
| **Security** | SEC-03 | API Key 和敏感信息保护 | P0 |
| **Reliability** | REL-01 | Agent 故障恢复测试 | P1 |
| **Reliability** | REL-02 | Redis/Postgres 故障转移 | P1 |
| **Reliability** | REL-03 | Socket 断线重连 | P2 |
| **Chaos** | CHAOS-01 | 级联冲突场景测试 | P1 |
| **Chaos** | CHAOS-02 | 时空时滞悖论处理 | P1 |
| **Chaos** | CHAOS-03 | 幽灵资源悖论验证 | P2 |

---

### 3. Execution Strategy

#### Test Triggers

| Trigger | Test Suite | Estimated Duration | Frequency |
|---------|------------|-------------------|-----------|
| **PR (Pull Request)** | All P0 Unit + Integration | ~10-15 min | On every PR |
| **PR (Pull Request)** | All P1 Unit + Integration | ~15-25 min | On every PR |
| **Nightly** | All P0 + P1 E2E | ~30-45 min | Daily |
| **Nightly** | Performance benchmarks | ~20-30 min | Daily |
| **Weekly (Sunday 2AM)** | Burn-in loop (5 iterations) | ~60 min | Weekly |
| **Weekly (Sunday 2AM)** | Chaos & Security tests | ~45-60 min | Weekly |
| **On-Demand** | Full regression (all tests) | ~2-3 hours | Before release |

#### CI/CD Pipeline Configuration

| Stage | Tests | Shards | Timeout | Artifacts |
|-------|-------|--------|---------|-----------|
| **Lint** | ESLint, Black, Flake8 | 1 | 5 min | N/A |
| **Backend Unit** | pytest (unit tests) | 4 | 30 min | Coverage XML |
| **Backend Integration** | pytest (integration) | 4 | 30 min | JUnit XML |
| **Frontend E2E** | Playwright | 4 | 30 min | HTML Report |
| **Performance** | Timing benchmarks | 1 | 30 min | Metrics JSON |
| **Security** | Red team tests | 1 | 30 min | Audit Log |
| **Quality Gate** | Coverage ≥80%, P0=100% | N/A | 5 min | Summary |

---

### 4. Resource Estimates

| Priority | Estimate (Hours) | Tests | Owner | Timeline |
|----------|------------------|-------|-------|----------|
| **P0** | ~35-50 hours | 25 tests | Core Team | Sprint 1-2 |
| **P1** | ~30-45 hours | 30 tests | Fullstack Team | Sprint 2-3 |
| **P2** | ~20-30 hours | 20 tests | QA Team | Sprint 3-4 |
| **P3** | ~5-10 hours | 10 tests | Exploratory | Sprint 4+ |
| **Total** | **~90-135 hours** | **85 tests** | All Teams | **4 Sprints** |

---

### 5. Quality Gates

| Gate | Threshold | Enforcement | Consequence |
|------|-----------|-------------|-------------|
| **P0 Pass Rate** | 100% | CI Blocker | PR rejected |
| **P1 Pass Rate** | ≥95% | CI Warning | PR allowed with notice |
| **Code Coverage** | ≥80% | CI Blocker | PR rejected |
| **Performance SLA** | 10-min decision | CI Blocker | Release blocked |
| **Performance SLA** | 90-sec physics | CI Warning | Optimization required |
| **Security Tests** | 100% pass | CI Blocker | Release blocked |
| **High-Risk Mitigation** | All complete | Release Gate | Release blocked |

---

## Step 05: Generate Output 🔄 IN PROGRESS

Proceeding to create final test design documents.

---

**Progress**: Step 04 Complete → Proceeding to Step 05
