"""Vision model client for analyzing screenshots and visual content."""

import base64
import logging
from pathlib import Path
from typing import Optional, Union, Any
from openai import AsyncOpenAI, OpenAIError
from PIL import Image
import io

from monitorlab.config.settings import get_settings

logger = logging.getLogger(__name__)


class VisionClient:
    """Client for interacting with vision models via LM Studio."""

    def __init__(self, settings: Optional[Any] = None):
        """Initialize vision client.

        Args:
            settings: Optional settings object. If None, uses get_settings().
        """
        self.settings = settings or get_settings()
        self.client = AsyncOpenAI(
            base_url=self.settings.vision_api_base,
            api_key=self.settings.llm_api_key,  # Same key for local setup
        )
        self.model = self.settings.vision_model

    def _encode_image(self, image_path: Union[str, Path, bytes]) -> str:
        """Encode image to base64 string.

        Args:
            image_path: Path to image file or bytes

        Returns:
            Base64 encoded image string
        """
        if isinstance(image_path, bytes):
            return base64.b64encode(image_path).decode("utf-8")

        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def _resize_image_if_needed(
        self, image_path: Union[str, Path], max_dimension: int = 1920
    ) -> bytes:
        """Resize image if it exceeds max dimension to save memory.

        Args:
            image_path: Path to image
            max_dimension: Maximum width or height

        Returns:
            Image bytes (JPEG format)
        """
        img = Image.open(image_path)

        # Check if resize is needed
        if max(img.size) > max_dimension:
            # Calculate new size maintaining aspect ratio
            ratio = max_dimension / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Convert to RGB if necessary
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Save to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG", quality=self.settings.screenshot_quality)
        return img_bytes.getvalue()

    async def analyze_image(
        self,
        image_path: Union[str, Path, bytes],
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        resize: bool = True,
    ) -> str:
        """Analyze an image with a vision model.

        Args:
            image_path: Path to image file or image bytes
            prompt: Question or task about the image
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            resize: Whether to resize large images

        Returns:
            Analysis result as text
        """
        # Prepare image
        if isinstance(image_path, bytes):
            image_data = image_path
        elif resize:
            image_data = self._resize_image_if_needed(image_path)
        else:
            with open(image_path, "rb") as f:
                image_data = f.read()

        base64_image = base64.b64encode(image_data).decode("utf-8")

        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.settings.vision_temperature,
                max_tokens=max_tokens or self.settings.vision_max_tokens,
            )
            return response.choices[0].message.content or ""

        except OpenAIError as e:
            logger.error(f"Vision model error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during vision analysis: {e}")
            raise

    async def validate_rendering(
        self,
        screenshot_path: Union[str, Path],
        expected_elements: list[str],
        additional_checks: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Validate that a webpage is rendered correctly.

        Args:
            screenshot_path: Path to screenshot
            expected_elements: List of elements that should be visible
            additional_checks: Optional additional validation checks

        Returns:
            Dictionary with validation results
        """
        checks = expected_elements.copy()
        if additional_checks:
            checks.extend(additional_checks)

        prompt = f"""Analyze this webpage screenshot and verify the following:

Expected elements:
{chr(10).join(f"- {elem}" for elem in expected_elements)}

{f'''Additional checks:
{chr(10).join(f"- {check}" for check in additional_checks)}''' if additional_checks else ''}

For each item, respond with whether it is present and correctly rendered.
Respond in JSON format with this structure:
{{
    "overall_valid": true/false,
    "checks": [
        {{"item": "element name", "present": true/false, "notes": "any issues or observations"}},
        ...
    ],
    "overall_notes": "general observations about the page"
}}
"""

        system_prompt = """You are a QA expert analyzing webpage screenshots.
Be thorough and detailed in your analysis. Check for visual issues like:
- Missing elements
- Layout problems
- CSS rendering issues
- Broken images
- Incorrect styling or colors
- Text readability issues"""

        response = await self.analyze_image(
            screenshot_path, prompt, system_prompt=system_prompt, temperature=0.2
        )

        # Parse JSON response
        import json

        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            else:
                return json.loads(response)
        except json.JSONDecodeError:
            logger.warning(f"Could not parse JSON from vision response: {response}")
            # Return a basic structure
            return {
                "overall_valid": False,
                "checks": [],
                "overall_notes": response,
                "error": "Could not parse structured response",
            }

    async def compare_screenshots(
        self, screenshot1: Union[str, Path], screenshot2: Union[str, Path]
    ) -> dict[str, Any]:
        """Compare two screenshots to detect visual differences.

        Args:
            screenshot1: Path to first screenshot
            screenshot2: Path to second screenshot

        Returns:
            Dictionary with comparison results
        """
        # Note: This is a simplified version. For production, you might want
        # to use both vision model analysis and pixel-based comparison.

        prompt = """Compare these two webpage screenshots and identify any visual differences.
Look for:
- Layout changes
- Content differences
- Styling changes
- Missing or added elements
- Color or font changes

Respond in JSON format:
{
    "identical": true/false,
    "differences": ["list of differences found"],
    "severity": "none/minor/moderate/major"
}
"""

        # For now, analyze them separately
        # In a real implementation, you'd want to send both images if the model supports it
        # or use a pixel-based comparison library

        analysis1 = await self.analyze_image(
            screenshot1,
            "Describe the key visual elements and layout of this webpage in detail.",
        )
        analysis2 = await self.analyze_image(
            screenshot2,
            "Describe the key visual elements and layout of this webpage in detail.",
        )

        # Use LLM to compare the descriptions
        comparison_prompt = f"""Compare these two webpage descriptions and identify differences:

Screenshot 1:
{analysis1}

Screenshot 2:
{analysis2}

{prompt}"""

        # You would need to import LLMClient here or pass it as a dependency
        # For now, return a basic structure
        return {
            "identical": analysis1 == analysis2,
            "differences": [],
            "severity": "none" if analysis1 == analysis2 else "unknown",
            "analysis1": analysis1,
            "analysis2": analysis2,
        }

    async def health_check(self) -> bool:
        """Check if the vision service is available.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            # Create a simple test image
            img = Image.new("RGB", (100, 100), color="red")
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="JPEG")
            img_bytes = img_bytes.getvalue()

            response = await self.analyze_image(
                img_bytes, "What color is this image?", resize=False
            )
            return len(response) > 0
        except Exception as e:
            logger.error(f"Vision health check failed: {e}")
            return False
