"""Gemini LLM driver for Google's Gemini API.

Implements text generation using Gemini 2.5 Flash via the Google Generative AI API.
Requires GOOGLE_API_KEY environment variable.
"""

import os
from random import Random
from typing import Optional

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


def _truncate(text: str, limit: int = 200) -> str:
    """Truncate long strings (e.g. response reprs) for error messages."""
    if len(text) <= limit:
        return text
    return text[:limit] + "... [truncated]"


class GeminiDriver:
    """Driver for Google Gemini 2.5 Flash API.
    
    Uses the google-generativeai Python SDK to generate text responses.
    Falls back gracefully if the SDK is not installed.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """Initialize Gemini driver.
        
        Args:
            model_name: Gemini model to use (default: from config.py or gemini-2.5-flash)
        
        Raises:
            RuntimeError: If google-generativeai is not installed
            ValueError: If GOOGLE_API_KEY is not set
        """
        if not GENAI_AVAILABLE:
            raise RuntimeError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )
        
        # Get API key from config.py or environment variable
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            try:
                import config
                api_key = getattr(config, "GOOGLE_API_KEY", None)
            except ImportError:
                pass
        
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found in config.py or environment variable. "
                "Get your free API key from: https://aistudio.google.com/apikey"
            )
        
        genai.configure(api_key=api_key)
        
        # Get model name from config.py if not specified
        if model_name is None:
            try:
                import config
                model_name = getattr(config, "GEMINI_MODEL", "gemini-2.5-flash")
            except ImportError:
                model_name = "gemini-2.5-flash"
        
        self.model_name = model_name
        
        # Configure safety settings for mature political simulation
        # This is a wargame with adult themes, political content, and strong language
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        self.safety_settings = safety_settings
        self.model = genai.GenerativeModel(
            model_name,
            safety_settings=safety_settings
        )

        # Get generation config from config.py
        try:
            import config
            temperature = getattr(config, "GEMINI_TEMPERATURE", 0.7)
            max_tokens = getattr(config, "GEMINI_MAX_TOKENS", 2048)
        except ImportError:
            temperature = 0.7
            max_tokens = 2048

        self.default_temperature = temperature
        self.default_max_tokens = max_tokens

        # Generation config for deterministic output
        self.generation_config = genai.GenerationConfig(
            temperature=temperature,
            top_p=0.9,
            top_k=40,
            max_output_tokens=max_tokens,
        )

    def _build_generation_config(self, temperature: Optional[float] = None,
                                 max_tokens: Optional[int] = None):
        """Generation config with optional per-call overrides (ER-011).

        Returns the shared default config when no override is given, so the
        common path allocates nothing new.
        """
        if temperature is None and max_tokens is None:
            return self.generation_config
        return genai.GenerationConfig(
            temperature=temperature if temperature is not None else self.default_temperature,
            top_p=0.9,
            top_k=40,
            max_output_tokens=max_tokens if max_tokens is not None else self.default_max_tokens,
        )

    def _model_for(self, system_instruction: Optional[str] = None):
        """The shared model, or a per-call variant carrying a system instruction.

        The SDK takes system instructions on the model object rather than in
        the generation config, so a call that supplies one gets a throwaway
        model built with the same name and safety settings.
        """
        if not system_instruction:
            return self.model
        return genai.GenerativeModel(
            self.model_name,
            safety_settings=self.safety_settings,
            system_instruction=system_instruction,
        )

    def generate_text(self, prompt: str, rng: Random,
                      system_instruction: Optional[str] = None,
                      temperature: Optional[float] = None,
                      max_tokens: Optional[int] = None) -> str:
        """Generate text response from prompt using Gemini.

        Args:
            prompt: Input prompt text
            rng: Random number generator (used to set seed for determinism)
            system_instruction: Optional system instruction for the model
            temperature: Optional temperature override
            max_tokens: Optional output cap override

        Returns:
            Generated text response

        Raises:
            Exception: If API call fails
        """
        try:
            # Use RNG seed to make generation more deterministic
            # Note: Gemini doesn't support explicit seed, but we can use temperature
            _seed = rng.randint(0, 2**31 - 1)

            generation_config = self._build_generation_config(temperature, max_tokens)
            model = self._model_for(system_instruction)

            # Generate response (60s timeout so a hung request can't stall the game)
            try:
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    request_options={"timeout": 60},
                )
            except TypeError:
                # Older SDK versions don't accept request_options
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config,
                )

            # Extract text from response
            if response.text:
                return response.text.strip()
            else:
                # Handle blocked or empty responses
                finish_reason = getattr(response.candidates[0], 'finish_reason', 'UNKNOWN') if response.candidates else 'NO_CANDIDATES'
                raise RuntimeError(f"Gemini returned no text. Finish reason: {finish_reason}. Response: {_truncate(repr(response))}")

        except Exception as e:
            # Re-raise exception so caller can handle it properly, keeping the
            # original type in the message and truncating verbose payloads
            raise Exception(f"Gemini API Error ({type(e).__name__}): {_truncate(str(e), 300)}") from e
    
    def batch_generate_text(self, prompts: list[str], rng: Random,
                            max_tokens: Optional[int] = None) -> list[str]:
        """Generate multiple text responses in parallel using concurrent processing.

        Uses ThreadPoolExecutor to make parallel API calls for faster processing.

        Args:
            prompts: List of prompt texts to generate responses for
            rng: Random number generator (used to set seed for determinism)
            max_tokens: Optional output cap applied to every prompt

        Returns:
            List of generated text responses in same order as prompts

        Raises:
            Exception: If API call fails
        """
        if not prompts:
            return []

        from concurrent.futures import ThreadPoolExecutor, as_completed

        generation_config = self._build_generation_config(max_tokens=max_tokens)

        def generate_single(prompt: str) -> str:
            """Generate single response - used by thread pool."""
            try:
                try:
                    response = self.model.generate_content(
                        prompt,
                        generation_config=generation_config,
                        request_options={"timeout": 60},
                    )
                except TypeError:
                    # Older SDK versions don't accept request_options
                    response = self.model.generate_content(
                        prompt,
                        generation_config=generation_config,
                    )

                if response.text:
                    return response.text.strip()
                else:
                    finish_reason = getattr(response.candidates[0], 'finish_reason', 'UNKNOWN') if response.candidates else 'NO_CANDIDATES'
                    return f"[ERROR: {finish_reason}]"
            except Exception as e:
                return f"[ERROR: {str(e)}]"
        
        # Use ThreadPoolExecutor for parallel processing
        # Process all prompts concurrently (up to max_workers)
        max_workers = min(len(prompts), 10)  # Limit concurrent requests
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_prompt = {executor.submit(generate_single, prompt): i 
                                for i, prompt in enumerate(prompts)}
            
            # Collect results in order
            results = [None] * len(prompts)
            for future in as_completed(future_to_prompt):
                index = future_to_prompt[future]
                try:
                    results[index] = future.result()
                except Exception as e:
                    results[index] = f"[ERROR: {str(e)}]"
        
        return results
    
    def __repr__(self) -> str:
        return f"GeminiDriver(model={self.model_name})"

