"""LLM model configuration for different system components.

Allows fine-grained control over which systems use which models.
"""

import os
from enum import Enum
from typing import Dict, Optional


class LLMContext(Enum):
    """Contexts for LLM usage in the game."""
    ADVISOR_QA = "advisor_qa"                    # Player questions to advisors
    DECISION_INTERPRETATION = "decision_interpretation"  # Parse player action
    ADVISOR_PUSHBACK = "advisor_pushback"        # Advisor concerns
    CRITICAL_OMISSIONS = "critical_omissions"    # Strategic gap detection
    INJECT_GENERATION = "inject_generation"      # Stochastic events
    DIPLOMACY_CONVERSATION = "diplomacy_conversation"  # Leader/diplomat responses
    DIPLOMACY_OUTCOME = "diplomacy_outcome"      # Assess conversation results
    CHARACTER_RESPONSE = "character_response"    # Flavor text
    QUALITY_ASSESSMENT = "quality_assessment"    # Action quality adjudication
    ACTOR_SIMULATION = "actor_simulation"        # State-actor responses
    SITUATION_SUMMARY = "situation_summary"      # End-of-turn summary refresh
    NARRATOR = "narrator"                        # Atmospheric bridges


class ModelTier(Enum):
    """Model tiers representing capability levels."""
    FLASH = "flash"  # Fast, cheap, good for routine tasks
    PRO = "pro"      # Sophisticated, expensive, for complex tasks


# Default model assignments
DEFAULT_MODEL_CONFIG: Dict[LLMContext, ModelTier] = {
    LLMContext.ADVISOR_QA: ModelTier.PRO,              # Complex strategic advice
    LLMContext.DECISION_INTERPRETATION: ModelTier.FLASH,  # Simple parsing
    LLMContext.ADVISOR_PUSHBACK: ModelTier.FLASH,      # Template warnings
    LLMContext.CRITICAL_OMISSIONS: ModelTier.PRO,      # Strategic analysis
    LLMContext.INJECT_GENERATION: ModelTier.PRO,       # Creative narrative
    LLMContext.DIPLOMACY_CONVERSATION: ModelTier.PRO,  # Sophisticated dialogue
    LLMContext.DIPLOMACY_OUTCOME: ModelTier.PRO,       # Strategic assessment
    LLMContext.CHARACTER_RESPONSE: ModelTier.FLASH,    # Simple flavor text
    LLMContext.QUALITY_ASSESSMENT: ModelTier.PRO,      # Decides what happens
    LLMContext.ACTOR_SIMULATION: ModelTier.PRO,        # In-character statecraft
    # The rolling synopsis is the campaign's memory: it anchors every
    # deciding call's context (ER-017), so a confabulated sentence here
    # propagates everywhere. That is PRO-tier work, one call per turn
    # (ER-048).
    LLMContext.SITUATION_SUMMARY: ModelTier.PRO,
    LLMContext.NARRATOR: ModelTier.FLASH,              # Short atmosphere text
}


# Model name mappings (Gemini tier names; other providers resolve through
# resolve_model_name below)
MODEL_NAMES: Dict[ModelTier, str] = {
    ModelTier.FLASH: "gemini-2.5-flash",
    ModelTier.PRO: "gemini-2.5-pro",
}


def _env_or_config(name: str) -> Optional[str]:
    """Resolve a setting from the environment first, then config.py."""
    value = os.getenv(name)
    if value:
        return value
    try:
        import config
        value = getattr(config, name, None)
        if value:
            return value
    except ImportError:
        pass
    return None


def resolve_model_name(provider: str, tier: ModelTier) -> Optional[str]:
    """Translate a model tier into a name the given provider understands.

    The tier table used to speak only Gemini: every name it produced began
    with "gemini", which the OpenAI-compatible driver rightly discards, so
    the table was inert on that provider. Resolving per provider makes the
    Flash/Pro selection meaningful everywhere it can be.

    Args:
        provider: Provider name ("gemini", "openai_compat", "mock", ...)
        tier: The model tier to resolve

    Returns:
        - gemini: the MODEL_NAMES entry for the tier
        - openai_compat: OPENAI_COMPAT_MODEL_FLASH / OPENAI_COMPAT_MODEL_PRO
          (environment first, then config.py), each falling back to
          OPENAI_COMPAT_MODEL; None when nothing is configured
        - mock/offline (and anything else): None - no notion of a model name
    """
    if provider == "gemini":
        return MODEL_NAMES[tier]
    if provider == "openai_compat":
        tier_var = ("OPENAI_COMPAT_MODEL_FLASH" if tier == ModelTier.FLASH
                    else "OPENAI_COMPAT_MODEL_PRO")
        return _env_or_config(tier_var) or _env_or_config("OPENAI_COMPAT_MODEL")
    return None


class ModelConfig:
    """Configuration for LLM model selection per context."""
    
    def __init__(self, custom_config: Optional[Dict[LLMContext, ModelTier]] = None):
        """Initialize model configuration.
        
        Args:
            custom_config: Optional custom configuration overriding defaults
        """
        self.config = DEFAULT_MODEL_CONFIG.copy()
        if custom_config:
            self.config.update(custom_config)
    
    def get_model_for_context(self, context: LLMContext) -> str:
        """Get model name for a specific context.
        
        Args:
            context: The LLM usage context
            
        Returns:
            Model name string (e.g., "gemini-2.5-pro")
        """
        tier = self.config.get(context, ModelTier.FLASH)
        return MODEL_NAMES[tier]

    def get_tier_for_context(self, context: LLMContext) -> ModelTier:
        """Get the configured model tier for a specific context.

        Args:
            context: The LLM usage context

        Returns:
            The ModelTier assigned to the context (FLASH if unconfigured)
        """
        return self.config.get(context, ModelTier.FLASH)

    def set_model_for_context(self, context: LLMContext, tier: ModelTier):
        """Override model for a specific context.
        
        Args:
            context: The LLM usage context
            tier: Model tier to use
        """
        self.config[context] = tier
    
    def use_flash_for_all(self):
        """Set all contexts to use Flash (cost-saving mode)."""
        for context in LLMContext:
            self.config[context] = ModelTier.FLASH
    
    def use_pro_for_all(self):
        """Set all contexts to use Pro (maximum quality mode)."""
        for context in LLMContext:
            self.config[context] = ModelTier.PRO
    
    def get_summary(self) -> Dict[str, str]:
        """Get human-readable summary of configuration.
        
        Returns:
            Dict mapping context names to model names
        """
        return {
            context.value: MODEL_NAMES[self.config[context]]
            for context in LLMContext
        }
    
    def estimate_cost_per_turn(self) -> float:
        """Estimate cost per turn based on configuration.
        
        Returns:
            Estimated cost in USD per turn
        """
        # Rough estimates based on typical call patterns
        call_estimates = {
            LLMContext.ADVISOR_QA: 3,           # 2-5 questions
            LLMContext.DECISION_INTERPRETATION: 1,
            LLMContext.ADVISOR_PUSHBACK: 5,
            LLMContext.CRITICAL_OMISSIONS: 1,
            LLMContext.INJECT_GENERATION: 0.5,  # Only after turn 6
            LLMContext.DIPLOMACY_CONVERSATION: 1.5,  # If used
            LLMContext.DIPLOMACY_OUTCOME: 0.5,  # If used
            LLMContext.CHARACTER_RESPONSE: 0.5,
            LLMContext.QUALITY_ASSESSMENT: 1,
            LLMContext.ACTOR_SIMULATION: 5,     # One per simulated capital
            LLMContext.SITUATION_SUMMARY: 1,
            LLMContext.NARRATOR: 1,
        }
        
        # Cost per call (very rough)
        flash_cost_per_call = 0.001  # $0.001
        pro_cost_per_call = 0.020    # $0.020
        
        total_cost = 0.0
        for context, calls in call_estimates.items():
            tier = self.config[context]
            cost_per = pro_cost_per_call if tier == ModelTier.PRO else flash_cost_per_call
            total_cost += calls * cost_per
        
        return total_cost


# Global config instance (can be overridden)
_global_config: Optional[ModelConfig] = None


def get_model_config() -> ModelConfig:
    """Get the global model configuration.
    
    Returns:
        Current ModelConfig instance
    """
    global _global_config
    if _global_config is None:
        _global_config = ModelConfig()
    return _global_config


def set_model_config(config: ModelConfig):
    """Set the global model configuration.
    
    Args:
        config: New ModelConfig instance
    """
    global _global_config
    _global_config = config


def reset_to_defaults():
    """Reset configuration to defaults."""
    global _global_config
    _global_config = ModelConfig()
