"""
LLM Service for product information queries.
Integrates with open-source LLM (Mistral via Ollama) with guardrails and deterministic outputs.
"""
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..api.models import ProductInfoResponse
from config.settings import LLM_CONFIG
from config.settings import VLM_CONFIG

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """Response from LLM service."""
    answer: str
    confidence: float
    caveats: Optional[str] = None
    source: str = "llm"

class LLMService:
    """Service for generating product information using LLM."""
    
    def __init__(self, base_url: str = None, model_name: str = None):
        """Initialize LLM service."""
        self.base_url = base_url or LLM_CONFIG.get("base_url", "http://localhost:11434")
        self.model_name = model_name or LLM_CONFIG.get("model_name", "mistral")
        self.temperature = LLM_CONFIG.get("temperature", 0.3)
        self.max_tokens = LLM_CONFIG.get("max_tokens", 200)
        self.timeout = LLM_CONFIG.get("timeout", 30)
        
        # Initialize prompt library
        self.prompt_library = PromptLibrary()
        
    def generate_info_answer(self, product: str, question: str, db_attributes: Dict[str, Any] = None) -> ProductInfoResponse:
        """
        Generate information answer for a product question.
        
        Args:
            product: Product name
            question: User's question
            db_attributes: Optional database attributes (price, size, etc.)
            
        Returns:
            ProductInfoResponse with answer, confidence, and caveats
        """
        try:
            # Get appropriate prompt template
            prompt_template = self.prompt_library.get_prompt_template(question)
            
            # Build context with DB attributes if available
            context = self._build_context(product, db_attributes)
            
            # Generate prompt
            prompt = self._build_prompt(product, question, prompt_template, context)
            
            # Call LLM
            response = self._call_llm(prompt)
            
            # Parse and validate response
            parsed_response = self._parse_response(response)
            
            # Add caveats based on confidence and context
            caveats = self._determine_caveats(parsed_response, db_attributes)
            
            return ProductInfoResponse(
                normalized_product=product,
                answer=parsed_response["answer"],
                caveats=caveats,
                confidence=parsed_response["confidence"]
            )
            
        except Exception as e:
            logger.error(f"Error generating LLM answer: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return self._create_fallback_response(product, question)
    
    def _build_context(self, product: str, db_attributes: Dict[str, Any] = None) -> str:
        """Build context from database attributes."""
        if not db_attributes or not isinstance(db_attributes, dict):
            return ""
        
        context_parts = []
        
        if "price" in db_attributes:
            context_parts.append(f"Price: ${db_attributes['price']}")
        
        if "size" in db_attributes:
            context_parts.append(f"Size: {db_attributes['size']}")
        
        if "brand" in db_attributes:
            context_parts.append(f"Brand: {db_attributes['brand']}")
        
        if "category" in db_attributes:
            context_parts.append(f"Category: {db_attributes['category']}")
        
        return " | ".join(context_parts) if context_parts else ""
    
    def _build_prompt(self, product: str, question: str, template: str, context: str) -> str:
        """Build the complete prompt for the LLM."""
        return template.format(
            product=product or "product",
            question=question or "question",
            context=context or ""
        )
    
    def _call_llm(self, prompt: str) -> str:
        """Call the LLM service via Ollama."""
        try:
            # Call Ollama API
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                raise Exception(f"Ollama API error: {response.status_code}")
            
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama. Make sure Ollama is running.")
            raise Exception("Cannot connect to Ollama. Make sure Ollama is running.")
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    def _mock_llm_call(self, prompt: str) -> str:
        """Mock LLM call for testing and development."""
        # Extract product name safely
        product_name = "product"
        if "Product:" in prompt:
            try:
                product_name = prompt.split("Product:")[1].split("\n")[0].strip()
            except:
                product_name = "product"
        
        # Simulate LLM response based on prompt content
        if "ingredients" in prompt.lower():
            return json.dumps({
                "answer": f"Based on the product '{product_name}', here are the typical ingredients: milk, cream, natural flavors, and preservatives. Please check the product label for the complete ingredient list.",
                "confidence": 0.8
            })
        elif "nutrition" in prompt.lower() or "calories" in prompt.lower():
            return json.dumps({
                "answer": f"For '{product_name}', the nutritional information varies by brand and type. A typical serving contains 150-200 calories, 8-12g protein, and 2-5g fat. Check the nutrition label for specific details.",
                "confidence": 0.7
            })
        elif "price" in prompt.lower():
            return json.dumps({
                "answer": f"The price of '{product_name}' varies by store and location. Typical range is $2.99-$4.99. Check with store staff or use the store's price checker for current pricing.",
                "confidence": 0.6
            })
        elif "vegan" in prompt.lower() or "vegetarian" in prompt.lower():
            return json.dumps({
                "answer": f"'{product_name}' may or may not be vegan/vegetarian depending on the specific brand and ingredients. Check the product label for vegan/vegetarian certifications and ingredient lists.",
                "confidence": 0.7
            })
        elif "gluten" in prompt.lower():
            return json.dumps({
                "answer": f"'{product_name}' gluten-free status depends on the specific brand and manufacturing process. Look for 'gluten-free' labeling on the package or check with store staff for certified gluten-free options.",
                "confidence": 0.8
            })
        else:
            return json.dumps({
                "answer": f"'{product_name}' is a quality product with various options available. For specific information about ingredients, nutrition, or dietary restrictions, please check the product label or ask store staff for assistance.",
                "confidence": 0.6
            })
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate LLM response."""
        try:
            # Try to parse as JSON first
            try:
                parsed = json.loads(response)
                
                # Validate required fields
                if "answer" not in parsed:
                    raise ValueError("Missing 'answer' field in LLM response")
                
                if "confidence" not in parsed:
                    parsed["confidence"] = 0.5  # Default confidence
                
                # Ensure confidence is between 0 and 1
                parsed["confidence"] = max(0.0, min(1.0, float(parsed["confidence"])))
                
                return parsed
                
            except json.JSONDecodeError:
                # If not JSON, treat as plain text response
                # Extract answer and estimate confidence
                answer = response.strip()
                confidence = 0.7  # Default confidence for plain text
                
                # Adjust confidence based on response characteristics
                if len(answer) < 20:
                    confidence = 0.4
                elif "sorry" in answer.lower() or "unable" in answer.lower():
                    confidence = 0.3
                elif "check" in answer.lower() or "label" in answer.lower():
                    confidence = 0.8
                
                return {
                    "answer": answer,
                    "confidence": confidence
                }
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return {
                "answer": "I'm sorry, I encountered an error processing your request. Please try again or ask store staff for assistance.",
                "confidence": 0.2
            }
    
    def _determine_caveats(self, response: Dict[str, Any], db_attributes: Dict[str, Any] = None) -> Optional[str]:
        """Determine caveats based on response and context."""
        caveats = []
        
        # Low confidence caveat
        if response["confidence"] < 0.6:
            caveats.append("Low confidence in answer")
        
        # Missing DB attributes caveat
        if not db_attributes:
            caveats.append("Limited product information available")
        
        # Price caveat
        if "price" in response["answer"].lower() and (not db_attributes or "price" not in db_attributes):
            caveats.append("Price information may not be current")
        
        return "; ".join(caveats) if caveats else None
    
    def _create_fallback_response(self, product: str, question: str) -> ProductInfoResponse:
        """Create fallback response when LLM fails."""
        return ProductInfoResponse(
            normalized_product=product,
            answer=f"I'm sorry, I couldn't process your question about '{product}'. Please check the product label or ask store staff for assistance.",
            caveats="Service temporarily unavailable",
            confidence=0.1
        )
    
    def _enrich_with_llm(self, base_description: str) -> Optional[str]:
        """Use the text LLM to expand a base VLM caption into a detailed, structured analysis.

        Returns enriched markdown text or None on failure.
        """
        try:
            if not base_description or not base_description.strip():
                return None

            prompt = (
                "You are a helpful grocery assistant. Expand the following product description into a structured, consumer-friendly analysis.\n"
                "Write clear, concise bullet points and short paragraphs. If some details are not visible, infer carefully and mark them as 'likely' rather than asserting.\n\n"
                "Base description:\n" + base_description.strip() + "\n\n"
                "Produce the analysis with the following sections (include only relevant ones):\n"
                "1) Identification (name, product type)\n"
                "2) Brand/Manufacturer (if visible or likely)\n"
                "3) Packaging & Size (material, approximate size/volume if inferable)\n"
                "4) Key Ingredients / Materials (if food or consumable)\n"
                "5) Nutrition Highlights (if applicable)\n"
                "6) Uses / How to Use\n"
                "7) Storage Recommendations\n"
                "8) Certifications/Badges (organic, non-GMO, vegan, etc., if visible or likely)\n"
                "9) Safety / Allergen Warnings\n"
                "10) Shopper Tips (compare unit price, freshness checks, alternatives)\n\n"
                "Keep it under 250-300 words."
            )

            enriched = self._call_llm(prompt)
            if isinstance(enriched, str) and enriched.strip():
                return enriched.strip()
            return None
        except Exception as e:
            logger.warning(f"LLM enrichment failed; falling back to heuristic enhancement: {e}")
            return None

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of LLM service."""
        try:
            # Test Ollama connectivity
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_available = any(model.get("name", "").startswith(self.model_name) for model in models)
                
                if model_available:
                    return {
                        "status": "healthy",
                        "model": self.model_name,
                        "base_url": self.base_url,
                        "available_models": [model.get("name") for model in models]
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"Model '{self.model_name}' not found in Ollama",
                        "model": self.model_name,
                        "base_url": self.base_url,
                        "available_models": [model.get("name") for model in models]
                    }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"Ollama API error: {response.status_code}",
                    "model": self.model_name,
                    "base_url": self.base_url
                }
        except requests.exceptions.ConnectionError:
            return {
                "status": "unhealthy",
                "error": "Cannot connect to Ollama. Make sure Ollama is running.",
                "model": self.model_name,
                "base_url": self.base_url
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": self.model_name,
                "base_url": self.base_url
            }

    def _enhance_product_description(self, base_description: str, img) -> str:
        """
        Enhance basic image caption with detailed product analysis.
        
        Args:
            base_description: Basic caption from VLM
            img: PIL Image object for additional analysis
            
        Returns:
            Enhanced description with product details
        """
        try:
            import numpy as np
            
            # Get image properties for context
            img_width, img_height = img.size
            img_array = np.array(img)
            
            # Analyze image characteristics
            brightness = np.mean(img_array)
            is_clear = brightness > 50 and brightness < 200  # Good lighting conditions
            
            # Start with base description
            enhanced = f"**Product Analysis:** {base_description}"
            
            # Add detailed product guidance based on common grocery items
            product_keywords = {
                'bottle': {
                    'analysis': 'This appears to be a bottled product.',
                    'guidance': 'Check the label for: brand name, volume/size, ingredients list, nutritional information, expiration date, and recycling instructions. Look for any certifications (organic, non-GMO, etc.).'
                },
                'can': {
                    'analysis': 'This looks like a canned product.',
                    'guidance': 'Important details include: brand, net weight, ingredient list, nutritional facts panel, best-by date, and any dietary icons (gluten-free, vegan, etc.). Check for dents or damage.'
                },
                'box': {
                    'analysis': 'This appears to be a boxed/packaged product.',
                    'guidance': 'Key information to look for: brand name, product type, serving size, nutritional information, ingredients, preparation instructions, and storage requirements.'
                },
                'fruit': {
                    'analysis': 'This appears to be fresh produce - fruit.',
                    'guidance': 'Consider: ripeness level, origin/source, organic certification, nutritional benefits (vitamins, fiber), storage tips, and best consumption timeframe.'
                },
                'vegetable': {
                    'analysis': 'This looks like fresh produce - vegetables.',
                    'guidance': 'Check for: freshness indicators, organic labeling, nutritional value (vitamins, minerals), preparation methods, and proper storage conditions.'
                },
                'bread': {
                    'analysis': 'This appears to be a bread or bakery product.',
                    'guidance': 'Important details: ingredients (check for allergens like gluten, nuts), nutritional info, fiber content, preservatives, expiration date, and storage instructions.'
                },
                'dairy': {
                    'analysis': 'This looks like a dairy product.',
                    'guidance': 'Key considerations: fat content, protein levels, calcium content, pasteurization, expiration date, storage temperature requirements, and any lactose-free labeling.'
                }
            }
            
            # Try to match product category and add relevant guidance
            description_lower = base_description.lower()
            matched_category = None
            
            for category, info in product_keywords.items():
                if category in description_lower:
                    matched_category = category
                    break
            
            # Add specific product analysis
            if matched_category:
                enhanced += f"\n\n**Product Category:** {product_keywords[matched_category]['analysis']}"
                enhanced += f"\n\n**What to Look For:** {product_keywords[matched_category]['guidance']}"
            else:
                # Generic product guidance
                enhanced += "\n\n**General Product Analysis:** When examining any grocery product, check for brand name, ingredients, nutritional information, expiration dates, and any certifications or dietary indicators."
            
            # Add image quality context
            if is_clear:
                enhanced += "\n\n**Image Quality:** The image appears clear enough for detailed label reading."
            else:
                enhanced += "\n\n**Image Quality:** For better product identification, ensure good lighting and clear focus on product labels."
            
            # Add practical shopping advice
            enhanced += "\n\n**Shopping Tips:** Compare prices per unit, check expiration dates, read ingredient lists for allergens, and look for any promotional offers or coupons."
            
            # Add health and safety reminders
            enhanced += "\n\n**Health & Safety:** Always check for damage to packaging, verify expiration dates, and be aware of any personal allergies or dietary restrictions when selecting products."
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"Failed to enhance product description: {e}")
            return f"**Product Analysis:** {base_description}\n\n**Note:** For detailed product information, please check the product label for ingredients, nutritional facts, and usage instructions."

    def generate_vision_answer(self, image_bytes: bytes, filename: str = "image.jpg") -> ProductInfoResponse:
        """
        Send image bytes to the configured VLM (Moondream) endpoint and return a
        ProductInfoResponse containing a description/labels and confidence.

        The VLM endpoint is configurable via `VLM_CONFIG` in settings. The
        implementation attempts a multipart upload with key 'image' and expects
        a JSON response containing at least a text description.
        """
        # Check if VLM is enabled
        if not VLM_CONFIG.get("enabled", True):
            logger.info("VLM functionality is disabled in configuration")
            return ProductInfoResponse(
                normalized_product="image",
                answer="Vision analysis is currently disabled. Please enable VLM in configuration to use this feature.",
                caveats="Vision service disabled",
                confidence=0.0
            )
            
        # Try Hugging Face local pipeline first if configured
        provider = VLM_CONFIG.get("provider", "http")
        if provider == "huggingface" and VLM_CONFIG.get("enabled", True):
            hf_model = VLM_CONFIG.get("hf_model")
            try:
                from transformers import pipeline
                from PIL import Image
                import io as _io

                logger.info(f"[VLM] Provider=huggingface Model={hf_model}")

                # Create image object
                try:
                    img = Image.open(_io.BytesIO(image_bytes)).convert("RGB")
                except Exception as e:
                    logger.error(f"Failed to open image for HF pipeline: {e}")
                    raise

                # Create pipeline; check for different VLM models
                try:
                    # Import torch for device management
                    import torch
                    
                    # Get trust_remote_code setting from config
                    trust_remote_code = VLM_CONFIG.get("trust_remote_code", False)
                    
                    # Use Microsoft GiT or other standard VLM models
                    logger.info(f"[VLM] Loading model: {hf_model}")
                    
                    # Microsoft GiT and other standard models work with standard pipelines
                    if any(model_name in hf_model.lower() for model_name in ["git", "blip", "vit-gpt2"]):
                        logger.info("[VLM] Using standard image-to-text pipeline (GiT/BLIP/VIT-GPT2)")
                        
                        # Create standard image-to-text pipeline
                        captioner = pipeline(
                            task="image-to-text",
                            model=hf_model,
                            trust_remote_code=trust_remote_code,
                            device=-1,  # CPU
                            torch_dtype=torch.float32
                        )
                        
                        # Generate caption with detailed product analysis prompt
                        logger.info("[VLM] Generating caption and enriching with LLM (if available)...")
                        
                        # Create a comprehensive prompt for product identification and analysis
                        detailed_prompts = [
                            "Analyze this image and provide detailed information about any product or object being held. Include: product name, brand if visible, type/category, key features, nutritional highlights, potential uses, and any safety information.",
                            "Describe the product shown in this image. Focus on: what it is, brand/manufacturer, size/packaging, ingredients or materials visible, recommended uses, and any warnings or certifications you can see.",
                            "Examine this image for any food or consumer product. Provide comprehensive details including: product identification, nutritional information, usage instructions, storage recommendations, and any health or safety considerations.",
                            "Look at this product being held and tell me everything useful about it: name, brand, category, key benefits, how to use it, nutritional value if applicable, and any important consumer information."
                        ]
                        
                        # Try multiple prompts for best results
                        best_result = None
                        best_length = 0
                        
                        for i, prompt in enumerate(detailed_prompts):
                            try:
                                # For standard image-to-text models, we can't use custom prompts directly
                                # But we can analyze the generated caption and enhance it
                                caption_results = captioner(img, max_new_tokens=64)
                                
                                if isinstance(caption_results, list) and caption_results:
                                    result = caption_results[0]
                                    if isinstance(result, dict):
                                        base_description = result.get('generated_text', str(result))
                                    else:
                                        base_description = str(result)
                                else:
                                    base_description = str(caption_results)
                                
                                # First try to enrich with text LLM for detailed structure
                                enriched = self._enrich_with_llm(base_description)
                                if enriched:
                                    enhanced_description = enriched
                                else:
                                    # Fall back to heuristic enhancement
                                    enhanced_description = self._enhance_product_description(base_description, img)
                                
                                if len(enhanced_description) > best_length:
                                    best_result = enhanced_description
                                    best_length = len(enhanced_description)
                                    
                                break  # Use first successful result
                                
                            except Exception as prompt_error:
                                logger.warning(f"Prompt {i+1} failed: {prompt_error}")
                                continue
                        
                        if best_result:
                            results = {"answer": best_result.strip()}
                            logger.info(f"Enhanced product analysis: {results['answer'][:100]}...")
                        else:
                            # Fallback to basic caption
                            caption_results = captioner(img)
                            if isinstance(caption_results, list) and caption_results:
                                result = caption_results[0]
                                if isinstance(result, dict):
                                    description = result.get('generated_text', str(result))
                                else:
                                    description = str(result)
                            else:
                                description = str(caption_results)
                            
                            # Try to enrich even for basic caption
                            enriched = self._enrich_with_llm(description)
                            if enriched:
                                results = {"answer": enriched.strip()}
                            else:
                                results = {"answer": description.strip()}
                            logger.info(f"Basic caption: {results['answer']}")
                        
                    # LLaVA models require different pipeline
                    elif "llava" in hf_model.lower():
                        logger.info("[VLM] Using LLaVA image-text-to-text pipeline")
                        
                        # For LLaVA, we need to use a different approach
                        from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration
                        
                        processor = LlavaNextProcessor.from_pretrained(hf_model)
                        model = LlavaNextForConditionalGeneration.from_pretrained(
                            hf_model, 
                            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                            device_map="auto" if torch.cuda.is_available() else "cpu"
                        )
                        
                        # Prepare detailed product analysis conversation
                        conversation = [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "You are a grocery shopping assistant. Analyze this image and provide comprehensive information about any product or object being held. Include: 1) Product identification (name, brand, type), 2) Key features and specifications, 3) Nutritional highlights if applicable, 4) Recommended uses or preparation methods, 5) Storage instructions, 6) Any visible certifications or dietary information, 7) Safety considerations or allergen warnings. Be as detailed and helpful as possible for someone making a purchasing decision."},
                                    {"type": "image", "image": img},
                                ],
                            },
                        ]
                        
                        # Apply chat template and generate
                        prompt = processor.apply_chat_template(conversation, add_generation_prompt=True)
                        inputs = processor(images=img, text=prompt, return_tensors="pt")
                        
                        with torch.no_grad():
                            output = model.generate(**inputs, max_new_tokens=100)
                        
                        description = processor.decode(output[0], skip_special_tokens=True)
                        # Clean up the description by removing the prompt
                        if "You are a grocery shopping assistant" in description:
                            description = description.split("You are a grocery shopping assistant.")[-1].strip()
                        if "Analyze this image and provide comprehensive information" in description:
                            description = description.split("Be as detailed and helpful as possible for someone making a purchasing decision.")[-1].strip()
                        
                        # Try to enrich LLaVA response as well
                        enriched = self._enrich_with_llm(description)
                        results = {"answer": enriched if enriched else description}
                        logger.info(f"LLaVA generated: {results['answer']}")
                        
                    else:
                        # Fallback to basic image analysis
                        logger.warning(f"[VLM] Unknown model family for '{hf_model}', using basic analysis")
                        import numpy as np
                        
                        # Get basic image properties
                        img_width, img_height = img.size
                        img_array = np.array(img)
                        
                        # Analyze image for product characteristics
                        if len(img_array.shape) == 3:
                            avg_colors = np.mean(img_array, axis=(0, 1))
                            dominant_channel = np.argmax(avg_colors)
                            color_names = ["red", "green", "blue"]
                            dominant_color = color_names[dominant_channel]
                            
                            # Try to infer product type from image characteristics
                            aspect_ratio = img_width / img_height
                            
                            if aspect_ratio > 1.5:
                                shape_desc = "elongated/rectangular packaging"
                            elif aspect_ratio < 0.7:
                                shape_desc = "tall/vertical packaging" 
                            else:
                                shape_desc = "square/round packaging"
                            
                            description = f"""**Product Analysis from Image:**

**Visual Characteristics:** This is a {img_width}x{img_height} pixel image showing {shape_desc} with {dominant_color} as the dominant color.

**What to Look For:** When examining this product, check for:
• Brand name and product type clearly visible on packaging
• Ingredient list (usually on back or side panel)
• Nutritional information panel
• Net weight or volume
• Expiration or best-by date
• Any certification badges (Organic, Non-GMO, Fair Trade, etc.)
• Barcode for price checking
• Storage instructions
• Allergen warnings

**Shopping Tips:**
• Compare unit prices (price per ounce/gram) with similar products
• Check for any promotional stickers or coupons
• Verify the product meets your dietary needs
• Ensure packaging is intact and undamaged

**Health & Safety:** Always read labels carefully for allergens and check expiration dates before purchasing."""
                        else:
                            description = f"""**Product Analysis:** This appears to be a grayscale image of a product.

**General Guidance:** For any grocery product, important information to check includes brand name, ingredients, nutritional facts, expiration date, and storage instructions. Look for certifications and compare prices with similar items."""
                        
                        # Try to enrich the generic analysis
                        enriched = self._enrich_with_llm(description)
                        results = {"answer": enriched if enriched else description}
                        logger.info(f"Basic analysis: {results['answer']}")
                        
                except ImportError as e:
                    logger.warning(f"[VLM] Missing dependencies: {e}")
                    raise
                except Exception as e:
                    # If the model or pipeline is unavailable, raise to fall back
                    logger.warning(f"[VLM] Pipeline/model failed: {e}")
                    if "not found" in str(e).lower() or "does not exist" in str(e).lower():
                        logger.info("Consider checking the model name or using a different VLM provider")
                    raise

                # Parse results
                description = None
                confidence = 0.6
                
                if isinstance(results, dict):
                    description = results.get("answer") or results.get("generated_text") or results.get("caption")
                    if "score" in results:
                        try:
                            confidence = max(0.0, min(1.0, float(results.get("score"))))
                        except Exception:
                            pass
                elif isinstance(results, list) and results:
                    first = results[0]
                    if isinstance(first, dict):
                        description = first.get("generated_text") or first.get("caption") or first.get("answer") or str(first)
                        # Some pipelines include score
                        if "score" in first:
                            try:
                                confidence = max(0.0, min(1.0, float(first.get("score"))))
                            except Exception:
                                pass
                    else:
                        description = str(first)

                if not description:
                    description = "Hugging Face VLM returned no caption"

                return ProductInfoResponse(
                    normalized_product="image",
                    answer=description,
                    caveats=None,
                    confidence=confidence
                )
            except Exception as hf_exc:
                logger.warning(f"[VLM] Hugging Face path failed: {hf_exc}; trying HTTP fallback if configured")

        # Fallback: HTTP POST to configured VLM endpoint (existing behaviour)
        try:
            base = VLM_CONFIG.get("base_url")
            if not base:
                logger.info("No HTTP VLM base_url configured, skipping HTTP VLM fallback")
                raise Exception("No HTTP VLM endpoint configured")
                
            path = VLM_CONFIG.get("predict_path", "/v1/vision/predict")
            url = base.rstrip("/") + path

            headers = {}
            api_key = VLM_CONFIG.get("api_key")
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            files = {
                "image": (filename, image_bytes, "image/jpeg")
            }

            resp = requests.post(url, files=files, headers=headers, timeout=VLM_CONFIG.get("timeout", 30))
            if resp.status_code != 200:
                logger.error(f"VLM API error: {resp.status_code} - {resp.text}")
                raise Exception(f"VLM API error: {resp.status_code}")

            data = resp.json()

            # Defensive parsing
            description = None
            confidence = 0.6

            if isinstance(data, dict):
                description = data.get("description") or data.get("caption") or data.get("answer")
                if not description and "labels" in data:
                    labels = data.get("labels")
                    if isinstance(labels, list) and labels:
                        description = ", ".join([str(l) for l in labels[:5]])
                if "confidence" in data:
                    try:
                        confidence = max(0.0, min(1.0, float(data.get("confidence"))))
                    except Exception:
                        pass

            if not description:
                if isinstance(data, str):
                    description = data
                else:
                    description = "The VLM returned a response but no description was found."

            return ProductInfoResponse(
                normalized_product="image",
                answer=description,
                caveats=None,
                confidence=confidence
            )

        except Exception as e:
            logger.error(f"VLM vision request failed: {e}")
            return ProductInfoResponse(
                normalized_product="image",
                answer="I'm sorry — I couldn't analyze the image right now.",
                caveats="Vision service unavailable",
                confidence=0.1
            )

class PromptLibrary:
    """Library of prompt templates for different question types."""
    
    def __init__(self):
        """Initialize prompt library."""
        self.templates = {
            "ingredients": self._get_ingredients_template(),
            "nutrition": self._get_nutrition_template(),
            "price": self._get_price_template(),
            "dietary": self._get_dietary_template(),
            "general": self._get_general_template()
        }
    
    def get_prompt_template(self, question: str) -> str:
        """Get appropriate prompt template based on question."""
        if not question:
            return self.templates["general"]
            
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["ingredient", "ingredients"]):
            return self.templates["ingredients"]
        elif any(word in question_lower for word in ["nutrition", "calorie", "calories", "protein", "fat", "sugar"]):
            return self.templates["nutrition"]
        elif any(word in question_lower for word in ["price", "cost", "expensive", "cheap"]):
            return self.templates["price"]
        elif any(word in question_lower for word in ["vegan", "vegetarian", "gluten", "dairy", "halal", "kosher"]):
            return self.templates["dietary"]
        else:
            return self.templates["general"]
    
    def _get_ingredients_template(self) -> str:
        """Template for ingredients questions."""
        return """You are a helpful retail assistant. Answer ONLY product information questions. NEVER provide location information.

Product: {product}
Question: {question}
Context: {context}

Instructions:
- Only answer about ingredients, never locations
- Be factual and helpful
- If unsure, recommend checking the product label
- Return JSON with "answer" and "confidence" fields

Examples:
Q: "What are the ingredients in bread?"
A: {{"answer": "Bread typically contains flour, water, yeast, salt, and sometimes sugar or oil. Check the product label for the complete ingredient list.", "confidence": 0.8}}

Q: "What's in this milk?"
A: {{"answer": "Milk typically contains milk, vitamins A and D, and sometimes added ingredients. Check the product label for the complete ingredient list.", "confidence": 0.9}}

Answer:"""
    
    def _get_nutrition_template(self) -> str:
        """Template for nutrition questions."""
        return """You are a helpful retail assistant. Answer ONLY product information questions. NEVER provide location information.

Product: {product}
Question: {question}
Context: {context}

Instructions:
- Only answer about nutrition, never locations
- Be factual and helpful
- If unsure, recommend checking the nutrition label
- Return JSON with "answer" and "confidence" fields

Examples:
Q: "How many calories in yogurt?"
A: {{"answer": "Yogurt typically contains 100-150 calories per serving, depending on the brand and type. Check the nutrition label for specific calorie information.", "confidence": 0.8}}

Q: "What's the protein content?"
A: {{"answer": "Protein content varies by product type. Greek yogurt typically has 15-20g protein per serving, while regular yogurt has 8-12g. Check the nutrition label for specific amounts.", "confidence": 0.9}}

Answer:"""
    
    def _get_price_template(self) -> str:
        """Template for price questions."""
        return """You are a helpful retail assistant. Answer ONLY product information questions. NEVER provide location information.

Product: {product}
Question: {question}
Context: {context}

Instructions:
- Only answer about pricing, never locations
- Be helpful but note that prices vary
- Recommend checking current pricing
- Return JSON with "answer" and "confidence" fields

Examples:
Q: "What's the price of cheese?"
A: {{"answer": "Cheese prices vary by brand, type, and size. Typical range is $3-8. Check the current price at the store or use the price checker.", "confidence": 0.6}}

Q: "How much does milk cost?"
A: {{"answer": "Milk prices vary by brand and size. Typical range is $2-5. Check the current price at the store or use the price checker.", "confidence": 0.7}}

Answer:"""
    
    def _get_dietary_template(self) -> str:
        """Template for dietary questions."""
        return """You are a helpful retail assistant. Answer ONLY product information questions. NEVER provide location information.

Product: {product}
Question: {question}
Context: {context}

Instructions:
- Only answer about dietary information, never locations
- Be factual and helpful
- Recommend checking product labels for certifications
- Return JSON with "answer" and "confidence" fields

Examples:
Q: "Is this product vegan?"
A: {{"answer": "Vegan status depends on the specific brand and ingredients. Look for 'vegan' labeling or check the ingredient list for animal products.", "confidence": 0.7}}

Q: "Is this gluten-free?"
A: {{"answer": "Gluten-free status depends on the specific brand and manufacturing process. Look for 'gluten-free' labeling or check with store staff for certified options.", "confidence": 0.8}}

Answer:"""
    
    def _get_general_template(self) -> str:
        """Template for general questions."""
        return """You are a helpful retail assistant. Answer ONLY product information questions. NEVER provide location information.

Product: {product}
Question: {question}
Context: {context}

Instructions:
- Only answer about product information, never locations
- Be factual and helpful
- If unsure, recommend checking the product label or asking store staff
- Return JSON with "answer" and "confidence" fields

Examples:
Q: "Tell me about this product"
A: {{"answer": "This is a quality product with various options available. For specific information about ingredients, nutrition, or dietary restrictions, please check the product label or ask store staff for assistance.", "confidence": 0.6}}

Q: "What is this?"
A: {{"answer": "This is a quality product. For specific information about ingredients, nutrition, or dietary restrictions, please check the product label or ask store staff for assistance.", "confidence": 0.5}}

Answer:"""
