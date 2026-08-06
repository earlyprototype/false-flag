import logging

from pydantic import BaseModel, Field
from typing import List, Optional

logger = logging.getLogger(__name__)

# Country-code aliases onto the ISO-3 codes the scenario's stance lists use
# (ER-012). The engine's diplomatic switchboard keys off profile names ("US",
# "Russia") while narratives.yaml writes ISO-3 ("USA", "RUS"), so the stance
# lookup must speak both. Deliberately independent of engine.diplomacy's
# COUNTRY_ALIASES: models/ must not import from engine/ (layering).
_CANON = {
    "US": "USA", "USA": "USA", "UNITED STATES": "USA",
    "RUSSIA": "RUS", "RUS": "RUS",
    "CHINA": "CHN", "CHN": "CHN", "PRC": "CHN",
    "IRELAND": "IRL", "IRL": "IRL", "IRE": "IRL",
    "FRANCE": "FRA", "FRA": "FRA",
    "GERMANY": "DEU", "DEU": "DEU", "GER": "DEU",
    "POLAND": "POL", "POL": "POL",
    "UKRAINE": "UKR", "UKR": "UKR",
    "UK": "GBR", "UNITED KINGDOM": "GBR", "GBR": "GBR",
}


def _canon(code: str) -> str:
    """Resolve a country code or name onto its ISO-3 canonical form.

    Unknown values pass through upper-cased, so an exact match still works
    for codes the alias table has never heard of.
    """
    key = str(code).strip().upper()
    return _CANON.get(key, key)


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

    def to_llm_context(self, target_country_code: Optional[str] = None,
                       audience: str = "roleplay") -> str:
        """Format the narrative truth as LLM context.

        Args:
            target_country_code: If provided, include the specific stance for this country.
                                If None, provide only the global narrative truth.
            audience: "roleplay" when the reader IS a faction being played (a
                     foreign leader, a state actor) and should act on its
                     secret motive; "briefing" when the reader is briefing or
                     judging the player (advisors, inject generation, quality
                     assessment) and must never deceive them (ER-021).

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

        # If a specific country is requested, add their specific stance.
        # Both sides of the comparison are canonicalised: the scenario writes
        # ISO-3, the engine passes diplomatic-profile keys (ER-012).
        if target_country_code:
            target = _canon(target_country_code)
            stance = next((s for s in self.stances if _canon(s.country_code) == target), None)

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
            else:
                logger.warning("[PARSE-MISS] narrative_stance %s", target_country_code)

        if audience == "briefing":
            # The reader advises or judges the Prime Minister. The truth is
            # background for the simulation, never a script to act out.
            context_lines.extend([
                "",
                "=" * 60,
                "INSTRUCTIONS:",
                "- This hidden truth is background for YOU, the simulation, only.",
                "- The player has not been told it and must not be told it directly.",
                "- Use it to judge plausibility and foresee consequences; never to deceive the Prime Minister.",
                "=" * 60,
                ""
            ])
        else:
            # The reader IS a faction being roleplayed.
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
