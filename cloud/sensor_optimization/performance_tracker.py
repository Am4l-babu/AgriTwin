# Performance tracker for sensor optimization

from typing import Dict, List, Any
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class PerformanceMetrics:
    """Performance metrics for sensor configuration"""
    timestamp: datetime
    sensor_count: int
    accuracy: float
    coverage: float
    cost: float
    iteration: int


class PerformanceTracker:
    """
    Track sensor optimization performance over time
    """
    
    def __init__(self):
        self.history: List[PerformanceMetrics] = []
        self.baseline_metrics: Dict[str, float] = {}
    
    def set_baseline(self, sensor_count: int, accuracy: float,
                    coverage: float, cost: float):
        """Set baseline metrics (before optimization)"""
        self.baseline_metrics = {
            "sensor_count": sensor_count,
            "accuracy": accuracy,
            "coverage": coverage,
            "cost": cost
        }
    
    def record_iteration(self, sensor_count: int, accuracy: float,
                        coverage: float, cost: float, iteration: int):
        """Record metrics for an iteration"""
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            sensor_count=sensor_count,
            accuracy=accuracy,
            coverage=coverage,
            cost=cost,
            iteration=iteration
        )
        self.history.append(metrics)
    
    def get_improvement_summary(self) -> Dict[str, Any]:
        """Calculate improvement over baseline"""
        if not self.history or not self.baseline_metrics:
            return {"error": "No data available"}
        
        latest = self.history[-1]
        baseline = self.baseline_metrics
        
        sensor_reduction = baseline["sensor_count"] - latest.sensor_count
        sensor_reduction_pct = (sensor_reduction / baseline["sensor_count"]) * 100
        
        accuracy_change = latest.accuracy - baseline["accuracy"]
        coverage_change = latest.coverage - baseline["coverage"]
        cost_savings = baseline["cost"] - latest.cost
        cost_savings_pct = (cost_savings / baseline["cost"]) * 100
        
        return {
            "baseline": baseline,
            "current": {
                "sensor_count": latest.sensor_count,
                "accuracy": latest.accuracy,
                "coverage": latest.coverage,
                "cost": latest.cost
            },
            "improvements": {
                "sensor_reduction": sensor_reduction,
                "sensor_reduction_percentage": round(sensor_reduction_pct, 1),
                "accuracy_change": round(accuracy_change, 3),
                "coverage_change": round(coverage_change, 1),
                "cost_savings": round(cost_savings, 2),
                "cost_savings_percentage": round(cost_savings_pct, 1)
            },
            "iterations": len(self.history)
        }
    
    def get_convergence_status(self, window: int = 5) -> Dict[str, Any]:
        """
        Check if optimization has converged
        
        Args:
            window: Number of recent iterations to check
        
        Returns:
            Convergence status
        """
        if len(self.history) < window:
            return {
                "converged": False,
                "reason": "Insufficient iterations"
            }
        
        recent = self.history[-window:]
        
        # Check if sensor selection is stable
        sensor_counts = [m.sensor_count for m in recent]
        sensor_stable = len(set(sensor_counts)) == 1
        
        # Check if accuracy is stable (within 1%)
        accuracies = [m.accuracy for m in recent]
        accuracy_range = max(accuracies) - min(accuracies)
        accuracy_stable = accuracy_range < 0.01
        
        converged = sensor_stable and accuracy_stable
        
        return {
            "converged": converged,
            "sensor_stable": sensor_stable,
            "accuracy_stable": accuracy_stable,
            "accuracy_range": round(accuracy_range, 4),
            "iterations_checked": window
        }
    
    def generate_report(self) -> str:
        """Generate performance report"""
        summary = self.get_improvement_summary()
        convergence = self.get_convergence_status()
        
        if "error" in summary:
            return "No performance data available"
        
        lines = []
        lines.append("="*60)
        lines.append("SENSOR OPTIMIZATION PERFORMANCE REPORT")
        lines.append("="*60)
        
        lines.append("\nBaseline (Before Optimization):")
        lines.append(f"  Sensors: {summary['baseline']['sensor_count']}")
        lines.append(f"  Accuracy: {summary['baseline']['accuracy']:.1%}")
        lines.append(f"  Coverage: {summary['baseline']['coverage']:.1f}%")
        lines.append(f"  Cost: ${summary['baseline']['cost']:.2f}")
        
        lines.append("\nCurrent (After Optimization):")
        lines.append(f"  Sensors: {summary['current']['sensor_count']}")
        lines.append(f"  Accuracy: {summary['current']['accuracy']:.1%}")
        lines.append(f"  Coverage: {summary['current']['coverage']:.1f}%")
        lines.append(f"  Cost: ${summary['current']['cost']:.2f}")
        
        lines.append("\nImprovements:")
        imp = summary['improvements']
        lines.append(f"  Sensor Reduction: {imp['sensor_reduction']} ({imp['sensor_reduction_percentage']:.1f}%)")
        lines.append(f"  Accuracy Change: {imp['accuracy_change']:+.1%}")
        lines.append(f"  Coverage Change: {imp['coverage_change']:+.1f}%")
        lines.append(f"  Cost Savings: ${imp['cost_savings']:.2f} ({imp['cost_savings_percentage']:.1f}%)")
        
        lines.append(f"\nIterations: {summary['iterations']}")
        lines.append(f"Converged: {'Yes' if convergence['converged'] else 'No'}")
        
        lines.append("="*60)
        
        return "\n".join(lines)
