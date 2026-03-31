"""
Epic 7: Agent Lifecycle Management Tests

Tests for:
- E7-T02: 智能体即插即用激活 (Plug-and-Play Activation)
- E7-T03: 智能体在线率监控 (>99%) (Availability Monitoring)

These tests validate the agent registration, activation, and health monitoring system.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
import asyncio

from src.mas.registry.agent_registry import AgentRegistry, get_registry
from src.mas.models.agent import AgentMetadata, AgentStatus, AgentCapability
from src.mas.protocol.schema import AgentType


# =============================================================================
# E7-T02: 智能体即插即用激活 Tests
# =============================================================================

class TestAgentRegistration:
    """Tests for E7-T02: 智能体即插即用激活"""

    @pytest.fixture
    def registry(self):
        """Create fresh registry instance"""
        return AgentRegistry()

    @pytest.fixture
    def sample_agent_metadata(self) -> AgentMetadata:
        """Create sample agent metadata for testing"""
        return AgentMetadata(
            agent_id="hydrology-agent-001",
            agent_type="hydrology",
            display_name="水文专家 Agent",
            description="负责水文分析和洪水预测",
            capabilities=[
                AgentCapability(
                    name="flood_prediction",
                    version="1.0.0",
                    description="洪水预测分析能力"
                ),
                AgentCapability(
                    name="water_level_analysis",
                    version="1.0.0",
                    description="水位数据分析能力"
                )
            ],
            config={
                "model": "deepseek-r1",
                "temperature": 0.7,
                "max_tokens": 2000
            }
        )

    def test_register_new_agent(self, registry, sample_agent_metadata):
        """Test registering a new agent"""
        # Act
        result = registry.register(sample_agent_metadata)

        # Assert
        assert result is True
        registered = registry.get("hydrology-agent-001")
        assert registered is not None
        assert registered.agent_id == "hydrology-agent-001"
        assert registered.status == AgentStatus.REGISTERING

    def test_register_duplicate_agent_fails(self, registry, sample_agent_metadata):
        """Test that registering duplicate agent fails"""
        # Register first time
        registry.register(sample_agent_metadata)

        # Try to register again with same ID
        result = registry.register(sample_agent_metadata)

        assert result is False

    def test_deregister_agent(self, registry, sample_agent_metadata):
        """Test deregistering an agent"""
        # Register
        registry.register(sample_agent_metadata)

        # Deregister
        result = registry.deregister("hydrology-agent-001")

        assert result is True
        assert registry.get("hydrology-agent-001") is None

    def test_deregister_nonexistent_agent_fails(self, registry):
        """Test that deregistering non-existent agent fails"""
        result = registry.deregister("nonexistent-agent")
        assert result is False

    def test_update_agent_status(self, registry, sample_agent_metadata):
        """Test updating agent status"""
        # Register
        registry.register(sample_agent_metadata)

        # Update to ACTIVE
        result = registry.update_status("hydrology-agent-001", AgentStatus.ACTIVE)

        assert result is True
        agent = registry.get("hydrology-agent-001")
        assert agent.status == AgentStatus.ACTIVE

    def test_heartbeat_updates_timestamp(self, registry, sample_agent_metadata):
        """Test that heartbeat updates last_heartbeat timestamp"""
        # Register
        registry.register(sample_agent_metadata)

        # Record time before heartbeat
        before_heartbeat = datetime.utcnow()

        # Send heartbeat
        result = registry.heartbeat("hydrology-agent-001")

        assert result is True
        agent = registry.get("hydrology-agent-001")
        assert agent.last_heartbeat is not None
        assert agent.last_heartbeat >= before_heartbeat

    def test_heartbeat_auto_activates_registering_agent(self, registry, sample_agent_metadata):
        """Test that first heartbeat auto-activates REGISTERING agent"""
        # Register (starts as REGISTERING)
        registry.register(sample_agent_metadata)
        agent = registry.get("hydrology-agent-001")
        assert agent.status == AgentStatus.REGISTERING

        # Send heartbeat
        registry.heartbeat("hydrology-agent-001")

        # Should auto-transition to ACTIVE
        agent = registry.get("hydrology-agent-001")
        assert agent.status == AgentStatus.ACTIVE

    def test_get_agents_by_type(self, registry):
        """Test getting agents by type"""
        # Register multiple hydrology agents
        hydro1 = AgentMetadata(
            agent_id="hydro-001",
            agent_type="hydrology",
            display_name="Hydro 1"
        )
        hydro2 = AgentMetadata(
            agent_id="hydro-002",
            agent_type="hydrology",
            display_name="Hydro 2"
        )
        emergency = AgentMetadata(
            agent_id="emergency-001",
            agent_type="emergency",
            display_name="Emergency 1"
        )

        registry.register(hydro1)
        registry.register(hydro2)
        registry.register(emergency)

        # Get by type
        hydrology_agents = registry.get_by_type("hydrology")

        assert len(hydrology_agents) == 2
        assert all(a.agent_type == "hydrology" for a in hydrology_agents)

    def test_get_active_agents(self, registry):
        """Test getting only active agents"""
        # Register and activate some agents
        active1 = AgentMetadata(agent_id="active-001", agent_type="hydrology", display_name="Active 1")
        active2 = AgentMetadata(agent_id="active-002", agent_type="hydrology", display_name="Active 2")
        offline = AgentMetadata(agent_id="offline-001", agent_type="emergency", display_name="Offline")

        registry.register(active1)
        registry.register(active2)
        registry.register(offline)

        # Activate
        registry.update_status("active-001", AgentStatus.ACTIVE)
        registry.update_status("active-002", AgentStatus.ACTIVE)
        registry.update_status("offline-001", AgentStatus.OFFLINE)

        # Get active
        active_agents = registry.get_active_agents()

        assert len(active_agents) == 2
        assert all(a.status == AgentStatus.ACTIVE for a in active_agents)

    def test_registry_stats(self, registry):
        """Test getting registry statistics"""
        # Register some agents
        for i in range(3):
            agent = AgentMetadata(
                agent_id=f"agent-{i:03d}",
                agent_type="hydrology",
                display_name=f"Agent {i}"
            )
            registry.register(agent)
            registry.update_status(f"agent-{i:03d}", AgentStatus.ACTIVE)

        # Get stats
        stats = registry.get_stats()

        assert stats['total_agents'] == 3
        assert 'by_status' in stats
        assert 'by_type' in stats


# =============================================================================
# E7-T03: 智能体在线率监控 Tests
# =============================================================================

class TestAgentHealthMonitoring:
    """Tests for E7-T03: 智能体在线率监控 (>99%)"""

    @pytest.fixture
    def registry(self):
        """Create fresh registry instance"""
        return AgentRegistry()

    def test_health_check_identifies_unhealthy_agents(self, registry):
        """Test health check identifies unhealthy agents"""
        # Create agent with old heartbeat
        old_agent = AgentMetadata(
            agent_id="old-agent-001",
            agent_type="hydrology",
            display_name="Old Agent"
        )
        # Set old heartbeat (beyond 30 second timeout)
        old_agent.last_heartbeat = datetime.utcnow() - timedelta(seconds=60)

        registry.register(old_agent)

        # Run health check
        health_result = registry.check_health()

        assert "old-agent-001" in health_result['unhealthy']
        assert "old-agent-001" not in health_result['healthy']

    def test_health_check_identifies_healthy_agents(self, registry):
        """Test health check identifies healthy agents"""
        # Create agent with recent heartbeat
        healthy_agent = AgentMetadata(
            agent_id="healthy-agent-001",
            agent_type="hydrology",
            display_name="Healthy Agent"
        )
        # Set recent heartbeat
        healthy_agent.last_heartbeat = datetime.utcnow() - timedelta(seconds=10)

        registry.register(healthy_agent)

        # Run health check
        health_result = registry.check_health()

        assert "healthy-agent-001" in health_result['healthy']
        assert "healthy-agent-001" not in health_result['unhealthy']

    def test_health_check_identifies_unknown_agents(self, registry):
        """Test health check identifies agents without heartbeat"""
        # Create agent without heartbeat
        unknown_agent = AgentMetadata(
            agent_id="unknown-agent-001",
            agent_type="hydrology",
            display_name="Unknown Agent"
        )
        # No heartbeat set

        registry.register(unknown_agent)

        # Run health check
        health_result = registry.check_health()

        assert "unknown-agent-001" in health_result['unknown']

    def test_auto_mark_unhealthy_as_offline(self, registry):
        """Test that unhealthy active agents are auto-marked as offline"""
        # Create active agent
        agent = AgentMetadata(
            agent_id="agent-to-offline",
            agent_type="hydrology",
            display_name="Agent to Offline",
            status=AgentStatus.REGISTERING  # Start as REGISTERING
        )

        registry.register(agent)

        # Manually set to ACTIVE with old heartbeat
        registry.update_status("agent-to-offline", AgentStatus.ACTIVE)
        agent = registry.get("agent-to-offline")
        agent.last_heartbeat = datetime.utcnow() - timedelta(seconds=60)

        # Run health check (should auto-mark as offline)
        registry.check_health()

        retrieved = registry.get("agent-to-offline")
        assert retrieved.status == AgentStatus.OFFLINE

    def test_availability_calculation(self, registry):
        """Test calculating agent availability percentage"""
        # Register 10 agents
        for i in range(10):
            agent = AgentMetadata(
                agent_id=f"agent-{i:03d}",
                agent_type="hydrology",
                display_name=f"Agent {i}"
            )
            registry.register(agent)

            # Make 9 active with heartbeat, 1 offline
            if i < 9:
                agent.last_heartbeat = datetime.utcnow() - timedelta(seconds=10)
                registry.update_status(f"agent-{i:03d}", AgentStatus.ACTIVE)
            else:
                agent.last_heartbeat = datetime.utcnow() - timedelta(seconds=60)

        # Run health check
        health_result = registry.check_health()

        # Calculate availability
        total = len(health_result['healthy']) + len(health_result['unhealthy'])
        availability = len(health_result['healthy']) / total if total > 0 else 0

        assert availability == 0.9  # 90% availability

    def test_availability_above_99_threshold(self, registry):
        """Test availability monitoring with >99% threshold"""
        # Register 100 agents
        for i in range(100):
            agent = AgentMetadata(
                agent_id=f"agent-{i:03d}",
                agent_type="hydrology",
                display_name=f"Agent {i}"
            )
            registry.register(agent)

            # Make 99 active, 1 offline
            if i < 99:
                agent.last_heartbeat = datetime.utcnow() - timedelta(seconds=10)
                registry.update_status(f"agent-{i:03d}", AgentStatus.ACTIVE)
            else:
                agent.last_heartbeat = None  # No heartbeat

        # Run health check
        health_result = registry.check_health()

        # Calculate availability
        healthy_count = len(health_result['healthy'])
        total_agents = registry.get_stats()['total_agents']
        availability = healthy_count / total_agents

        # Should be 99%
        assert availability == 0.99

        # Check if meets >99% SLA (should fail with 99%)
        meets_sla = availability > 0.99
        assert meets_sla is False


# =============================================================================
# Integration Tests: Agent Lifecycle
# =============================================================================

class TestAgentLifecycleIntegration:
    """Integration tests for complete agent lifecycle"""

    @pytest.fixture
    def registry(self):
        """Create fresh registry instance"""
        return AgentRegistry()

    def test_full_agent_lifecycle_workflow(self):
        """Test complete agent lifecycle: register -> activate -> monitor -> deregister"""
        registry = AgentRegistry()

        # Step 1: Register
        agent = AgentMetadata(
            agent_id="lifecycle-agent-001",
            agent_type="economy",
            display_name="Lifecycle Test Agent",
            capabilities=[
                AgentCapability(name="analysis", version="1.0.0")
            ]
        )
        registry.register(agent)

        assert agent.status == AgentStatus.REGISTERING

        # Step 2: Activate via heartbeat
        registry.heartbeat("lifecycle-agent-001")

        retrieved = registry.get("lifecycle-agent-001")
        assert retrieved.status == AgentStatus.ACTIVE

        # Step 3: Simulate activity
        retrieved.mark_error()  # Simulate an error
        assert retrieved.error_count == 1
        assert retrieved.health_score < 1.0

        # Step 4: Health check
        health_result = registry.check_health()
        assert "lifecycle-agent-001" in health_result['healthy']

        # Step 5: Agent becomes unhealthy (simulate timeout)
        retrieved.last_heartbeat = datetime.utcnow() - timedelta(seconds=60)
        health_result = registry.check_health()
        assert "lifecycle-agent-001" in health_result['unhealthy']

        # Step 6: Deregister
        registry.deregister("lifecycle-agent-001")
        assert registry.get("lifecycle-agent-001") is None

    def test_global_registry_singleton(self):
        """Test that get_registry() returns singleton instance"""
        # Get registry twice
        registry1 = get_registry()
        registry2 = get_registry()

        # Should be same instance
        assert registry1 is registry2

    def test_multiple_agents_concurrent_operation(self, registry):
        """Test concurrent operations with multiple agents"""
        # Register 10 agents
        for i in range(10):
            agent = AgentMetadata(
                agent_id=f"concurrent-{i:03d}",
                agent_type="hydrology",
                display_name=f"Concurrent Agent {i}"
            )
            registry.register(agent)
            registry.heartbeat(f"concurrent-{i:03d}")

        # Verify all active
        stats = registry.get_stats()
        assert stats['total_agents'] == 10
        assert stats['by_status'].get('active', 0) == 10

        # Send heartbeats to all
        for i in range(10):
            registry.heartbeat(f"concurrent-{i:03d}")

        # Health check
        health = registry.check_health()
        assert len(health['healthy']) == 10


# =============================================================================
# E7-T02: Plug-and-Play Template Tests
# =============================================================================

class TestAgentTemplate:
    """Tests for agent creation templates (E7-T01 support)"""

    def test_create_hydrology_agent_template(self):
        """Test creating hydrology agent from template"""
        agent = AgentMetadata(
            agent_id=f"hydrology-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            agent_type="hydrology",
            display_name="水文专家",
            description="负责水文数据分析和洪水预测",
            capabilities=[
                AgentCapability(name="water_level_analysis", version="1.0.0"),
                AgentCapability(name="flood_forecast", version="1.0.0")
            ],
            config={
                "model": "deepseek-r1",
                "temperature": 0.7
            }
        )

        assert agent.agent_type == "hydrology"
        assert len(agent.capabilities) == 2
        assert agent.status == AgentStatus.REGISTERING

    def test_create_emergency_agent_template(self):
        """Test creating emergency agent from template"""
        agent = AgentMetadata(
            agent_id=f"emergency-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            agent_type="emergency",
            display_name="应急指挥专家",
            description="负责应急响应和资源调度",
            capabilities=[
                AgentCapability(name="resource_allocation", version="1.0.0"),
                AgentCapability(name="evacuation_planning", version="1.0.0")
            ]
        )

        assert agent.agent_type == "emergency"
        assert len(agent.capabilities) == 2

    def test_create_economy_agent_template(self):
        """Test creating economy agent from template"""
        agent = AgentMetadata(
            agent_id=f"economy-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            agent_type="economy",
            display_name="经济损失评估专家",
            description="负责经济损失评估和 ROI 分析",
            capabilities=[
                AgentCapability(name="damage_assessment", version="1.0.0"),
                AgentCapability(name="roi_analysis", version="1.0.0")
            ]
        )

        assert agent.agent_type == "economy"
        assert len(agent.capabilities) == 2


# =============================================================================
# Performance Tests: Agent Registry
# =============================================================================

class TestAgentRegistryPerformance:
    """Performance tests for agent registry operations"""

    @pytest.fixture
    def registry(self):
        """Create fresh registry instance"""
        return AgentRegistry()

    def test_registry_scale_100_agents(self):
        """Test registry performance with 100 agents"""
        registry = AgentRegistry()

        import time
        start = time.time()

        # Register 100 agents
        for i in range(100):
            agent = AgentMetadata(
                agent_id=f"perf-agent-{i:03d}",
                agent_type="hydrology",
                display_name=f"Perf Agent {i}"
            )
            registry.register(agent)
            registry.heartbeat(f"perf-agent-{i:03d}")

        elapsed = time.time() - start

        # Should complete in under 1 second
        assert elapsed < 1.0
        assert registry.get_stats()['total_agents'] == 100

    def test_lookup_performance(self, registry):
        """Test O(1) lookup performance"""
        import time

        # Register agent
        agent = AgentMetadata(
            agent_id="lookup-test",
            agent_type="hydrology",
            display_name="Lookup Test"
        )
        registry.register(agent)

        # Measure lookup time
        start = time.time()
        for _ in range(1000):
            registry.get("lookup-test")
        elapsed = time.time() - start

        # 1000 lookups should complete quickly
        assert elapsed < 0.5  # Under 500ms for 1000 lookups
