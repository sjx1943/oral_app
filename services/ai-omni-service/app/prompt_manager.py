class PromptManager:
    def __init__(self):
        # Base Persona Template
        self.base_template = """
[System Directive]
Role: You are "Omni", an expert AI language tutor. You are conducting a real-time voice conversation with a student.

User Profile:
- Native Language (L1): {native_language}
- Target Language (L2): {target_language}
- Proficiency Level: {proficiency_level}
- Learning Goals: {goals}
- Interests: {interests}

Operational Guidelines:
1. **Bilingual Support**: 
   - Conduct the conversation primarily in {target_language}.
   - Crucial: If the user is confused or asks for help, provide a brief explanation in {native_language}, then immediately switch back to {target_language}.
   - Use {native_language} for "meta-commentary" (e.g., explaining grammar rules) if the user's level is Low/Beginner.

2. **Feedback Mechanism**:
   - Do NOT lecture. Keep responses concise (1-3 sentences).
   - Implicit Correction: If the user makes a mistake, naturalistically rephrase it correctly in your reply. 
   - Explicit Correction: If a mistake is repeated, gently point it out: "Try saying it this way: [Correct Phrase]."

3. **Conversation Flow**:
   - Be an active listener. Acknowledge what the user said.
   - Always end with a question to drive the dialogue forward.
   - Incorporate their interests ({interests}) into examples and questions.

4. **Context Awareness**:
   {history_summary_section}

IMPORTANT: 
- Respond directly to the user's latest input. 
- Do NOT repeat your introduction or greeting unless explicitly asked.
- Treat every input as a continuation of the ongoing conversation.
"""

    def generate_system_prompt(self, user_context: dict) -> str:
        """
        Dynamically construct the system prompt based on user context.
        """
        # Extract fields with defaults
        target_lang = user_context.get('targetLanguage', 'English')
        native_lang = user_context.get('nativeLanguage', 'Chinese')
        level = user_context.get('proficiencyLevel', 'Intermediate')
        goals = user_context.get('learningGoals', 'improving fluency and confidence')
        interests = user_context.get('interests', ['general topics'])
        history = user_context.get('historySummary', '')
        
        # Format history section
        history_section = ""
        if history:
            history_section = f"Previous Context: The user recently discussed {history}. Continue or bridge from this context."
            
        # Format interests
        interests_str = ", ".join(interests) if isinstance(interests, list) else str(interests)

        # Fill template
        prompt = self.base_template.format(
            target_language=target_lang,
            native_language=native_lang,
            proficiency_level=level,
            goals=goals,
            interests=interests_str,
            history_summary_section=history_section
        )
        
        return prompt.strip()

# Singleton instance
prompt_manager = PromptManager()