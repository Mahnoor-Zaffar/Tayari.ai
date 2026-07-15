"""Evaluator registry — maps interview types to evaluator classes."""

from __future__ import annotations

from ai.provider import AIProvider
from evaluation.evaluators.base import BaseEvaluator
from evaluation.evaluators.behavioral import BehavioralEvaluator
from evaluation.evaluators.coding import CodingEvaluator
from evaluation.evaluators.communication import CommunicationEvaluator
from evaluation.evaluators.system_design import SystemDesignEvaluator

# Primary evaluators per interview type
PRIMARY_EVALUATORS: dict[str, type[BaseEvaluator]] = {
    "coding": CodingEvaluator,
    "behavioral": BehavioralEvaluator,
    "system-design": SystemDesignEvaluator,
}

# Evaluators that run for ALL interview types
CROSS_CUTTING_EVALUATORS: list[type[BaseEvaluator]] = [
    CommunicationEvaluator,
]


def get_evaluators(
    interview_type: str,
    provider: AIProvider,
) -> list[BaseEvaluator]:
    """Return all evaluators applicable to the given interview type.

    Includes the type-specific primary evaluator plus cross-cutting evaluators.
    """
    evaluators: list[BaseEvaluator] = []
    primary_cls = PRIMARY_EVALUATORS.get(interview_type)
    if primary_cls:
        evaluators.append(primary_cls(provider))
    for cls in CROSS_CUTTING_EVALUATORS:
        evaluators.append(cls(provider))
    return evaluators
