# Sustainability impact assessor

from typing import Dict, Any, List
from .metrics import SUSTAINABILITY_METRICS


class SustainabilityAssessor:
    """
    Assess system impacts across social, ecological, and economic dimensions
    """
    
    def __init__(self, farm_id: str):
        self.farm_id = farm_id
        self.metrics = SUSTAINABILITY_METRICS
    
    def assess(self, farm_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive sustainability assessment
        
        Args:
            farm_data: Dictionary with current farm metrics
        
        Returns:
            Assessment with scores and recommendations
        """
        social_score = self._assess_social(farm_data)
        ecological_score = self._assess_ecological(farm_data)
        economic_score = self._assess_economic(farm_data)
        technological_score = self._assess_technological(farm_data)
        
        overall = (social_score + ecological_score + 
                  economic_score + technological_score) / 4
        
        return {
            "overall_score": overall,
            "social": social_score,
            "ecological": ecological_score,
            "economic": economic_score,
            "technological": technological_score,
            "grade": self._score_to_grade(overall),
            "recommendations": self._generate_recommendations(
                social_score, ecological_score, economic_score, technological_score
            ),
            "detailed_metrics": self._detailed_assessment(farm_data)
        }
    
    def _assess_social(self, data: Dict) -> float:
        """Assess social impact (0-100)"""
        score = 100.0
        
        # Labor impact
        labor_hours = data.get("labor_hours_per_hectare", 10)
        if labor_hours < 5:  # Too automated
            score -= 20
        elif labor_hours > 20:  # Too labor intensive
            score -= 10
        
        # Affordability
        cost = data.get("cost_per_hectare", 500)
        if cost > 1000:  # Too expensive
            score -= 30
        elif cost > 700:
            score -= 15
        
        # Accessibility
        accessibility = data.get("technology_accessibility", 70)
        if accessibility < 50:
            score -= 25
        
        return max(0, score)
    
    def _assess_ecological(self, data: Dict) -> float:
        """Assess ecological impact (0-100)"""
        score = 100.0
        
        # Water usage
        water = data.get("water_usage", 400)
        target = self.metrics["ecological"]["water_usage"]["target"]
        if water > target * 1.5:  # 50% over target
            score -= 25
        elif water > target * 1.2:
            score -= 15
        
        # Fertilizer
        fertilizer = data.get("fertilizer_usage", 150)
        target = self.metrics["ecological"]["fertilizer_usage"]["target"]
        if fertilizer > target * 1.5:
            score -= 25
        elif fertilizer > target * 1.2:
            score -= 15
        
        # GHG emissions
        emissions = data.get("ghg_emissions", 1000)
        target = self.metrics["ecological"]["ghg_emissions"]["target"]
        if emissions > target * 1.5:
            score -= 25
        elif emissions > target * 1.2:
            score -= 15
        
        # Soil health
        soil_health = data.get("soil_health", 2.5)
        target = self.metrics["ecological"]["soil_health"]["target"]
        if soil_health < target * 0.7:
            score -= 15
        
        return max(0, score)
    
    def _assess_economic(self, data: Dict) -> float:
        """Assess economic viability (0-100)"""
        score = 100.0
        
        # Yield
        yield_val = data.get("yield", 4.0)
        target = self.metrics["economic"]["yield"]["target"]
        if yield_val < target * 0.6:  # 40% below target
            score -= 40
        elif yield_val < target * 0.8:
            score -= 20
        
        # Profit margin
        profit = data.get("profit_margin", 25)
        target = self.metrics["economic"]["profit_margin"]["target"]
        if profit < target * 0.5:
            score -= 30
        elif profit < target * 0.7:
            score -= 15
        
        # Input efficiency
        efficiency = data.get("input_efficiency", 75)
        if efficiency < 60:
            score -= 20
        
        return max(0, score)
    
    def _assess_technological(self, data: Dict) -> float:
        """Assess technological aspects (0-100)"""
        score = 100.0
        
        # Transparency
        transparency = data.get("model_transparency", 70)
        if transparency < 60:
            score -= 25
        
        # Resilience
        resilience = data.get("system_resilience", 80)
        if resilience < 70:
            score -= 25
        
        # Privacy
        privacy = data.get("data_privacy", 85)
        if privacy < 80:
            score -= 20
        
        # Uptime
        uptime = data.get("uptime", 95)
        if uptime < 90:
            score -= 20
        
        return max(0, score)
    
    def _score_to_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return "A (Excellent)"
        elif score >= 80:
            return "B (Good)"
        elif score >= 70:
            return "C (Fair)"
        elif score >= 60:
            return "D (Poor)"
        else:
            return "F (Failing)"
    
    def _generate_recommendations(self, social: float, ecological: float,
                                  economic: float, technological: float) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if social < 70:
            recommendations.append("Improve social impact: Ensure affordability and accessibility")
        if ecological < 70:
            recommendations.append("Reduce environmental footprint: Optimize water and fertilizer use")
        if economic < 70:
            recommendations.append("Improve economic viability: Focus on yield and efficiency")
        if technological < 70:
            recommendations.append("Enhance system: Improve transparency and resilience")
        
        if not recommendations:
            recommendations.append("Excellent performance! Continue monitoring and optimization")
        
        return recommendations
    
    def _detailed_assessment(self, data: Dict) -> Dict[str, Any]:
        """Detailed metric-by-metric assessment"""
        detailed = {}
        
        for category, metrics in self.metrics.items():
            detailed[category] = {}
            for metric_name, metric_info in metrics.items():
                current = data.get(metric_name, 0)
                target = metric_info["target"]
                
                # Calculate performance
                if current == 0:
                    performance = 0
                else:
                    performance = min(100, (current / target) * 100)
                
                detailed[category][metric_name] = {
                    "current": current,
                    "target": target,
                    "unit": metric_info["unit"],
                    "performance": performance,
                    "status": "good" if performance >= 80 else "needs_improvement"
                }
        
        return detailed
