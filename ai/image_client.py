"""Client for image generation via OpenRouter API."""
import os
import time
import base64
import logging
from typing import Optional, Dict
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

from models.models import (
    IMAGE_MODEL,
    IMAGE_DEFAULT_SIZE,
    IMAGE_DEFAULT_QUALITY,
    IMAGE_ASPECT_RATIOS
)

logger = logging.getLogger(__name__)


class ImageGenerationRequest:
    """Container for image generation request data."""

    def __init__(
        self,
        prompt: str,
        model: str,
        size: str,
        quality: str,
        seed: Optional[int] = None
    ):
        self.prompt = prompt
        self.model = model
        self.size = size
        self.quality = quality
        self.seed = seed
        self.timestamp = datetime.now()


class ImageGenerationResponse:
    """Container for image generation response data."""

    def __init__(
        self,
        image_data: str,  # Base64 encoded image data
        request: ImageGenerationRequest,
        latency_ms: float,
        cost_estimate: Optional[float] = None,
        raw_response: Optional[Dict] = None
    ):
        self.image_data = image_data
        self.request = request
        self.latency_ms = latency_ms
        self.cost_estimate = cost_estimate
        self.raw_response = raw_response or {}

    @property
    def image_url(self) -> str:
        """Return data URL for the image (for compatibility)."""
        return f"data:image/png;base64,{self.image_data[:50]}..."


class ImageGenerationLogger:
    """Logger for image generation requests."""

    def __init__(self, log_file: str = "image_generation.log"):
        self.log_file = log_file
        self._setup_file_logger()

    def _setup_file_logger(self):
        """Setup file logger for image generation."""
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)

        img_logger = logging.getLogger('image_generation')
        img_logger.setLevel(logging.INFO)
        img_logger.addHandler(file_handler)

        self.logger = img_logger

    def log_request(self, response: ImageGenerationResponse):
        """Log image generation request details."""
        request = response.request

        prompt_preview = request.prompt[:100] + "..." \
            if len(request.prompt) > 100 else request.prompt
        img_size = len(response.image_data) \
            if response.image_data else 0

        log_entry = {
            "timestamp": request.timestamp.isoformat(),
            "model": request.model,
            "prompt": prompt_preview,
            "size": request.size,
            "quality": request.quality,
            "seed": request.seed,
            "latency_ms": round(response.latency_ms, 2),
            "cost_estimate": response.cost_estimate,
            "image_size_bytes": img_size
        }

        self.logger.info(f"Image generation: {log_entry}")

        return log_entry


class ImageClient:
    """Client for image generation using OpenRouter API."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        log_requests: bool = True
    ):
        """
        Initialize the image generation client.

        Args:
            api_key: Optional API key. If not provided, loads from environment.
            log_requests: Whether to log requests to file.

        Raises:
            ValueError: If API key is not configured
        """
        load_dotenv()

        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key not configured. "
                "Set OPENROUTER_API_KEY environment variable."
            )

        self.log_requests = log_requests
        if log_requests:
            self.request_logger = ImageGenerationLogger()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authorization."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",
            "X-Title": "Image Generation CLI"
        }

    def _parse_size(self, size: str) -> tuple[int, int]:
        """Parse size string (e.g., '1024x1024') to width and height."""
        try:
            width, height = map(int, size.lower().split('x'))
            return width, height
        except (ValueError, AttributeError):
            raise ValueError(
                f"Invalid size format: {size}. "
                "Expected format: WIDTHxHEIGHT (e.g., '1024x1024')"
            )

    def _get_aspect_ratio(self, size: str) -> str:
        """Get aspect ratio for the given size."""
        # Check if we have a predefined mapping
        if size in IMAGE_ASPECT_RATIOS:
            return IMAGE_ASPECT_RATIOS[size]

        # Calculate aspect ratio from dimensions
        try:
            width, height = self._parse_size(size)
            from math import gcd
            divisor = gcd(width, height)
            ratio_w = width // divisor
            ratio_h = height // divisor
            return f"{ratio_w}:{ratio_h}"
        except (ValueError, ZeroDivisionError):
            return "1:1"  # Default to square

    def generate_image(
        self,
        prompt: str,
        model: str = IMAGE_MODEL,
        size: str = IMAGE_DEFAULT_SIZE,
        quality: str = IMAGE_DEFAULT_QUALITY,
        seed: Optional[int] = None,
        save_to: Optional[str] = None
    ) -> ImageGenerationResponse:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Text description of the image to generate
            model: Model to use for generation (must support image output)
            size: Image size in format "WIDTHxHEIGHT" (e.g., "1024x1024")
            quality: Image quality/detail level
            seed: Optional seed for reproducibility
            save_to: Optional file path to save the generated image

        Returns:
            ImageGenerationResponse containing image data and metadata

        Raises:
            requests.exceptions.RequestException: If API request fails
        """
        # Create request object for logging
        request = ImageGenerationRequest(
            prompt=prompt,
            model=model,
            size=size,
            quality=quality,
            seed=seed
        )

        # Build request payload for chat completions
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "modalities": ["image", "text"]  # Enable image generation
        }

        # Add image configuration (for Gemini models)
        aspect_ratio = self._get_aspect_ratio(size)
        if "gemini" in model.lower():
            payload["image_config"] = {
                "aspect_ratio": aspect_ratio
            }

        # Add seed if provided (model-dependent)
        if seed is not None:
            payload["seed"] = seed

        # Make API request with timing
        start_time = time.time()

        try:
            response = requests.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=120  # Image generation can take longer
            )
            response.raise_for_status()
            response_data = response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Image generation failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"Error details: {error_detail}")
                except (ValueError, AttributeError):
                    logger.error(f"Response text: {e.response.text[:500]}")
            raise

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        # Extract image data from response
        # OpenRouter returns images in the assistant message
        try:
            assistant_message = response_data["choices"][0]["message"]

            # Check if images are in the response
            if "images" in assistant_message and assistant_message["images"]:
                # Images can be strings or dicts with 'url' field
                image_item = assistant_message["images"][0]

                if isinstance(image_item, dict):
                    # Handle Gemini format: image_url is itself a dict
                    if "image_url" in image_item:
                        img_url_obj = image_item["image_url"]
                        if isinstance(img_url_obj, dict):
                            image_data_url = img_url_obj.get("url", "")
                        else:
                            image_data_url = img_url_obj
                    else:
                        # Try other possible fields
                        image_data_url = (
                            image_item.get("url") or
                            image_item.get("data") or
                            image_item.get("base64") or
                            ""
                        )
                else:
                    # Image is a string (data URL)
                    image_data_url = image_item

                # Extract base64 data from data URL
                if isinstance(image_data_url, str) and "," in image_data_url:
                    image_data = image_data_url.split(",", 1)[1]
                elif isinstance(image_data_url, str):
                    image_data = image_data_url
                else:
                    raise ValueError(
                        f"Unexpected image data format: {type(image_data_url)}"
                    )
            else:
                # Some models might include image in content
                raise ValueError(
                    "No images found in response. "
                    f"Model: {model}. "
                    "Ensure the model supports image output modality."
                )

        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected response format: {response_data}")
            raise ValueError(
                f"Could not extract image data from response: {e}"
            )

        # Estimate cost (if available in response)
        cost_estimate = None
        if "usage" in response_data:
            # OpenRouter may provide cost in usage metadata
            usage = response_data["usage"]
            if "cost" in usage:
                cost_estimate = usage["cost"]
            elif "total_cost" in usage:
                cost_estimate = usage["total_cost"]

        # Create response object
        result = ImageGenerationResponse(
            image_data=image_data,
            request=request,
            latency_ms=latency_ms,
            cost_estimate=cost_estimate,
            raw_response=response_data
        )

        # Log request if enabled
        if self.log_requests:
            self.request_logger.log_request(result)

        # Save image if requested
        if save_to:
            self._save_image(image_data, save_to)

        return result

    def _save_image(self, base64_data: str, file_path: str):
        """Decode and save base64 image data to file."""
        try:
            if not base64_data:
                raise ValueError("Empty base64 data")

            # Decode base64 data
            image_bytes = base64.b64decode(base64_data)

            if not image_bytes:
                raise ValueError("Decoded image is empty")

            # Create directory if it doesn't exist
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            # Save image
            with open(file_path, 'wb') as f:
                f.write(image_bytes)

            logger.info(
                f"Image saved to: {file_path} ({len(image_bytes)} bytes)"
            )

        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            logger.error(f"Base64 data preview: {base64_data[:100]}")
            raise
