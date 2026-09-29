# Zone classifier

from typing import Dict, List, Any


class ZoneClassifier:
    """Classify field zones based on yield stability"""
    
    @staticmethod
    def classify_zones(stability_results: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Group zones by classification
        
        Returns:
        {
            "stable_high": ["zone_A", "zone_D"],
            "stable_low": ["zone_B", "zone_E"],
            "unstable": ["zone_C"]
        }
        """
        classified = {
            "stable_high": [],
            "stable_low": [],
            "unstable": []
        }
        
        for zone, result in stability_results.items():
            classification = result.get("classification")
            if classification in classified:
                classified[classification].append(zone)
        
        return classified
    
    @staticmethod
    def get_zone_statistics(stability_results: Dict[str, Any]) -> Dict[str, Any]:
        """Get statistics for each zone type"""
        classified = ZoneClassifier.classify_zones(stability_results)
        
        stats = {}
        for zone_type, zones in classified.items():
            if not zones:
                stats[zone_type] = {
                    "count": 0,
                    "percentage": 0,
                    "avg_yield": 0,
                    "avg_cv": 0
                }
                continue
            
            yields = [stability_results[z]["average_yield"] for z in zones]
            cvs = [stability_results[z]["coefficient_of_variation"] for z in zones]
            
            stats[zone_type] = {
                "count": len(zones),
                "percentage": len(zones) / len(stability_results) * 100,
                "avg_yield": sum(yields) / len(yields),
                "avg_cv": sum(cvs) / len(cvs),
                "zones": zones
            }
        
        return stats
