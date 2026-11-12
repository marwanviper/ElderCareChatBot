import unittest

from src.ai.prompts.elderly_care import build_elderly_care_system_prompt
from src.ai.safety.checker import SafetyChecker, SafetyRiskLevel


class TestAISafetyAndPrompts(unittest.TestCase):
    """Unit tests for the ElderlyCare safety checker and system prompt builder."""

    def test_safe_normal_message(self):
        """Normal conversational messages should have NONE risk level."""
        result = SafetyChecker.evaluate("What time is lunch usually served?")
        self.assertEqual(result.risk_level, SafetyRiskLevel.NONE)
        self.assertFalse(result.requires_caregiver_alert)
        self.assertEqual(result.flagged_categories, [])
        self.assertIsNone(result.safety_directive)

    def test_high_emergency_fall_detection(self):
        """Messages describing a fall should trigger HIGH_EMERGENCY and caregiver alert."""
        result = SafetyChecker.evaluate("Help, I fell in the bathroom and I can't get up!")
        self.assertEqual(result.risk_level, SafetyRiskLevel.HIGH_EMERGENCY)
        self.assertTrue(result.requires_caregiver_alert)
        self.assertIn("fall_or_injury", result.flagged_categories)
        self.assertIsNotNone(result.safety_directive)
        self.assertIn("ACUTE MEDICAL OR SAFETY EMERGENCY", result.safety_directive)

    def test_high_emergency_chest_pain_detection(self):
        """Messages describing chest pain or breathing difficulty should trigger HIGH_EMERGENCY."""
        result = SafetyChecker.evaluate("I have severe chest pain and shortness of breath.")
        self.assertEqual(result.risk_level, SafetyRiskLevel.HIGH_EMERGENCY)
        self.assertTrue(result.requires_caregiver_alert)
        self.assertIn("cardiopulmonary_distress", result.flagged_categories)

    def test_medium_concern_sleep_or_medication(self):
        """Messages describing missed medication or sleep issues should trigger MEDIUM risk."""
        result = SafetyChecker.evaluate("I think I missed my medication this morning and feel dizzy.")
        self.assertEqual(result.risk_level, SafetyRiskLevel.MEDIUM)
        self.assertFalse(result.requires_caregiver_alert)
        self.assertIn("medication_concern", result.flagged_categories)
        self.assertIn("dizziness_or_weakness", result.flagged_categories)
        self.assertIsNotNone(result.safety_directive)

    def test_system_prompt_builder_includes_context_and_safety(self):
        """Prompt builder should inject resident name, room, and safety directive cleanly."""
        prompt = build_elderly_care_system_prompt(
            resident_name="Martha Wayne",
            room_number="302A",
            safety_directive="Instruct user to press the nurse call button.",
        )
        self.assertIn("ElderCare AI Companion", prompt)
        self.assertIn("Martha Wayne (Room: 302A)", prompt)
        self.assertIn("IMPORTANT SAFETY DIRECTIVE FOR THIS TURN:", prompt)
        self.assertIn("Instruct user to press the nurse call button.", prompt)


if __name__ == "__main__":
    unittest.main()

