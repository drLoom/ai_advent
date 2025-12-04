# Image Generation Guide

Complete guide for AI-powered image generation using the CLI.

## Overview

The image generation module provides a full-featured pipeline for creating AI images from text prompts with:
- Multiple model support via OpenRouter
- Full parameter control (size, quality, seed)
- Comprehensive request logging
- Automatic latency tracking
- Cost estimation
- Image saving capabilities

## Architecture

### Components

```
┌─────────────────┐
│  CLI Commands   │  cli/image_commands.py
│  (Typer)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Image Client   │  ai/image_client.py
│  (API Handler)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  OpenRouter     │  https://openrouter.ai/api/v1
│  API            │
└─────────────────┘
```

### Files

1. **`models/models.py`**: Configuration constants
   - `IMAGE_MODEL`: Default model name
   - `IMAGE_DEFAULT_SIZE`: Default image dimensions
   - `IMAGE_DEFAULT_QUALITY`: Default quality setting

2. **`ai/image_client.py`**: Core image generation logic
   - `ImageClient`: Main client class
   - `ImageGenerationRequest`: Request data container
   - `ImageGenerationResponse`: Response data container
   - `ImageGenerationLogger`: Request logging handler

3. **`cli/image_commands.py`**: CLI interface
   - `generate`: Generate images
   - `logs`: View request logs
   - `info`: Display configuration

## Quick Start

### Basic Usage

```bash
# Generate an image
uv run python main.py image generate "a serene lake at sunset"

# With custom size
uv run python main.py image generate "cyberpunk cityscape" --size 512x512

# Save to file
uv run python main.py image generate "mountain landscape" --output mountain.png
```

### View Configuration

```bash
uv run python main.py image info
```

Output:
```
Image Generation Configuration

┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Setting         ┃ Value                 ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ Default Model   │ amazon/nova-2-lite-v1 │
│ Default Size    │ 1024x1024             │
│ Default Quality │ standard              │
│ Log File        │ image_generation.log  │
└─────────────────┴───────────────────────┘
```

## Parameters

### Required Parameters

#### `prompt` (string)
Text description of the image to generate.

**Examples:**
```bash
"a beautiful sunset over mountains"
"cyberpunk city with neon lights"
"abstract geometric patterns in blue and gold"
"photorealistic portrait of a wise old wizard"
```

**Best practices:**
- Be specific and descriptive
- Include style hints (photorealistic, watercolor, digital art, etc.)
- Mention colors, mood, lighting
- Specify composition (close-up, wide shot, etc.)

### Optional Parameters

#### `--model` / `-m` (string)
Image generation model to use.

**Default:** `amazon/nova-2-lite-v1`

**Examples:**
```bash
--model amazon/nova-2-lite-v1
--model flux/schnell
--model dall-e-3
```

**Available models via OpenRouter:**
- `amazon/nova-2-lite-v1`: Fast, cost-effective
- `flux/schnell`: High quality, fast generation
- `flux/dev`: Premium quality
- `dall-e-3`: OpenAI's DALL-E 3

---

#### `--size` / `-s` (string)
Image dimensions in format WIDTHxHEIGHT.

**Default:** `1024x1024`

**Common sizes:**
```bash
--size 512x512    # Small, fast
--size 768x768    # Medium
--size 1024x1024  # Large, square (default)
--size 1024x768   # Landscape
--size 768x1024   # Portrait
--size 1920x1080  # HD (if supported)
```

**Notes:**
- Not all models support all sizes
- Larger sizes take longer and may cost more
- Square sizes often work best

---

#### `--quality` / `-q` (string or number)
Quality/detail level or number of generation steps.

**Default:** `standard`

**Options:**
```bash
--quality standard  # Standard quality
--quality high      # High quality/detail
--quality 20        # Specific number of steps
--quality 50        # More steps = more detail
```

**Notes:**
- String values: `standard`, `high`, `ultra`
- Numeric values: Number of generation steps (typically 10-100)
- More steps = higher quality but slower generation

---

#### `--seed` (integer)
Random seed for reproducible results.

**Default:** None (random)

**Examples:**
```bash
--seed 42
--seed 12345
--seed 999999
```

**Use cases:**
- Reproduce exact same image
- Generate variations with slight prompt changes
- A/B testing different parameters

**Example workflow:**
```bash
# Generate with seed
uv run python main.py image generate "sunset" --seed 42 --output v1.png

# Modify prompt, keep seed for similar composition
uv run python main.py image generate "sunset with birds" --seed 42 --output v2.png
```

---

#### `--output` / `-o` (string)
File path to save the generated image.

**Default:** None (image URL only)

**Examples:**
```bash
--output image.png
--output images/sunset_001.png
--output ../outputs/$(date +%Y%m%d_%H%M%S).png
```

**Supported formats:**
- PNG (recommended)
- JPG/JPEG
- Format determined by file extension

**Notes:**
- Parent directories are created automatically
- Existing files are overwritten
- Image is also accessible via URL regardless of saving

---

#### `--no-log` (flag)
Disable request logging.

**Default:** Logging enabled

**Usage:**
```bash
uv run python main.py image generate "test" --no-log
```

**When to use:**
- Testing/development
- Privacy concerns
- Temporary generations
- Reducing disk usage

## Request Logging

### What Gets Logged

Every image generation request logs:

1. **Timestamp**: When the request was made
2. **Model**: Which model was used
3. **Prompt**: The text prompt (truncated to 100 chars in log)
4. **Size**: Image dimensions
5. **Quality**: Quality/steps parameter
6. **Seed**: Random seed (if provided)
7. **Latency**: Response time in milliseconds
8. **Cost Estimate**: Estimated cost (if available from API)
9. **Image URL**: Generated image URL (truncated in log)

### Log File Location

**Default:** `image_generation.log` in project root

### Log Format

```
2025-12-03 16:30:45 - image_generation - INFO - Image generation: {
  "timestamp": "2025-12-03T16:30:45.123456",
  "model": "amazon/nova-2-lite-v1",
  "prompt": "a beautiful sunset over mountains with dramatic clouds",
  "size": "1024x1024",
  "quality": "standard",
  "seed": 42,
  "latency_ms": 2543.21,
  "cost_estimate": 0.0023,
  "image_url": "https://api.openrouter.ai/..."
}
```

### Viewing Logs

```bash
# View last 10 logs
uv run python main.py image logs

# View last 50 logs
uv run python main.py image logs --limit 50

# View specific log file
uv run python main.py image logs --file custom.log
```

### Log Analysis

Extract useful metrics from logs:

```bash
# Count total generations
grep "Image generation:" image_generation.log | wc -l

# Average latency (requires jq)
grep "latency_ms" image_generation.log | \
  grep -oP '"latency_ms": \K[0-9.]+' | \
  awk '{sum+=$1; count++} END {print sum/count}'

# Total estimated cost
grep "cost_estimate" image_generation.log | \
  grep -oP '"cost_estimate": \K[0-9.]+' | \
  awk '{sum+=$1} END {print sum}'

# Most used models
grep "model" image_generation.log | \
  grep -oP '"model": "\K[^"]+' | \
  sort | uniq -c | sort -rn
```

## Examples

### 1. Basic Generation

```bash
uv run python main.py image generate "a serene mountain lake at sunrise"
```

**Output:**
```
Image Generation Request
Model: amazon/nova-2-lite-v1
Prompt: a serene mountain lake at sunrise
Size: 1024x1024
Quality: standard

✓ Image Generated Successfully!

┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Metric       ┃ Value                            ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Image URL    │ https://...                      │
│ Latency      │ 2543.21 ms                       │
│ Cost Estimate│ $0.0023                          │
└──────────────┴──────────────────────────────────┘

View your image at:
https://api.openrouter.ai/...

Request logged to: image_generation.log
```

---

### 2. High Quality with Seed

```bash
uv run python main.py image generate \
  "photorealistic portrait of a astronaut" \
  --quality high \
  --seed 42 \
  --output astronaut.png
```

**Use case:** High-quality image with reproducible seed, saved to file

---

### 3. Custom Size and Model

```bash
uv run python main.py image generate \
  "abstract geometric art in vibrant colors" \
  --model flux/schnell \
  --size 768x768 \
  --output art.png
```

**Use case:** Using alternative model with custom dimensions

---

### 4. Batch Generation

```bash
# Generate multiple variations with different seeds
for seed in 42 123 456 789; do
  uv run python main.py image generate \
    "fantasy castle on a cliff" \
    --seed $seed \
    --output "castle_${seed}.png"
done
```

**Use case:** Generate variations of the same prompt

---

### 5. Size Comparison

```bash
# Generate same prompt in different sizes
for size in 512x512 768x768 1024x1024; do
  uv run python main.py image generate \
    "minimalist logo design" \
    --size $size \
    --seed 42 \
    --output "logo_${size}.png"
done
```

**Use case:** Test optimal size for your use case

---

### 6. Quality Comparison

```bash
# Compare different quality settings
uv run python main.py image generate "detailed landscape" \
  --quality standard --seed 42 --output standard.png

uv run python main.py image generate "detailed landscape" \
  --quality high --seed 42 --output high.png
```

**Use case:** Compare quality vs generation time

## Configuration

### Changing Default Model

Edit `models/models.py`:

```python
# Before
IMAGE_MODEL = 'amazon/nova-2-lite-v1'

# After
IMAGE_MODEL = 'flux/schnell'
```

### Changing Default Parameters

Edit `models/models.py`:

```python
IMAGE_DEFAULT_SIZE = "768x768"      # Was: 1024x1024
IMAGE_DEFAULT_QUALITY = "high"      # Was: standard
IMAGE_DEFAULT_STEPS = 50            # Was: 20
```

### Custom Log File

When using the client directly:

```python
from ai.image_client import ImageClient

client = ImageClient(log_requests=True)
client.request_logger.log_file = "custom_logs.log"
```

## Programmatic Usage

### Using ImageClient in Code

```python
from ai.image_client import ImageClient

# Initialize client
client = ImageClient()

# Generate image
response = client.generate_image(
    prompt="a beautiful sunset",
    size="1024x1024",
    quality="standard",
    seed=42,
    save_to="output.png"
)

# Access results
print(f"Image URL: {response.image_url}")
print(f"Latency: {response.latency_ms}ms")
print(f"Cost: ${response.cost_estimate}")
```

### Disable Logging Programmatically

```python
client = ImageClient(log_requests=False)
```

## Troubleshooting

### Error: API Key Not Configured

**Problem:**
```
ValueError: OpenRouter API key not configured
```

**Solution:**
1. Create/edit `.env` file:
```bash
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

2. Or export environment variable:
```bash
export OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

---

### Error: Invalid Size Format

**Problem:**
```
ValueError: Invalid size format: 1024. Expected format: WIDTHxHEIGHT
```

**Solution:**
Use correct format with 'x' separator:
```bash
--size 1024x1024  # Correct
--size 1024       # Wrong
```

---

### Error: Request Timeout

**Problem:**
Image generation takes too long and times out.

**Solution:**
- Try smaller image size
- Use faster model (e.g., `amazon/nova-2-lite-v1`)
- Reduce quality/steps
- Check internet connection

---

### Error: Model Not Found

**Problem:**
```
Error: Model 'xyz' not found
```

**Solution:**
- Check available models in OpenRouter documentation
- Verify model name spelling
- Some models require specific API access

## Best Practices

1. **Start Small**: Test with 512x512 before generating larger images
2. **Use Seeds**: For consistent results, always use seeds during testing
3. **Save Important Images**: Use `--output` for images you want to keep
4. **Monitor Costs**: Check logs regularly for cost estimates
5. **Descriptive Prompts**: More detail = better results
6. **Model Selection**: Choose model based on speed vs quality needs
7. **Batch Processing**: Use seeds and loops for variations
8. **Log Analysis**: Review logs to optimize parameters

## Performance Tips

1. **Latency Optimization**:
   - Use `amazon/nova-2-lite-v1` for fastest generation
   - Smaller sizes generate faster
   - Lower quality/steps = faster generation

2. **Quality Optimization**:
   - Use `flux/dev` or `dall-e-3` for best quality
   - Increase steps (20 → 50+) for more detail
   - Larger sizes provide more detail

3. **Cost Optimization**:
   - Monitor cost estimates in logs
   - Use smaller sizes when possible
   - Choose cost-effective models

## API Reference

### ImageClient

```python
class ImageClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        log_requests: bool = True
    )

    def generate_image(
        self,
        prompt: str,
        model: str = IMAGE_MODEL,
        size: str = IMAGE_DEFAULT_SIZE,
        quality: str = IMAGE_DEFAULT_QUALITY,
        seed: Optional[int] = None,
        save_to: Optional[str] = None
    ) -> ImageGenerationResponse
```

### ImageGenerationResponse

```python
class ImageGenerationResponse:
    image_url: str              # URL of generated image
    request: ImageGenerationRequest  # Original request
    latency_ms: float           # Generation time in ms
    cost_estimate: Optional[float]  # Estimated cost
    raw_response: Dict          # Full API response
```

## Related Documentation

- [Main README](README.md)
- [Models Configuration](models/models.py)
- [OpenRouter API Documentation](https://openrouter.ai/docs)

---

*Last updated: December 3, 2025*
