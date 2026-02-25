# Available Google/Gemini Models via API

**Last Updated:** 2025-10-27  
**API Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models`

Total Models: 50

---

## IMAGE GENERATION MODELS

### Imagen 3.0
- **Model ID:** `models/imagen-3.0-generate-002`
- **Method:** `predict`
- **Description:** Vertex served Imagen 3.0 002 model

### Imagen 4.0 (Latest Stable)
- **Model ID:** `models/imagen-4.0-generate-001`
- **Method:** `predict`
- **Description:** Vertex served Imagen 4.0 model

### Imagen 4.0 (Preview)
- **Model ID:** `models/imagen-4.0-generate-preview-06-06`
- **Method:** `predict`
- **Description:** Vertex served Imagen 4.0 model (preview)

### Imagen 4.0 Ultra (Preview)
- **Model ID:** `models/imagen-4.0-ultra-generate-preview-06-06`
- **Method:** `predict`
- **Description:** Vertex served Imagen 4.0 ultra model (highest quality)

### Gemini 2.5 Flash Image (Stable) ⭐
- **Model ID:** `models/gemini-2.5-flash-image`
- **Display Name:** Nano Banana
- **Method:** `generateContent`, `countTokens`, `batchGenerateContent`
- **Description:** Gemini 2.5 Flash Image (stable version)
- **Note:** Simpler API, uses standard generateContent method

### Gemini 2.5 Flash Image (Preview)
- **Model ID:** `models/gemini-2.5-flash-image-preview`
- **Display Name:** Nano Banana
- **Method:** `generateContent`, `countTokens`, `batchGenerateContent`
- **Description:** Gemini 2.5 Flash Preview Image

---

## TEXT/MULTIMODAL GENERATION MODELS

### Gemini 2.5 Pro (Latest Stable)
- **Model ID:** `models/gemini-2.5-pro`
- **Display Name:** Gemini 2.5 Pro
- **Methods:** `generateContent`, `countTokens`, `createCachedContent`, `batchGenerateContent`
- **Description:** Stable release (June 17th, 2025) of Gemini 2.5 Pro

### Gemini 2.5 Flash (Latest Stable)
- **Model ID:** `models/gemini-2.5-flash`
- **Display Name:** Gemini 2.5 Flash
- **Methods:** `generateContent`, `countTokens`, `createCachedContent`, `batchGenerateContent`
- **Description:** Stable version of Gemini 2.5 Flash, mid-size multimodal model supporting up to 1 million tokens (June 2025)

### Gemini 2.5 Flash-Lite (Latest Stable)
- **Model ID:** `models/gemini-2.5-flash-lite`
- **Display Name:** Gemini 2.5 Flash-Lite
- **Methods:** `generateContent`, `countTokens`, `createCachedContent`, `batchGenerateContent`
- **Description:** Stable version of Gemini 2.5 Flash-Lite (July 2025)

### Gemini 2.0 Flash (Latest Stable)
- **Model ID:** `models/gemini-2.0-flash-001`
- **Display Name:** Gemini 2.0 Flash 001
- **Methods:** `generateContent`, `countTokens`, `createCachedContent`, `batchGenerateContent`
- **Description:** Fast and versatile multimodal model (January 2025)

### Gemini 2.0 Flash-Lite
- **Model ID:** `models/gemini-2.0-flash-lite-001`
- **Display Name:** Gemini 2.0 Flash-Lite 001
- **Methods:** `generateContent`, `countTokens`, `createCachedContent`, `batchGenerateContent`
- **Description:** Stable version of Gemini 2.0 Flash-Lite

---

## PREVIEW/EXPERIMENTAL MODELS

### Gemini 2.5 Pro Preview (Latest)
- **Model ID:** `models/gemini-2.5-pro-preview-06-05`
- **Display Name:** Gemini 2.5 Pro Preview
- **Methods:** `generateContent`, `countTokens`, `createCachedContent`, `batchGenerateContent`
- **Description:** Preview release (June 5th, 2025)

### Gemini 2.5 Flash Preview (Latest)
- **Model ID:** `models/gemini-2.5-flash-preview-05-20`
- **Display Name:** Gemini 2.5 Flash Preview 05-20
- **Methods:** `generateContent`, `countTokens`, `createCachedContent`, `batchGenerateContent`
- **Description:** Preview release (April 17th, 2025)

### Gemini 2.0 Flash Experimental
- **Model ID:** `models/gemini-2.0-flash-exp`
- **Display Name:** Gemini 2.0 Flash Experimental
- **Methods:** `generateContent`, `countTokens`, `bidiGenerateContent`

### Gemini 2.0 Pro Experimental
- **Model ID:** `models/gemini-2.0-pro-exp`
- **Display Name:** Gemini 2.0 Pro Experimental
- **Methods:** `generateContent`, `countTokens`, `createCachedContent`, `batchGenerateContent`
- **Description:** Experimental release (March 25th, 2025)

### Gemini Experimental 1206
- **Model ID:** `models/gemini-exp-1206`
- **Display Name:** Gemini Experimental 1206
- **Methods:** `generateContent`, `countTokens`, `createCachedContent`, `batchGenerateContent`

### Gemini 2.0 Flash Thinking (Experimental)
- **Model ID:** `models/gemini-2.0-flash-thinking-exp`
- **Display Name:** Gemini 2.5 Flash Preview 05-20
- **Methods:** `generateContent`, `countTokens`, `createCachedContent`, `batchGenerateContent`

---

## SPECIALIZED MODELS

### Text-to-Speech (TTS)

#### Gemini 2.5 Flash Preview TTS
- **Model ID:** `models/gemini-2.5-flash-preview-tts`
- **Methods:** `countTokens`, `generateContent`

#### Gemini 2.5 Pro Preview TTS
- **Model ID:** `models/gemini-2.5-pro-preview-tts`
- **Methods:** `countTokens`, `generateContent`

### Computer Use
- **Model ID:** `models/gemini-2.5-computer-use-preview-10-2025`
- **Display Name:** Gemini 2.5 Computer Use Preview 10-2025
- **Methods:** `generateContent`, `countTokens`

### Robotics
- **Model ID:** `models/gemini-robotics-er-1.5-preview`
- **Display Name:** Gemini Robotics-ER 1.5 Preview
- **Methods:** `generateContent`, `countTokens`

### Learning-Optimized
- **Model ID:** `models/learnlm-2.0-flash-experimental`
- **Display Name:** LearnLM 2.0 Flash Experimental
- **Methods:** `generateContent`, `countTokens`

---

## EMBEDDING MODELS

### Text Embedding 004 (Recommended)
- **Model ID:** `models/text-embedding-004`
- **Display Name:** Text Embedding 004
- **Methods:** `embedContent`
- **Description:** Distributed text representation

### Gemini Embedding 001
- **Model ID:** `models/gemini-embedding-001`
- **Display Name:** Gemini Embedding 001
- **Methods:** `embedContent`, `countTextTokens`, `countTokens`, `asyncBatchEmbedContent`

### Gemini Embedding Experimental
- **Model ID:** `models/gemini-embedding-exp`
- **Display Name:** Gemini Embedding Experimental
- **Methods:** `embedContent`, `countTextTokens`, `countTokens`

### Embedding 001 (Legacy)
- **Model ID:** `models/embedding-001`
- **Methods:** `embedContent`

### Embedding Gecko 001 (Legacy)
- **Model ID:** `models/embedding-gecko-001`
- **Display Name:** Embedding Gecko
- **Methods:** `embedText`, `countTextTokens`

---

## GEMMA OPEN MODELS

### Gemma 3 Series (Open Source)
- **Gemma 3 1B:** `models/gemma-3-1b-it`
- **Gemma 3 4B:** `models/gemma-3-4b-it`
- **Gemma 3 12B:** `models/gemma-3-12b-it`
- **Gemma 3 27B:** `models/gemma-3-27b-it`
- **Gemma 3n E2B:** `models/gemma-3n-e2b-it`
- **Gemma 3n E4B:** `models/gemma-3n-e4b-it`
- **Methods:** `generateContent`, `countTokens`

---

## CONVENIENCE ALIASES

### Latest Stable Versions
- **Flash Latest:** `models/gemini-flash-latest`
- **Flash-Lite Latest:** `models/gemini-flash-lite-latest`
- **Pro Latest:** `models/gemini-pro-latest`

---

## SPECIALIZED TASKS

### Attributed Question Answering
- **Model ID:** `models/aqa`
- **Display Name:** Model that performs Attributed Question Answering
- **Methods:** `generateAnswer`
- **Description:** Returns answers grounded in provided sources with answerable probability

---

## NOTES

### For Image Generation Tasks:
- **Recommended:** `models/gemini-2.5-flash-image` (simple API, good quality)
- **Best Quality:** `models/imagen-4.0-ultra-generate-preview-06-06` (requires Vertex AI setup)
- **Stable Imagen:** `models/imagen-4.0-generate-001`

### For Text/Chat Tasks:
- **Fast & Efficient:** `models/gemini-2.5-flash`
- **Highest Quality:** `models/gemini-2.5-pro`
- **Lightweight:** `models/gemini-2.5-flash-lite`

### For Embeddings:
- **Recommended:** `models/text-embedding-004`

---

**Authentication:** All models require `GOOGLE_API_KEY` parameter in API requests  
**Base URL:** `https://generativelanguage.googleapis.com/v1beta/`


