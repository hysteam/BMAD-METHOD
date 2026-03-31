"""
Epic 3: Consultative Multi-Objective Decision Analysis Tests

Tests for:
- E3-T01: 多维风险研判报告生成 (Multi-dimensional Risk Assessment Report)
- E3-T02: Plan A/B/C 并行生成 (Parallel Plan Generation)
- E3-T03: 证据桥强制引用 (Evidence Bridge Mandatory Citation)

These tests validate the decision analysis and plan generation system.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import hashlib
import json


# =============================================================================
# Mock Classes for Decision Analysis
# =============================================================================

class PlanType:
    """Plan type enumeration"""
    PLAN_A_SAFETY = "plan_a_safety_first"
    PLAN_A_BALANCED = "plan_b_balanced"
    PLAN_C_MINIMAL = "plan_c_minimal"


class ReportStatus:
    """Report status enumeration"""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class EvidenceBridge:
    """Evidence bridge for mandatory citation validation"""

    def __init__(self):
        self.evidence_registry: Dict[str, Dict[str, Any]] = {}
        self.citation_log: List[Dict[str, str]] = []

    def register_evidence(
        self,
        evidence_id: str,
        evidence_type: str,
        source: str,
        content: Dict[str, Any]
    ):
        """Register evidence in the bridge"""
        self.evidence_registry[evidence_id] = {
            'id': evidence_id,
            'type': evidence_type,
            'source': source,
            'content': content,
            'registered_at': datetime.utcnow().isoformat()
        }

    def get_evidence(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve evidence by ID"""
        return self.evidence_registry.get(evidence_id)

    def log_citation(self, claim: str, evidence_id: str) -> bool:
        """Log a citation claim"""
        if evidence_id not in self.evidence_registry:
            return False

        self.citation_log.append({
            'claim': claim,
            'evidence_id': evidence_id,
            'cited_at': datetime.utcnow().isoformat()
        })
        return True

    def validate_citation(self, claim: str, evidence_id: str) -> Dict[str, Any]:
        """Validate a citation has proper evidence backing"""
        evidence = self.get_evidence(evidence_id)

        if not evidence:
            return {
                'is_valid': False,
                'reason': 'Evidence not found',
                'evidence_id': evidence_id
            }

        # Check if citation was logged
        citation_found = any(
            c['evidence_id'] == evidence_id and c['claim'] == claim
            for c in self.citation_log
        )

        return {
            'is_valid': citation_found,
            'reason': 'Valid citation' if citation_found else 'Citation not logged',
            'evidence': evidence
        }

    def get_uncited_claims(self, claims: List[str]) -> List[str]:
        """Get claims without proper citation"""
        cited_claims = {c['claim'] for c in self.citation_log}
        return [c for c in claims if c not in cited_claims]


class RiskAssessmentReport:
    """Multi-dimensional risk assessment report"""

    def __init__(
        self,
        report_id: str,
        scenario_id: str,
        risk_dimensions: Dict[str, Any]
    ):
        self.report_id = report_id
        self.scenario_id = scenario_id
        self.risk_dimensions = risk_dimensions
        self.created_at = datetime.utcnow()
        self.status = ReportStatus.DRAFT
        self.evidence_refs: List[str] = []

    def add_dimension(self, name: str, score: float, evidence_ids: List[str]):
        """Add risk dimension to report"""
        self.risk_dimensions[name] = {
            'score': score,
            'evidence_refs': evidence_ids,
            'assessed_at': datetime.utcnow().isoformat()
        }
        self.evidence_refs.extend(evidence_ids)

    def get_overall_risk_score(self) -> float:
        """Calculate overall risk score"""
        if not self.risk_dimensions:
            return 0.0

        scores = [d['score'] for d in self.risk_dimensions.values()]
        return sum(scores) / len(scores)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary"""
        return {
            'report_id': self.report_id,
            'scenario_id': self.scenario_id,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'risk_dimensions': self.risk_dimensions,
            'overall_risk_score': self.get_overall_risk_score(),
            'evidence_refs': list(set(self.evidence_refs))
        }


class PlanGenerator:
    """Parallel plan generator for Plan A/B/C"""

    def __init__(self, evidence_bridge: EvidenceBridge):
        self.evidence_bridge = evidence_bridge
        self.generated_plans: Dict[str, Dict[str, Any]] = {}

    def generate_parallel_plans(
        self,
        scenario_id: str,
        risk_report: RiskAssessmentReport
    ) -> Dict[str, Dict[str, Any]]:
        """Generate Plan A/B/C in parallel"""
        plans = {}

        # Plan A: Safety First
        plans[PlanType.PLAN_A_SAFETY] = self._generate_plan(
            plan_type=PlanType.PLAN_A_SAFETY,
            scenario_id=scenario_id,
            risk_report=risk_report,
            priority_weights={'safety': 0.7, 'roi': 0.2, 'minimal': 0.1}
        )

        # Plan B: Balanced
        plans[PlanType.PLAN_A_BALANCED] = self._generate_plan(
            plan_type=PlanType.PLAN_A_BALANCED,
            scenario_id=scenario_id,
            risk_report=risk_report,
            priority_weights={'safety': 0.4, 'roi': 0.4, 'minimal': 0.2}
        )

        # Plan C: Minimal Impact
        plans[PlanType.PLAN_C_MINIMAL] = self._generate_plan(
            plan_type=PlanType.PLAN_C_MINIMAL,
            scenario_id=scenario_id,
            risk_report=risk_report,
            priority_weights={'safety': 0.2, 'roi': 0.3, 'minimal': 0.5}
        )

        self.generated_plans = plans
        return plans

    def _generate_plan(
        self,
        plan_type: str,
        scenario_id: str,
        risk_report: RiskAssessmentReport,
        priority_weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate individual plan"""
        # Calculate plan score based on weights
        overall_risk = risk_report.get_overall_risk_score()

        safety_score = priority_weights['safety'] * (1.0 - overall_risk)
        roi_score = priority_weights['roi'] * 0.8  # Base ROI assumption
        minimal_score = priority_weights['minimal'] * 0.5

        plan_score = safety_score + roi_score + minimal_score

        plan = {
            'plan_id': f"{plan_type}_{scenario_id}",
            'plan_type': plan_type,
            'scenario_id': scenario_id,
            'priority_weights': priority_weights,
            'scores': {
                'safety': safety_score,
                'roi': roi_score,
                'minimal': minimal_score,
                'overall': plan_score
            },
            'recommendations': self._generate_recommendations(plan_type, priority_weights),
            'evidence_refs': list(set(risk_report.evidence_refs)),
            'generated_at': datetime.utcnow().isoformat()
        }

        # Log citations for evidence
        for ref in risk_report.evidence_refs:
            self.evidence_bridge.log_citation(
                f"Plan recommendation based on {ref}",
                ref
            )

        return plan

    def _generate_recommendations(
        self,
        plan_type: str,
        weights: Dict[str, float]
    ) -> List[str]:
        """Generate plan-specific recommendations"""
        recommendations = []

        if weights['safety'] >= 0.5:
            recommendations.append("优先保障人员安全，立即疏散高风险区域")
        if weights['roi'] >= 0.4:
            recommendations.append("平衡经济损失，优化资源配置")
        if weights['minimal'] >= 0.4:
            recommendations.append("最小化干预，监测态势发展")

        return recommendations


# =============================================================================
# E3-T01: 多维风险研判报告生成 Tests
# =============================================================================

class TestRiskAssessmentReport:
    """Tests for E3-T01: 多维风险研判报告生成"""

    @pytest.fixture
    def sample_risk_report(self) -> RiskAssessmentReport:
        """Create sample risk assessment report"""
        return RiskAssessmentReport(
            report_id="risk-report-001",
            scenario_id="flood-scenario-001",
            risk_dimensions={
                'hydrological': {
                    'score': 0.8,
                    'evidence_refs': ['PHYSICS_001'],
                    'assessed_at': datetime.utcnow().isoformat()
                }
            }
        )

    def test_create_risk_report(self, sample_risk_report):
        """Test creating risk assessment report"""
        assert sample_risk_report.report_id == "risk-report-001"
        assert sample_risk_report.scenario_id == "flood-scenario-001"
        assert sample_risk_report.status == ReportStatus.DRAFT

    def test_add_risk_dimension(self, sample_risk_report):
        """Test adding risk dimension to report"""
        sample_risk_report.add_dimension(
            name='economic',
            score=0.6,
            evidence_ids=['ECON_001', 'ECON_002']
        )

        assert 'economic' in sample_risk_report.risk_dimensions
        assert sample_risk_report.risk_dimensions['economic']['score'] == 0.6
        assert len(sample_risk_report.evidence_refs) == 2  # Only ECON_001 and ECON_002

    def test_calculate_overall_risk_score(self, sample_risk_report):
        """Test calculating overall risk score"""
        sample_risk_report.add_dimension('social', 0.7, ['SOCIAL_001'])
        sample_risk_report.add_dimension('infrastructure', 0.5, ['INFRA_001'])

        # Average of 0.8, 0.7, 0.5
        overall = sample_risk_report.get_overall_risk_score()
        assert 0.66 <= overall <= 0.67  # Approximately 2.0/3

    def test_report_to_dict(self, sample_risk_report):
        """Test converting report to dictionary"""
        # Add two dimensions for this test
        sample_risk_report.add_dimension('economic', 0.6, ['ECON_001'])
        sample_risk_report.add_dimension('social', 0.7, ['SOCIAL_001'])

        report_dict = sample_risk_report.to_dict()

        assert 'report_id' in report_dict
        assert 'risk_dimensions' in report_dict
        assert 'overall_risk_score' in report_dict
        assert 'evidence_refs' in report_dict
        assert len(report_dict['evidence_refs']) >= 2  # At least 2 evidence refs


# =============================================================================
# E3-T02: Plan A/B/C 并行生成 Tests
# =============================================================================

class TestParallelPlanGeneration:
    """Tests for E3-T02: Plan A/B/C 并行生成"""

    @pytest.fixture
    def evidence_bridge(self) -> EvidenceBridge:
        """Create evidence bridge"""
        bridge = EvidenceBridge()
        # Register some evidence
        bridge.register_evidence(
            evidence_id="PHYSICS_001",
            evidence_type="simulation",
            source="physics_sidecar",
            content={'flood_depth': 3.5}
        )
        bridge.register_evidence(
            evidence_id="CASE_001",
            evidence_type="historical",
            source="rag_corpus",
            content={'case_year': 2020}
        )
        return bridge

    @pytest.fixture
    def risk_report(self) -> RiskAssessmentReport:
        """Create risk report for plan generation"""
        report = RiskAssessmentReport(
            report_id="plan-risk-001",
            scenario_id="scenario-001",
            risk_dimensions={}
        )
        report.add_dimension('hydrological', 0.8, ['PHYSICS_001'])
        report.add_dimension('economic', 0.6, ['CASE_001'])
        return report

    def test_generate_parallel_plans(self, evidence_bridge, risk_report):
        """Test generating Plan A/B/C in parallel"""
        generator = PlanGenerator(evidence_bridge)
        plans = generator.generate_parallel_plans("scenario-001", risk_report)

        assert len(plans) == 3
        assert PlanType.PLAN_A_SAFETY in plans
        assert PlanType.PLAN_A_BALANCED in plans
        assert PlanType.PLAN_C_MINIMAL in plans

    def test_plan_a_safety_priority(self, evidence_bridge, risk_report):
        """Test Plan A prioritizes safety"""
        generator = PlanGenerator(evidence_bridge)
        plans = generator.generate_parallel_plans("scenario-001", risk_report)

        plan_a = plans[PlanType.PLAN_A_SAFETY]
        assert plan_a['priority_weights']['safety'] == 0.7
        assert plan_a['scores']['safety'] > plan_a['scores']['roi']

    def test_plan_b_balanced(self, evidence_bridge, risk_report):
        """Test Plan B has balanced priorities"""
        generator = PlanGenerator(evidence_bridge)
        plans = generator.generate_parallel_plans("scenario-001", risk_report)

        plan_b = plans[PlanType.PLAN_A_BALANCED]
        assert plan_b['priority_weights']['safety'] == 0.4
        assert plan_b['priority_weights']['roi'] == 0.4
        assert abs(plan_b['priority_weights']['safety'] - plan_b['priority_weights']['roi']) < 0.01

    def test_plan_c_minimal_impact(self, evidence_bridge, risk_report):
        """Test Plan C minimizes intervention"""
        generator = PlanGenerator(evidence_bridge)
        plans = generator.generate_parallel_plans("scenario-001", risk_report)

        plan_c = plans[PlanType.PLAN_C_MINIMAL]
        assert plan_c['priority_weights']['minimal'] == 0.5
        assert plan_c['priority_weights']['safety'] == 0.2

    def test_plan_recommendations_generation(self, evidence_bridge, risk_report):
        """Test plan-specific recommendations"""
        generator = PlanGenerator(evidence_bridge)
        plans = generator.generate_parallel_plans("scenario-001", risk_report)

        plan_a = plans[PlanType.PLAN_A_SAFETY]
        assert "优先保障人员安全" in plan_a['recommendations'][0]

        plan_b = plans[PlanType.PLAN_A_BALANCED]
        assert "平衡经济损失" in plan_b['recommendations'][0]

    def test_plan_evidence_references(self, evidence_bridge, risk_report):
        """Test plans include evidence references"""
        generator = PlanGenerator(evidence_bridge)
        plans = generator.generate_parallel_plans("scenario-001", risk_report)

        for plan_type, plan in plans.items():
            assert 'evidence_refs' in plan
            assert len(plan['evidence_refs']) >= 2
            assert 'PHYSICS_001' in plan['evidence_refs']


# =============================================================================
# E3-T03: 证据桥强制引用 Tests
# =============================================================================

class TestEvidenceBridgeCitation:
    """Tests for E3-T03: 证据桥强制引用"""

    @pytest.fixture
    def evidence_bridge(self) -> EvidenceBridge:
        """Create evidence bridge"""
        bridge = EvidenceBridge()

        # Register evidence
        bridge.register_evidence(
            evidence_id="EVID_001",
            evidence_type="physics",
            source="simulation",
            content={'depth': 3.5}
        )
        bridge.register_evidence(
            evidence_id="EVID_002",
            evidence_type="historical",
            source="rag",
            content={'year': 2020}
        )

        return bridge

    @pytest.fixture
    def risk_report_for_citation(self) -> RiskAssessmentReport:
        """Create risk report for citation tests"""
        report = RiskAssessmentReport(
            report_id="citation-risk-001",
            scenario_id="scenario-001",
            risk_dimensions={}
        )
        report.add_dimension('hydrological', 0.8, ['EVID_001'])
        report.add_dimension('economic', 0.6, ['EVID_002'])
        return report

    def test_register_evidence(self, evidence_bridge):
        """Test registering evidence in bridge"""
        assert evidence_bridge.get_evidence("EVID_001") is not None
        assert evidence_bridge.get_evidence("EVID_001")['type'] == 'physics'

    def test_log_citation(self, evidence_bridge):
        """Test logging a citation"""
        result = evidence_bridge.log_citation(
            claim="预测水位 3.5 米",
            evidence_id="EVID_001"
        )

        assert result is True
        assert len(evidence_bridge.citation_log) == 1

    def test_validate_citation(self, evidence_bridge):
        """Test validating a citation"""
        # Log citation first
        evidence_bridge.log_citation(
            claim="预测水位 3.5 米",
            evidence_id="EVID_001"
        )

        # Validate
        result = evidence_bridge.validate_citation(
            claim="预测水位 3.5 米",
            evidence_id="EVID_001"
        )

        assert result['is_valid'] is True
        assert result['evidence'] is not None

    def test_validate_missing_evidence(self, evidence_bridge):
        """Test validation fails for missing evidence"""
        result = evidence_bridge.validate_citation(
            claim="Some claim",
            evidence_id="NONEXISTENT"
        )

        assert result['is_valid'] is False
        assert result['reason'] == 'Evidence not found'

    def test_get_uncited_claims(self, evidence_bridge):
        """Test getting uncited claims"""
        # Log one citation
        evidence_bridge.log_citation(
            claim="Claim with evidence",
            evidence_id="EVID_001"
        )

        all_claims = ["Claim with evidence", "Claim without evidence"]
        uncited = evidence_bridge.get_uncited_claims(all_claims)

        assert len(uncited) == 1
        assert "Claim without evidence" in uncited

    def test_citation_required_for_plan(self, evidence_bridge, risk_report_for_citation):
        """Test that plans must cite evidence"""
        generator = PlanGenerator(evidence_bridge)
        plans = generator.generate_parallel_plans("scenario-001", risk_report_for_citation)

        # Verify citations were logged
        assert len(evidence_bridge.citation_log) > 0

        # Verify each plan has evidence refs
        for plan in plans.values():
            assert len(plan['evidence_refs']) > 0


# =============================================================================
# Integration Tests: Decision Analysis Pipeline
# =============================================================================

class TestDecisionAnalysisPipeline:
    """Integration tests for complete decision analysis pipeline"""

    def test_full_decision_workflow(self):
        """Test complete workflow: Risk Report -> Plans -> Citation Validation"""
        # Step 1: Create evidence bridge
        evidence_bridge = EvidenceBridge()
        evidence_bridge.register_evidence(
            evidence_id="PHYSICS_001",
            evidence_type="simulation",
            source="physics_sidecar",
            content={'flood_depth': 4.0, 'area_km2': 50.0}
        )
        evidence_bridge.register_evidence(
            evidence_id="CASE_2020_001",
            evidence_type="historical",
            source="rag_corpus",
            content={'year': 2020, 'location': 'Beijing'}
        )

        # Step 2: Generate risk assessment report
        risk_report = RiskAssessmentReport(
            report_id="integration-risk-001",
            scenario_id="integration-scenario-001",
            risk_dimensions={}
        )
        risk_report.add_dimension('hydrological', 0.85, ['PHYSICS_001'])
        risk_report.add_dimension('economic', 0.65, ['CASE_2020_001'])
        risk_report.add_dimension('social', 0.70, ['CASE_2020_001'])

        assert risk_report.get_overall_risk_score() > 0.7

        # Step 3: Generate parallel plans
        generator = PlanGenerator(evidence_bridge)
        plans = generator.generate_parallel_plans("integration-scenario-001", risk_report)

        assert len(plans) == 3
        assert all('evidence_refs' in p for p in plans.values())

        # Step 4: Validate all citations
        for claim in ["Plan recommendation based on PHYSICS_001"]:
            result = evidence_bridge.validate_citation(claim, "PHYSICS_001")
            assert result['is_valid'] is True

    def test_consultative_report_generation(self):
        """Test generating complete consultative report"""
        evidence_bridge = EvidenceBridge()

        # Register evidence
        for i in range(3):
            evidence_bridge.register_evidence(
                evidence_id=f"EVID_{i:03d}",
                evidence_type="mixed",
                source="system",
                content={'index': i}
            )

        # Create risk report
        report = RiskAssessmentReport(
            report_id="consult-report-001",
            scenario_id="scenario-001",
            risk_dimensions={}
        )
        report.add_dimension('hydrological', 0.8, ['EVID_000'])
        report.add_dimension('economic', 0.6, ['EVID_001'])
        report.add_dimension('social', 0.7, ['EVID_002'])

        # Generate plans
        generator = PlanGenerator(evidence_bridge)
        plans = generator.generate_parallel_plans("scenario-001", report)

        # Build consultative report
        consult_report = {
            'report_id': 'consult-report-001',
            'risk_assessment': report.to_dict(),
            'plans': plans,
            'recommendation': max(
                plans.keys(),
                key=lambda k: plans[k]['scores']['overall']
            ),
            'evidence_summary': {
                'total_evidence': len(evidence_bridge.evidence_registry),
                'total_citations': len(evidence_bridge.citation_log)
            }
        }

        assert consult_report['recommendation'] is not None
        assert consult_report['evidence_summary']['total_citations'] > 0


# =============================================================================
# Evidence Void Detection Tests
# =============================================================================

class TestEvidenceVoidDetection:
    """Tests for evidence void detection (EVIDENCE_VOID flag)"""

    def test_detect_evidence_void(self):
        """Test detecting claims without evidence"""
        bridge = EvidenceBridge()

        # Register one piece of evidence
        bridge.register_evidence(
            evidence_id="VALID_001",
            evidence_type="physics",
            source="simulation",
            content={}
        )

        # Try to validate claim without proper citation
        result = bridge.validate_citation(
            claim="水位将达到 5 米",
            evidence_id="NONEXISTENT"
        )

        assert result['is_valid'] is False

    def test_flag_unsupported_recommendations(self):
        """Test flagging recommendations without evidence"""
        bridge = EvidenceBridge()

        claims = [
            "建议立即疏散 (有证据)",
            "建议开闸泄洪 (无证据)"
        ]

        # Only cite first claim
        bridge.register_evidence("EVID_001", "official", "gov", {})
        bridge.log_citation(claims[0], "EVID_001")

        uncited = bridge.get_uncited_claims(claims)

        assert len(uncited) == 1
        assert "建议开闸泄洪 (无证据)" in uncited
