# Sustainability metrics definitions

SUSTAINABILITY_METRICS = {
    "social": {
        "labor_hours_per_hectare": {
            "target": 10.0,  # Maintain employment
            "unit": "hours/ha",
            "description": "Labor requirements per hectare"
        },
        "cost_per_hectare": {
            "target": 500.0,  # Affordable for small farmers
            "unit": "$/ha",
            "description": "System cost per hectare"
        },
        "technology_accessibility": {
            "target": 80.0,  # High accessibility
            "unit": "score (0-100)",
            "description": "Can small farmers afford and use this?"
        },
        "knowledge_retention": {
            "target": 75.0,  # Preserve traditional knowledge
            "unit": "score (0-100)",
            "description": "Is farmer knowledge preserved?"
        }
    },
    
    "ecological": {
        "water_usage": {
            "target": 400.0,  # Efficient water use
            "unit": "mm/season",
            "description": "Total water applied per season"
        },
        "fertilizer_usage": {
            "target": 150.0,  # Optimal fertilization
            "unit": "kg/ha",
            "description": "Nitrogen fertilizer per hectare"
        },
        "ghg_emissions": {
            "target": 1000.0,  # Low emissions
            "unit": "kg CO2-eq/ha",
            "description": "Greenhouse gas emissions"
        },
        "biodiversity_index": {
            "target": 2.5,  # Maintain diversity
            "unit": "Shannon index",
            "description": "Species diversity on farm"
        },
        "soil_health": {
            "target": 3.0,  # Healthy soil
            "unit": "percent organic matter",
            "description": "Soil organic matter content"
        },
        "water_quality": {
            "target": 10.0,  # Below limit
            "unit": "mg/L nitrate",
            "description": "Nitrate leaching to groundwater"
        }
    },
    
    "economic": {
        "yield": {
            "target": 5.0,  # Good yield
            "unit": "tons/ha",
            "description": "Crop yield per hectare"
        },
        "profit_margin": {
            "target": 30.0,  # Profitable
            "unit": "percent",
            "description": "Profit as percentage of revenue"
        },
        "input_efficiency": {
            "target": 80.0,  # Efficient use
            "unit": "percent",
            "description": "Efficiency of input use"
        },
        "roi": {
            "target": 200.0,  # 2x return
            "unit": "percent",
            "description": "Return on investment"
        }
    },
    
    "technological": {
        "model_transparency": {
            "target": 80.0,  # High transparency
            "unit": "score (0-100)",
            "description": "Can decisions be explained?"
        },
        "system_resilience": {
            "target": 90.0,  # High resilience
            "unit": "score (0-100)",
            "description": "Failure recovery capability"
        },
        "data_privacy": {
            "target": 95.0,  # Strong privacy
            "unit": "score (0-100)",
            "description": "Farmer data protection"
        },
        "uptime": {
            "target": 99.0,  # High availability
            "unit": "percent",
            "description": "System availability"
        }
    }
}
