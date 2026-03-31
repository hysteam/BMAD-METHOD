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

# Test Design for Architecture: 洪涝灾害 AI 协同辅助决策系统

**Purpose:** Architectural concerns, testability gaps, and NFR requirements for review by Architecture/Dev teams. Serves as a contract between QA and Engineering on what must be addressed before test development begins.

**Date:** 2026-03-31
**Author:** BMad Test Architect
**Status:** Architecture Review Pending
**Project:** BMAD-METHOD (洪涝灾害智能体系统)
**PRD Reference:** `_bmad-output/planning-artifacts/prd.md` (V2.0)
**ADR Reference:** `_bmad-output/planning-artifacts/architecture.md`

---

## Executive Summary

**Scope:** System-level test design for AI-powered flood emergency decision support system with multi-agent debate, physics simulation coupling, and real-time evidence streaming.

**Business Context** (from PRD):

- **Revenue/Impact:** Life-safety critical system for emergency response optimization
- **Problem:** Reduce decision time from warning to SOP issuance from hours to <10 minutes
- **GA Launch:** Target V1.0-CLI validation by Q2 2026

**Architecture** (from ADR):

- **Key Decision 1:** MACP v1.0 Protocol for all inter-agent communication (SDP/DCP/VIAP separation)
- **Key Decision 2:** DEMS v1.0 Data Element Master Schema for semantic consistency
- **Key Decision 3:** Stack: Python (LangGraph), React/Mapbox, Godunov Physics Solver, Redis Pub/Sub
- **Key Decision 4:** Evidence Bridge with SHA-256 physical fingerprints for AI decisions

**Expected Scale** (from ADR):

- 100+ concurrent agent connections
- 90-second physics feedback SLA (60-min preview)
- 10-minute end-to-end decision workflow
- 99% agent availability target
- 16GB RAM resource constraints (single-machine deployment)

**Risk Summary:**

- **Total risks**: 12
- **High-priority (≥6)**: 4 risks requiring immediate mitigation
- **Test effort**: ~85 tests (~4-6 weeks for 1 QA, ~2-3 weeks for 2 QAs)

---

## Quick Guide

### 🚨 BLOCKERS - Team Must Decide (Can't Proceed Without)

**Pre-Implementation Critical Path** - These MUST be completed before QA can write integration tests:

1. **BLK-01: MACP Protocol Implementation** - Complete VIAP validator middleware with schema enforcement (recommended owner: Backend Team)
2. **BLK-02: Physics Simulation Interface** - Abstract physics interface with dependency injection for test mocking (recommended owner: Physics Team)
3. **BLK-03: Semantic Gateway** - Complete DEMS translation layer before AI agent integration tests (recommended owner: Backend Team)
4. **BLK-04: Evidence Trace ID Infrastructure** - Implement trace ID propagation middleware across all layers (recommended owner: Fullstack Team)

**What we need from team:** Complete these 4 items pre-implementation or test development is blocked.

---

### ⚠️ HIGH PRIORITY - Team Should Validate (We Provide Recommendation, You Approve)

1. **R-01: LLM API Unavailability** - Implement RAG fallback with circuit breaker pattern (implementation phase: Sprint 1)
2. **R-02: Physics Timeout Handling** - Progressive mesh coarsening with early termination (implementation phase: Sprint 2)
3. **R-05: Cascading Data Conflict** - Event buffering with cascade operator validation (implementation phase: Sprint 3)
4. **R-12: Physical Conservation Violation** - Dimensional analysis firewall middleware (implementation phase: Sprint 4)

**What we need from team:** Review recommendations and approve (or suggest changes).

---

### 📋 INFO ONLY - Solutions Provided (Review, No Decisions Needed)

1. **Test strategy**: System-level test design with 4-level test pyramid (Unit → Integration → E2E → Performance)
2. **Tooling**: pytest (backend), Playwright (frontend), custom physics harness, chaos testing framework
3. **Tiered CI/CD**: PR (P0/P1, 15-25min), Nightly (E2E/Perf, 45-60min), Weekly (Chaos/Burn-in, 60min)
4. **Coverage**: ~85 test scenarios prioritized P0-P3 with risk-based classification
5. **Quality gates**: P0=100%, P1≥95%, Coverage≥80%, Security=100%

**What we need from team:** Just review and acknowledge (we already have the solution).

---

## For Architects and Devs - Open Topics 👷

### Risk Assessment

**Total risks identified**: 12 (4 high-priority score ≥6, 7 medium, 1 low)

#### High-Priority Risks (Score ≥6) - IMMEDIATE ATTENTION

| Risk ID    | Category  | Description   | Probability | Impact | Score       | Mitigation            | Owner   | Timeline |
| ---------- | --------- | ------------- | ----------- | ------ | ----------- | --------------------- | ------- | -------- |
| **R-01** | **TECH** | DeepSeek API outages block all decision-making | 2 | 3 | **6** | RAG fallback mode with historical evidence; circuit breaker pattern | Backend | Sprint 1 |
| **R-02** | **PERF** | Godunov solver exceeds 90-second SLA | 2 | 3 | **6** | Progressive mesh coarsening; early termination with degraded fidelity | Physics | Sprint 2 |
| **R-05** | **DATA** | DGM signal conflicts with physical simulation state | 2 | 3 | **6** | Event buffering; cascade operator validation | Architecture | Sprint 3 |
| **R-12** | **SEC** | Red team injects impossible parameters violating physical laws | 2 | 3 | **6** | Dimensional analysis firewall; physics常识校验 middleware | Security | Sprint 4 |

#### Medium-Priority Risks (Score 3-5)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
|---------|----------|-------------|-------------|--------|-------|------------|-------|----------|
| R-03 | TECH | MACP Protocol Violation | 2 | 2 | 4 | VIAP validator middleware; schema-first code generation | Backend | Sprint 1 |
| R-04 | PERF | Memory Exhaustion (16GB RAM) | 2 | 2 | 4 | Docker memory limits; monitoring and alerting | DevOps | Sprint 1 |
| R-06 | TECH | Socket.io Connection Loss | 2 | 2 | 4 | Reconnection logic with backpressure; caching | Frontend | Sprint 1 |
| R-07 | DATA | Evidence Trace ID Loss | 2 | 2 | 4 | Middleware-level trace injection; assertions | Backend | Sprint 2 |
| R-09 | DATA | Rescue Team "Ghost Resource" | 2 | 2 | 4 | Resource exclusivity bus; dynamic obstacle injection | Simulation | Sprint 3 |
| R-10 | DATA | Precision Mismatch (sub-meter vs 30m) | 2 | 2 | 4 | Precision degradation operator; semantic smoothing | Architecture | Sprint 2 |
| R-11 | BUS | Cognitive Dissonance (RAG vs physics) | 2 | 2 | 4 | Evidence weighting model; physics-dominant rules | AI | Sprint 3 |

#### Low-Priority Risks (Score ≤3)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
|---------|----------|-------------|-------------|--------|-------|------------|-------|----------|
| R-08 | SEC | SOP Execution Without Confirmation | 1 | 3 | 3 | UI confirmation dialogs; backend confirmation tokens | Fullstack | Sprint 4 |

---

## Testability Review

### 🚨 Testability Concerns (Actionable Issues)

| ID | Concern | Impact | Mitigation | Priority |
|----|---------|--------|------------|----------|
| **T-01** | LLM Non-Determinism | High | Mock LLM for unit/integration; real LLM for E2E with tolerant assertions | P0 |
| **T-02** | Physics Simulation Coupling | High | Dependency injection; recorded snapshots for replay | P0 |
| **T-03** | MACP Protocol Complexity | Medium | Schema-based property testing; contract testing | P1 |
| **T-04** | Real-Time Socket Events | Medium | socket.io-mock; record/replay sequences | P1 |
| **T-05** | Multi-Agent Concurrency | Medium | Deterministic round-robin scheduling; logical clocks | P1 |
| **T-06** | Evidence Trace ID Propagation | Medium | Trace ID validation middleware; completeness checks | P1 |
| **T-07** | Resource Contention | Low | Docker Compose profiles; resource budget testing | P2 |

### ✅ Testability Strengths (Existing Advantages)

| Strength | Description | Test Benefit |
|----------|-------------|--------------|
| MACP Explicit State | All agent state in MACP SDP field | Easy state seeding and verification |
| Semantic Gateway | Single translation layer | Clear boundary for integration tests |
| Evidence Bridge | SHA-256 physical fingerprints | Deterministic validation |
| Idempotent Nodes | LangGraph nodes stateless/idempotent | Repeatable tests without complex cleanup |
| Redis Pub/Sub Bus | Centralized event bus | Easy record/replay for testing |
| Existing CI/CD | GitHub Actions with sharding | Fast feedback loop |

---

## Quality Gates & Entry/Exit Criteria

### Phase Entry Criteria (Inception → Implementation)

| Criterion | Threshold | Owner |
|-----------|-----------|-------|
| PRD Approved | V2.0 signed off | PM |
| Architecture Review | ADR approved with testability concerns addressed | Architecture |
| Test Design Complete | This document reviewed and approved | QA Lead |
| Blockers Resolved | All BLK items complete | Dev Lead |

### Phase Exit Criteria (Implementation → Release)

| Criterion | Threshold | Owner |
|-----------|-----------|-------|
| P0 Tests | 100% pass | QA |
| P1 Tests | ≥95% pass | QA |
| Code Coverage | ≥80% | Dev |
| Performance SLA | 10-min decision, 90-sec physics | QA + Perf |
| Security Tests | 100% pass | Security |
| High-Risk Mitigation | All 4 high risks mitigated | All Teams |

---

## NFR Test Requirements

| NFR | Target | Test Method | Owner |
|-----|--------|-------------|-------|
| **Decision Speed** | <10 min (warning → SOP) | E2E timing test with stopwatch | QA |
| **Physics Feedback** | <90 sec (60-min preview) | Performance benchmark | Physics |
| **Agent Availability** | >99% online rate | Chaos testing with failure injection | Backend |
| **Evidence Traceability** | 100% MACP with Trace ID | Integration test assertions | Backend |
| **Defensive Blocking** | 100% high-risk pre-simulated | Security test scenarios | Security |
| **Data Quality** | >95 points (SL/T 860-2026) | Validation test suite | Data |

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

## Completion Report

**Mode Used:** System-Level Test Design (Phase 3)

**Output Files:**
- `test-artifacts/test-design-architecture.md` (this document)
- `test-artifacts/test-design-qa.md` (companion QA execution doc)

**Key Risks:**
- 4 High-priority risks (R-01, R-02, R-05, R-12) requiring Sprint 1-4 mitigation
- 7 Medium-priority risks to be addressed in implementation
- 1 Low-priority risk accepted with monitoring

**Quality Gate Thresholds:**
- P0 Pass Rate: 100% (CI Blocker)
- P1 Pass Rate: ≥95% (CI Warning)
- Code Coverage: ≥80% (CI Blocker)
- Performance SLA: 10-min decision, 90-sec physics
- Security Tests: 100% pass

**Open Assumptions:**
1. DeepSeek API availability assumed for E2E tests (mock for unit/integration)
2. Physics simulation environment available for integration testing
3. WSL2 Docker environment for local test execution
4. Test data factories to be built for MACP message generation

---

**Next Steps:**
1. Architecture team reviews and approves this document
2. Blocker items (BLK-01 to BLK-04) assigned to owners
3. QA team proceeds with test implementation per `test-design-qa.md`
4. CI/CD pipeline updated with quality gates

---

*Document generated by BMad Test Architect - bmad-testarch-test-design workflow*
