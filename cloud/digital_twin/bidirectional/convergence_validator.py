# Convergence validator - Check physical-virtual alignment

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any


@dataclass
class ConvergenceMetrics:
    """Metrics for physical-virtual convergence"""
    entity_id: str
    physical_value: float
    virtual_value: float
    divergence: float
    converged: bool
    timestamp: datetime


class ConvergenceValidator:
    """
    Validate convergence between physical and virtual states
    
    ISO/IEC 30173 requirement: Digital Twin must maintain convergence
    """
    
    def __init__(self, convergence_threshold: float = 0.10):
        """
        Args:
            convergence_threshold: Max allowed divergence (default 10%)
        """
        self.convergence_threshold = convergence_threshold
        self.convergence_history: Dict[str, list] = {}
    
    def validate(self, entity_id: str, physical_value: float,
                virtual_value: float) -> ConvergenceMetrics:
        """
        Check if physical and virtual states have converged
        
        Example:
        - Virtual predicts soil moisture = 45%
        - Physical sensor reads = 42%
        - Divergence = |45-42|/45 = 6.7%
        - Converged = True (< 10% threshold)
        """
        if physical_value == 0:
            divergence = abs(virtual_value)
        else:
            divergence = abs(physical_value - virtual_value) / abs(physical_value)
        
        converged = divergence <= self.convergence_threshold
        
        metrics = ConvergenceMetrics(
            entity_id=entity_id,
            physical_value=physical_value,
            virtual_value=virtual_value,
            divergence=divergence,
            converged=converged,
            timestamp=datetime.now()
        )
        
        # Store history
        if entity_id not in self.convergence_history:
            self.convergence_history[entity_id] = []
        self.convergence_history[entity_id].append(metrics)
        
        return metrics
    
    def apply_correction(self, metrics: ConvergenceMetrics,
                        trust_physical: float = 0.7) -> float:
        """
        Apply Kalman-like correction to align virtual with physical
        
        Corrected = trust_physical * physical + (1-trust_physical) * virtual
        Default: Trust physical 70%, virtual 30%
        """
        if not metrics.converged:
            corrected = (trust_physical * metrics.physical_value + 
                        (1 - trust_physical) * metrics.virtual_value)
            return corrected
        
        return metrics.virtual_value
    
    def get_convergence_report(self, entity_id: str) -> Dict[str, Any]:
        """Get convergence statistics for an entity"""
        if entity_id not in self.convergence_history:
            return {"error": "No history for entity"}
        
        history = self.convergence_history[entity_id]
        converged_count = sum(1 for m in history if m.converged)
        avg_divergence = sum(m.divergence for m in history) / len(history)
        
        return {
            "entity_id": entity_id,
            "total_checks": len(history),
            "converged_count": converged_count,
            "convergence_rate": converged_count / len(history),
            "average_divergence": avg_divergence,
            "last_check": history[-1].timestamp.isoformat(),
            "currently_converged": history[-1].converged
        }
