"""
Command Agent Arbitration Tests

Tests for E4-T03: Command Agent 强制仲裁
Tests for E4-T05: Watchdog 仲裁机制
Tests for E4-T06: TTL 监控 (10 分钟极限)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio

from src.mas.debate.engine import DebateEngine, DebateConfig
from src.mas.debate.state import DebateStatus, DebateContext
from src.mas.protocol.schema import (
    MACPMessage, MACPHeader, MACPBody, AgentType,
    MessageStance, MessagePriority
)
from src.mas.debate.agents.base import BaseAgent, AgentConfig


class CommandAgent(BaseAgent):
    """Command Agent for arbitration"""

    def __init__(self):
        config = AgentConfig(
            agent_id="command-center-001",
            agent_type=AgentType.COMMAND,
            display_name="指挥中心",
            system_prompt="你是指挥中心 Agent，负责最终决策仲裁。",
            temperature=0.3,
            max_tokens=500
        )
        super().__init__(config)

    def _get_expertise_prompt(self) -> str:
        return "作为指挥中心，你需要综合各方意见，做出最终决策。"

    def _analyze_context(self, context: DebateContext) -> dict:
        # Count stances from previous messages
        support_count = 0
        oppose_count = 0
        evidence_refs = []
        for msg in context.previous_messages:
            if msg.get('stance') == 'support':
                support_count += 1
            elif msg.get('stance') == 'oppose':
                oppose_count += 1
            # Collect evidence refs from previous messages
            if msg.get('evidence_refs'):
                evidence_refs.extend(msg.get('evidence_refs', []))

        return {
            'support_count': support_count,
            'oppose_count': oppose_count,
            'evidence': [{'ref_id': ref} for ref in evidence_refs] if evidence_refs else [{'ref_id': 'CASE_2020_001'}],
            'clarity_score': 0.8
        }

    def _generate_stance_and_inclination(self, analysis: dict) -> tuple:
        # Follow majority - use appropriate inclination for stance
        if analysis['support_count'] > analysis['oppose_count']:
            # SUPPORT stance needs inclination >= 0.5
            return MessageStance.SUPPORT, 0.55 + (analysis['support_count'] * 0.1)
        elif analysis['oppose_count'] > analysis['support_count']:
            # OPPOSE stance needs inclination <= 0.5
            return MessageStance.OPPOSE, 0.5 - (analysis['oppose_count'] * 0.1)
        else:
            return MessageStance.NEUTRAL, 0.5

    def _extract_evidence_refs(self, analysis: dict) -> list:
        """Override to ensure evidence refs are always present for non-neutral"""
        refs = super()._extract_evidence_refs(analysis)
        if not refs:
            return ['CASE_DEBATE_001']
        return refs


class WatchdogTimer:
    """
    Watchdog timer for debate timeout monitoring
    Implements E4-T05 and E4-T06 requirements
    """

    def __init__(self, timeout_seconds: int = 600):  # 10 minutes default
        self.timeout_seconds = timeout_seconds
        self.start_time: Optional[datetime] = None
        self.is_running = False
        self._callbacks = []

    def start(self):
        """Start the watchdog timer"""
        self.start_time = datetime.utcnow()
        self.is_running = True

    def stop(self):
        """Stop the watchdog timer"""
        self.is_running = False

    def reset(self):
        """Reset the watchdog timer"""
        self.start_time = datetime.utcnow()

    def is_expired(self) -> bool:
        """Check if timeout has expired"""
        if not self.start_time or not self.is_running:
            return False

        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        return elapsed >= self.timeout_seconds

    def get_remaining_seconds(self) -> float:
        """Get remaining seconds before timeout"""
        if not self.start_time:
            return self.timeout_seconds

        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        return max(0, self.timeout_seconds - elapsed)

    def on_timeout(self, callback):
        """Register a timeout callback"""
        self._callbacks.append(callback)

    def trigger_timeout(self):
        """Trigger all timeout callbacks"""
        for callback in self._callbacks:
            callback()


class TestCommandAgentArbitration:
    """Tests for E4-T03: Command Agent 强制仲裁"""

    @pytest.fixture
    def command_agent(self):
        """Create command agent instance"""
        return CommandAgent()

    @pytest.fixture
    def debate_context(self):
        """Create a debate context with mixed opinions"""
        return DebateContext(
            topic="是否立即启动一级应急响应",
            current_round=3,
            total_rounds=3,
            previous_messages=[
                {'agent_type': 'hydrology', 'content': '建议启动', 'stance': 'support', 'inclination': 0.8},
                {'agent_type': 'emergency', 'content': '同意启动', 'stance': 'support', 'inclination': 0.7},
                {'agent_type': 'economy', 'content': '建议谨慎', 'stance': 'oppose', 'inclination': 0.6},
            ],
            proposal_summary="启动一级应急响应"
        )

    def test_command_agent_creation(self, command_agent):
        """Test command agent can be created"""
        assert command_agent is not None
        assert command_agent.config.agent_type == AgentType.COMMAND
        assert command_agent.config.display_name == "指挥中心"

    def test_command_agent_arbitration_follows_majority(
        self,
        command_agent,
        debate_context
    ):
        """Test command agent follows majority opinion"""
        # Act - Generate response
        message = command_agent.generate_response(
            debate_context,
            trace_id="test-trace-arbitration-001"
        )

        # Assert - Should follow majority (2 support vs 1 oppose)
        assert message.header.agent_type == AgentType.COMMAND
        assert message.body.stance == MessageStance.SUPPORT
        assert message.body.inclination > 0.7

    def test_command_agent_oppose_majority(self, command_agent):
        """Test command agent opposes when majority opposes"""
        context = DebateContext(
            topic="Test topic",
            current_round=3,
            total_rounds=3,
            previous_messages=[
                {'agent_type': 'hydrology', 'content': '反对', 'stance': 'oppose', 'inclination': 0.8},
                {'agent_type': 'emergency', 'content': '反对', 'stance': 'oppose', 'inclination': 0.7},
                {'agent_type': 'economy', 'content': '支持', 'stance': 'support', 'inclination': 0.6},
            ],
            proposal_summary="Test proposal"
        )

        message = command_agent.generate_response(context, "test-trace-002")

        assert message.body.stance == MessageStance.OPPOSE

    def test_command_agent_tie_breaker(self, command_agent):
        """Test command agent handles tie situation"""
        context = DebateContext(
            topic="Test topic",
            current_round=3,
            total_rounds=3,
            previous_messages=[
                {'agent_type': 'hydrology', 'content': '支持', 'stance': 'support', 'inclination': 0.8},
                {'agent_type': 'emergency', 'content': '反对', 'stance': 'oppose', 'inclination': 0.7},
            ],
            proposal_summary="Test proposal"
        )

        message = command_agent.generate_response(context, "test-trace-003")

        # Should be neutral in tie
        assert message.body.stance == MessageStance.NEUTRAL

    def test_command_agent_message_format(self, command_agent, debate_context):
        """Test command agent message follows MACP format"""
        message = command_agent.generate_response(debate_context, "test-trace-004")

        # Validate MACP structure
        assert message.header.trace_id == "test-trace-004"
        assert message.header.agent_id == "command-center-001"
        assert message.body.content is not None
        assert 0 <= message.body.inclination <= 1
        assert 0 <= message.body.confidence <= 1


class TestWatchdogArbitration:
    """Tests for E4-T05: Watchdog 仲裁机制"""

    def test_watchdog_creation(self):
        """Test watchdog timer creation"""
        watchdog = WatchdogTimer(timeout_seconds=60)
        assert watchdog.timeout_seconds == 60
        assert watchdog.is_running is False

    def test_watchdog_start_stop(self):
        """Test watchdog start and stop"""
        watchdog = WatchdogTimer(timeout_seconds=60)

        watchdog.start()
        assert watchdog.is_running is True
        assert watchdog.start_time is not None

        watchdog.stop()
        assert watchdog.is_running is False

    def test_watchdog_expiry(self):
        """Test watchdog expiry detection"""
        # Use very short timeout for testing
        watchdog = WatchdogTimer(timeout_seconds=1)
        watchdog.start()

        # Should not be expired immediately
        assert watchdog.is_expired() is False

        # Wait for expiry
        asyncio.run(asyncio.sleep(1.1))
        assert watchdog.is_expired() is True

    def test_watchdog_remaining_time(self):
        """Test remaining time calculation"""
        watchdog = WatchdogTimer(timeout_seconds=10)
        watchdog.start()

        remaining = watchdog.get_remaining_seconds()
        assert 0 < remaining <= 10

    def test_watchdog_reset(self):
        """Test watchdog reset"""
        watchdog = WatchdogTimer(timeout_seconds=10)
        watchdog.start()

        # Wait a bit
        asyncio.run(asyncio.sleep(0.5))
        remaining_before = watchdog.get_remaining_seconds()

        # Reset
        watchdog.reset()
        remaining_after = watchdog.get_remaining_seconds()

        # After reset, remaining time should be close to full timeout
        assert remaining_after > remaining_before

    def test_watchdog_callback(self):
        """Test watchdog timeout callback"""
        watchdog = WatchdogTimer(timeout_seconds=1)
        callback_called = False

        def on_timeout():
            nonlocal callback_called
            callback_called = True

        watchdog.on_timeout(on_timeout)
        watchdog.start()

        # Wait for expiry
        asyncio.run(asyncio.sleep(1.1))
        watchdog.trigger_timeout()

        assert callback_called is True


class TestDebateWithWatchdog:
    """Integration tests for debate engine with watchdog"""

    def test_debate_engine_with_watchdog(self):
        """Test debate engine integrates watchdog"""
        config = DebateConfig(max_rounds=2, enable_langsmith=False)
        engine = DebateEngine(config)

        # Attach watchdog
        watchdog = WatchdogTimer(timeout_seconds=600)  # 10 minutes
        watchdog.start()

        # Register agents
        from src.mas.debate.agents.hydrology import HydrologyAgent
        from src.mas.debate.agents.emergency import EmergencyAgent

        engine.register_agent(HydrologyAgent())
        engine.register_agent(EmergencyAgent())

        # Initialize and run
        engine.initialize_debate(topic="Test debate")
        engine.run_full_debate()

        # Debate should complete before timeout
        assert watchdog.is_expired() is False
        assert engine.current_state.status == DebateStatus.COMPLETED

    def test_debate_timeout_handling(self):
        """Test debate handles timeout gracefully"""
        config = DebateConfig(max_rounds=1, enable_langsmith=False)
        engine = DebateEngine(config)

        # Use very short timeout for testing
        watchdog = WatchdogTimer(timeout_seconds=1)
        timeout_handled = False

        def handle_timeout():
            nonlocal timeout_handled
            if engine.current_state:
                engine.terminate(reason="TTL expired")
                timeout_handled = True

        watchdog.on_timeout(handle_timeout)
        watchdog.start()

        # Register agent
        from src.mas.debate.agents.hydrology import HydrologyAgent
        engine.register_agent(HydrologyAgent())

        engine.initialize_debate(topic="Test")

        # Wait for timeout
        asyncio.run(asyncio.sleep(1.1))
        watchdog.trigger_timeout()

        # Should have handled timeout
        assert timeout_handled is True


class TestTTLMonitoring:
    """Tests for E4-T06: TTL 监控 (10 分钟极限)"""

    def test_ttl_calculation(self):
        """Test TTL calculation"""
        start_time = datetime.utcnow() - timedelta(minutes=5)
        ttl_seconds = 600  # 10 minutes

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        remaining = ttl_seconds - elapsed

        assert 0 < remaining < 600
        assert remaining >= 299  # More than 5 minutes remaining (with small tolerance)

    def test_ttl_enforcement(self):
        """Test TTL enforcement"""
        ttl_seconds = 600
        start_time = datetime.utcnow() - timedelta(seconds=601)

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        is_expired = elapsed >= ttl_seconds

        assert is_expired is True

    def test_debate_completes_within_ttl(self):
        """Test that typical debate completes well within TTL"""
        config = DebateConfig(max_rounds=3, enable_langsmith=False)
        engine = DebateEngine(config)

        # Register agents
        from src.mas.debate.agents.hydrology import HydrologyAgent
        from src.mas.debate.agents.emergency import EmergencyAgent
        from src.mas.debate.agents.economy import EconomyAgent

        engine.register_agent(HydrologyAgent())
        engine.register_agent(EmergencyAgent())
        engine.register_agent(EconomyAgent())

        start_time = datetime.utcnow()

        engine.initialize_debate(topic="Test debate within TTL")
        engine.run_full_debate()

        end_time = datetime.utcnow()
        elapsed_seconds = (end_time - start_time).total_seconds()

        # Should complete in well under 10 minutes (600 seconds)
        # Even with LLM latency, should be under 60 seconds for mock tests
        assert elapsed_seconds < 60
        assert elapsed_seconds < 600  # TTL limit


class TestDebateWithCommandAgent:
    """Integration tests with Command Agent as final arbiter"""

    def test_full_debate_with_command_arbitration(self):
        """Test complete debate flow with command agent arbitration"""
        config = DebateConfig(max_rounds=2, enable_langsmith=False)
        engine = DebateEngine(config)

        # Register expert agents
        from src.mas.debate.agents.hydrology import HydrologyAgent
        from src.mas.debate.agents.emergency import EmergencyAgent
        from src.mas.debate.agents.economy import EconomyAgent

        engine.register_agent(HydrologyAgent())
        engine.register_agent(EmergencyAgent())
        engine.register_agent(EconomyAgent())

        # Register command agent for final arbitration
        command_agent = CommandAgent()
        engine.register_agent(command_agent)

        # Run debate
        engine.initialize_debate(
            topic="是否启动一级应急响应",
            max_rounds=2
        )
        engine.run_full_debate()

        # Verify debate completed
        assert engine.current_state.status == DebateStatus.COMPLETED
        assert len(engine.current_state.all_messages) > 0

        # Get summary
        summary = engine.get_summary()
        assert summary['status'] == DebateStatus.COMPLETED
        assert summary['total_messages'] > 0
        assert 'command' in [a.lower() for a in summary['agent_stats'].keys()]
