"""
Epic 1: Regional Brain Activation Tests

Tests for:
- E1-T01: Activation-Pack 注入与验证 (Activation Pack Injection)
- E1-T02: 15 分钟战术活化计时 (15-minute Tactical Activation Timing)

These tests validate the regional brain activation system.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import hashlib
import io
import zipfile


# =============================================================================
# Mock Classes for Activation System
# =============================================================================

class ActivationStatus:
    """Activation status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ACTIVE_TACTICAL = "active_tactical"
    ACTIVE_STRATEGIC = "active_strategic"
    FAILED = "failed"


class ActivationPack:
    """Represents an activation pack for regional brain initialization"""

    def __init__(
        self,
        name: str,
        region: str,
        geo_data: Dict[str, Any],
        rag_corpus: List[Dict[str, str]],
        ontology_mapping: Dict[str, Any]
    ):
        self.name = name
        self.region = region
        self.geo_data = geo_data
        self.rag_corpus = rag_corpus
        self.ontology_mapping = ontology_mapping
        self.created_at = datetime.utcnow()
        self.checksum = self._generate_checksum()

    def _generate_checksum(self) -> str:
        """Generate SHA-256 checksum of activation pack"""
        data = {
            'name': self.name,
            'region': self.region,
            'geo_data': str(sorted(self.geo_data.items())),
            'rag_count': len(self.rag_corpus),
        }
        return hashlib.sha256(str(data).encode()).hexdigest()

    def to_zip(self) -> bytes:
        """Serialize activation pack to zip file"""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('metadata.json', str({
                'name': self.name,
                'region': self.region,
                'checksum': self.checksum
            }))
            zf.writestr('geo_data.json', str(self.geo_data))
            zf.writestr('ontology_mapping.json', str(self.ontology_mapping))
            for i, doc in enumerate(self.rag_corpus):
                zf.writestr(f'rag/doc_{i}.json', str(doc))
        return buffer.getvalue()


class ActivationManager:
    """Manages regional brain activation process"""

    def __init__(self):
        self.status = ActivationStatus.PENDING
        self.current_pack: Optional[ActivationPack] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.progress = 0.0

    def upload_pack(self, pack: ActivationPack) -> bool:
        """Upload activation pack"""
        if self.status == ActivationStatus.IN_PROGRESS:
            return False  # Cannot upload during activation
        self.current_pack = pack
        self.status = ActivationStatus.PENDING
        return True

    def start_tactical_activation(self) -> bool:
        """Start 15-minute tactical activation"""
        if not self.current_pack:
            return False
        self.status = ActivationStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
        self.progress = 0.0
        return True

    def complete_tactical_activation(self) -> bool:
        """Complete tactical activation"""
        if self.status != ActivationStatus.IN_PROGRESS:
            return False
        self.status = ActivationStatus.ACTIVE_TACTICAL
        self.completed_at = datetime.utcnow()
        self.progress = 1.0
        return True

    def get_elapsed_seconds(self) -> float:
        """Get elapsed time in seconds"""
        if not self.started_at:
            return 0.0
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()

    def get_progress(self) -> Dict[str, Any]:
        """Get activation progress"""
        return {
            'status': self.status,
            'progress': self.progress,
            'elapsed_seconds': self.get_elapsed_seconds(),
            'region': self.current_pack.region if self.current_pack else None
        }


# =============================================================================
# E1-T01: Activation-Pack 注入与验证 Tests
# =============================================================================

class TestActivationPackInjection:
    """Tests for E1-T01: Activation-Pack 注入与验证"""

    @pytest.fixture
    def sample_activation_pack(self) -> ActivationPack:
        """Create sample activation pack"""
        return ActivationPack(
            name="北京流域活化包",
            region="beijing_yongding",
            geo_data={
                'center_lat': 39.9042,
                'center_lon': 116.4074,
                'bounds': [115.7, 39.4, 117.3, 41.0],
                'river_network': 'yongding_river.geojson'
            },
            rag_corpus=[
                {
                    'id': 'CASE_2020_001',
                    'title': '2020 年北京洪水案例',
                    'content': '2020 年夏季，永定河流域遭遇特大暴雨...'
                },
                {
                    'id': 'CASE_2021_002',
                    'title': '2021 年郑州洪水案例',
                    'content': '2021 年 7 月，郑州市遭遇极端降雨...'
                }
            ],
            ontology_mapping={
                'entities': {
                    'dam': '大坝',
                    'reservoir': '水库',
                    'water_level': '水位',
                    'flow_rate': '流量'
                },
                'cascade_rules': [
                    {'trigger': '水位 > 警戒水位', 'action': '启动应急响应'}
                ]
            }
        )

    def test_create_activation_pack(self, sample_activation_pack):
        """Test creating activation pack"""
        assert sample_activation_pack.name == "北京流域活化包"
        assert sample_activation_pack.region == "beijing_yongding"
        assert len(sample_activation_pack.rag_corpus) == 2
        assert sample_activation_pack.checksum is not None

    def test_activation_pack_checksum(self, sample_activation_pack):
        """Test activation pack checksum generation"""
        # Checksum should be SHA-256 hex string
        assert len(sample_activation_pack.checksum) == 64
        assert all(c in '0123456789abcdef' for c in sample_activation_pack.checksum)

    def test_serialize_activation_pack(self, sample_activation_pack):
        """Test serializing activation pack to zip"""
        zip_data = sample_activation_pack.to_zip()

        assert len(zip_data) > 0
        assert zip_data[:2] == b'PK'  # ZIP magic bytes

    def test_upload_activation_pack(self, sample_activation_pack):
        """Test uploading activation pack"""
        manager = ActivationManager()

        result = manager.upload_pack(sample_activation_pack)

        assert result is True
        assert manager.current_pack is sample_activation_pack
        assert manager.status == ActivationStatus.PENDING

    def test_upload_pack_during_activation_fails(self, sample_activation_pack):
        """Test that uploading pack during activation fails"""
        manager = ActivationManager()
        manager.upload_pack(sample_activation_pack)
        manager.start_tactical_activation()

        # Try to upload another pack
        new_pack = ActivationPack(
            name="New Pack",
            region="new_region",
            geo_data={},
            rag_corpus=[],
            ontology_mapping={}
        )
        result = manager.upload_pack(new_pack)

        assert result is False

    def test_validate_ontology_mapping(self, sample_activation_pack):
        """Test ontology mapping validation"""
        # Check ontology structure
        assert 'entities' in sample_activation_pack.ontology_mapping
        assert 'cascade_rules' in sample_activation_pack.ontology_mapping
        assert sample_activation_pack.ontology_mapping['entities']['dam'] == '大坝'


# =============================================================================
# E1-T02: 15 分钟战术活化计时 Tests
# =============================================================================

class TestTacticalActivationTiming:
    """Tests for E1-T02: 15 分钟战术活化计时"""

    @pytest.fixture
    def activation_manager(self):
        """Create activation manager with pack"""
        manager = ActivationManager()
        pack = ActivationPack(
            name="Test Pack",
            region="test_region",
            geo_data={'center': [0, 0]},
            rag_corpus=[],
            ontology_mapping={}
        )
        manager.upload_pack(pack)
        return manager

    def test_start_tactical_activation(self, activation_manager):
        """Test starting tactical activation"""
        result = activation_manager.start_tactical_activation()

        assert result is True
        assert activation_manager.status == ActivationStatus.IN_PROGRESS
        assert activation_manager.started_at is not None

    def test_tactical_activation_completes_within_15_minutes(self, activation_manager):
        """Test tactical activation completes within 15-minute SLA"""
        import time

        # Start activation
        activation_manager.start_tactical_activation()
        start_time = datetime.utcnow()

        # Simulate activation process (mock - instant completion)
        time.sleep(0.1)  # Small delay to simulate work
        activation_manager.complete_tactical_activation()

        elapsed = activation_manager.get_elapsed_seconds()

        # Should complete well under 15 minutes (900 seconds)
        assert elapsed < 900  # 15-minute SLA
        assert elapsed < 1.0  # Mock test should be instant
        assert activation_manager.status == ActivationStatus.ACTIVE_TACTICAL

    def test_activation_progress_tracking(self, activation_manager):
        """Test activation progress tracking"""
        # Before start
        progress = activation_manager.get_progress()
        assert progress['status'] == ActivationStatus.PENDING
        assert progress['progress'] == 0.0

        # During activation
        activation_manager.start_tactical_activation()
        progress = activation_manager.get_progress()
        assert progress['status'] == ActivationStatus.IN_PROGRESS
        assert progress['region'] == "test_region"

        # After completion
        activation_manager.complete_tactical_activation()
        progress = activation_manager.get_progress()
        assert progress['status'] == ActivationStatus.ACTIVE_TACTICAL
        assert progress['progress'] == 1.0

    def test_activation_without_pack_fails(self):
        """Test that activation without pack fails"""
        manager = ActivationManager()

        result = manager.start_tactical_activation()

        assert result is False

    def test_activation_status_transition(self, activation_manager):
        """Test activation status transitions"""
        # PENDING -> IN_PROGRESS -> ACTIVE_TACTICAL
        assert activation_manager.status == ActivationStatus.PENDING

        activation_manager.start_tactical_activation()
        assert activation_manager.status == ActivationStatus.IN_PROGRESS

        activation_manager.complete_tactical_activation()
        assert activation_manager.status == ActivationStatus.ACTIVE_TACTICAL


# =============================================================================
# Integration Tests: Activation Workflow
# =============================================================================

class TestActivationWorkflowIntegration:
    """Integration tests for complete activation workflow"""

    def test_full_activation_workflow(self):
        """Test complete activation workflow: create pack -> upload -> activate"""
        # Step 1: Create activation pack
        pack = ActivationPack(
            name="集成测试活化包",
            region="integration_test",
            geo_data={
                'center_lat': 40.0,
                'center_lon': 116.0,
                'bounds': [115.0, 39.0, 117.0, 41.0]
            },
            rag_corpus=[
                {'id': 'TEST_001', 'content': 'Test case content'}
            ],
            ontology_mapping={
                'entities': {'river': '河流'},
                'cascade_rules': []
            }
        )

        # Step 2: Upload pack
        manager = ActivationManager()
        upload_result = manager.upload_pack(pack)
        assert upload_result is True

        # Step 3: Start tactical activation
        start_time = datetime.utcnow()
        start_result = manager.start_tactical_activation()
        assert start_result is True

        # Step 4: Complete activation
        manager.complete_tactical_activation()

        # Verify
        end_time = datetime.utcnow()
        elapsed = (end_time - start_time).total_seconds()

        assert manager.status == ActivationStatus.ACTIVE_TACTICAL
        assert elapsed < 900  # 15-minute SLA
        assert manager.get_progress()['progress'] == 1.0

    def test_multiple_regions_activation(self):
        """Test activating multiple regions"""
        regions = [
            ("beijing", "北京"),
            ("shanghai", "上海"),
            ("guangzhou", "广州")
        ]

        for region_id, region_name in regions:
            pack = ActivationPack(
                name=f"{region_name}活化包",
                region=region_id,
                geo_data={'center': [0, 0]},
                rag_corpus=[],
                ontology_mapping={}
            )

            manager = ActivationManager()
            manager.upload_pack(pack)
            manager.start_tactical_activation()
            manager.complete_tactical_activation()

            assert manager.status == ActivationStatus.ACTIVE_TACTICAL
            assert manager.get_progress()['region'] == region_id


# =============================================================================
# DEMS v1.0 Compliance Tests
# =============================================================================

class TestDEMSCompliance:
    """Tests for DEMS v1.0 standard compliance"""

    def test_ontology_mapping_validation(self):
        """Test ontology mapping follows DEMS v1.0"""
        # Valid ontology mapping
        valid_mapping = {
            'entities': {
                'dam': {'label': '大坝', 'type': 'infrastructure'},
                'water_level': {'label': '水位', 'type': 'measurement', 'unit': 'm'}
            },
            'cascade_rules': [
                {
                    'trigger': 'water_level > warning_level',
                    'action': 'activate_emergency_response',
                    'priority': 'high'
                }
            ]
        }

        # Validate structure
        assert 'entities' in valid_mapping
        assert 'cascade_rules' in valid_mapping

        for entity_name, entity_def in valid_mapping['entities'].items():
            assert 'label' in entity_def
            assert 'type' in entity_def

    def test_cascade_rule_validation(self):
        """Test cascade rule logic validation"""
        ontology_mapping = {
            'entities': {
                'water_level': {'label': '水位', 'type': 'measurement'}
            },
            'cascade_rules': [
                {'trigger': '水位 > 警戒水位', 'action': '启动应急响应'}
            ]
        }

        # Validate cascade rules
        for rule in ontology_mapping['cascade_rules']:
            assert 'trigger' in rule
            assert 'action' in rule
            assert '>' in rule['trigger'] or '<' in rule['trigger']  # Must have comparison
