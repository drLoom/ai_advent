# Image Quality Validation System

## Overview

The image generation pipeline now includes an automated quality validation system that uses vision AI to analyze generated images against your style profile criteria.

## How It Works

### Pipeline: Generate → Analyze → Score

1. **Generate**: Image is created using your style profile
2. **Analyze**: Vision model examines the image
3. **Score**: Each criterion is scored 0.0-1.0
4. **Decision**: Pass/fail based on threshold

## Quality Checklist

The validation automatically builds a checklist from your style profile:

### From `color_palette`:
- ✓ Uses specified colors (purple, white, blue, yellow, green, etc.)

### From `visual_style`:
- ✓ Matches dimension requirements (DSLR camera, bokeh blur, etc.)
- ✓ Has correct texture (macro detail, sand grains, weathering)
- ✓ Meets detail level (hyper-realistic 8K photography)

### From `dos`:
- ✓ Contains required elements (surfboard only, no people, reggae colors)

### From `donts`:
- ✓ Does NOT contain forbidden elements (no digital art, no people, no waves)

### Photorealism Check:
- ✓ Looks like real photograph (not illustration or digital art)

## Usage

### Basic Validation

```bash
uv run python main.py image generate "surfboard" \
  --prompt-file surfing_ocean \
  --validate
```

### Custom Threshold

Set minimum score required to pass (0.0-1.0):

```bash
uv run python main.py image generate "surfboard" \
  --prompt-file surfing_ocean \
  --validate \
  --threshold 0.8
```

### With Retry (Future)

Automatically regenerate if image fails:

```bash
uv run python main.py image generate "surfboard" \
  --prompt-file surfing_ocean \
  --validate \
  --retry
```

## Output Example

```
Quality Analysis Results

┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┓
┃ Criterion          ┃ Score ┃ Status ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━┩
│ Color Palette      │  1.00 │ ✓      │
│ Dimension          │  0.90 │ ✓      │
│ Texture            │  0.90 │ ✓      │
│ Detail Level       │  0.80 │ ✓      │
│ Required Elements  │  1.00 │ ✓      │
│ Forbidden Elements │  1.00 │ ✓      │
│ Photorealism       │  0.90 │ ✓      │
└────────────────────┴───────┴────────┘

Overall Score: 0.93 PASS

Feedback: This image very closely matches the requested attributes,
with high photorealism, correct color palette, and texture.
```

## Score Interpretation

- **1.0** = Perfect match
- **0.8-0.9** = Very good, minor issues
- **0.6-0.7** = Acceptable, some issues
- **<0.6** = Poor quality, needs regeneration

## Vision Model

Uses: `google/gemini-2.0-flash-exp:free` via OpenRouter

- Analyzes images against detailed criteria
- Provides scores for each quality dimension
- Gives actionable feedback on issues

## API Files

### `ai/vision_client.py`

**VisionClient**: Analyzes images with vision models

```python
from ai.vision_client import VisionClient, build_checklist_from_profile

# Build checklist from profile
checklist = build_checklist_from_profile(profile_dict)

# Analyze image
client = VisionClient()
analysis = client.analyze_image("image.png", checklist, threshold=0.7)

# Check results
if analysis.passes_threshold:
    print(f"PASS - Score: {analysis.overall_score:.2f}")
else:
    print(f"FAIL - Issues: {analysis.issues}")
```

**ImageAnalysis** dataclass:
- `scores`: Dict of criterion → score
- `overall_score`: Average of all scores
- `passes_threshold`: True if passes
- `feedback`: AI-generated feedback
- `issues`: List of specific problems

## Benefits

1. **Automatic Quality Control**: No manual inspection needed
2. **Consistent Standards**: Same criteria applied to all images
3. **Objective Scoring**: Vision AI provides unbiased analysis
4. **Detailed Feedback**: Know exactly what's wrong
5. **Profile-Driven**: Checklist auto-generated from your JSON
6. **Cost-Effective**: Only validates when requested

## Example Workflow

```bash
# Generate with validation
uv run python main.py image generate "weathered surfboard" \
  --prompt-file surfing_ocean \
  --size 1024x1024 \
  --validate \
  --threshold 0.75 \
  --open

# If score < 0.75:
#   - See detailed feedback
#   - Adjust style profile
#   - Regenerate

# If score >= 0.75:
#   - Image automatically opens
#   - Ready to use!
```

## Future Enhancements

- **Auto-retry**: Regenerate failed images up to 3 times
- **Learning**: Track which settings produce best scores
- **Batch validation**: Analyze multiple images at once
- **Custom checklists**: Override auto-generated criteria
- **Score history**: Track quality trends over time
