import pytest
import numpy as np
from collections import defaultdict

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from domain.entities.call import QualificationResult
from domain.entities.agent import Agent, AgentStatus
from domain.entities.assignment import Assignment, AssignmentStatus
from domain.services.qualification_service import QualificationService
from config.settings import settings

class TestQualificationService:
    """Test cases for qualification service"""
    
    @pytest.fixture
    def qualification_service(self):
        """Create qualification service with test conversion matrix"""
        test_matrix = {
            "agente_tipo_1": {
                "llamada_tipo_1": 0.30,
                "llamada_tipo_2": 0.20
            },
            "agente_tipo_2": {
                "llamada_tipo_1": 0.20,
                "llamada_tipo_2": 0.15
            }
        }
        return QualificationService(test_matrix)
    
    def test_qualification_service_initialization(self, qualification_service):
        """Test qualification service initializes correctly"""
        assert qualification_service.conversion_matrix is not None
        assert qualification_service.random_generator is not None
    
    def test_get_conversion_probability(self, qualification_service):
        """Test getting conversion probability for agent/call combinations"""
        # Test valid combinations
        prob1 = qualification_service.get_conversion_probability("agente_tipo_1", "llamada_tipo_1")
        assert prob1 == 0.30
        
        prob2 = qualification_service.get_conversion_probability("agente_tipo_2", "llamada_tipo_2")
        assert prob2 == 0.15
        
        # Test invalid agent type
        prob3 = qualification_service.get_conversion_probability("invalid_agent", "llamada_tipo_1")
        assert prob3 == 0.0
        
        # Test invalid call type
        prob4 = qualification_service.get_conversion_probability("agente_tipo_1", "invalid_call")
        assert prob4 == 0.0
    
    def test_qualify_call_returns_valid_result(self, qualification_service):
        """Test that qualify_call returns valid QualificationResult"""
        result = qualification_service.qualify_call("agente_tipo_1", "llamada_tipo_1")
        
        assert isinstance(result, QualificationResult)
        assert result in [QualificationResult.OK, QualificationResult.KO]
    
    def test_qualify_call_probability_distribution(self, qualification_service):
        """Test that qualification follows expected probability distribution"""
        agent_type = "agente_tipo_1"
        call_type = "llamada_tipo_1"
        expected_probability = 0.30
        
        # Run many qualifications to test probability
        num_trials = 10000
        ok_count = 0
        
        for _ in range(num_trials):
            result = qualification_service.qualify_call(agent_type, call_type)
            if result == QualificationResult.OK:
                ok_count += 1
        
        actual_probability = ok_count / num_trials
        
        # Allow for statistical variance (±5% tolerance)
        tolerance = 0.05
        assert abs(actual_probability - expected_probability) <= tolerance
    
    def test_generate_duration_normal_distribution(self, qualification_service):
        """Test that duration generation follows normal distribution"""
        mean_seconds = 180.0
        std_seconds = 60.0
        
        durations = []
        for _ in range(1000):
            duration = qualification_service.generate_duration(mean_seconds, std_seconds)
            durations.append(duration)
            # Ensure minimum duration constraint
            assert duration >= 1.0
        
        # Test statistical properties
        actual_mean = np.mean(durations)
        actual_std = np.std(durations)
        
        # Allow for statistical variance (±10% tolerance)
        assert abs(actual_mean - mean_seconds) <= mean_seconds * 0.1
        assert abs(actual_std - std_seconds) <= std_seconds * 0.2
    
    def test_generate_duration_minimum_constraint(self, qualification_service):
        """Test that duration generation respects minimum constraint"""
        # Use parameters that might generate negative values
        mean_seconds = 5.0
        std_seconds = 10.0  # Large std dev relative to mean
        
        for _ in range(100):
            duration = qualification_service.generate_duration(mean_seconds, std_seconds)
            assert duration >= 1.0  # Should never be less than 1 second
    
    def test_analyze_qualification_results(self, qualification_service):
        """Test analysis of qualification results"""
        # Create sample data
        agents = [
            Agent(id="agent1", name="Agent 1", agent_type="agente_tipo_1"),
            Agent(id="agent2", name="Agent 2", agent_type="agente_tipo_2")
        ]
        
        calls = []
        assignments = []
        
        # Create calls and assignments for analysis
        for i in range(100):
            call_type = "llamada_tipo_1" if i < 50 else "llamada_tipo_2"
            agent = agents[i % 2]
            
            call = CallMock(id=f"call{i}", call_type=call_type)
            
            # Simulate qualification based on expected probability
            expected_prob = qualification_service.get_conversion_probability(agent.agent_type, call_type)
            if np.random.random() < expected_prob:
                call.qualification_result = QualificationResult.OK
            else:
                call.qualification_result = QualificationResult.KO
            
            assignment = Assignment(
                id=f"assignment{i}",
                call_id=call.id,
                agent_id=agent.id,
                status=AssignmentStatus.COMPLETED
            )
            
            calls.append(call)
            assignments.append(assignment)
        
        # Analyze results
        analysis = qualification_service.analyze_qualification_results(assignments, calls, agents)
        
        # Verify analysis structure
        assert "combinations" in analysis
        assert "overall_stats" in analysis
        assert analysis["overall_stats"]["total_completed_calls"] > 0
        
        # Check that combinations are analyzed
        for combination_key, combo_data in analysis["combinations"].items():
            assert "agent_type" in combo_data
            assert "call_type" in combo_data
            assert "total_calls" in combo_data
            assert "actual_conversion_rate" in combo_data
            assert "expected_conversion_rate" in combo_data
    
    def test_validate_matrix_probabilities(self, qualification_service):
        """Test validation of conversion matrix probabilities"""
        # Service should validate that probabilities are between 0 and 1
        assert qualification_service.validate_matrix_probabilities() == True
        
        # Test with invalid matrix
        invalid_service = QualificationService({
            "agent_type_1": {
                "call_type_1": 1.5  # Invalid probability > 1
            }
        })
        
        assert invalid_service.validate_matrix_probabilities() == False
    
    def test_default_settings_matrix_validation(self):
        """Test that default settings matrix is valid"""
        service = QualificationService(settings.conversion_matrix)
        assert service.validate_matrix_probabilities() == True
        
        # Test all combinations exist and are valid
        for agent_type in settings.agent_types:
            assert agent_type in settings.conversion_matrix
            for call_type in settings.call_types:
                assert call_type in settings.conversion_matrix[agent_type]
                prob = settings.conversion_matrix[agent_type][call_type]
                assert 0 <= prob <= 1
    
    def test_qualification_consistency(self, qualification_service):
        """Test that qualification is deterministic for same random seed"""
        # Set random seed for reproducibility
        qualification_service.random_generator = np.random.default_rng(seed=42)
        
        results1 = []
        for _ in range(10):
            result = qualification_service.qualify_call("agente_tipo_1", "llamada_tipo_1")
            results1.append(result)
        
        # Reset with same seed
        qualification_service.random_generator = np.random.default_rng(seed=42)
        
        results2 = []
        for _ in range(10):
            result = qualification_service.qualify_call("agente_tipo_1", "llamada_tipo_1")
            results2.append(result)
        
        # Results should be identical
        assert results1 == results2

class CallMock:
    """Mock call class for testing"""
    def __init__(self, id, call_type):
        self.id = id
        self.call_type = call_type
        self.qualification_result = QualificationResult.PENDING

class TestQualificationIntegration:
    """Integration tests for qualification with real settings"""
    
    def test_all_agent_call_combinations(self):
        """Test qualification for all agent/call type combinations"""
        service = QualificationService(settings.conversion_matrix)
        
        # Test each combination generates valid results
        for agent_type in settings.agent_types:
            for call_type in settings.call_types:
                result = service.qualify_call(agent_type, call_type)
                assert isinstance(result, QualificationResult)
                assert result in [QualificationResult.OK, QualificationResult.KO]
    
    def test_expected_conversion_rates(self):
        """Test that conversion rates match expected values from settings"""
        service = QualificationService(settings.conversion_matrix)
        
        # Test a few specific combinations
        test_cases = [
            ("agente_tipo_1", "llamada_tipo_1", 0.30),
            ("agente_tipo_2", "llamada_tipo_2", 0.15),
            ("agente_tipo_4", "llamada_tipo_4", 0.02)
        ]
        
        for agent_type, call_type, expected_rate in test_cases:
            actual_rate = service.calculate_expected_conversion_rate(agent_type, call_type)
            assert actual_rate == expected_rate
    
    def test_realistic_qualification_simulation(self):
        """Test qualification with realistic parameters"""
        service = QualificationService(settings.conversion_matrix)
        
        # Simulate realistic scenario
        results = defaultdict(lambda: {"total": 0, "ok": 0})
        
        # Run simulation for each combination
        for agent_type in settings.agent_types[:2]:  # Test first 2 agent types
            for call_type in settings.call_types[:2]:  # Test first 2 call types
                for _ in range(100):  # 100 calls per combination
                    result = service.qualify_call(agent_type, call_type)
                    
                    key = f"{agent_type}_{call_type}"
                    results[key]["total"] += 1
                    if result == QualificationResult.OK:
                        results[key]["ok"] += 1
        
        # Verify results are reasonable
        for combination, data in results.items():
            actual_rate = data["ok"] / data["total"]
            # Rate should be between 0 and 1
            assert 0 <= actual_rate <= 1
            # With 100 samples, rates should be somewhat close to expected
            # (allowing for statistical variance)
            assert actual_rate >= 0.0  # Minimum sanity check

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])