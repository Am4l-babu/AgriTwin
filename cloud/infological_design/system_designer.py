# Infological system designer
# Complete workflow: Problem → Decision → Information → Data → Sensors

from typing import Dict, List, Any
from .problem_catalog import FARM_PROBLEMS, FarmProblem
from .decision_mapper import PROBLEM_TO_DECISION, INFORMATION_TO_DATA, get_sensor_requirements


class InfologicalDesigner:
    """
    Design system from problems, not data
    
    Workflow:
    1. Identify problem
    2. Define decision needed
    3. Determine information required
    4. Identify data needed
    5. Select sensors
    """
    
    def __init__(self, farm_id: str):
        self.farm_id = farm_id
        self.identified_problems: List[str] = []
    
    def identify_problem(self, symptoms: List[str]) -> Dict[str, Any]:
        """
        Identify problem from observed symptoms
        
        Example:
        symptoms = ["yellowing leaves", "stunted growth"]
        → Identifies: nutrient_deficiency
        """
        matches = []
        
        for problem_id, problem in FARM_PROBLEMS.items():
            # Count matching symptoms
            matching_symptoms = sum(
                1 for symptom in symptoms
                if any(s.lower() in symptom.lower() for s in problem.symptoms)
            )
            
            if matching_symptoms > 0:
                matches.append({
                    "problem_id": problem_id,
                    "problem": problem,
                    "matching_symptoms": matching_symptoms,
                    "confidence": matching_symptoms / len(problem.symptoms)
                })
        
        # Sort by confidence
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        
        if matches:
            best_match = matches[0]
            self.identified_problems.append(best_match["problem_id"])
            return {
                "identified_problem": best_match["problem_id"],
                "confidence": best_match["confidence"],
                "problem_details": best_match["problem"],
                "other_possibilities": matches[1:3]  # Top 3
            }
        
        return {
            "identified_problem": None,
            "confidence": 0,
            "message": "No matching problem found. Consider creating custom problem."
        }
    
    def design_for_problem(self, problem_id: str) -> Dict[str, Any]:
        """
        Complete design workflow for a problem
        
        Returns exactly what you need to implement
        """
        if problem_id not in FARM_PROBLEMS:
            return {"error": "Problem not found"}
        
        problem = FARM_PROBLEMS[problem_id]
        
        # Step 1: Problem identified
        print(f"\n=== INFOLOGICAL DESIGN ===")
        print(f"Problem: {problem.name}")
        print(f"Description: {problem.description}")
        print(f"Priority: {problem.priority}")
        
        # Step 2: Decision needed
        if problem_id not in PROBLEM_TO_DECISION:
            return {"error": "No decision mapping for this problem"}
        
        decision = PROBLEM_TO_DECISION[problem_id]
        print(f"\nDecision: {decision['decision']}")
        print(f"Options: {', '.join(decision['options'])}")
        
        # Step 3: Information required
        information_needed = decision["information_needed"]
        print(f"\nInformation needed ({len(information_needed)} items):")
        for info in information_needed:
            print(f"  - {info}")
        
        # Step 4: Data requirements
        all_data = []
        all_sensors = set()
        data_details = []
        
        for info in information_needed:
            if info in INFORMATION_TO_DATA:
                data_spec = INFORMATION_TO_DATA[info]
                all_data.extend(data_spec["data_needed"])
                all_sensors.update(data_spec["sensors_required"])
                data_details.append({
                    "information": info,
                    "data": data_spec["data_needed"],
                    "sensors": data_spec["sensors_required"],
                    "frequency": data_spec["frequency"],
                    "accuracy": data_spec["accuracy_required"]
                })
        
        print(f"\nData needed ({len(set(all_data))} types):")
        for data in set(all_data):
            print(f"  - {data}")
        
        # Step 5: Sensors required
        print(f"\nSensors required ({len(all_sensors)} types):")
        for sensor in all_sensors:
            print(f"  - {sensor}")
        
        # Cost estimate
        sensor_reqs = get_sensor_requirements(problem_id)
        cost = sensor_reqs["estimated_cost"]
        print(f"\nEstimated cost: ${cost['total_usd']}")
        
        return {
            "problem": {
                "id": problem_id,
                "name": problem.name,
                "description": problem.description,
                "priority": problem.priority
            },
            "decision": decision,
            "information_requirements": information_needed,
            "data_requirements": list(set(all_data)),
            "sensor_requirements": list(all_sensors),
            "data_details": data_details,
            "estimated_cost": cost,
            "implementation_steps": self._generate_implementation_steps(
                problem_id, list(all_sensors)
            )
        }
    
    def _generate_implementation_steps(self, problem_id: str, 
                                      sensors: List[str]) -> List[str]:
        """Generate step-by-step implementation guide"""
        steps = [
            f"1. Confirm problem: {FARM_PROBLEMS[problem_id].name}",
            f"2. Purchase required sensors: {', '.join(sensors)}",
            "3. Install sensors at appropriate locations",
            "4. Configure data collection frequency",
            "5. Set up data processing pipeline",
            "6. Implement decision logic",
            "7. Test and validate system",
            "8. Monitor and refine"
        ]
        return steps
    
    def compare_approaches(self):
        """
        Compare datalogical vs infological approaches
        """
        print("\n" + "="*60)
        print("DATALOGICAL APPROACH (Traditional - WRONG)")
        print("="*60)
        print("1. Buy sensors (DHT11, LDR, soil moisture)")
        print("2. Collect data (temperature, humidity, light)")
        print("3. Store in database")
        print("4. Analyze data")
        print("5. Try to find patterns")
        print("6. Hmm... what can we do with this?")
        print("❌ Problem: Started with technology, not problem!")
        print("❌ Result: Wasted money on unnecessary sensors")
        
        print("\n" + "="*60)
        print("INFOLOGICAL APPROACH (Research-Based - CORRECT)")
        print("="*60)
        print("1. Identify problem (low yield)")
        print("2. Define decision (how much fertilizer?)")
        print("3. Determine information (plant N status, soil N)")
        print("4. Identify data (NDVI, chlorophyll, soil samples)")
        print("5. Select sensors (multispectral camera, soil sensor)")
        print("✅ Result: Buy EXACTLY what you need!")
        print("✅ Benefit: No wasted resources")
    
    def generate_report(self) -> str:
        """Generate implementation report"""
        if not self.identified_problems:
            return "No problems identified yet."
        
        report = []
        report.append("="*60)
        report.append("INFOLOGICAL DESIGN REPORT")
        report.append(f"Farm ID: {self.farm_id}")
        report.append("="*60)
        
        for problem_id in self.identified_problems:
            design = self.design_for_problem(problem_id)
            report.append(f"\nProblem: {design['problem']['name']}")
            report.append(f"Decision: {design['decision']['decision']}")
            report.append(f"Sensors: {len(design['sensor_requirements'])}")
            report.append(f"Cost: ${design['estimated_cost']['total_usd']}")
        
        return "\n".join(report)


# Example usage
if __name__ == "__main__":
    designer = InfologicalDesigner("farm_001")
    
    # Compare approaches
    designer.compare_approaches()
    
    # Design for a specific problem
    print("\n" + "="*60)
    print("EXAMPLE: Designing for Low Yield Problem")
    print("="*60)
    
    design = designer.design_for_problem("low_yield")
    
    print("\n" + "="*60)
    print("IMPLEMENTATION STEPS")
    print("="*60)
    for step in design["implementation_steps"]:
        print(step)
