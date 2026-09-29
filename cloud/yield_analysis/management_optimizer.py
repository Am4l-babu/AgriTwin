# Management optimizer - Zone-specific recommendations

from typing import Dict, Any


class ManagementOptimizer:
    """Optimize management practices per zone"""
    
    def __init__(self):
        self.fertilizer_costs = {
            "high": 200,  # $/ha
            "medium": 150,
            "low": 100,
            "minimal": 50
        }
    
    def calculate_savings(self, stability_results: Dict[str, Any],
                         current_fertilizer_rate: float = 150) -> Dict[str, Any]:
        """
        Calculate potential savings from zone-specific management
        
        Args:
            stability_results: Results from YieldStabilityAnalyzer
            current_fertilizer_rate: Current uniform rate (kg/ha)
        
        Returns:
            Savings analysis
        """
        total_zones = len(stability_results)
        stable_low_zones = sum(
            1 for r in stability_results.values()
            if r.get("classification") == "stable_low"
        )
        
        # Current cost (uniform rate)
        current_cost = current_fertilizer_rate * total_zones * 2  # $2/kg
        
        # Optimized cost (zone-specific)
        optimized_cost = 0
        for zone, result in stability_results.items():
            classification = result.get("classification")
            
            if classification == "stable_high":
                optimized_cost += 175 * 2  # 175 kg/ha
            elif classification == "stable_low":
                optimized_cost += 75 * 2  # 75 kg/ha (50% reduction)
            else:  # unstable
                optimized_cost += 125 * 2  # 125 kg/ha
        
        savings = current_cost - optimized_cost
        savings_percentage = (savings / current_cost * 100) if current_cost > 0 else 0
        
        return {
            "current_cost": round(current_cost, 2),
            "optimized_cost": round(optimized_cost, 2),
            "total_savings": round(savings, 2),
            "savings_percentage": round(savings_percentage, 1),
            "stable_low_zones": stable_low_zones,
            "total_zones": total_zones,
            "recommendation": f"Reduce fertilizer in {stable_low_zones} stable low zones"
        }
    
    def generate_application_map(self, stability_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate variable rate application map
        
        Returns fertilizer rates per zone
        """
        application_map = {}
        
        for zone, result in stability_results.items():
            classification = result.get("classification")
            
            if classification == "stable_high":
                rate = 175  # kg/ha
                priority = "high"
            elif classification == "stable_low":
                rate = 75  # kg/ha
                priority = "low"
            else:  # unstable
                rate = 125  # kg/ha
                priority = "medium"
            
            application_map[zone] = {
                "fertilizer_rate": rate,
                "priority": priority,
                "classification": classification,
                "expected_yield": result.get("average_yield", 0)
            }
        
        return application_map
