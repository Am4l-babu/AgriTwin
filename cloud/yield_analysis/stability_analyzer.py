# Yield stability analyzer

import numpy as np
from typing import Dict, List, Any


class YieldStabilityAnalyzer:
    """
    Analyze yield stability over multiple years
    Classify into: Stable High, Stable Low, Unstable
    
    Based on Paper 12: 44% of N loss comes from stable low-yield areas
    """
    
    def __init__(self):
        self.stability_threshold = 0.15  # CV < 15% = stable
        self.high_yield_threshold = 4.0  # tons/ha
    
    def analyze(self, yield_data: Dict[str, List[float]]) -> Dict[str, Any]:
        """
        Analyze yield stability for each zone
        
        Input:
        {
            "zone_A": [4.5, 4.8, 4.6, 4.7],  # tons/ha over 4 years
            "zone_B": [2.1, 2.3, 2.0, 2.2],
            "zone_C": [3.0, 5.2, 2.8, 4.9]   # Unstable!
        }
        
        Output:
        {
            "zone_A": {"class": "stable_high", "avg": 4.65, "cv": 0.03},
            "zone_B": {"class": "stable_low", "avg": 2.15, "cv": 0.06},
            "zone_C": {"class": "unstable", "avg": 3.98, "cv": 0.31}
        }
        """
        results = {}
        
        for zone, yields in yield_data.items():
            if len(yields) < 2:
                results[zone] = {
                    "classification": "insufficient_data",
                    "message": "Need at least 2 years of data"
                }
                continue
            
            avg_yield = np.mean(yields)
            std_yield = np.std(yields)
            cv = std_yield / avg_yield if avg_yield > 0 else 0  # Coefficient of variation
            
            # Classify stability
            if cv < self.stability_threshold:  # Stable
                if avg_yield >= self.high_yield_threshold:
                    classification = "stable_high"
                else:
                    classification = "stable_low"
            else:  # Unstable
                classification = "unstable"
            
            results[zone] = {
                "classification": classification,
                "average_yield": round(avg_yield, 2),
                "std_dev": round(std_yield, 2),
                "coefficient_of_variation": round(cv, 3),
                "years": len(yields),
                "yield_range": (round(min(yields), 2), round(max(yields), 2))
            }
        
        return results
    
    def calculate_n_loss_risk(self, stability_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate nitrogen loss risk per zone
        
        Research finding: 44% of N loss from stable low-yield areas
        """
        total_zones = len(stability_results)
        stable_low_count = sum(
            1 for r in stability_results.values() 
            if r.get("classification") == "stable_low"
        )
        
        # Estimate N loss
        n_loss_by_zone = {}
        for zone, result in stability_results.items():
            classification = result.get("classification")
            
            if classification == "stable_low":
                # High N loss risk (44% of total)
                n_loss_risk = "high"
                n_loss_percentage = 44 / stable_low_count if stable_low_count > 0 else 0
            elif classification == "stable_high":
                # Low N loss risk (efficient use)
                n_loss_risk = "low"
                n_loss_percentage = 10
            else:  # unstable
                # Medium N loss risk (variable)
                n_loss_risk = "medium"
                n_loss_percentage = 25
            
            n_loss_by_zone[zone] = {
                "risk": n_loss_risk,
                "estimated_loss_percentage": round(n_loss_percentage, 1)
            }
        
        return {
            "by_zone": n_loss_by_zone,
            "total_stable_low_zones": stable_low_count,
            "total_zones": total_zones,
            "stable_low_percentage": round(stable_low_count / total_zones * 100, 1) if total_zones > 0 else 0
        }
    
    def recommend_management(self, stability_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recommend management strategy per zone
        """
        recommendations = {}
        
        for zone, result in stability_results.items():
            classification = result.get("classification")
            
            if classification == "stable_high":
                recommendations[zone] = {
                    "fertilizer": "high",  # 150-200 kg/ha
                    "fertilizer_amount": "150-200 kg/ha",
                    "irrigation": "optimal",  # Full schedule
                    "priority": "maintain",
                    "reason": "High yield zone - maximize production",
                    "expected_roi": "high"
                }
            elif classification == "stable_low":
                recommendations[zone] = {
                    "fertilizer": "low",  # 50-100 kg/ha
                    "fertilizer_amount": "50-100 kg/ha",
                    "irrigation": "minimal",  # Reduce water
                    "priority": "reduce_inputs",
                    "reason": "Low yield zone - avoid waste (44% N loss here!)",
                    "expected_roi": "low",
                    "potential_savings": "50-70% on fertilizer"
                }
            else:  # unstable
                recommendations[zone] = {
                    "fertilizer": "adaptive",  # Based on weather
                    "fertilizer_amount": "100-150 kg/ha (adjust yearly)",
                    "irrigation": "weather_dependent",
                    "priority": "monitor_closely",
                    "reason": "Unstable zone - adapt to yearly conditions",
                    "expected_roi": "variable"
                }
        
        return recommendations
    
    def generate_summary(self, stability_results: Dict[str, Any]) -> str:
        """Generate human-readable summary"""
        total = len(stability_results)
        stable_high = sum(1 for r in stability_results.values() if r.get("classification") == "stable_high")
        stable_low = sum(1 for r in stability_results.values() if r.get("classification") == "stable_low")
        unstable = sum(1 for r in stability_results.values() if r.get("classification") == "unstable")
        
        lines = []
        lines.append("="*60)
        lines.append("YIELD STABILITY ANALYSIS SUMMARY")
        lines.append("="*60)
        lines.append(f"Total zones analyzed: {total}")
        lines.append(f"Stable high-yield zones: {stable_high} ({stable_high/total*100:.1f}%)")
        lines.append(f"Stable low-yield zones: {stable_low} ({stable_low/total*100:.1f}%)")
        lines.append(f"Unstable zones: {unstable} ({unstable/total*100:.1f}%)")
        lines.append("")
        lines.append("KEY INSIGHT:")
        lines.append(f"  {stable_low} zones are stable low-yield")
        lines.append(f"  These zones account for ~44% of nitrogen loss")
        lines.append(f"  Recommendation: Reduce fertilizer in these zones by 50-70%")
        lines.append("="*60)
        
        return "\n".join(lines)
