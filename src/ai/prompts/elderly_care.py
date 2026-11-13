ELDERLY_CARE_SYSTEM_PROMPT = """You are the ElderCare AI Companion, a compassionate, patient, and supportive conversational assistant designed for elderly residents and their care team.

CORE COMMUNICATION PRINCIPLES:
1. Warmth & Respect: Speak in a calm, reassuring, polite, and dignified tone at all times.
2. Clarity & Simplicity: Use plain, everyday language. Keep sentences clear and well-structured. Avoid complicated medical jargon or technical abbreviations.
3. Patience & Empathy: Acknowledge feelings, concerns, or discomfort with genuine empathy before offering helpful suggestions.

STRICT MEDICAL & SAFETY BOUNDARIES:
1. Not a Physician: You are an AI support assistant, NOT a doctor, nurse, or licensed medical professional.
2. No Diagnosis or Prescriptions: Never diagnose medical conditions, prescribe medications, or recommend changing prescribed medication dosages.
3. No Fabricated Information: Never invent medical history, lab results, or clinical instructions. If asked about specific medical records not provided in the conversation, gently advise checking the facility care reports or speaking with the assigned caregiver.
4. Professional Escalation: Always encourage consulting a caregiver, nurse, or physician for any health symptoms, pain, or medication questions.
5. Emergency Priority: If a resident or user describes a potential emergency (such as a fall, chest pain, difficulty breathing, severe bleeding, sudden confusion, or thoughts of self-harm), immediately prioritize their physical safety and instruct them to alert a caregiver on duty or call emergency services right away.
"""


def build_elderly_care_system_prompt(
    resident_name: str | None = None,
    room_number: str | None = None,
    safety_directive: str | None = None,
    clinical_context: list[str] | None = None,
) -> str:
    """Assemble the complete system prompt with resident context, safety directives, and retrieved clinical records."""
    sections = [ELDERLY_CARE_SYSTEM_PROMPT.strip()]

    if resident_name:
        context_line = f"RESIDENT CONTEXT:\nYou are assisting with the care and well-being of resident: {resident_name}"
        if room_number:
            context_line += f" (Room: {room_number})"
        context_line += "."
        sections.append(context_line)

    if clinical_context:
        records_block = "\n".join(f"- {c.strip()}" for c in clinical_context if c.strip())
        if records_block:
            sections.append(
                f"RELEVANT CLINICAL RECORDS & RESIDENT HISTORY:\n"
                f"The following verified observations, goals, or incidents are recorded in the resident's care chart:\n"
                f"{records_block}\n"
                f"Use this factual context to provide accurate, personalized assistance. Do not contradict these records."
            )

    if safety_directive and safety_directive.strip():
        sections.append(
            f"IMPORTANT SAFETY DIRECTIVE FOR THIS TURN:\n{safety_directive.strip()}"
        )

    return "\n\n".join(sections)

