"""Test script for image generation module."""
import os
from ai.image_client import (
    ImageClient,
    ImageGenerationRequest,
    ImageGenerationResponse
)


def test_request_object():
    """Test ImageGenerationRequest creation."""
    request = ImageGenerationRequest(
        prompt="test prompt",
        model="amazon/nova-2-lite-v1",
        size="1024x1024",
        quality="standard",
        seed=42
    )

    assert request.prompt == "test prompt"
    assert request.model == "amazon/nova-2-lite-v1"
    assert request.size == "1024x1024"
    assert request.quality == "standard"
    assert request.seed == 42
    print("✓ ImageGenerationRequest works correctly")


def test_response_object():
    """Test ImageGenerationResponse creation."""
    request = ImageGenerationRequest(
        prompt="test",
        model="test-model",
        size="512x512",
        quality="standard"
    )

    response = ImageGenerationResponse(
        image_data="base64encodeddata",  # Changed from image_url
        request=request,
        latency_ms=1234.56,
        cost_estimate=0.01
    )

    assert response.image_data == "base64encodeddata"
    assert response.latency_ms == 1234.56
    assert response.cost_estimate == 0.01
    assert response.request == request
    print("✓ ImageGenerationResponse works correctly")


def test_size_parsing():
    """Test size string parsing."""
    has_key = os.getenv("OPENROUTER_API_KEY")
    client = ImageClient(log_requests=False) if has_key else None

    if client:
        width, height = client._parse_size("1024x1024")
        assert width == 1024
        assert height == 1024

        width, height = client._parse_size("512x768")
        assert width == 512
        assert height == 768

        try:
            client._parse_size("invalid")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

        print("✓ Size parsing works correctly")
    else:
        print("⊘ Size parsing test skipped (no API key)")


def test_client_initialization():
    """Test ImageClient initialization."""
    # Test with API key in environment
    if os.getenv("OPENROUTER_API_KEY"):
        client = ImageClient(log_requests=False)
        assert client.api_key is not None
        print("✓ ImageClient initialization works correctly")
    else:
        print("⊘ ImageClient test skipped (no API key)")


def test_models_config():
    """Test models configuration."""
    from models.models import (
        IMAGE_MODEL,
        IMAGE_DEFAULT_SIZE,
        IMAGE_DEFAULT_QUALITY
    )

    assert IMAGE_MODEL is not None
    assert IMAGE_DEFAULT_SIZE is not None
    assert IMAGE_DEFAULT_QUALITY is not None

    print("✓ Models config loaded:")
    print(f"  - Model: {IMAGE_MODEL}")
    print(f"  - Size: {IMAGE_DEFAULT_SIZE}")
    print(f"  - Quality: {IMAGE_DEFAULT_QUALITY}")


def main():
    """Run all tests."""
    print("="*60)
    print("Testing Image Generation Module")
    print("="*60)
    print()

    test_request_object()
    test_response_object()
    test_size_parsing()
    test_client_initialization()
    test_models_config()

    print()
    print("="*60)
    print("All tests completed!")
    print("="*60)
    print()
    print("Note: Full API integration testing requires OPENROUTER_API_KEY")
    print("      in your environment variables.")


if __name__ == "__main__":
    main()
