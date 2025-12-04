"""Model constants for the application."""

# Image generation model (must support image output modality)
# IMAGE_MODEL = 'amazon/nova-2-lite-v1'
IMAGE_MODEL = 'google/gemini-2.5-flash-image-preview'

# Default parameters for image generation
IMAGE_DEFAULT_SIZE = "1024x1024"  # Maps to aspect ratios
IMAGE_DEFAULT_QUALITY = "standard"
IMAGE_DEFAULT_STEPS = 20

# Image aspect ratio mappings (for Gemini models)
IMAGE_ASPECT_RATIOS = {
    "1024x1024": "1:1",
    "1024x768": "4:3",
    "768x1024": "3:4",
    "1920x1080": "16:9",
    "1080x1920": "9:16",
    "512x512": "1:1",
    "768x768": "1:1",
}
