from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SafetyRiskLevel(str, Enum):
    """Risk severity classification for user messages in an elderly care context."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH_EMERGENCY = "high_emergency"

    def __str__(self) -> str:
        return self.value


@dataclass
class SafetyCheckResult:
    """Structured output from the pre-generation safety screening stage."""

    risk_level: SafetyRiskLevel = SafetyRiskLevel.NONE
    requires_caregiver_alert: bool = False
    flagged_categories: list[str] = field(default_factory=list)
    matched_indicators: list[str] = field(default_factory=list)
    safety_directive: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_level": str(self.risk_level.value),
            "requires_caregiver_alert": self.requires_caregiver_alert,
            "flagged_categories": list(self.flagged_categories),
            "matched_indicators": list(self.matched_indicators),
        }


class SafetyChecker:
    """Initial rule-based safety screening foundation for elderly care conversations.

    Designed as a modular stage in the LangGraph workflow that can be extended
    with ML/LLM crisis classifiers, automated incident creation, and caregiver notifications.
    """

    EMERGENCY_CATEGORIES: dict[str, list[str]] = {
        "fall_or_injury": [
            "i fell",
            "have fallen",
            "fell down",
            "can't get up",
            "cannot get up",
            "hit my head",
            "broke my",
        ],
        "cardiopulmonary_distress": [
            "chest pain",
            "heart attack",
            "can't breathe",
            "cannot breathe",
            "hard to breathe",
            "shortness of breath",
            "choking",
        ],
        "neurological_or_acute_emergency": [
            "stroke",
            "face drooping",
            "slurred speech",
            "bleeding heavily",
            "unconscious",
            "fainted",
            "seizure",
        ],
        "self_harm_or_crisis": [
            "hurt myself",
            "end my life",
            "want to die",
            "suicide",
            "suicidal",
        ],
    }

    MEDIUM_CONCERN_CATEGORIES: dict[str, list[str]] = {
        "dizziness_or_weakness": [
            "dizzy",
            "lightheaded",
            "feeling faint",
            "very weak",
            "unsteady",
        ],
        "medication_concern": [
            "forgot my pill",
            "missed my medication",
            "missed my dose",
            "wrong pill",
            "took too many",
            "double dose",
        ],
        "pain_or_discomfort": [
            "severe pain",
            "sharp pain",
            "stomach pain",
            "headache won't go away",
        ],
        "sleep_or_confusion": [
            "trouble sleeping",
            "can't sleep",
            "insomnia",
            "feel confused",
            "don't know where i am",
        ],
    }

    @classmethod
    def evaluate(cls, message_content: str) -> SafetyCheckResult:
        """Evaluate user message text and return structured safety metadata."""
        if not message_content or not message_content.strip():
            return SafetyCheckResult()

        normalized = message_content.lower().strip()
        flagged_categories: list[str] = []
        matched_indicators: list[str] = []
        is_emergency = False
        is_medium = False

        for category, phrases in cls.EMERGENCY_CATEGORIES.items():
            for phrase in phrases:
                if phrase in normalized:
                    is_emergency = True
                    if category not in flagged_categories:
                        flagged_categories.append(category)
                    matched_indicators.append(phrase)

        for category, phrases in cls.MEDIUM_CONCERN_CATEGORIES.items():
            for phrase in phrases:
                if phrase in normalized:
                    is_medium = True
                    if category not in flagged_categories:
                        flagged_categories.append(category)
                    matched_indicators.append(phrase)

        if is_emergency:
            directive = (
                "The user's message indicates a potential ACUTE MEDICAL OR SAFETY EMERGENCY "
                f"(categories: {', '.join(flagged_categories)}). "
                "1. Immediately express calm, clear concern for their safety. "
                "2. Explicitly instruct them to press their caregiver call button, alert a nurse/caregiver on duty immediately, or call emergency services (911). "
                "3. Do NOT attempt to diagnose or provide complex medical instructions. Keep instructions brief, reassuring, and focused on getting immediate human help."
            )
            return SafetyCheckResult(
                risk_level=SafetyRiskLevel.HIGH_EMERGENCY,
                requires_caregiver_alert=True,
                flagged_categories=flagged_categories,
                matched_indicators=matched_indicators,
                safety_directive=directive,
            )

        if is_medium:
            directive = (
                "The user mentioned a health or care concern "
                f"(categories: {', '.join(flagged_categories)}). "
                "Provide gentle, practical, non-medical comfort and reminders, and clearly encourage them to inform their caregiver or nurse so it can be properly noted and checked."
            )
            return SafetyCheckResult(
                risk_level=SafetyRiskLevel.MEDIUM,
                requires_caregiver_alert=False,
                flagged_categories=flagged_categories,
                matched_indicators=matched_indicators,
                safety_directive=directive,
            )

        return SafetyCheckResult(
            risk_level=SafetyRiskLevel.NONE,
            requires_caregiver_alert=False,
        )

