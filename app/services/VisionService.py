import os
import base64
import json
import httpx
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from app.schemas.Claim import DamageDetectionResult

load_dotenv()

class VisionService:
    """Service for analyzing car damage images using vision models."""

    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("Missing GROQ_API_KEY environment variable")
        
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def _encode_image_to_base64(self, image_bytes: bytes) -> str:
        """Encode image bytes to base64 string."""
        return base64.b64encode(image_bytes).decode('utf-8')

    def _analyze_damage_sync(
        self,
        image_bytes: bytes,
        accident_description: Optional[str] = None,
        damage_location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synchronous method to analyze car damage from image (used in threading).
        
        Args:
            image_bytes: Image file bytes
            accident_description: Description of the accident from claim form
            damage_location: Expected damage location (front, rear, left, right)
            
        Returns:
            Dictionary with damage analysis results
        """
        try:
            image_base64 = self._encode_image_to_base64(image_bytes)
            
            prompt_text = f"""Analyze this car image for damage. 
            
Expected damage location: {damage_location or "Not specified"}
Accident description: {accident_description or "Not provided"}

Provide a JSON response with:
- detected_damage: List of detected damage items with part name and severity (e.g., [{{"part": "front bumper", "severity": "moderate"}}])
- damage_locations: List of locations where damage is visible (front, rear, left, right)
- likely_damaged_parts: List of car parts that are likely damaged
- matches_description: Boolean indicating if detected damage matches the description
- confidence: Confidence score (0.0 to 1.0)

Return ONLY valid JSON, no markdown or code blocks."""
            
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert automotive damage assessor. Analyze car damage images and provide structured assessment. Return ONLY valid JSON."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt_text
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 4096
            }
            
            with httpx.Client(timeout=60.0) as client:
                response = client.post(self.api_url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"].strip()
                    
                    if content.startswith("```"):
                        content = content.split("```")[1]
                        if content.startswith("json"):
                            content = content[4:]
                        content = content.strip()
                    
                    data = json.loads(content)
                    
                    confidence = data.get("confidence", 0.0)
                    confidence = max(0.0, min(1.0, float(confidence) if confidence is not None else 0.0))
                    
                    return {
                        "success": True,
                        "data": data,
                        "confidence": confidence
                    }
                else:
                    raise Exception("No response from Groq API")
            
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"Groq Vision API error: {e.response.status_code} - {e.response.text}",
                "data": {
                    "detected_damage": [],
                    "damage_locations": [],
                    "likely_damaged_parts": [],
                    "matches_description": False,
                    "confidence": 0.0
                },
                "confidence": 0.0
            }
        except Exception as e:
            # Fallback response
            return {
                "success": False,
                "error": str(e),
                "data": {
                    "detected_damage": [],
                    "damage_locations": [],
                    "likely_damaged_parts": [],
                    "matches_description": False,
                    "confidence": 0.0
                },
                "confidence": 0.0
            }

    async def analyze_damage(
        self,
        image_bytes: bytes,
        accident_description: Optional[str] = None,
        damage_location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze car damage from image.
        
        Args:
            image_bytes: Image file bytes
            accident_description: Description of the accident from claim form
            damage_location: Expected damage location (front, rear, left, right)
            
        Returns:
            Dictionary with damage analysis results
        """
        # Run synchronous method in thread pool for async compatibility
        loop = None
        try:
            import asyncio
            loop = asyncio.get_event_loop()
        except:
            pass
        
        if loop:
            return await loop.run_in_executor(
                None,
                self._analyze_damage_sync,
                image_bytes,
                accident_description,
                damage_location
            )
        else:
            return self._analyze_damage_sync(image_bytes, accident_description, damage_location)

    async def analyze_multiple_images(
        self,
        images: List[Dict[str, Any]],  # List of {bytes, angle_description}
        accident_description: Optional[str] = None,
        expected_damage_location: Optional[str] = None
    ) -> DamageDetectionResult:
        """
        Analyze multiple car images from different angles using threading for parallel processing.
        
        Args:
            images: List of image dictionaries with 'bytes' and optional 'angle_description'
            accident_description: Description of the accident
            expected_damage_location: Expected location of damage
            
        Returns:
            DamageDetectionResult with aggregated analysis
        """
        all_damage = []
        all_locations = set()
        all_parts = set()
        confidences = []
        matches = []

        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=min(len(images), 5)) as executor:
            # Submit all tasks
            future_to_image = {
                executor.submit(
                    self._analyze_damage_sync,
                    img_data.get("bytes"),
                    accident_description,
                    img_data.get("angle_description") or expected_damage_location
                ): img_data
                for img_data in images
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_image):
                result = future.result()
                
                if result["success"]:
                    data = result["data"]
                    all_damage.extend(data.get("detected_damage", []))
                    all_locations.update(data.get("damage_locations", []))
                    all_parts.update(data.get("likely_damaged_parts", []))
                    confidences.append(result.get("confidence", 0.5))
                    matches.append(data.get("matches_description", False))

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        overall_match = any(matches) if matches else False

        return DamageDetectionResult(
            detected_damage=all_damage,
            damage_locations=list(all_locations),
            confidence=avg_confidence,
            matches_description=overall_match,
            likely_damaged_parts=list(all_parts)
        )

