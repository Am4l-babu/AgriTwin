# Infological Design Approach
# Problem → Decision → Information → Data (not data-first)

from .problem_catalog import FARM_PROBLEMS, FarmProblem
from .decision_mapper import PROBLEM_TO_DECISION, INFORMATION_TO_DATA
from .system_designer import InfologicalDesigner

__all__ = [
    'FARM_PROBLEMS',
    'FarmProblem',
    'PROBLEM_TO_DECISION',
    'INFORMATION_TO_DATA',
    'InfologicalDesigner'
]
