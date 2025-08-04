import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict

from domain.entities.call import Call, QualificationResult
from domain.entities.agent import Agent
from domain.entities.assignment import Assignment

class QualificationService:
    """Domain service for call qualification based on conversion matrix"""
    
    def __init__(self, conversion_matrix: Dict[str, Dict[str, float]]):
        """
        Initialize with conversion probability matrix
        
        Args:
            conversion_matrix: Dict mapping agent_type -> call_type -> probability
        """
        self.conversion_matrix = conversion_matrix
        self.random_generator = np.random.default_rng()
    
    def qualify_call(self, agent_type: str, call_type: str) -> QualificationResult:
        """
        Qualify a call based on agent type and call type using binomial distribution
        
        Args:
            agent_type: Type of agent handling the call
            call_type: Type of the call
            
        Returns:
            QualificationResult: OK or KO based on probability
        """
        # Get conversion probability
        probability = self.get_conversion_probability(agent_type, call_type)
        
        # Use binomial distribution (n=1 for single trial)
        result = self.random_generator.binomial(n=1, p=probability)
        
        return QualificationResult.OK if result == 1 else QualificationResult.KO
    
    def get_conversion_probability(self, agent_type: str, call_type: str) -> float:
        """Get conversion probability for agent type and call type combination"""
        if agent_type not in self.conversion_matrix:
            return 0.0
        
        if call_type not in self.conversion_matrix[agent_type]:
            return 0.0
        
        return self.conversion_matrix[agent_type][call_type]
    
    def calculate_expected_conversion_rate(self, agent_type: str, call_type: str) -> float:
        """Calculate expected conversion rate for a combination"""
        return self.get_conversion_probability(agent_type, call_type)
    
    def generate_duration(self, mean_seconds: float, std_seconds: float) -> float:
        """
        Generate call duration using normal distribution
        
        Args:
            mean_seconds: Mean duration in seconds
            std_seconds: Standard deviation in seconds
            
        Returns:
            Duration in seconds (minimum 1 second)
        """
        duration = self.random_generator.normal(mean_seconds, std_seconds)
        return max(1.0, duration)  # Ensure minimum 1 second duration
    
    def analyze_qualification_results(self, assignments: List[Assignment], 
                                    calls: List[Call], agents: List[Agent]) -> Dict:
        """
        Analyze qualification results and compare with expected rates
        
        Returns:
            Dict with analysis results
        """
        # Create lookup maps
        call_map = {call.id: call for call in calls}
        agent_map = {agent.id: agent for agent in agents}
        
        # Group results by agent_type and call_type
        results_by_combination = defaultdict(list)
        
        for assignment in assignments:
            if assignment.status.value != "COMPLETED":
                continue
                
            call = call_map.get(assignment.call_id)
            agent = agent_map.get(assignment.agent_id)
            
            if not call or not agent:
                continue
            
            key = (agent.agent_type, call.call_type)
            results_by_combination[key].append(call.qualification_result)
        
        # Calculate actual vs expected rates
        analysis = {
            "combinations": {},
            "overall_stats": {
                "total_completed_calls": 0,
                "total_ok_calls": 0,
                "overall_conversion_rate": 0.0
            }
        }
        
        total_completed = 0
        total_ok = 0
        
        for (agent_type, call_type), results in results_by_combination.items():
            ok_count = sum(1 for r in results if r == QualificationResult.OK)
            total_calls = len(results)
            actual_rate = ok_count / total_calls if total_calls > 0 else 0.0
            expected_rate = self.get_conversion_probability(agent_type, call_type)
            
            analysis["combinations"][f"{agent_type}_{call_type}"] = {
                "agent_type": agent_type,
                "call_type": call_type,
                "total_calls": total_calls,
                "ok_calls": ok_count,
                "ko_calls": total_calls - ok_count,
                "actual_conversion_rate": actual_rate,
                "expected_conversion_rate": expected_rate,
                "rate_difference": actual_rate - expected_rate,
                "rate_difference_percentage": ((actual_rate - expected_rate) / expected_rate * 100) if expected_rate > 0 else 0
            }
            
            total_completed += total_calls
            total_ok += ok_count
        
        analysis["overall_stats"] = {
            "total_completed_calls": total_completed,
            "total_ok_calls": total_ok,
            "overall_conversion_rate": total_ok / total_completed if total_completed > 0 else 0.0
        }
        
        return analysis
    
    def validate_matrix_probabilities(self) -> bool:
        """Validate that all probabilities in matrix are between 0 and 1"""
        for agent_type, call_types in self.conversion_matrix.items():
            for call_type, probability in call_types.items():
                if not (0 <= probability <= 1):
                    return False
        return True