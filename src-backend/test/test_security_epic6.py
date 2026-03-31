"""
Epic 6: Security and Safety Tests

Tests for:
- E6-T03: 红蓝对抗引擎拦截 (Red Team Interception)
- E6-T04: 违反水利标准拦截 (Water Standard Compliance)
- E6-T05: 防御性指令阻断协议 (Defensive Blocking)
- E6-T06: 双重签名验证 (Dual Signature Verification)

These tests define the security interface requirements before implementation.
"""

import pytest
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
import hashlib
import hmac

from src.mas.protocol.schema import (
    MACPMessage, MACPHeader, MACPBody, AgentType,
    MessageStance, MessagePriority
)
from src.mas.protocol.validator import VIAPValidator, ValidationError


# =============================================================================
# Security Types and Classes (To be moved to src/mas/security/*.py)
# =============================================================================

class RiskLevel(str, Enum):
    """Risk levels for command classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WaterStandardViolation(Exception):
    """Raised when a command violates national water standards"""
    pass


class RemonstranceLock:
    """
    谏阻锁 (Remonstrance Lock) - 90-second physics preview blocking

    Implements E6-T05: 防御性指令阻断协议

    Before any high-risk SOP can be executed, the system must:
    1. Run 90-second physics simulation preview
    2. Show consequences to commander
    3. Require explicit confirmation
    """

    def __init__(self, preview_seconds: int = 90):
        self.preview_seconds = preview_seconds
        self._pending_commands: Dict[str, Dict[str, Any]] = {}

    def request_execution(self, command: str, trace_id: str) -> str:
        """
        Request to execute a high-risk command

        Returns a pending command ID for tracking
        """
        pending_id = hashlib.sha256(
            f"{command}:{trace_id}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

        self._pending_commands[pending_id] = {
            'command': command,
            'trace_id': trace_id,
            'requested_at': datetime.utcnow(),
            'status': 'pending_preview',
            'physics_preview_complete': False,
            'commander_confirmed': False
        }

        return pending_id

    def complete_physics_preview(self, pending_id: str, preview_result: Dict[str, Any]):
        """Mark physics preview as complete"""
        if pending_id not in self._pending_commands:
            raise ValueError(f"Unknown pending command: {pending_id}")

        self._pending_commands[pending_id]['physics_preview_complete'] = True
        self._pending_commands[pending_id]['preview_result'] = preview_result

    def confirm_command(self, pending_id: str, commander_signature: str) -> bool:
        """
        Commander confirms the command after physics preview

        Requires explicit confirmation (dual signature for critical commands)
        """
        if pending_id not in self._pending_commands:
            return False

        cmd = self._pending_commands[pending_id]

        # Check physics preview completed
        if not cmd['physics_preview_complete']:
            raise ValueError("Physics preview not completed. Cannot confirm.")

        # Verify signature
        expected_signature = self._generate_signature(
            cmd['command'],
            cmd['trace_id']
        )

        if commander_signature != expected_signature:
            return False

        cmd['commander_confirmed'] = True
        cmd['confirmed_at'] = datetime.utcnow()
        cmd['status'] = 'ready_for_execution'

        return True

    def can_execute(self, pending_id: str) -> bool:
        """Check if command is ready for execution"""
        if pending_id not in self._pending_commands:
            return False

        cmd = self._pending_commands[pending_id]
        return (
            cmd['physics_preview_complete'] and
            cmd['commander_confirmed'] and
            cmd['status'] == 'ready_for_execution'
        )

    def _generate_signature(self, command: str, trace_id: str) -> str:
        """Generate expected signature for verification"""
        # In production, this would use HMAC with a secret key
        data = f"{command}:{trace_id}:CONFIRM"
        return hashlib.sha256(data.encode()).hexdigest()[:32]


class RedTeamEngine:
    """
    红蓝对抗引擎 - Automatically intercept dangerous commands

    Implements E6-T03: 红蓝对抗引擎拦截
    """

    # Patterns that trigger automatic interception
    DANGEROUS_PATTERNS = [
        'immediate evacuation without notice',
        'destroy dam',
        'flood zone',
        'bypass safety',
        'ignore standard',
        'override protocol',
    ]

    # National water standard codes (GB/T standards)
    WATER_STANDARDS = {
        'GB/T 50095-2014': '水文基本术语和符号标准',
        'SL 252-2017': '水利水电工程等级划分及洪水标准',
        'GB 50286-2013': '堤防工程设计规范',
    }

    def __init__(self):
        self.intercepted_count = 0
        self._intercept_log: List[Dict[str, Any]] = []

    def analyze_command(self, message: MACPMessage) -> Dict[str, Any]:
        """
        Analyze a command message for potential violations

        Returns analysis result with risk assessment
        """
        content = message.body.content.lower()

        risks = []
        violations = []

        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in content:
                risks.append({
                    'type': 'dangerous_pattern',
                    'pattern': pattern,
                    'severity': 'high'
                })

        # Check for standard violations
        for std_code, std_name in self.WATER_STANDARDS.items():
            if self._check_standard_violation(content, std_code):
                violations.append({
                    'type': 'standard_violation',
                    'standard': std_code,
                    'name': std_name,
                    'severity': 'critical'
                })

        # Check for physical impossibility
        if self._check_physical_impossibility(message):
            risks.append({
                'type': 'physical_impossibility',
                'severity': 'critical'
            })

        return {
            'message_id': message.message_id,
            'trace_id': message.header.trace_id,
            'risk_level': self._calculate_risk_level(risks, violations),
            'risks': risks,
            'violations': violations,
            'should_intercept': (
                len(violations) > 0 or
                any(r['severity'] == 'critical' for r in risks) or
                any(r['type'] == 'dangerous_pattern' for r in risks)
            ),
            'analyzed_at': datetime.utcnow()
        }

    def should_intercept(self, message: MACPMessage) -> bool:
        """Check if message should be intercepted"""
        analysis = self.analyze_command(message)
        return analysis['should_intercept']

    def intercept(self, message: MACPMessage, reason: str) -> Dict[str, Any]:
        """
        Intercept a dangerous command

        Logs the interception and returns interception record
        """
        self.intercepted_count += 1

        record = {
            'interception_id': f"INT-{self.intercepted_count:04d}",
            'message_id': message.message_id,
            'trace_id': message.header.trace_id,
            'agent_id': message.header.agent_id,
            'agent_type': message.header.agent_type,
            'reason': reason,
            'intercepted_at': datetime.utcnow(),
            'status': 'blocked'
        }

        self._intercept_log.append(record)
        return record

    def _check_standard_violation(self, content: str, std_code: str) -> bool:
        """Check if content suggests violation of a water standard"""
        # Simplified check - in production would use NLP and rule engine
        violation_keywords = {
            'SL 252-2017': ['ignore flood level', 'exceed dam capacity'],
            'GB 50286-2013': ['bypass dike design', 'ignore embankment'],
        }

        keywords = violation_keywords.get(std_code, [])
        return any(kw in content for kw in keywords)

    def _check_physical_impossibility(self, message: MACPMessage) -> bool:
        """Check for physically impossible claims"""
        # Check for inclination/physics mismatches
        # E.g., claiming 100% safety with 0.1 inclination
        if message.body.inclination < 0.2 and message.body.confidence > 0.99:
            return True

        # Check for impossible flow rates, water levels, etc.
        content = message.body.content

        # Pattern: "100% safe" or "zero risk"
        if '100% safe' in content or 'zero risk' in content or '无风险' in content:
            return True

        return False

    def _calculate_risk_level(self, risks: list, violations: list) -> RiskLevel:
        """Calculate overall risk level"""
        if any(v['severity'] == 'critical' for v in violations):
            return RiskLevel.CRITICAL

        if any(r['severity'] == 'critical' for r in risks):
            return RiskLevel.CRITICAL

        if len(violations) > 0 or any(r['severity'] == 'high' for r in risks):
            return RiskLevel.HIGH

        if len(risks) > 2:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW


class DualSignatureVerifier:
    """
    双重签名验证 - Require two authorized signatures for critical commands

    Implements E6-T06: 双重签名验证
    """

    def __init__(self, secret_key: bytes = None):
        self.secret_key = secret_key or b"test-secret-key-for-development"

    def sign(self, command: str, user_id: str) -> str:
        """Generate HMAC signature for command"""
        message = f"{command}:{user_id}"
        signature = hmac.new(
            self.secret_key,
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    def verify(self, command: str, user_id: str, signature: str) -> bool:
        """Verify HMAC signature"""
        expected = self.sign(command, user_id)
        return hmac.compare_digest(signature, expected)

    def require_dual_signature(
        self,
        command: str,
        user1_id: str,
        user1_sig: str,
        user2_id: str,
        user2_sig: str
    ) -> bool:
        """
        Verify both signatures for critical command

        Both signatures must be valid and from different users
        """
        # Check users are different
        if user1_id == user2_id:
            return False

        # Verify both signatures
        sig1_valid = self.verify(command, user1_id, user1_sig)
        sig2_valid = self.verify(command, user2_id, user2_sig)

        return sig1_valid and sig2_valid


# =============================================================================
# E6-T03: 红蓝对抗引擎拦截 Tests
# =============================================================================

class TestRedTeamInterception:
    """Tests for E6-T03: 红蓝对抗引擎拦截"""

    @pytest.fixture
    def red_team_engine(self):
        """Create red team engine instance"""
        return RedTeamEngine()

    def test_intercept_dangerous_pattern(self, red_team_engine):
        """Test interception of dangerous pattern commands"""
        message = MACPMessage(
            header=MACPHeader(
                trace_id="trace-red-team-001",
                agent_id="agent-001",
                agent_type=AgentType.COMMAND
            ),
            body=MACPBody(
                content="建议立即执行：immediate evacuation without notice to zone A",
                inclination=0.9,
                confidence=0.85,
                stance=MessageStance.SUPPORT,
                evidence_refs=["CASE_2020_001"]
            )
        )

        # Should intercept
        assert red_team_engine.should_intercept(message) is True

        # Perform interception
        record = red_team_engine.intercept(
            message,
            reason="Contains dangerous pattern: immediate evacuation without notice"
        )

        assert record['interception_id'].startswith("INT-")
        assert record['status'] == 'blocked'
        assert record['trace_id'] == "trace-red-team-001"

    def test_intercept_standard_violation(self, red_team_engine):
        """Test interception of water standard violations"""
        message = MACPMessage(
            header=MACPHeader(
                trace_id="trace-red-team-002",
                agent_id="agent-002",
                agent_type=AgentType.COMMAND
            ),
            body=MACPBody(
                content="建议 ignore flood level standards and proceed with construction",
                inclination=0.7,
                confidence=0.8,
                stance=MessageStance.SUPPORT,
                evidence_refs=["RAG_001"]
            )
        )

        analysis = red_team_engine.analyze_command(message)

        assert analysis['should_intercept'] is True
        assert len(analysis['violations']) > 0
        assert any(v['type'] == 'standard_violation' for v in analysis['violations'])

    def test_allow_safe_command(self, red_team_engine):
        """Test that safe commands pass through"""
        message = MACPMessage(
            header=MACPHeader(
                trace_id="trace-safe-001",
                agent_id="agent-003",
                agent_type=AgentType.HYDROLOGY
            ),
            body=MACPBody(
                content="建议继续监测水位变化，每小时报告一次数据",
                inclination=0.5,
                confidence=0.7,
                stance=MessageStance.NEUTRAL,
                evidence_refs=["MONITORING_001"]
            )
        )

        assert red_team_engine.should_intercept(message) is False


# =============================================================================
# E6-T04: 违反水利标准拦截 Tests
# =============================================================================

class TestWaterStandardCompliance:
    """Tests for E6-T04: 违反水利标准拦截"""

    @pytest.fixture
    def red_team_engine(self):
        """Create red team engine for standard checks"""
        return RedTeamEngine()

    def test_violation_sl_252_2017(self, red_team_engine):
        """Test detection of SL 252-2017 violation"""
        message = MACPMessage(
            header=MACPHeader(
                trace_id="trace-std-001",
                agent_id="agent-std-001",
                agent_type=AgentType.COMMAND
            ),
            body=MACPBody(
                content="建议 ignore flood level and exceed dam capacity for testing",
                inclination=0.8,
                confidence=0.9,
                stance=MessageStance.SUPPORT,
                evidence_refs=[]
            )
        )

        analysis = red_team_engine.analyze_command(message)

        # Should detect SL 252-2017 violation
        assert any(
            v['standard'] == 'SL 252-2017'
            for v in analysis['violations']
        )

    def test_violation_gb_50286_2013(self, red_team_engine):
        """Test detection of GB 50286-2013 violation"""
        message = MACPMessage(
            header=MACPHeader(
                trace_id="trace-std-002",
                agent_id="agent-std-002",
                agent_type=AgentType.COMMAND
            ),
            body=MACPBody(
                content="建议 bypass dike design and ignore embankment protocols",
                inclination=0.75,
                confidence=0.85,
                stance=MessageStance.SUPPORT,
                evidence_refs=[]
            )
        )

        analysis = red_team_engine.analyze_command(message)

        assert any(
            v['standard'] == 'GB 50286-2013'
            for v in analysis['violations']
        )


# =============================================================================
# E6-T05: 防御性指令阻断协议 Tests (Remonstrance Lock)
# =============================================================================

class TestDefensiveBlocking:
    """Tests for E6-T05: 防御性指令阻断协议"""

    @pytest.fixture
    def remonstrance_lock(self):
        """Create remonstrance lock instance"""
        return RemonstranceLock(preview_seconds=90)

    def test_request_execution_creates_pending(self, remonstrance_lock):
        """Test that requesting execution creates pending command"""
        pending_id = remonstrance_lock.request_execution(
            command="启动一级应急响应",
            trace_id="trace-block-001"
        )

        assert pending_id is not None
        assert len(pending_id) == 16
        assert remonstrance_lock.can_execute(pending_id) is False

    def test_cannot_execute_without_physics_preview(self, remonstrance_lock):
        """Test that command cannot execute without physics preview"""
        pending_id = remonstrance_lock.request_execution(
            command="启动一级应急响应",
            trace_id="trace-block-002"
        )

        # Should not be executable
        assert remonstrance_lock.can_execute(pending_id) is False

        # Attempting to confirm should fail
        signature = remonstrance_lock._generate_signature(
            "启动一级应急响应",
            "trace-block-002"
        )

        with pytest.raises(ValueError, match="Physics preview not completed"):
            remonstrance_lock.confirm_command(pending_id, signature)

    def test_complete_workflow_with_physics_preview(self, remonstrance_lock):
        """Test complete workflow: request -> preview -> confirm -> execute"""
        pending_id = remonstrance_lock.request_execution(
            command="启动一级应急响应",
            trace_id="trace-block-003"
        )

        # Complete physics preview
        remonstrance_lock.complete_physics_preview(pending_id, {
            'flood_depth': 2.5,
            'affected_area_km2': 150,
            'evacuation_needed': 50000
        })

        # Still not executable without confirmation
        assert remonstrance_lock.can_execute(pending_id) is False

        # Commander confirms
        signature = remonstrance_lock._generate_signature(
            "启动一级应急响应",
            "trace-block-003"
        )
        result = remonstrance_lock.confirm_command(pending_id, signature)

        assert result is True
        assert remonstrance_lock.can_execute(pending_id) is True


# =============================================================================
# E6-T06: 双重签名验证 Tests
# =============================================================================

class TestDualSignatureVerification:
    """Tests for E6-T06: 双重签名验证"""

    @pytest.fixture
    def verifier(self):
        """Create dual signature verifier"""
        return DualSignatureVerifier()

    def test_single_signature_valid(self, verifier):
        """Test single signature verification"""
        command = "启动一级应急响应"
        user_id = "commander-001"

        signature = verifier.sign(command, user_id)

        assert verifier.verify(command, user_id, signature) is True

    def test_single_signature_invalid(self, verifier):
        """Test invalid signature detection"""
        command = "启动一级应急响应"
        user_id = "commander-001"
        fake_signature = "fake-signature-12345"

        assert verifier.verify(command, user_id, fake_signature) is False

    def test_dual_signature_success(self, verifier):
        """Test successful dual signature verification"""
        command = "开闸泄洪 - CRITICAL COMMAND"

        # Two different commanders sign
        user1_id = "commander-001"
        user1_sig = verifier.sign(command, user1_id)

        user2_id = "commander-002"
        user2_sig = verifier.sign(command, user2_id)

        result = verifier.require_dual_signature(
            command,
            user1_id, user1_sig,
            user2_id, user2_sig
        )

        assert result is True

    def test_dual_signature_same_user_fails(self, verifier):
        """Test that same user cannot provide both signatures"""
        command = "开闸泄洪 - CRITICAL COMMAND"

        user_id = "commander-001"
        sig1 = verifier.sign(command, user_id)
        sig2 = verifier.sign(command, user_id)  # Same user!

        result = verifier.require_dual_signature(
            command,
            user_id, sig1,
            user_id, sig2
        )

        assert result is False

    def test_dual_signature_one_invalid_fails(self, verifier):
        """Test that one invalid signature causes failure"""
        command = "开闸泄洪 - CRITICAL COMMAND"

        user1_id = "commander-001"
        user1_sig = verifier.sign(command, user1_id)

        user2_id = "commander-002"
        fake_sig = "fake-signature"

        result = verifier.require_dual_signature(
            command,
            user1_id, user1_sig,
            user2_id, fake_sig
        )

        assert result is False


# =============================================================================
# Integration Tests: Security Pipeline
# =============================================================================

class TestSecurityPipelineIntegration:
    """Integration tests for complete security pipeline"""

    def test_command_goes_through_full_security_check(self):
        """Test command passes through red team -> remonstrance -> dual sig"""
        # Create message
        message = MACPMessage(
            header=MACPHeader(
                trace_id="trace-integration-001",
                agent_id="command-001",
                agent_type=AgentType.COMMAND
            ),
            body=MACPBody(
                content="建议启动一级应急响应，疏散 A 区居民",
                inclination=0.8,
                confidence=0.85,
                stance=MessageStance.SUPPORT,
                evidence_refs=["CASE_2020_001", "PHYSICS_sim_001"]
            )
        )

        # Step 1: Red team analysis (should pass - safe command)
        red_team = RedTeamEngine()
        assert red_team.should_intercept(message) is False

        # Step 2: Remonstrance lock (high-risk command needs preview)
        lock = RemonstranceLock()
        pending_id = lock.request_execution(
            command=message.body.content,
            trace_id=message.header.trace_id
        )

        # Complete physics preview
        lock.complete_physics_preview(pending_id, {'preview': 'complete'})

        # Step 3: Dual signature confirmation
        verifier = DualSignatureVerifier()

        # Two commanders confirm
        sig1 = verifier.sign(pending_id, "commander-001")
        sig2 = verifier.sign(pending_id, "commander-002")

        # Confirm in remonstrance lock
        signature = lock._generate_signature(
            message.body.content,
            message.header.trace_id
        )
        lock.confirm_command(pending_id, signature)

        # Verify dual signature
        dual_sig_valid = verifier.require_dual_signature(
            pending_id,
            "commander-001", sig1,
            "commander-002", sig2
        )

        # Command is now ready for execution
        assert lock.can_execute(pending_id) is True
        assert dual_sig_valid is True
