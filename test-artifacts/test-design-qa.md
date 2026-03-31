---
stepsCompleted: ['step-01-detect-mode', 'step-02-load-context', 'step-03-risk-and-testability', 'step-04-coverage-plan', 'step-05-generate-output']
lastStep: 'step-05-generate-output'
lastSaved: '2026-03-31T00:00:00Z'
workflowType: 'testarch-test-design'
inputDocuments: [
  '_bmad-output/planning-artifacts/prd.md',
  '_bmad-output/planning-artifacts/architecture.md',
  '_bmad-output/planning-artifacts/epics.md',
  '_bmad-output/project-context.md'
]
---

# Test Design for QA: 洪涝灾害 AI 协同辅助决策系统

**Purpose:** Test execution recipe for QA team. Defines what to test, how to test it, and what QA needs from other teams.

**Date:** 2026-03-31
**Author:** BMad Test Architect
**Status:** Draft
**Project:** BMAD-METHOD (洪涝灾害智能体系统)

**Related:** See Architecture doc (`test-design-architecture.md`) for testability concerns and architectural blockers.

---

## Executive Summary

**Scope:** System-level test coverage for AI-powered flood decision support system including multi-agent debate (MAD), physics-AI coupling, real-time evidence streaming, and defensive blocking mechanisms.

**Risk Summary:**

- **Total Risks:** 12 (4 high-priority score ≥6, 7 medium, 1 low)
- **Critical Categories:** TECH (3), DATA (4), PERF (2), SEC (3)
- **Highest Risk:** R-01 (LLM API Unavailable), R-02 (Physics Timeout), R-12 (Physical Conservation Violation)

**Coverage Summary:**

- P0 tests: ~25 (critical paths, security, performance SLAs)
- P1 tests: ~30 (integration points, traceability, reliability)
- P2 tests: ~20 (edge cases, secondary flows, chaos)
- P3 tests: ~10 (exploratory, benchmarks, nice-to-have)
- **Total:** ~85 tests (~4-6 weeks with 1 QA, ~2-3 weeks with 2 QAs)

---

## Not in Scope

**Components or systems explicitly excluded from this test plan:**

| Item | Reasoning | Mitigation |
|------|-----------|------------|
| **DGM Internal Physics** | Physics simulator has own test suite | Validated via Evidence Bridge interface only |
| **Mapbox GL Rendering** | Third-party library | Tested via visual regression only |
| **DeepSeek LLM Training** | External service | Test fallback behavior, not model quality |
| **Redis Stack Internals** | Managed service | Test pub/sub behavior, not Redis itself |
| **Docker Compose Orchestration** | Infrastructure concern | Tested via integration smoke tests |

**Note:** Items listed here have been reviewed and accepted as out-of-scope by QA, Dev, and PM.

---

## Dependencies & Test Blockers

**CRITICAL:** QA cannot proceed without these items from other teams.

### Backend/Architecture Dependencies (Pre-Implementation)

**Source:** See Architecture doc "Quick Guide" for detailed mitigation plans

1. **MACP Protocol Implementation** - Backend Team - Sprint 1
   - Complete VIAP validator middleware with full schema enforcement
   - Provide MACP message builders for test fixtures
   - Why it blocks testing: All agent integration tests require valid MACP messages

2. **Physics Simulation Interface** - Physics Team - Sprint 2
   - Abstract physics interface with dependency injection
   - Provide recorded simulation snapshots for replay testing
   - Why it blocks testing: Cannot test AI-physics coupling without mockable interface

3. **Semantic Gateway** - Backend Team - Sprint 1
   - Complete DEMS translation layer implementation
   - Provide semantic tag dictionaries for test data generation
   - Why it blocks testing: AI agents cannot consume raw simulation data

4. **Evidence Trace ID Infrastructure** - Fullstack Team - Sprint 2
   - Implement trace ID propagation middleware
   - Provide trace completeness validation utilities
   - Why it blocks testing: Traceability tests require end-to-end trace ID flow

### QA Infrastructure Setup (Pre-Implementation)

1. **Test Data Factories** - QA
   - MACP message factory with faker-based randomization
   - DebateContext fixtures for multi-agent scenarios
   - Auto-cleanup fixtures for parallel safety

2. **Test Environments** - QA + DevOps
   - Local: WSL2 Docker Compose setup
   - CI/CD: GitHub Actions with PostgreSQL/Redis services
   - Staging: Full deployment with mock LLM

**Example factory pattern:**

```python
from src.mas.protocol.schema import MACPMessage, MACPHeader, MACPBody, AgentType
from src.mas.protocol.validator import VIAPValidator

def create_test_macp_message(agent_type: AgentType, stance: str, inclination: float):
    """Factory for creating valid MACP messages for testing."""
    message = MACPMessage(
        header=MACPHeader(
            trace_id=f"test-trace-{uuid.uuid4().hex[:8]}",
            agent_id=f"test-{agent_type.value}",
            agent_type=agent_type,
        ),
        body=MACPBody(
            content="Test message content",
            inclination=inclination,
            confidence=0.85,
            stance=stance,
            evidence_refs=[f"PHYSICS_test_{uuid.uuid4().hex[:6]}"]
        )
    )
    assert VIAPValidator.validate_message(message).is_valid
    return message
```

---

## Test Coverage Matrix

### Epic 0: 基础框架与交互底座 (7 tests)

| Test ID | Scenario | Level | Priority | Type | Status |
|---------|----------|-------|----------|------|--------|
| E0-T01 | Monorepo Docker 环境初始化 | Integration | P0 | Functional | ✅ Existing |
| E0-T02 | WSL2 Ext4 卷挂载验证 | Integration | P0 | Configuration | ⏳ TODO |
| E0-T03 | React/Mapbox 前端骨架加载 | Component | P0 | Functional | ✅ Existing |
| E0-T04 | Socket.io 双向事件总线 | Integration | P0 | Functional | ⏳ TODO |
| E0-T05 | MACP 协议消息格式验证 | Unit | P0 | Schema | ✅ Existing |
| E0-T06 | X-Decision-Trace-ID 传播 | Integration | P1 | Traceability | ⏳ TODO |
| E0-T07 | Redis Pub/Sub 消息路由 | Unit | P1 | Functional | ⏳ TODO |

### Epic 1: 地域大脑极速活化中心 (5 tests)

| Test ID | Scenario | Level | Priority | Type | Status |
|---------|----------|-------|----------|------|--------|
| E1-T01 | Activation-Pack 注入与验证 | Integration | P0 | Functional | ⏳ TODO |
| E1-T02 | 15 分钟战术活化计时 | Performance | P0 | Timing | ⏳ TODO |
| E1-T03 | RAG 知识灌装完整性 | Integration | P1 | Validation | ⏳ TODO |
| E1-T04 | 增量知识注入 (热更新) | Integration | P1 | Functional | ⏳ TODO |
| E1-T05 | 活化状态机转换 | Unit | P2 | State Machine | ⏳ TODO |

### Epic 2: 专业数据生成与双轨激发引擎 (8 tests)

| Test ID | Scenario | Level | Priority | Type | Status |
|---------|----------|-------|----------|------|--------|
| E2-T01 | DGM 激发模拟预警 | Integration | P0 | Functional | ⏳ TODO |
| E2-T02 | 真实监测数据流接入 | Integration | P0 | Integration | ⏳ TODO |
| E2-T03 | GIS 矢量数据表生成 | Unit | P0 | Data Quality | ⏳ TODO |
| E2-T04 | 水文传感器时序数据 | Unit | P1 | Data Quality | ⏳ TODO |
| E2-T05 | 基础设施存活状态表 | Unit | P1 | Data Quality | ⏳ TODO |
| E2-T06 | 社会域动态模拟 | Unit | P2 | Simulation | ⏳ TODO |
| E2-T07 | 干扰指令级联激发 | Integration | P1 | Chaos | ⏳ TODO |
| E2-T08 | 精度降级对齐算子 | Unit | P2 | Validation | ⏳ TODO |

### Epic 3: 咨询级多目标决策分析 (6 tests)

| Test ID | Scenario | Level | Priority | Type | Status |
|---------|----------|-------|----------|------|--------|
| E3-T01 | 多维风险研判报告生成 | Integration | P0 | Functional | ⏳ TODO |
| E3-T02 | Plan A/B/C 并行生成 | Integration | P0 | Functional | ⏳ TODO |
| E3-T03 | 证据桥强制引用 | Integration | P0 | Traceability | ⏳ TODO |
| E3-T04 | 咨询级文档自动生成 | Integration | P1 | Functional | ⏳ TODO |
| E3-T05 | ROI 动态修正 | Integration | P2 | Functional | ⏳ TODO |
| E3-T06 | 证据权重模型验证 | Unit | P1 | Validation | ⏳ TODO |

### Epic 4: 专家智能体虚拟会商与 MAD 辩论 (8 tests)

| Test ID | Scenario | Level | Priority | Type | Status |
|---------|----------|-------|----------|------|--------|
| E4-T01 | 虚拟会商室召集 | Integration | P0 | Functional | ✅ Existing |
| E4-T02 | 不少于三轮对抗辩论 | Integration | P0 | Functional | ✅ Existing |
| E4-T03 | Command Agent 强制仲裁 | Integration | P0 | Functional | ⏳ TODO |
| E4-T04 | 辩论流实时穿透展示 | E2E | P1 | UI | ⏳ TODO |
| E4-T05 | Watchdog 仲裁机制 | Integration | P0 | Timeout | ⏳ TODO |
| E4-T06 | TTL 监控 (10 分钟极限) | Performance | P0 | Timing | ⏳ TODO |
| E4-T07 | 辩论证据快照持久化 | Integration | P1 | Redis | ⏳ TODO |
| E4-T08 | 智能体推理逻辑热更新 | Integration | P2 | Functional | ⏳ TODO |

### Epic 5: 物理 - 逻辑实时耦合与交互看板 (7 tests)

| Test ID | Scenario | Level | Priority | Type | Status |
|---------|----------|-------|----------|------|--------|
| E5-T01 | What-if 干预仿真 (30 秒反馈) | Performance | P0 | Timing | ⏳ TODO |
| E5-T02 | 物理后果预演 (90 秒/60 分钟) | Performance | P0 | Timing | ⏳ TODO |
| E5-T03 | 参数化因果图渲染 | E2E | P1 | UI | ⏳ TODO |
| E5-T04 | 防线崩溃概率观察 | E2E | P1 | UI | ⏳ TODO |
| E5-T05 | Remonstrance Lock 验证 | Integration | P0 | Safety | ⏳ TODO |
| E5-T06 | 增量关键帧推送 | Integration | P1 | Streaming | ⏳ TODO |
| E5-T07 | 动态优先级调度 (DQS) | Performance | P2 | Resource | ⏳ TODO |

### Epic 6: 权威 SOP 落地与防御性阻断 (8 tests)

| Test ID | Scenario | Level | Priority | Type | Status |
|---------|----------|-------|----------|------|--------|
| E6-T01 | 原子级 SOP 自动生成 | Integration | P0 | Functional | ⏳ TODO |
| E6-T02 | 任务分流 (冷静指挥/人文关怀) | Integration | P1 | Functional | ⏳ TODO |
| E6-T03 | 红蓝对抗引擎拦截 | Security | P0 | Validation | ⏳ TODO |
| E6-T04 | 违反水利标准拦截 | Security | P0 | Compliance | ⏳ TODO |
| E6-T05 | 防御性指令阻断协议 | Security | P0 | Safety | ⏳ TODO |
| E6-T06 | 双重签名验证 | Security | P0 | Auth | ⏳ TODO |
| E6-T07 | 黑匣子记录完整性 | Integration | P1 | Audit | ⏳ TODO |
| E6-T08 | SOP 导出格式验证 | Unit | P1 | Validation | ⏳ TODO |

### Epic 7: 智能体全生命周期管理系统 (7 tests)

| Test ID | Scenario | Level | Priority | Type | Status |
|---------|----------|-------|----------|------|--------|
| E7-T01 | 智能体快速创建模板 | Integration | P1 | Functional | ⏳ TODO |
| E7-T02 | 智能体即插即用激活 | Integration | P0 | Functional | ⏳ TODO |
| E7-T03 | 智能体在线率监控 (>99%) | Performance | P0 | Reliability | ⏳ TODO |
| E7-T04 | 智能体状态可视化 | E2E | P1 | UI | ⏳ TODO |
| E7-T05 | 智能体手动下线/静默 | Integration | P2 | Functional | ⏳ TODO |
| E7-T06 | 智能体决策历史追溯 | E2E | P1 | Traceability | ⏳ TODO |
| E7-T07 | 资源预算监控 | Performance | P2 | Resource | ⏳ TODO |

### Cross-Cutting Tests (13 tests)

| Category | Test ID | Description | Priority | Status |
|----------|---------|-------------|----------|--------|
| **Performance** | PERF-01 | 10 分钟决策全链路计时 | P0 | ⏳ TODO |
| **Performance** | PERF-02 | 90 秒物理反馈 SLA 验证 | P0 | ⏳ TODO |
| **Performance** | PERF-03 | 并发 Agent 压力测试 (100+ 连接) | P1 | ⏳ TODO |
| **Performance** | PERF-04 | 内存限制验证 (16GB 上限) | P1 | ⏳ TODO |
| **Security** | SEC-01 | 物理定律防火墙验证 | P0 | ⏳ TODO |
| **Security** | SEC-02 | 高风险命令预演拦截 | P0 | ⏳ TODO |
| **Security** | SEC-03 | API Key 和敏感信息保护 | P0 | ⏳ TODO |
| **Reliability** | REL-01 | Agent 故障恢复测试 | P1 | ⏳ TODO |
| **Reliability** | REL-02 | Redis/Postgres 故障转移 | P1 | ⏳ TODO |
| **Reliability** | REL-03 | Socket 断线重连 | P2 | ⏳ TODO |
| **Chaos** | CHAOS-01 | 级联冲突场景测试 | P1 | ⏳ TODO |
| **Chaos** | CHAOS-02 | 时空时滞悖论处理 | P1 | ⏳ TODO |
| **Chaos** | CHAOS-03 | 幽灵资源悖论验证 | P2 | ⏳ TODO |

---

## Test Execution Strategy

### CI/CD Pipeline Configuration

| Stage | Tests | Shards | Timeout | Artifacts |
|-------|-------|--------|---------|-----------|
| **Lint** | ESLint, Black, Flake8 | 1 | 5 min | N/A |
| **Backend Unit** | pytest (unit tests) | 4 | 30 min | Coverage XML |
| **Backend Integration** | pytest (integration) | 4 | 30 min | JUnit XML |
| **Frontend E2E** | Playwright | 4 | 30 min | HTML Report |
| **Performance** | Timing benchmarks | 1 | 30 min | Metrics JSON |
| **Security** | Red team tests | 1 | 30 min | Audit Log |
| **Quality Gate** | Coverage ≥80%, P0=100% | N/A | 5 min | Summary |

### Test Triggers

| Trigger | Test Suite | Estimated Duration | Frequency |
|---------|------------|-------------------|-----------|
| **PR (Pull Request)** | All P0 Unit + Integration | ~10-15 min | On every PR |
| **PR (Pull Request)** | All P1 Unit + Integration | ~15-25 min | On every PR |
| **Nightly** | All P0 + P1 E2E | ~30-45 min | Daily |
| **Nightly** | Performance benchmarks | ~20-30 min | Daily |
| **Weekly (Sunday 2AM)** | Burn-in loop (5 iterations) | ~60 min | Weekly |
| **Weekly (Sunday 2AM)** | Chaos & Security tests | ~45-60 min | Weekly |
| **On-Demand** | Full regression (all tests) | ~2-3 hours | Before release |

---

## Quality Gates

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

## Resource Estimates

| Priority | Estimate (Hours) | Tests | Owner | Timeline |
|----------|------------------|-------|-------|----------|
| **P0** | ~35-50 hours | 25 tests | Core Team | Sprint 1-2 |
| **P1** | ~30-45 hours | 30 tests | Fullstack Team | Sprint 2-3 |
| **P2** | ~20-30 hours | 20 tests | QA Team | Sprint 3-4 |
| **P3** | ~5-10 hours | 10 tests | Exploratory | Sprint 4+ |
| **Total** | **~90-135 hours** | **85 tests** | All Teams | **4 Sprints** |

---

## Test Development Checklist

### Sprint 1-2 (P0 Tests)

- [ ] E0-T01 to E0-T05: Foundation tests
- [ ] E1-T01, E1-T02: Activation tests
- [ ] E2-T01 to E2-T03: Data generation tests
- [ ] E3-T01 to E3-T03: Decision analysis tests
- [ ] E4-T01 to E4-T03, E4-T05, E4-T06: MAD debate tests
- [ ] E5-T01, E5-T02, E5-T05: Physics coupling tests
- [ ] E6-T01, E6-T03 to E6-T06: Security tests
- [ ] E7-T02, E7-T03: Agent lifecycle tests
- [ ] PERF-01, PERF-02: Performance SLA tests
- [ ] SEC-01 to SEC-03: Security tests

### Sprint 2-3 (P1 Tests)

- [ ] E0-T06, E0-T07: Traceability tests
- [ ] E1-T03, E1-T04: RAG tests
- [ ] E2-T04, E2-T05, E2-T07: Data quality tests
- [ ] E3-T04, E3-T06: Documentation tests
- [ ] E4-T04, E4-T07: UI辩论 tests
- [ ] E5-T03, E5-T04, E5-T06: Visualization tests
- [ ] E6-T02, E6-T07, E6-T08: SOP tests
- [ ] E7-T01, E7-T04, E7-T06: Lifecycle UI tests
- [ ] PERF-03, PERF-04: Stress tests
- [ ] REL-01, REL-02: Reliability tests
- [ ] CHAOS-01, CHAOS-02: Chaos tests

### Sprint 3-4 (P2/P3 Tests)

- [ ] Remaining E2 tests (simulation)
- [ ] Remaining E3 tests (ROI)
- [ ] Remaining E4 tests (hot update)
- [ ] Remaining E5 tests (DQS)
- [ ] Remaining E7 tests (silent/downline)
- [ ] REL-03: Socket reconnection
- [ ] CHAOS-03: Ghost resource test
- [ ] P3 exploratory tests

---

## Appendix: Test Templates

### Unit Test Template (pytest)

```python
"""Unit test template for MACP protocol testing."""
import pytest
from src.mas.protocol.schema import MACPMessage, MACPHeader, MACPBody, AgentType
from src.mas.protocol.validator import VIAPValidator


class TestMACPProtocol:
    """Test MACP protocol validation."""

    def test_valid_message_passes_validation(self):
        """Test that valid MACP message passes VIAP validation."""
        # Arrange
        message = MACPMessage(
            header=MACPHeader(
                trace_id="test-00001",
                agent_id="test-agent-001",
                agent_type=AgentType.HYDROLOGY,
            ),
            body=MACPBody(
                content="Test content",
                inclination=0.8,
                confidence=0.85,
                stance="support",
                evidence_refs=["PHYSICS_test_001"]
            )
        )

        # Act
        result = VIAPValidator.validate_message(message)

        # Assert
        assert result.is_valid, f"Validation failed: {result.errors}"
```

### Integration Test Template (pytest-asyncio)

```python
"""Integration test template for Agent debate testing."""
import pytest
import asyncio
from src.mas.debate.state import DebateContext
from src.mas.debate.agents.hydrology import HydrologyAgent
from src.mas.debate.agents.emergency import EmergencyAgent


@pytest.mark.asyncio
class TestAgentDebate:
    """Test multi-agent debate integration."""

    async def test_debate_engine_basic(self, debate_engine):
        """Test basic debate engine with two agents."""
        # Arrange
        context = DebateContext(
            topic="建议立即启动一级响应",
            current_round=1,
            total_rounds=3,
            previous_messages=[]
        )

        # Act
        result = await debate_engine.run_debate(context)

        # Assert
        assert result is not None
        assert len(result.previous_messages) >= 2  # At least 2 agent messages
```

### E2E Test Template (Playwright)

```typescript
/**
 * E2E test template for debate flow visualization.
 */
import { test, expect } from '@playwright/test';

test.describe('MAD Debate Flow', () => {
  test('should display real-time debate messages @p1', async ({ page }) => {
    // Arrange
    await page.goto('/');
    await page.waitForSelector('[data-testid="debate-panel"]');

    // Act - Trigger debate
    await page.click('[data-testid="start-debate-button"]');

    // Assert - Messages appear in order
    await expect(page.locator('[data-testid^="message-"]'))
      .toHaveCount(3, { timeout: 30000 });

    // Assert - Trace IDs displayed
    const traceIds = await page.locator('[data-testid^="trace-id-"]').allTextContents();
    expect(traceIds).toHaveLength(3);
    expect(traceIds.every(id => id.length >= 8)).toBeTruthy();
  });
});
```

---

**Document generated by BMad Test Architect - bmad-testarch-test-design workflow**
