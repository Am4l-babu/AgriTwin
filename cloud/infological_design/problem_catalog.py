# Farm problem catalog
# Start with problems, not sensors

from dataclasses import dataclass
from typing import List


@dataclass
class FarmProblem:
    """Structured representation of a farm problem"""
    problem_id: str
    name: str
    description: str
    symptoms: List[str]
    potential_causes: List[str]
    priority: str  # "high", "medium", "low"


# Catalog of common farm problems
FARM_PROBLEMS = {
    "low_yield": FarmProblem(
        problem_id="low_yield",
        name="Low Crop Yield",
        description="Crop yield below expected levels",
        symptoms=[
            "Small plants",
            "Yellowing leaves",
            "Slow growth",
            "Poor fruit development"
        ],
        potential_causes=[
            "Insufficient water",
            "Nutrient deficiency",
            "Pest or disease",
            "Poor soil health",
            "Inadequate sunlight"
        ],
        priority="high"
    ),
    
    "water_waste": FarmProblem(
        problem_id="water_waste",
        name="Excessive Water Usage",
        description="Water consumption higher than necessary",
        symptoms=[
            "High water bills",
            "Waterlogged soil",
            "Runoff observed",
            "Constant wet conditions"
        ],
        potential_causes=[
            "Over-irrigation",
            "Poor drainage",
            "Leaking pipes",
            "Inefficient irrigation system"
        ],
        priority="medium"
    ),
    
    "nutrient_deficiency": FarmProblem(
        problem_id="nutrient_deficiency",
        name="Nutrient Deficiency",
        description="Plants lack essential nutrients",
        symptoms=[
            "Yellowing leaves (chlorosis)",
            "Stunted growth",
            "Poor leaf color",
            "Weak stems"
        ],
        potential_causes=[
            "Low soil fertility",
            "Wrong soil pH",
            "Poor nutrient uptake",
            "Insufficient fertilization"
        ],
        priority="high"
    ),
    
    "heat_stress": FarmProblem(
        problem_id="heat_stress",
        name="Heat Stress",
        description="Plants suffering from excessive heat",
        symptoms=[
            "Wilting during day",
            "Leaf curling",
            "Flower drop",
            "Reduced growth"
        ],
        potential_causes=[
            "High temperatures",
            "Insufficient water",
            "Lack of shade",
            "Poor ventilation"
        ],
        priority="high"
    ),
    
    "pest_disease": FarmProblem(
        problem_id="pest_disease",
        name="Pest or Disease Infestation",
        description="Crops affected by pests or diseases",
        symptoms=[
            "Spots on leaves",
            "Holes in leaves",
            "Discoloration",
            "Visible insects",
            "Mold or fungus"
        ],
        potential_causes=[
            "Pest infestation",
            "Fungal disease",
            "Bacterial infection",
            "Viral disease",
            "Poor air circulation"
        ],
        priority="high"
    ),
    
    "soil_degradation": FarmProblem(
        problem_id="soil_degradation",
        name="Soil Health Degradation",
        description="Declining soil quality over time",
        symptoms=[
            "Poor water retention",
            "Compacted soil",
            "Low organic matter",
            "Erosion"
        ],
        potential_causes=[
            "Over-cultivation",
            "Lack of organic matter",
            "Erosion",
            "Chemical buildup"
        ],
        priority="medium"
    )
}


# Template for adding custom problems
def create_custom_problem(name: str, description: str, symptoms: List[str], 
                         causes: List[str], priority: str = "medium") -> FarmProblem:
    """
    Create a custom farm problem
    
    Example:
    problem = create_custom_problem(
        name="Uneven Growth",
        description="Some areas grow better than others",
        symptoms=["Patchy field", "Variable plant height"],
        causes=["Soil variability", "Uneven irrigation"],
        priority="medium"
    )
    """
    problem_id = name.lower().replace(" ", "_")
    return FarmProblem(
        problem_id=problem_id,
        name=name,
        description=description,
        symptoms=symptoms,
        potential_causes=causes,
        priority=priority
    )
