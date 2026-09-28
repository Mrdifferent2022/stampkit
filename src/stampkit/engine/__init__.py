"""Evaluation orchestration: pluggable evaluators routed by feature kind."""

from stampkit.engine.evaluator import Evaluator, EvaluatorRegistry
from stampkit.engine.pipeline import evaluate

__all__ = ["Evaluator", "EvaluatorRegistry", "evaluate"]
