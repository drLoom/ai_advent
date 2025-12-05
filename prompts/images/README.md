# Image Generation Style Profiles

This directory contains brand/style profile JSON files used to guide image generation with consistent visual styling.

## Usage

Use a style profile with the `--prompt-file` parameter:

```bash
uv run python main.py image generate "your subject" --prompt-file corporate_minimal
```

List available profiles:

```bash
uv run python main.py image profiles
```

## Profile Structure

Each JSON profile includes:

### Required Fields
- **name**: Display name for the profile
- **description**: Short description of the style
- **prompt_template**: Template with `{subject}` placeholder that defines the full prompt

### Recommended Fields
- **color_palette**:
  - `primary`: Array of hex colors for main elements
  - `accent`: Array of hex colors for highlights
  - `background`: Array of hex colors for backgrounds
  - `description`: Text description of the palette

- **mood**: Array of mood keywords (e.g., "professional", "playful", "nostalgic")

- **visual_style**:
  - `dimension`: "flat", "3D", "2.5D", etc.
  - `texture`: Texture description
  - `detail_level`: "low", "medium", "high"
  - `composition`: Composition guidelines
  - `typography`: Font style preferences
  - `iconography`: Icon style guidelines

- **dos**: Array of things to include in the style
- **donts**: Array of things to avoid in the style
- **reference_styles**: Array of reference style descriptions

## Available Profiles

### corporate_minimal
Clean, professional corporate aesthetic with minimal design.
- Colors: Cool blues and grays
- Mood: Professional, trustworthy, modern
- Best for: Business content, presentations, corporate branding

### vibrant_creative
Bold, energetic creative style with rich colors and dynamic compositions.
- Colors: Multi-color vibrant palette
- Mood: Energetic, playful, inspiring
- Best for: Creative agencies, youth brands, entertainment

### retro_vintage
Nostalgic 70s-80s inspired aesthetic with warm tones and analog feel.
- Colors: Warm earthy tones
- Mood: Nostalgic, authentic, timeless
- Best for: Heritage brands, craft products, retro campaigns

### surfing_ocean
Dynamic ocean and surf culture aesthetic with vibrant water colors and energetic movement.
- Colors: Ocean blues and teals, sunset oranges and golds
- Mood: Energetic, adventurous, free-spirited, oceanic
- Best for: Surf brands, beach lifestyle, water sports, ocean conservation

## Creating Custom Profiles

1. Create a new JSON file in this directory (e.g., `my_style.json`)
2. Follow the structure of existing profiles
3. Define your brand colors, mood, and styling rules
4. Create a comprehensive `prompt_template` that incorporates all styling details

Example minimal profile:

```json
{
  "name": "My Style",
  "description": "Brief style description",
  "color_palette": {
    "primary": ["#000000"],
    "description": "Color scheme description"
  },
  "mood": ["modern", "clean"],
  "visual_style": {
    "dimension": "flat",
    "detail_level": "medium"
  },
  "dos": ["Use simple shapes"],
  "donts": ["Avoid clutter"],
  "prompt_template": "Create a {subject} with [your detailed style guidelines here]."
}
```

## Tips

- Be specific in your `prompt_template` - include colors (with hex codes), textures, composition rules
- Include both positive (dos) and negative (donts) guidelines for better control
- Test your profiles with different subjects to ensure consistency
- Keep mood keywords relevant to your brand identity
- Use the `prompt_template` to embed all critical styling information
