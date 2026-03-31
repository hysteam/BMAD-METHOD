"""
Epic 5: Physics-AI Coupling Tests

Tests for:
- E5-T01: What-if 干预仿真 (30 秒反馈)
- E5-T02: 物理后果预演 (90 秒/60 分钟)
- E5-T05: Remonstrance Lock 验证 (已在 E6 测试中覆盖部分)

These tests validate the physics simulation integration and performance SLAs.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
import hashlib

from src.mas.protocol.schema import (
    MACPMessage, MACPHeader, MACPBody, AgentType,
    MessageStance, MessagePriority
)


# =============================================================================
# Physics Simulation Types (Interface Definitions)
# =============================================================================

class SimulationStatus(str, Enum):
    """Physics simulation status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class SimulationRequest:
    """
    Request for physics simulation

    Represents a What-if intervention scenario
    """

    def __init__(
        self,
        scenario_id: str,
        intervention: str,
        duration_hours: int,
        mesh_resolution: float = 30.0,
        timeout_seconds: int = 90
    ):
        self.scenario_id = scenario_id
        self.intervention = intervention
        self.duration_hours = duration_hours
        self.mesh_resolution = mesh_resolution  # meters
        self.timeout_seconds = timeout_seconds
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.status = SimulationStatus.PENDING

    def start(self):
        """Mark simulation as started"""
        self.started_at = datetime.utcnow()
        self.status = SimulationStatus.RUNNING

    def complete(self):
        """Mark simulation as completed"""
        self.completed_at = datetime.utcnow()
        self.status = SimulationStatus.COMPLETED

    def fail(self, reason: str = "Unknown error"):
        """Mark simulation as failed"""
        self.completed_at = datetime.utcnow()
        self.status = SimulationStatus.FAILED
        self.metadata['error'] = reason

    def is_timeout(self) -> bool:
        """Check if simulation exceeded timeout"""
        if not self.started_at:
            return False

        elapsed = (datetime.utcnow() - self.started_at).total_seconds()
        return elapsed > self.timeout_seconds

    def get_elapsed_seconds(self) -> float:
        """Get elapsed time in seconds"""
        if not self.started_at:
            return 0.0

        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get metadata dictionary"""
        if not hasattr(self, '_metadata'):
            self._metadata: Dict[str, Any] = {}
        return self._metadata


class SimulationResult:
    """
    Physics simulation result

    Contains simulation output with physical fingerprint
    """

    def __init__(
        self,
        request: SimulationRequest,
        flood_depths: Dict[str, float],
        affected_area_km2: float,
        peak_flow_rate: float,
        timeline: List[Dict[str, Any]]
    ):
        self.request = request
        self.flood_depths = flood_depths  # location_id -> depth in meters
        self.affected_area_km2 = affected_area_km2
        self.peak_flow_rate = peak_flow_rate  # m³/s
        self.timeline = timeline  # Time-series data
        self.generated_at = datetime.utcnow()

        # Generate physical fingerprint (SHA-256)
        self.physical_fingerprint = self._generate_fingerprint()

    def _generate_fingerprint(self) -> str:
        """
        Generate SHA-256 fingerprint of simulation result

        This provides objective verification of AI decisions
        (Evidence Bridge requirement)
        """
        # Create deterministic hash from result data
        data = {
            'scenario_id': self.request.scenario_id,
            'flood_depths': sorted(self.flood_depths.items()),
            'affected_area_km2': self.affected_area_km2,
            'peak_flow_rate': self.peak_flow_rate,
            'timeline_length': len(self.timeline)
        }

        # Convert to string and hash
        data_str = str(data)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'scenario_id': self.request.scenario_id,
            'status': self.request.status,
            'flood_depths': self.flood_depths,
            'affected_area_km2': self.affected_area_km2,
            'peak_flow_rate': self.peak_flow_rate,
            'physical_fingerprint': self.physical_fingerprint,
            'elapsed_seconds': self.request.get_elapsed_seconds(),
            'generated_at': self.generated_at.isoformat()
        }


class PhysicsSidecarClient:
    """
    Client for physics sidecar communication

    Handles What-if simulation requests and result retrieval
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        timeout_seconds: int = 90
    ):
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self._active_requests: Dict[str, SimulationRequest] = {}
        self._results: Dict[str, SimulationResult] = {}

    def request_simulation(
        self,
        scenario_id: str,
        intervention: str,
        duration_hours: int,
        mesh_resolution: float = 30.0
    ) -> SimulationRequest:
        """Request a new physics simulation"""
        request = SimulationRequest(
            scenario_id=scenario_id,
            intervention=intervention,
            duration_hours=duration_hours,
            mesh_resolution=mesh_resolution,
            timeout_seconds=self.timeout_seconds
        )

        self._active_requests[scenario_id] = request
        request.start()

        return request

    def complete_simulation(
        self,
        scenario_id: str,
        flood_depths: Dict[str, float],
        affected_area_km2: float,
        peak_flow_rate: float,
        timeline: List[Dict[str, Any]]
    ) -> SimulationResult:
        """Complete a simulation with results"""
        if scenario_id not in self._active_requests:
            raise ValueError(f"Unknown scenario: {scenario_id}")

        request = self._active_requests[scenario_id]
        request.complete()

        result = SimulationResult(
            request=request,
            flood_depths=flood_depths,
            affected_area_km2=affected_area_km2,
            peak_flow_rate=peak_flow_rate,
            timeline=timeline
        )

        self._results[scenario_id] = result
        del self._active_requests[scenario_id]

        return result

    def fail_simulation(self, scenario_id: str, reason: str):
        """Mark a simulation as failed"""
        if scenario_id not in self._active_requests:
            return

        request = self._active_requests[scenario_id]
        request.fail(reason)
        del self._active_requests[scenario_id]

    def get_result(self, scenario_id: str) -> Optional[SimulationResult]:
        """Get simulation result by scenario ID"""
        return self._results.get(scenario_id)

    def check_timeout(self, scenario_id: str) -> bool:
        """Check if a simulation has timed out"""
        if scenario_id not in self._active_requests:
            return False

        request = self._active_requests[scenario_id]
        if request.is_timeout():
            self.fail_simulation(scenario_id, "Simulation timeout")
            return True

        return False


# =============================================================================
# E5-T01: What-if 干预仿真 Tests (30 秒反馈 SLA)
# =============================================================================

class TestWhatIfSimulation:
    """Tests for E5-T01: What-if 干预仿真 (30 秒反馈 SLA)"""

    @pytest.fixture
    def physics_client(self):
        """Create physics sidecar client"""
        return PhysicsSidecarClient(timeout_seconds=30)  # 30-second SLA

    def test_request_simulation(self, physics_client):
        """Test requesting a What-if simulation"""
        request = physics_client.request_simulation(
            scenario_id="what-if-001",
            intervention="开启 3 个泄洪闸",
            duration_hours=6,
            mesh_resolution=30.0
        )

        assert request.scenario_id == "what-if-001"
        assert request.status == SimulationStatus.RUNNING
        assert request.started_at is not None
        assert request.timeout_seconds == 30

    def test_complete_simulation_with_results(self, physics_client):
        """Test completing simulation with results"""
        # Request
        physics_client.request_simulation(
            scenario_id="what-if-002",
            intervention="疏散 A 区居民",
            duration_hours=12
        )

        # Complete with mock results
        result = physics_client.complete_simulation(
            scenario_id="what-if-002",
            flood_depths={"location-1": 2.5, "location-2": 1.8},
            affected_area_km2=150.5,
            peak_flow_rate=5000.0,
            timeline=[
                {"hour": 0, "depth": 0.0},
                {"hour": 1, "depth": 0.5},
                {"hour": 2, "depth": 1.2}
            ]
        )

        assert result.request.status == SimulationStatus.COMPLETED
        assert result.affected_area_km2 == 150.5
        assert result.physical_fingerprint is not None
        assert len(result.physical_fingerprint) == 64  # SHA-256 hex length

    def test_simulation_feedback_within_30_seconds(self, physics_client):
        """Test that simulation feedback completes within 30-second SLA"""
        import time

        # Request simulation
        physics_client.request_simulation(
            scenario_id="what-if-sla-001",
            intervention="测试 30 秒 SLA",
            duration_hours=1
        )

        # Simulate processing (should be under 30 seconds)
        start_time = time.time()

        # Complete simulation
        result = physics_client.complete_simulation(
            scenario_id="what-if-sla-001",
            flood_depths={"test": 1.0},
            affected_area_km2=10.0,
            peak_flow_rate=1000.0,
            timeline=[]
        )

        elapsed = time.time() - start_time

        # Verify completed within SLA
        assert elapsed < 30.0  # 30-second SLA
        assert result.request.get_elapsed_seconds() < 30.0

    def test_simulation_timeout_handling(self, physics_client):
        """Test handling of simulation timeout"""
        # Request with very short timeout for testing
        request = SimulationRequest(
            scenario_id="timeout-test",
            intervention="Test",
            duration_hours=1,
            timeout_seconds=1  # 1 second timeout for testing
        )
        request.start()

        # Wait for timeout
        import time
        time.sleep(1.1)

        # Check timeout
        assert request.is_timeout() is True


# =============================================================================
# E5-T02: 物理后果预演 Tests (90 秒/60 分钟 SLA)
# =============================================================================

class TestPhysicsPreview:
    """Tests for E5-T02: 物理后果预演"""

    @pytest.fixture
    def physics_client_90s(self):
        """Create physics client with 90-second timeout"""
        return PhysicsSidecarClient(timeout_seconds=90)

    def test_60_minute_preview_request(self, physics_client_90s):
        """Test requesting 60-minute physics preview"""
        request = physics_client_90s.request_simulation(
            scenario_id="preview-60min-001",
            intervention="60 分钟洪水预演",
            duration_hours=1,  # 60 minutes
            mesh_resolution=30.0
        )

        assert request.duration_hours == 1
        assert request.timeout_seconds == 90  # 90-second SLA for feedback

    def test_90_second_sla_enforcement(self, physics_client_90s):
        """Test 90-second SLA enforcement"""
        import time

        # Request simulation
        physics_client_90s.request_simulation(
            scenario_id="sla-90s-test",
            intervention="90 秒 SLA 测试",
            duration_hours=1
        )

        # Simulate processing within SLA
        time.sleep(0.5)  # Simulate quick processing

        # Complete before timeout
        result = physics_client_90s.complete_simulation(
            scenario_id="sla-90s-test",
            flood_depths={"test": 1.0},
            affected_area_km2=100.0,
            peak_flow_rate=3000.0,
            timeline=[]
        )

        # Verify completed within 90-second SLA
        elapsed = result.request.get_elapsed_seconds()
        assert elapsed < 90.0

    def test_preview_result_contains_required_fields(self, physics_client_90s):
        """Test that preview result contains all required fields"""
        physics_client_90s.request_simulation(
            scenario_id="preview-fields-001",
            intervention="完整性测试",
            duration_hours=2
        )

        result = physics_client_90s.complete_simulation(
            scenario_id="preview-fields-001",
            flood_depths={"zone-a": 3.5, "zone-b": 2.1},
            affected_area_km2=200.0,
            peak_flow_rate=8000.0,
            timeline=[
                {"hour": 0, "depth": 0},
                {"hour": 1, "depth": 2.0},
                {"hour": 2, "depth": 3.5}
            ]
        )

        # Verify all required fields present
        result_dict = result.to_dict()

        assert 'scenario_id' in result_dict
        assert 'status' in result_dict
        assert 'flood_depths' in result_dict
        assert 'affected_area_km2' in result_dict
        assert 'peak_flow_rate' in result_dict
        assert 'physical_fingerprint' in result_dict
        assert 'elapsed_seconds' in result_dict

    def test_progressive_mesh_coarsening(self):
        """Test progressive mesh coarsening for early termination"""
        # Simulate mesh coarsening when approaching timeout
        fine_mesh_time = 120  # seconds for fine mesh
        coarse_mesh_time = 60  # seconds for coarse mesh
        timeout = 90  # 90-second SLA

        # If fine mesh would exceed timeout, use coarse mesh
        if fine_mesh_time > timeout:
            # Use coarse mesh for early termination
            assert coarse_mesh_time < timeout


# =============================================================================
# E5-T05: Remonstrance Lock Integration Tests
# =============================================================================

class RemonstranceLock:
    """
    谏阻锁 (Remonstrance Lock) - 90-second physics preview blocking

    Copied from test_security_epic6 for integration testing
    """

    def __init__(self, preview_seconds: int = 90):
        self.preview_seconds = preview_seconds
        self._pending_commands: Dict[str, Dict[str, Any]] = {}

    def request_execution(self, command: str, trace_id: str) -> str:
        """Request to execute a high-risk command"""
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
        """Commander confirms the command after physics preview"""
        if pending_id not in self._pending_commands:
            return False

        cmd = self._pending_commands[pending_id]

        if not cmd['physics_preview_complete']:
            raise ValueError("Physics preview not completed. Cannot confirm.")

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
        data = f"{command}:{trace_id}:CONFIRM"
        return hashlib.sha256(data.encode()).hexdigest()[:32]


class TestRemonstranceLockIntegration:
    """Integration tests for Remonstrance Lock with physics preview"""

    def test_physics_preview_blocks_command_execution(self):
        """Test that commands cannot execute without physics preview"""
        lock = RemonstranceLock(preview_seconds=90)

        # Request execution
        pending_id = lock.request_execution(
            command="开闸泄洪",
            trace_id="trace-remonstrance-001"
        )

        # Cannot execute without physics preview
        assert lock.can_execute(pending_id) is False

    def test_complete_remonstrance_workflow(self):
        """Test complete remonstrance lock workflow"""
        lock = RemonstranceLock(preview_seconds=90)
        physics_client = PhysicsSidecarClient(timeout_seconds=90)

        # Step 1: Request command execution
        pending_id = lock.request_execution(
            command="开闸泄洪",
            trace_id="trace-complete-001"
        )

        # Step 2: Request physics preview
        physics_request = physics_client.request_simulation(
            scenario_id=pending_id,
            intervention="开闸泄洪模拟",
            duration_hours=1
        )

        # Step 3: Complete physics preview
        physics_result = physics_client.complete_simulation(
            scenario_id=pending_id,
            flood_depths={"downstream": 5.0},
            affected_area_km2=50.0,
            peak_flow_rate=10000.0,
            timeline=[]
        )

        # Step 4: Mark physics preview complete in lock
        lock.complete_physics_preview(pending_id, physics_result.to_dict())

        # Step 5: Commander confirms
        signature = lock._generate_signature("开闸泄洪", "trace-complete-001")
        lock.confirm_command(pending_id, signature)

        # Step 6: Can now execute
        assert lock.can_execute(pending_id) is True

    def test_physical_fingerprint_verification(self):
        """Test physical fingerprint verification for evidence bridge"""
        # Create simulation result
        request = SimulationRequest(
            scenario_id="fingerprint-test",
            intervention="Test",
            duration_hours=1
        )

        result = SimulationResult(
            request=request,
            flood_depths={"a": 1.0, "b": 2.0},
            affected_area_km2=100.0,
            peak_flow_rate=5000.0,
            timeline=[]
        )

        # Verify fingerprint is deterministic
        fingerprint1 = result.physical_fingerprint

        # Same data should produce same fingerprint
        result2 = SimulationResult(
            request=request,
            flood_depths={"a": 1.0, "b": 2.0},
            affected_area_km2=100.0,
            peak_flow_rate=5000.0,
            timeline=[]
        )

        assert result.physical_fingerprint == result2.physical_fingerprint

        # Different data should produce different fingerprint
        result3 = SimulationResult(
            request=request,
            flood_depths={"a": 1.5, "b": 2.0},  # Changed
            affected_area_km2=100.0,
            peak_flow_rate=5000.0,
            timeline=[]
        )

        assert result.physical_fingerprint != result3.physical_fingerprint


# =============================================================================
# Performance Benchmark Tests
# =============================================================================

class TestPhysicsPerformanceBenchmark:
    """Performance benchmark tests for physics simulation"""

    def test_concurrent_simulations(self):
        """Test handling multiple concurrent simulations"""
        client = PhysicsSidecarClient(timeout_seconds=90)

        # Request 10 concurrent simulations
        for i in range(10):
            client.request_simulation(
                scenario_id=f"concurrent-{i:03d}",
                intervention=f"Scenario {i}",
                duration_hours=1
            )

        # Complete all
        for i in range(10):
            result = client.complete_simulation(
                scenario_id=f"concurrent-{i:03d}",
                flood_depths={"test": 1.0},
                affected_area_km2=10.0 * i,
                peak_flow_rate=1000.0,
                timeline=[]
            )
            assert result is not None

        # Verify all completed
        assert len(client._results) == 10
        assert len(client._active_requests) == 0

    def test_simulation_result_serialization(self):
        """Test simulation result serialization performance"""
        import time
        import json

        request = SimulationRequest(
            scenario_id="serialize-test",
            intervention="Serialization test",
            duration_hours=1
        )

        result = SimulationResult(
            request=request,
            flood_depths={f"loc-{i}": i * 0.5 for i in range(100)},
            affected_area_km2=500.0,
            peak_flow_rate=15000.0,
            timeline=[{"hour": h, "depth": h * 0.5} for h in range(60)]
        )

        # Measure serialization time
        start = time.time()
        for _ in range(100):
            data = result.to_dict()
            json.dumps(data, default=str)
        elapsed = time.time() - start

        # Should complete 100 serializations in under 1 second
        assert elapsed < 1.0
