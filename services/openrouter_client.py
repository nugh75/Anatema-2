"""
Client per l'integrazione con OpenRouter
"""

import requests
import json
from typing import List, Dict, Optional


class OpenRouterClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://anatema.ai4educ.org",
            "X-Title": "Anatema - AI Annotation System"
        }
    
    def test_connection(self) -> bool:
        """Testa la validità dell'API key"""
        try:
            response = requests.get(
                f"{self.base_url}/auth/key",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def get_models(self) -> List[Dict]:
        """Recupera la lista dei modelli disponibili"""
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=15
            )
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            print(f"Errore nel recupero modelli OpenRouter: {e}")
            return []
    
    def list_models(self) -> List[Dict]:
        """Alias per get_models() per compatibilità"""
        return self.get_models()
    
    def get_free_models(self) -> List[Dict]:
        """Recupera solo i modelli gratuiti"""
        models = self.get_models()
        free_models = []
        
        for model in models:
            pricing = model.get('pricing', {})
            prompt_price = float(pricing.get('prompt', '0'))
            completion_price = float(pricing.get('completion', '0'))
            
            if prompt_price == 0 and completion_price == 0:
                free_models.append(model)
        
        return free_models
    
    def get_paid_models(self) -> List[Dict]:
        """Recupera i modelli a pagamento"""
        models = self.get_models()
        paid_models = []
        
        for model in models:
            pricing = model.get('pricing', {})
            prompt_price = float(pricing.get('prompt', '0'))
            completion_price = float(pricing.get('completion', '0'))
            
            if prompt_price > 0 or completion_price > 0:
                paid_models.append(model)
        
        return paid_models
    
    def generate_chat(self, model: str, messages: List[Dict], 
                     temperature: float = 0.7, max_tokens: int = 1000) -> Dict:
        """Genera una risposta usando il modello specificato"""
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_usage(self) -> Dict:
        """Recupera informazioni sull'utilizzo dell'API"""
        try:
            response = requests.get(
                f"{self.base_url}/auth/key",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


# Modelli gratuiti noti di OpenRouter (aggiornata periodicamente)
KNOWN_FREE_MODELS = [
    {
        "id": "microsoft/phi-3-mini-128k-instruct:free",
        "name": "Phi-3 Mini 128K Instruct (Free)",
        "description": "Microsoft's small but capable model with 128K context",
        "context_length": 128000,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "mistralai/mistral-7b-instruct:free",
        "name": "Mistral 7B Instruct (Free)",
        "description": "Mistral's 7B parameter instruction-tuned model",
        "context_length": 32768,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "huggingfaceh4/zephyr-7b-beta:free",
        "name": "Zephyr 7B Beta (Free)",
        "description": "A fine-tuned version of Mistral 7B",
        "context_length": 32768,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "openchat/openchat-7b:free",
        "name": "OpenChat 7B (Free)",
        "description": "An open-source language model fine-tuned with C-RLHF",
        "context_length": 8192,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "google/gemma-7b-it:free",
        "name": "Gemma 7B Instruct (Free)",
        "description": "Google's Gemma 7B instruction-tuned model",
        "context_length": 8192,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "qwen/qwen-3-4b:free",
        "name": "Qwen 3 4B (Free)",
        "description": "Dual thinking/non-thinking; instruction-following, agent workflows",
        "context_length": 128000,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "nvidia/llama-3.1-nemotron-ultra-253b:free",
        "name": "NVIDIA Llama 3.1 Nemotron Ultra 253B v1 (Free)",
        "description": "Advanced reasoning, RAG, tool-calling (needs explicit reasoning prompt)",
        "context_length": 128000,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "deepseek/deepseek-r1-distill-qwen-14b:free",
        "name": "DeepSeek R1 Distill Qwen 14B (Free)",
        "description": "Distilled from R1; strong math & code (AIME 69.7, MATH-500 93.9)",
        "context_length": 64000,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "meta-llama/llama-3.2-3b-instruct:free",
        "name": "Meta Llama 3.2 3B Instruct (Free)",
        "description": "8 languages; dialogue, reasoning, summarization",
        "context_length": 131000,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "meta-llama/llama-3.1-405b-instruct:free",
        "name": "Meta Llama 3.1 405B Instruct (Free)",
        "description": "High-quality dialogue; rivals GPT-4o & Claude 3.5",
        "context_length": 131000,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "deepseek/deepseek-v3-0324:free",
        "name": "DeepSeek V3 0324 (Free)",
        "description": "Latest V3; strong all-round performance",
        "context_length": 16000,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "deepseek/deepseek-r1-0528:free",
        "name": "DeepSeek R1 0528 (Free)",
        "description": "Open reasoning tokens; MIT-licensed update of R1",
        "context_length": 64000,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "deepseek/deepseek-r1:free",
        "name": "DeepSeek R1 (Free)",
        "description": "Performance on par with OpenAI o1; fully open source",
        "context_length": 64000,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "deepseek/deepseek-v3:free",
        "name": "DeepSeek V3 (Free)",
        "description": "Pre-trained on 15T tokens; rivals closed models",
        "context_length": 64000,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "cypher/cypher-alpha:free",
        "name": "Cypher Alpha (Free)",
        "description": "Long-context general model; provider logs prompts & outputs",
        "context_length": 1000000,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "tng/deepseek-r1t-chimera:free",
        "name": "TNG DeepSeek R1T Chimera (Free)",
        "description": "Combines R1 reasoning with V3 efficiency; MIT licence",
        "context_length": 64000,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "google/gemini-2.0-flash-experimental:free",
        "name": "Google Gemini 2.0 Flash Experimental (Free)",
        "description": "Very fast TTFT; multimodal, coding, complex instructions, function calling",
        "context_length": 1050000,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "qwen/qwq-32b:free",
        "name": "Qwen QwQ 32B (Free)",
        "description": "Medium-size reasoning model; competitive with DeepSeek R1",
        "context_length": 33000,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "mistralai/mistral-nemo:free",
        "name": "Mistral Nemo (Free)",
        "description": "Multilingual (11 langs), 128K context, function calling (Apache 2.0)",
        "context_length": 131000,
        "pricing": {"prompt": "0", "completion": "0"}
    }
]

# Modelli a pagamento popolari
POPULAR_PAID_MODELS = [
    {
        "id": "openai/gpt-4o",
        "name": "GPT-4o",
        "description": "OpenAI's latest multimodal flagship model",
        "context_length": 128000,
        "pricing": {"prompt": "0.000005", "completion": "0.000015"}
    },
    {
        "id": "openai/gpt-4o-mini",
        "name": "GPT-4o Mini", 
        "description": "OpenAI's affordable small model for fast, lightweight tasks",
        "context_length": 128000,
        "pricing": {"prompt": "0.00000015", "completion": "0.0000006"}
    },
    {
        "id": "anthropic/claude-3.5-sonnet",
        "name": "Claude 3.5 Sonnet",
        "description": "Anthropic's most intelligent model",
        "context_length": 200000,
        "pricing": {"prompt": "0.000003", "completion": "0.000015"}
    },
    {
        "id": "anthropic/claude-3-haiku",
        "name": "Claude 3 Haiku",
        "description": "Anthropic's fastest and most compact model",
        "context_length": 200000,
        "pricing": {"prompt": "0.00000025", "completion": "0.00000125"}
    },
    {
        "id": "google/gemini-pro-1.5",
        "name": "Gemini Pro 1.5",
        "description": "Google's latest Gemini model with 2M context",
        "context_length": 2000000,
        "pricing": {"prompt": "0.0000025", "completion": "0.0000075"}
    }
]
