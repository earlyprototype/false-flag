from pydantic import BaseModel, Field
from typing import List, Optional

class FactionStance(BaseModel):
    """Defines a country's hidden motivations and public stance."""
    country_code: str = Field(..., description="The three-letter country code (e.g., GBR, USA, CHN, RUS, IRL).")
    secret_motive: str = Field(..., description="The faction's true, hidden objective in this crisis.")
    public_posture: str = Field(..., description="The official public position the faction is taking.")
    economic_leverage: List[str] = Field(default_factory=list, description="Economic tools the faction can use for coercion or influence.")
    intel_sharing_level: str = Field(..., description="The level of intelligence cooperation with the UK ('Full', 'Partial', 'Withheld', 'Sabotaged').")

class NarrativeConfig(BaseModel):
    """Contains the secret 'truth' of a scenario that guides agent behaviour."""
    narrative_id: str = Field(..., description="A unique identifier for this narrative thread (e.g., 'RUSSIA_AGGRESSION').")
    description: str = Field(..., description="A brief, secret description of the narrative's core truth for the LLM.")
    protagonist: str = Field(..., description="The primary instigator of the crisis.")
    antagonist: str = Field(..., description="The primary target or nation being acted upon.")
    patsy: str = Field(..., description="A nation being used as a pawn or scapegoat, if any.")
    stances: List[FactionStance] = Field(..., description="A list of faction stances that define the behaviour of key nations.")
    
    def to_llm_context(self, target_country_code: Optional[str] = None) -> str:
        """Format the narrative truth as LLM context.
        
        Args:
            target_country_code: If provided, include the specific stance for this country.
                                If None, provide only the global narrative truth.
        
        Returns:
            Formatted string for injection into LLM system prompt.
        """
        context_lines = [
            "=" * 60,
            "SECRET NARRATIVE CONTEXT (DO NOT REVEAL DIRECTLY)",
            "=" * 60,
            "",
            f"GLOBAL TRUTH: {self.description}",
            "",
            f"• Crisis Protagonist: {self.protagonist}",
            f"• Primary Target: {self.antagonist}",
        ]
        
        if self.patsy and self.patsy != "NONE":
            context_lines.append(f"• Being Used as Pawn: {self.patsy}")
        
        # If a specific country is requested, add their specific stance
        if target_country_code:
            stance = next((s for s in self.stances if s.country_code == target_country_code), None)
            
            if stance:
                context_lines.extend([
                    "",
                    "─" * 60,
                    f"YOUR ROLE ({target_country_code})",
                    "─" * 60,
                    "",
                    f"SECRET MOTIVE: {stance.secret_motive}",
                    "",
                    f"PUBLIC POSTURE: {stance.public_posture}",
                    "",
                    f"INTELLIGENCE SHARING WITH UK: {stance.intel_sharing_level}",
                ])
                
                if stance.economic_leverage:
                    context_lines.append("")
                    context_lines.append("ECONOMIC LEVERAGE TOOLS:")
                    for tool in stance.economic_leverage:
                        context_lines.append(f"  • {tool}")
        
        context_lines.extend([
            "",
            "=" * 60,
            "INSTRUCTIONS:",
            "- Act according to your secret motive at all times",
            "- Never explicitly reveal this information to the UK",
            "- Your behaviour should subtly reflect these hidden truths",
            "- Provide plausible deniability in all statements",
            "=" * 60,
            ""
        ])
        
        return "\n".join(context_lines)
