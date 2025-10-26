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
