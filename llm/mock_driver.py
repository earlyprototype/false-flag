"""Mock LLM driver for deterministic testing.

Provides simple template-based responses for conversational system.
"""

from random import Random


class MockDeterministicDriver:
    """Deterministic mock LLM driver for testing.
    
    Generates simple template-based responses that are deterministic
    given the same RNG seed.
    """

    def generate_text(self, prompt: str, rng: Random) -> str:
        """Generate mock response based on prompt keywords.
        
        Args:
            prompt: Input prompt
            rng: Random number generator (for future use)
        
        Returns:
            Mock response text
        """
        prompt_lower = prompt.lower()

        # Task-shaped prompts are checked BEFORE advisor personas: these prompts
        # embed the narrative context, which mentions advisors by title, so a
        # persona keyword would otherwise shadow the actual task.

        # Action quality assessment (narrative adjudication)
        if "assess this action" in prompt_lower:
            return ("QUALITY: adequate\n"
                    "\n"
                    "REASONING: A measured response that addresses the immediate situation without "
                    "overcommitting forces or foreclosing diplomatic options.\n"
                    "\n"
                    "EFFECTS:\n"
                    "escalation_risk: -2\n"
                    "alliance_cohesion: 3\n"
                    "domestic_stability: 1\n"
                    "\n"
                    "QUALITY MULTIPLIER: 1.0")

        # Situation summary refresh (end of turn)
        if "summarise the current situation" in prompt_lower:
            return ("The crisis continues to develop as Russian forces maintain their posture in the "
                    "North Atlantic. Allied consultations are ongoing and the public mood remains tense. "
                    "The Government's latest decision is being watched closely at home and abroad.")

        # Narrator bridge between turns
        if "atmospheric bridge" in prompt_lower:
            return ("The hours drag past in the bunker beneath Whitehall, each update thinning the "
                    "silence a little further. Then an aide appears at the door, folder in hand.")

        # Advisor response templates
        if "chief of the defence staff" in prompt_lower or "military commander" in prompt_lower:
            return ("Prime Minister, from a military perspective, we have limited options given our force posture. "
                    "Our Type-45 destroyers provide ballistic missile defence, but we can only maintain two simultaneous "
                    "combat air patrols across the entire UK. Any deployment must be carefully considered.")
        
        if "national security advisor" in prompt_lower or "intelligence coordinator" in prompt_lower:
            return ("Prime Minister, the intelligence picture suggests this is a coordinated campaign of coercion. "
                    "We assess Russia is testing NATO resolve. I recommend we coordinate closely with allies "
                    "and avoid actions that could be seen as escalatory without defensive justification.")
        
        if "foreign secretary" in prompt_lower or "diplomatic lead" in prompt_lower:
            return ("Prime Minister, diplomatically we must secure US and NATO commitment immediately. "
                    "Any unilateral action risks isolating us. I propose we activate Article 4 consultations "
                    "and engage directly with Washington.")
        
        if "home secretary" in prompt_lower or "domestic security" in prompt_lower:
            return ("Prime Minister, my concern is public safety and critical infrastructure protection. "
                    "We've already seen attacks on power and transport. We need to reassure the public "
                    "while preparing civil defence measures.")
        
        if "attorney general" in prompt_lower or "legal advisor" in prompt_lower:
            return ("Prime Minister, from a legal perspective, any use of force must be proportionate and "
                    "justified under international law. Self-defence is permitted, but we must document "
                    "the threat clearly. Nuclear first-use would be legally and politically catastrophic.")
        
        # Decision interpretation
        if "interpret this action" in prompt_lower:
            return ("INTERPRETATION: Deploy naval and air assets to defensive posture\n"
                    "FORCES INVOLVED: Type-45 destroyers, combat air patrols, P-8 reconnaissance\n"
                    "RESOURCES CONSUMED: Minimal (patrol operations)\n"
                    "TIMELINE: Immediate (within 1 turn)\n"
                    "FEASIBILITY: Feasible within current constraints")
        
        # Pushback generation
        if "pushback triggers" in prompt_lower:
            # Check for common trigger scenarios
            if "nuclear" in prompt_lower:
                return ("Attorney General: Prime Minister, nuclear first-use without imminent existential threat "
                        "violates our legal framework and would fracture NATO immediately.\n"
                        "Foreign Secretary: This would end US support and isolate us internationally.")
            
            if "deploy" in prompt_lower and ("carrier" in prompt_lower or "prince of wales" in prompt_lower):
                return ("Chief of the Defence Staff: Prime Minister, HMS Prince of Wales is not at highest readiness. "
                        "We can surge her immediately at reduced capability, or wait 3 turns for full readiness.")
            
            return "NO PUSHBACK"
        
        # Inject generation
        if "generate the next inject" in prompt_lower:
            return """```yaml
id: turn_002_inject
title: "Russian Submarine Surfaces Near UK Waters"
description: |
  A Russian Kilo-class submarine has surfaced approximately 12 nautical miles off the Orkney Islands,
  within sight of a commercial ferry. The submarine remained on the surface for approximately 15 minutes
  before submerging. This provocative act was witnessed by civilians and is already spreading on social media.
  
  Intelligence assessment: This is a deliberate show of force designed to intimidate and test UK response.
  The submarine is part of the larger Northern Fleet deployment.
channel: intelligence
effects:
  - metric: escalation_risk
    delta: 5..10
  - metric: domestic_stability
    delta: -3..-5
```"""
        
        # Default response
        return "Understood, Prime Minister. I'll provide my assessment based on the current situation."
    
    def batch_generate_text(self, prompts: list[str], rng: Random) -> list[str]:
        """Generate multiple mock responses in parallel (simulated).
        
        Args:
            prompts: List of prompt texts
            rng: Random number generator
        
        Returns:
            List of mock responses in same order as prompts
        """
        # For mock driver, just call generate_text sequentially
        # (No actual parallelism needed for testing)
        return [self.generate_text(prompt, rng) for prompt in prompts]


