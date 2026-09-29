# Sustainability reporter - Generate reports

from typing import Dict, Any
from datetime import datetime


class SustainabilityReporter:
    """Generate sustainability reports"""
    
    @staticmethod
    def generate_text_report(assessment: Dict[str, Any]) -> str:
        """Generate human-readable text report"""
        lines = []
        lines.append("="*60)
        lines.append("SUSTAINABILITY ASSESSMENT REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("="*60)
        lines.append("")
        
        # Overall score
        lines.append(f"Overall Score: {assessment['overall_score']:.1f}/100")
        lines.append(f"Grade: {assessment['grade']}")
        lines.append("")
        
        # Category scores
        lines.append("Category Scores:")
        lines.append(f"  Social:        {assessment['social']:.1f}/100")
        lines.append(f"  Ecological:    {assessment['ecological']:.1f}/100")
        lines.append(f"  Economic:      {assessment['economic']:.1f}/100")
        lines.append(f"  Technological: {assessment['technological']:.1f}/100")
        lines.append("")
        
        # Recommendations
        lines.append("Recommendations:")
        for i, rec in enumerate(assessment['recommendations'], 1):
            lines.append(f"  {i}. {rec}")
        lines.append("")
        
        lines.append("="*60)
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_json_report(assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JSON report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "assessment": assessment,
            "report_version": "1.0"
        }
