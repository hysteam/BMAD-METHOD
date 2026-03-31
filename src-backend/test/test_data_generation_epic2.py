"""
Epic 2: Data Generation and Dual-Track Triggering Tests

Tests for:
- E2-T01: DGM 激发模拟预警 (DGM Simulation Warning)
- E2-T02: 真实监测数据流接入 (Real-time Monitoring Data Stream)
- E2-T03: GIS 矢量数据表生成 (GIS Vector Data Generation)

These tests validate the data generation engine and triggering system.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import hashlib
import json


# =============================================================================
# Mock Classes for Data Generation
# =============================================================================

class DataStatus:
    """Data status enumeration"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class DEMSValidator:
    """DEMS v1.0 data validator"""

    REQUIRED_FIELDS = ['type', 'coordinates', 'properties']

    @classmethod
    def validate_geojson(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate GeoJSON against DEMS v1.0"""
        errors = []

        if 'type' not in data:
            errors.append("Missing 'type' field")
            return {'is_valid': False, 'errors': errors}

        if data['type'] not in ['Feature', 'FeatureCollection', 'Point', 'LineString', 'Polygon']:
            errors.append(f"Invalid type: {data['type']}")

        # Handle FeatureCollection
        if data.get('type') == 'FeatureCollection':
            if 'features' not in data:
                errors.append("FeatureCollection missing 'features' field")
            else:
                # Validate each feature
                for i, feature in enumerate(data['features']):
                    if isinstance(feature, dict):
                        if feature.get('type') != 'Feature':
                            errors.append(f"Feature {i} is not of type 'Feature'")
                        if 'geometry' not in feature:
                            errors.append(f"Feature {i} missing 'geometry'")
        # Handle single Feature
        elif data.get('type') == 'Feature':
            if 'geometry' not in data:
                errors.append("Feature missing 'geometry' field")
            if 'properties' not in data:
                errors.append("Feature missing 'properties' field")
        # Handle geometry types
        elif data['type'] in ['Point', 'LineString', 'Polygon']:
            if 'coordinates' not in data:
                errors.append("Geometry type missing 'coordinates' field")

        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }

    @classmethod
    def validate_ontology_alignment(
        cls,
        data: Dict[str, Any],
        ontology: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate data aligns with ontology"""
        errors = []

        # Get entity types from ontology
        entity_types = set(ontology.get('entities', {}).keys())

        # Extract properties from data
        data_properties = set()

        # Handle FeatureCollection
        if data.get('type') == 'FeatureCollection':
            for feature in data.get('features', []):
                if isinstance(feature, dict) and 'properties' in feature:
                    props = feature.get('properties', {})
                    if 'feature_type' in props:
                        data_properties.add(props['feature_type'])
        # Handle single Feature
        elif data.get('type') == 'Feature':
            props = data.get('properties', {})
            if 'feature_type' in props:
                data_properties.add(props['feature_type'])

        # Check if required entity types are present
        for required in ontology.get('required_entities', []):
            if required not in data_properties:
                errors.append(f"Missing required entity: {required}")

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'aligned_properties': entity_types.intersection(data_properties)
        }


class SimulationResult:
    """Represents a DGM simulation result"""

    def __init__(
        self,
        scenario_id: str,
        flood_depths: Dict[str, float],
        affected_area_km2: float,
        peak_flow_rate: float,
        timeline: List[Dict[str, Any]]
    ):
        self.scenario_id = scenario_id
        self.flood_depths = flood_depths
        self.affected_area_km2 = affected_area_km2
        self.peak_flow_rate = peak_flow_rate
        self.timeline = timeline
        self.created_at = datetime.utcnow()
        self.status = DataStatus.COMPLETED
        self.fingerprint = self._generate_fingerprint()

    def _generate_fingerprint(self) -> str:
        """Generate SHA-256 fingerprint of simulation result"""
        data = {
            'scenario_id': self.scenario_id,
            'flood_depths': sorted(self.flood_depths.items()),
            'affected_area_km2': self.affected_area_km2,
        }
        return hashlib.sha256(str(data).encode()).hexdigest()

    def to_geojson(self) -> Dict[str, Any]:
        """Convert to GeoJSON format"""
        features = []
        for location_id, depth in self.flood_depths.items():
            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [0, 0]  # Placeholder
                },
                'properties': {
                    'location_id': location_id,
                    'flood_depth_m': depth,
                    'timestamp': self.created_at.isoformat()
                }
            })

        return {
            'type': 'FeatureCollection',
            'features': features,
            'metadata': {
                'scenario_id': self.scenario_id,
                'affected_area_km2': self.affected_area_km2,
                'peak_flow_rate': self.peak_flow_rate,
                'fingerprint': self.fingerprint
            }
        }


class DGMSimulator:
    """Data Generation Module simulator"""

    def __init__(self):
        self.results: Dict[str, SimulationResult] = {}

    def generate_warning(
        self,
        scenario_id: str,
        rainfall_mm: float,
        duration_hours: int
    ) -> SimulationResult:
        """Generate DGM simulation warning"""
        # Simulate flood depths based on rainfall
        flood_depths = {
            f"point_{i}": min(rainfall_mm / 100.0 * (1 - i * 0.1), 10.0)
            for i in range(10)
        }

        affected_area = rainfall_mm * duration_hours / 50.0
        peak_flow = rainfall_mm * 10.0

        result = SimulationResult(
            scenario_id=scenario_id,
            flood_depths=flood_depths,
            affected_area_km2=affected_area,
            peak_flow_rate=peak_flow,
            timeline=[
                {'hour': h, 'depth': rainfall_mm / 100.0 * h}
                for h in range(1, duration_hours + 1)
            ]
        )

        self.results[scenario_id] = result
        return result


class SensorDataStream:
    """Simulates real-time sensor data stream"""

    def __init__(self):
        self.readings: List[Dict[str, Any]] = []
        self.connected = False

    def connect(self) -> bool:
        """Connect to sensor stream"""
        self.connected = True
        return True

    def disconnect(self):
        """Disconnect from sensor stream"""
        self.connected = False

    def read_water_level(self, station_id: str) -> Dict[str, Any]:
        """Read water level from station"""
        if not self.connected:
            return {'error': 'Not connected'}

        reading = {
            'station_id': station_id,
            'timestamp': datetime.utcnow().isoformat(),
            'water_level_m': 3.5 + len(self.readings) * 0.1,
            'flow_rate_m3s': 150.0 + len(self.readings) * 10.0,
            'quality': 'good'
        }
        self.readings.append(reading)
        return reading

    def get_readings_count(self) -> int:
        """Get total readings count"""
        return len(self.readings)


class GISVectorGenerator:
    """GIS vector data generator"""

    def __init__(self, ontology: Dict[str, Any]):
        self.ontology = ontology
        self.generated_features: List[Dict[str, Any]] = []

    def generate_flood_boundary(
        self,
        simulation: SimulationResult,
        center: tuple = (116.4, 39.9)
    ) -> Dict[str, Any]:
        """Generate flood boundary GeoJSON"""
        # Create polygon from flood depths
        coordinates = []
        for location_id, depth in simulation.flood_depths.items():
            if depth > 0.5:  # Only include significant flooding
                # Simplified boundary generation
                offset = float(location_id.split('_')[1]) * 0.01
                coordinates.append([
                    center[0] + offset,
                    center[1] + offset
                ])

        # Create bounding polygon
        if coordinates:
            min_lon = min(c[0] for c in coordinates)
            max_lon = max(c[0] for c in coordinates)
            min_lat = min(c[1] for c in coordinates)
            max_lat = max(c[1] for c in coordinates)

            boundary_coords = [
                [min_lon, min_lat],
                [max_lon, min_lat],
                [max_lon, max_lat],
                [min_lon, max_lat],
                [min_lon, min_lat]  # Close polygon
            ]
        else:
            boundary_coords = [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]

        geojson = {
            'type': 'Feature',
            'geometry': {
                'type': 'Polygon',
                'coordinates': [boundary_coords]
            },
            'properties': {
                'feature_type': 'flood_boundary',
                'affected_area_km2': simulation.affected_area_km2,
                'peak_flow_rate': simulation.peak_flow_rate,
                'fingerprint': simulation.fingerprint,
                'generated_at': datetime.utcnow().isoformat()
            }
        }

        self.generated_features.append(geojson)
        return geojson

    def generate_risk_points(
        self,
        simulation: SimulationResult,
        risk_threshold: float = 2.0
    ) -> Dict[str, Any]:
        """Generate risk point locations"""
        features = []

        for location_id, depth in simulation.flood_depths.items():
            if depth >= risk_threshold:
                features.append({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [0, 0]
                    },
                    'properties': {
                        'feature_type': 'risk_point',
                        'location_id': location_id,
                        'risk_level': 'high' if depth > 5.0 else 'medium',
                        'flood_depth_m': depth
                    }
                })

        return {
            'type': 'FeatureCollection',
            'features': features,
            'metadata': {
                'risk_threshold': risk_threshold,
                'total_risk_points': len(features)
            }
        }


# =============================================================================
# E2-T01: DGM 激发模拟预警 Tests
# =============================================================================

class TestDGMSimulationWarning:
    """Tests for E2-T01: DGM 激发模拟预警"""

    @pytest.fixture
    def dgm_simulator(self) -> DGMSimulator:
        """Create DGM simulator"""
        return DGMSimulator()

    def test_generate_warning(self, dgm_simulator):
        """Test generating DGM simulation warning"""
        result = dgm_simulator.generate_warning(
            scenario_id="warning-001",
            rainfall_mm=100.0,
            duration_hours=3
        )

        assert result.scenario_id == "warning-001"
        assert len(result.flood_depths) == 10
        assert result.affected_area_km2 > 0
        assert result.peak_flow_rate > 0
        assert result.status == DataStatus.COMPLETED

    def test_warning_fingerprint_generation(self, dgm_simulator):
        """Test fingerprint generation for warning"""
        result = dgm_simulator.generate_warning(
            scenario_id="warning-002",
            rainfall_mm=150.0,
            duration_hours=6
        )

        # Fingerprint should be SHA-256 hex
        assert len(result.fingerprint) == 64
        assert all(c in '0123456789abcdef' for c in result.fingerprint)

    def test_warning_to_geojson(self, dgm_simulator):
        """Test converting warning to GeoJSON"""
        result = dgm_simulator.generate_warning(
            scenario_id="warning-003",
            rainfall_mm=200.0,
            duration_hours=12
        )

        geojson = result.to_geojson()

        assert geojson['type'] == 'FeatureCollection'
        assert len(geojson['features']) == 10
        assert 'fingerprint' in geojson['metadata']
        assert 'affected_area_km2' in geojson['metadata']

    def test_warning_timeline_generation(self, dgm_simulator):
        """Test timeline generation in warning"""
        result = dgm_simulator.generate_warning(
            scenario_id="warning-004",
            rainfall_mm=100.0,
            duration_hours=5
        )

        assert len(result.timeline) == 5
        assert result.timeline[0]['hour'] == 1
        assert result.timeline[4]['hour'] == 5


# =============================================================================
# E2-T02: 真实监测数据流接入 Tests
# =============================================================================

class TestRealTimeSensorStream:
    """Tests for E2-T02: 真实监测数据流接入"""

    @pytest.fixture
    def sensor_stream(self) -> SensorDataStream:
        """Create sensor data stream"""
        return SensorDataStream()

    def test_connect_to_stream(self, sensor_stream):
        """Test connecting to sensor stream"""
        result = sensor_stream.connect()

        assert result is True
        assert sensor_stream.connected is True

    def test_read_water_level(self, sensor_stream):
        """Test reading water level from stream"""
        sensor_stream.connect()

        reading = sensor_stream.read_water_level("station-001")

        assert 'station_id' in reading
        assert 'water_level_m' in reading
        assert 'flow_rate_m3s' in reading
        assert reading['station_id'] == "station-001"
        assert reading['quality'] == 'good'

    def test_read_without_connection_fails(self, sensor_stream):
        """Test reading without connection fails"""
        reading = sensor_stream.read_water_level("station-001")

        assert 'error' in reading
        assert reading['error'] == 'Not connected'

    def test_multiple_readings(self, sensor_stream):
        """Test multiple sequential readings"""
        sensor_stream.connect()

        for i in range(5):
            sensor_stream.read_water_level(f"station-{i:03d}")

        assert sensor_stream.get_readings_count() == 5

    def test_reading_timestamp(self, sensor_stream):
        """Test reading includes timestamp"""
        sensor_stream.connect()
        reading = sensor_stream.read_water_level("station-001")

        assert 'timestamp' in reading
        # Verify ISO format timestamp
        from datetime import datetime
        datetime.fromisoformat(reading['timestamp'])


# =============================================================================
# E2-T03: GIS 矢量数据表生成 Tests
# =============================================================================

class TestGISVectorGeneration:
    """Tests for E2-T03: GIS 矢量数据表生成"""

    @pytest.fixture
    def ontology(self) -> Dict[str, Any]:
        """Sample ontology for validation"""
        return {
            'entities': {
                'flood_boundary': {'label': '洪水边界', 'type': 'polygon'},
                'risk_point': {'label': '风险点', 'type': 'point'},
                'water_depth': {'label': '水深', 'type': 'measurement'}
            },
            'required_entities': ['flood_boundary']
        }

    @pytest.fixture
    def vector_generator(self, ontology) -> GISVectorGenerator:
        """Create GIS vector generator"""
        return GISVectorGenerator(ontology)

    @pytest.fixture
    def sample_simulation(self) -> SimulationResult:
        """Create sample simulation result"""
        return SimulationResult(
            scenario_id="gis-test-001",
            flood_depths={
                'point_0': 0.5,
                'point_1': 1.5,
                'point_2': 3.0,
                'point_3': 5.5,
                'point_4': 0.2
            },
            affected_area_km2=25.0,
            peak_flow_rate=500.0,
            timeline=[]
        )

    def test_generate_flood_boundary(
        self,
        vector_generator,
        sample_simulation
    ):
        """Test generating flood boundary GeoJSON"""
        geojson = vector_generator.generate_flood_boundary(sample_simulation)

        assert geojson['type'] == 'Feature'
        assert geojson['geometry']['type'] == 'Polygon'
        assert 'coordinates' in geojson['geometry']
        assert geojson['properties']['feature_type'] == 'flood_boundary'
        assert 'fingerprint' in geojson['properties']

    def test_generate_risk_points(
        self,
        vector_generator,
        sample_simulation
    ):
        """Test generating risk points"""
        result = vector_generator.generate_risk_points(
            sample_simulation,
            risk_threshold=2.0
        )

        assert result['type'] == 'FeatureCollection'
        # Only points with depth >= 2.0 should be included
        assert len(result['features']) == 2  # point_2 (3.0) and point_3 (5.5)
        assert result['metadata']['total_risk_points'] == 2

    def test_dem_validation_geojson(
        self,
        vector_generator,
        sample_simulation
    ):
        """Test DEMS validation of generated GeoJSON"""
        geojson = vector_generator.generate_flood_boundary(sample_simulation)

        result = DEMSValidator.validate_geojson(geojson)

        assert result['is_valid'] is True
        assert len(result['errors']) == 0

    def test_dem_ontology_alignment(
        self,
        vector_generator,
        sample_simulation,
        ontology
    ):
        """Test DEMS ontology alignment validation"""
        geojson = vector_generator.generate_flood_boundary(sample_simulation)

        result = DEMSValidator.validate_ontology_alignment(geojson, ontology)

        assert result['is_valid'] is True
        assert len(result['aligned_properties']) > 0

    def test_invalid_geojson_missing_type(self):
        """Test DEMS validation catches missing type"""
        invalid_data = {
            'geometry': {'type': 'Point', 'coordinates': [0, 0]},
            'properties': {}
        }

        result = DEMSValidator.validate_geojson(invalid_data)

        assert result['is_valid'] is False
        assert "Missing 'type' field" in result['errors']

    def test_fingerprint_in_geojson_metadata(
        self,
        vector_generator,
        sample_simulation
    ):
        """Test that simulation fingerprint is included in GeoJSON"""
        geojson = vector_generator.generate_flood_boundary(sample_simulation)

        assert geojson['properties']['fingerprint'] == sample_simulation.fingerprint


# =============================================================================
# Integration Tests: Data Generation Pipeline
# =============================================================================

class TestDataGenerationPipeline:
    """Integration tests for complete data generation pipeline"""

    def test_full_dgm_to_gis_workflow(self):
        """Test complete workflow: DGM warning -> GIS vector generation"""
        # Step 1: Generate DGM warning
        dgm = DGMSimulator()
        simulation = dgm.generate_warning(
            scenario_id="integration-001",
            rainfall_mm=150.0,
            duration_hours=6
        )

        # Step 2: Generate GIS vectors
        ontology = {
            'entities': {'flood_boundary': {'label': '洪水边界', 'type': 'polygon'}},
            'required_entities': ['flood_boundary']
        }
        generator = GISVectorGenerator(ontology)

        boundary = generator.generate_flood_boundary(simulation)
        risk_points = generator.generate_risk_points(simulation)

        # Validate outputs
        assert simulation.status == DataStatus.COMPLETED
        assert boundary['properties']['feature_type'] == 'flood_boundary'
        assert risk_points['type'] == 'FeatureCollection'

        # Validate DEMS compliance
        boundary_valid = DEMSValidator.validate_geojson(boundary)
        assert boundary_valid['is_valid'] is True

    def test_sensor_stream_with_dgm_simulation(self):
        """Test integrating sensor stream with DGM simulation"""
        # Generate DGM simulation
        dgm = DGMSimulator()
        simulation = dgm.generate_warning(
            scenario_id="sensor-fusion-001",
            rainfall_mm=100.0,
            duration_hours=3
        )

        # Read sensor data
        sensor = SensorDataStream()
        sensor.connect()

        readings = []
        for i in range(3):
            reading = sensor.read_water_level(f"station-{i:03d}")
            readings.append(reading)

        # Verify both data sources
        assert len(simulation.flood_depths) == 10
        assert len(readings) == 3
        assert all(r['quality'] == 'good' for r in readings)

    def test_multiple_simulations_concurrent(self):
        """Test handling multiple concurrent simulations"""
        dgm = DGMSimulator()

        scenarios = [
            ("scenario-A", 100.0, 3),
            ("scenario-B", 150.0, 6),
            ("scenario-C", 200.0, 12)
        ]

        results = []
        for scenario_id, rainfall, duration in scenarios:
            result = dgm.generate_warning(scenario_id, rainfall, duration)
            results.append(result)

        # Verify all simulations completed
        assert len(dgm.results) == 3
        assert all(r.status == DataStatus.COMPLETED for r in results)
        assert len(set(r.fingerprint for r in results)) == 3  # Unique fingerprints


# =============================================================================
# Dual-Track Trigger Tests
# =============================================================================

class TestDualTrackTrigger:
    """Tests for dual-track trigger (real + simulated data)"""

    def test_simulated_data_trigger(self):
        """Test trigger from simulated data"""
        dgm = DGMSimulator()
        simulation = dgm.generate_warning(
            scenario_id="sim-trigger-001",
            rainfall_mm=120.0,
            duration_hours=4
        )

        # Simulated data should trigger downstream
        assert simulation.status == DataStatus.COMPLETED
        assert simulation.affected_area_km2 > 0

    def test_real_sensor_data_trigger(self):
        """Test trigger from real sensor data"""
        sensor = SensorDataStream()
        sensor.connect()

        # Simulate threshold crossing
        critical_readings = []
        for i in range(5):
            reading = sensor.read_water_level(f"station-{i:03d}")
            if reading.get('water_level_m', 0) > 3.0:
                critical_readings.append(reading)

        # Should detect critical readings
        assert len(critical_readings) > 0

    def test_dual_track_unified_output(self):
        """Test that both tracks produce unified output format"""
        # Track 1: Simulated
        dgm = DGMSimulator()
        sim_result = dgm.generate_warning(
            scenario_id="dual-sim-001",
            rainfall_mm=100.0,
            duration_hours=3
        )
        sim_geojson = sim_result.to_geojson()

        # Track 2: Sensor (converted to same format)
        sensor = SensorDataStream()
        sensor.connect()
        reading = sensor.read_water_level("station-001")

        sensor_geojson = {
            'type': 'FeatureCollection',
            'features': [{
                'type': 'Feature',
                'geometry': {'type': 'Point', 'coordinates': [0, 0]},
                'properties': reading
            }]
        }

        # Both should be valid GeoJSON
        assert DEMSValidator.validate_geojson(sim_geojson)['is_valid']
        assert DEMSValidator.validate_geojson(sensor_geojson)['is_valid']
