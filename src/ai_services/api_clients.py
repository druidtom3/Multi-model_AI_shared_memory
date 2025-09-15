"""
AI API客戶端 - 統一的多AI供應商調用介面

基於 Linus 工程哲學設計：
- 統一的API調用介面（好品味原則）
- 簡潔的錯誤處理和重試機制
- 實用的回應格式標準化
"""

import os
import json
import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class AIAPIClients:
    """
    統一的AI API客戶端
    
    職責：
    1. 各家AI API的統一調用介面
    2. API金鑰管理和認證
    3. 請求/回應格式標準化
    4. API錯誤處理和重試
    """
    
    def __init__(self):
        # API金鑰從環境變數載入
        self.api_keys = {
            'openai': os.getenv('OPENAI_API_KEY'),
            'anthropic': os.getenv('ANTHROPIC_API_KEY'),
            'xai': os.getenv('XAI_API_KEY'),
            'google': os.getenv('GOOGLE_AI_KEY')
        }
        
        # API端點配置
        self.api_endpoints = {
            'openai': 'https://api.openai.com/v1/chat/completions',
            'anthropic': 'https://api.anthropic.com/v1/messages',
            'xai': 'https://api.x.ai/v1/chat/completions',
            'google': 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
        }
        
        # 請求配置
        self.default_timeout = 60  # 60秒超時
        self.max_retries = 3
        self.retry_delay = 1.0  # 秒
        
        # 會話管理
        self.session = None
        
        logger.info("AIAPIClients initialized")
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.default_timeout))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def _ensure_session(self):
        """確保會話存在"""
        if self.session is None:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.default_timeout))
    
    async def call_openai(self, model: str, messages: List[Dict[str, str]], 
                         temperature: float = 0.7, **kwargs) -> str:
        """調用OpenAI API"""
        if not self.api_keys['openai']:
            raise Exception("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        
        headers = {
            'Authorization': f"Bearer {self.api_keys['openai']}",
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': model,
            'messages': messages,
            'temperature': temperature,
            **kwargs
        }
        
        return await self._make_request('openai', headers, payload)
    
    async def call_anthropic(self, model: str, messages: List[Dict[str, str]], 
                            temperature: float = 0.7, **kwargs) -> str:
        """調用Anthropic API"""
        if not self.api_keys['anthropic']:
            raise Exception("Anthropic API key not found. Please set ANTHROPIC_API_KEY environment variable.")
        
        # Anthropic API格式轉換
        system_message = ""
        user_messages = []
        
        for msg in messages:
            if msg['role'] == 'system':
                system_message = msg['content']
            else:
                user_messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
        
        headers = {
            'x-api-key': self.api_keys['anthropic'],
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        payload = {
            'model': model,
            'max_tokens': kwargs.get('max_tokens', 4000),
            'temperature': temperature,
            'messages': user_messages
        }
        
        if system_message:
            payload['system'] = system_message
        
        return await self._make_request('anthropic', headers, payload)
    
    async def call_xai(self, model: str, messages: List[Dict[str, str]], 
                      temperature: float = 0.7, **kwargs) -> str:
        """調用xAI API"""
        if not self.api_keys['xai']:
            raise Exception("xAI API key not found. Please set XAI_API_KEY environment variable.")
        
        headers = {
            'Authorization': f"Bearer {self.api_keys['xai']}",
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': model,
            'messages': messages,
            'temperature': temperature,
            **kwargs
        }
        
        return await self._make_request('xai', headers, payload)
    
    async def call_google(self, model: str, messages: List[Dict[str, str]], 
                         temperature: float = 0.7, **kwargs) -> str:
        """調用Google AI API"""
        if not self.api_keys['google']:
            raise Exception("Google AI API key not found. Please set GOOGLE_AI_KEY environment variable.")
        
        # Google AI API格式轉換
        contents = []
        for msg in messages:
            if msg['role'] == 'system':
                # Google AI的系統訊息需要特殊處理
                contents.append({
                    'role': 'user',
                    'parts': [{'text': f"[System] {msg['content']}"}]
                })
            elif msg['role'] == 'user':
                contents.append({
                    'role': 'user',
                    'parts': [{'text': msg['content']}]
                })
            elif msg['role'] == 'assistant':
                contents.append({
                    'role': 'model',
                    'parts': [{'text': msg['content']}]
                })
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            'contents': contents,
            'generationConfig': {
                'temperature': temperature,
                'maxOutputTokens': kwargs.get('max_tokens', 4000)
            }
        }
        
        # Google API需要在URL中包含API密鑰
        api_url = self.api_endpoints['google'].format(model=model)
        api_url += f"?key={self.api_keys['google']}"
        
        return await self._make_request('google', headers, payload, custom_url=api_url)
    
    async def _make_request(self, provider: str, headers: Dict[str, str], 
                           payload: Dict[str, Any], custom_url: str = None) -> str:
        """統一的API請求處理"""
        await self._ensure_session()
        
        url = custom_url or self.api_endpoints[provider]
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Making request to {provider} (attempt {attempt + 1})")
                
                async with self.session.post(url, headers=headers, json=payload) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        response_data = json.loads(response_text)
                        return self.standardize_response(provider, response_data)
                    
                    elif response.status == 429:  # Rate limit
                        if attempt < self.max_retries - 1:
                            wait_time = self.retry_delay * (2 ** attempt)  # 指數退避
                            logger.warning(f"Rate limited by {provider}, waiting {wait_time} seconds")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise Exception(f"Rate limited by {provider} after {self.max_retries} attempts")
                    
                    elif response.status >= 400:
                        error_info = self._parse_error_response(response_text, provider)
                        raise Exception(f"{provider} API error: {error_info}")
                    
                    else:
                        raise Exception(f"Unexpected response status {response.status} from {provider}")
            
            except asyncio.TimeoutError:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Timeout calling {provider} API, retrying...")
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    raise Exception(f"Timeout calling {provider} API after {self.max_retries} attempts")
            
            except Exception as e:
                if attempt < self.max_retries - 1 and "rate limit" not in str(e).lower():
                    logger.warning(f"Error calling {provider} API: {str(e)}, retrying...")
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    raise
        
        raise Exception(f"Failed to call {provider} API after {self.max_retries} attempts")
    
    def standardize_response(self, provider: str, raw_response: Dict[str, Any]) -> str:
        """標準化不同供應商的回應格式"""
        try:
            if provider == 'openai' or provider == 'xai':
                return raw_response['choices'][0]['message']['content']
            
            elif provider == 'anthropic':
                content = raw_response['content']
                if isinstance(content, list) and len(content) > 0:
                    return content[0]['text']
                else:
                    return str(content)
            
            elif provider == 'google':
                candidates = raw_response.get('candidates', [])
                if candidates and len(candidates) > 0:
                    content = candidates[0].get('content', {})
                    parts = content.get('parts', [])
                    if parts and len(parts) > 0:
                        return parts[0].get('text', '')
                
                return "No response content"
            
            else:
                # 通用降級處理
                logger.warning(f"Unknown provider {provider}, attempting generic extraction")
                if 'content' in raw_response:
                    return str(raw_response['content'])
                elif 'text' in raw_response:
                    return str(raw_response['text'])
                elif 'message' in raw_response:
                    return str(raw_response['message'])
                else:
                    return str(raw_response)
                    
        except Exception as e:
            logger.error(f"Error standardizing response from {provider}: {str(e)}")
            # 最後的降級措施
            return str(raw_response)
    
    def _parse_error_response(self, response_text: str, provider: str) -> str:
        """解析錯誤回應"""
        try:
            error_data = json.loads(response_text)
            
            if provider == 'openai' or provider == 'xai':
                return error_data.get('error', {}).get('message', 'Unknown error')
            
            elif provider == 'anthropic':
                return error_data.get('error', {}).get('message', 'Unknown error')
            
            elif provider == 'google':
                error = error_data.get('error', {})
                return error.get('message', error.get('status', 'Unknown error'))
            
            else:
                return str(error_data)
                
        except json.JSONDecodeError:
            return response_text[:200]  # 返回前200個字符
    
    def check_api_keys(self) -> Dict[str, bool]:
        """檢查API金鑰是否配置"""
        return {provider: key is not None and key.strip() != '' 
                for provider, key in self.api_keys.items()}
    
    def get_available_providers(self) -> List[str]:
        """獲取可用的AI供應商列表"""
        availability = self.check_api_keys()
        return [provider for provider, available in availability.items() if available]
    
    async def test_connection(self, provider: str) -> Dict[str, Any]:
        """測試與指定供應商的連接"""
        if not self.api_keys.get(provider):
            return {
                'provider': provider,
                'status': 'error',
                'error': 'API key not found'
            }
        
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello!"}
        ]
        
        try:
            start_time = time.time()
            
            if provider == 'openai':
                response = await self.call_openai('gpt-3.5-turbo', test_messages)
            elif provider == 'anthropic':
                response = await self.call_anthropic('claude-3-haiku-20240307', test_messages)
            elif provider == 'xai':
                response = await self.call_xai('grok-beta', test_messages)
            elif provider == 'google':
                response = await self.call_google('gemini-1.5-flash', test_messages)
            else:
                return {
                    'provider': provider,
                    'status': 'error',
                    'error': 'Unsupported provider'
                }
            
            end_time = time.time()
            
            return {
                'provider': provider,
                'status': 'success',
                'response_time': round(end_time - start_time, 2),
                'test_response': response[:100] + '...' if len(response) > 100 else response
            }
            
        except Exception as e:
            return {
                'provider': provider,
                'status': 'error',
                'error': str(e)
            }
    
    async def close(self):
        """關閉會話"""
        if self.session:
            await self.session.close()
            self.session = None


# 同步版本的包裝器
class SyncAIAPIClients:
    """同步版本的API客戶端包裝器"""
    
    def __init__(self):
        self.async_client = AIAPIClients()
    
    def call_openai(self, model: str, messages: List[Dict[str, str]], 
                   temperature: float = 0.7, **kwargs) -> str:
        return asyncio.run(self.async_client.call_openai(model, messages, temperature, **kwargs))
    
    def call_anthropic(self, model: str, messages: List[Dict[str, str]], 
                      temperature: float = 0.7, **kwargs) -> str:
        return asyncio.run(self.async_client.call_anthropic(model, messages, temperature, **kwargs))
    
    def call_xai(self, model: str, messages: List[Dict[str, str]], 
                temperature: float = 0.7, **kwargs) -> str:
        return asyncio.run(self.async_client.call_xai(model, messages, temperature, **kwargs))
    
    def call_google(self, model: str, messages: List[Dict[str, str]], 
                   temperature: float = 0.7, **kwargs) -> str:
        return asyncio.run(self.async_client.call_google(model, messages, temperature, **kwargs))
    
    def check_api_keys(self) -> Dict[str, bool]:
        return self.async_client.check_api_keys()
    
    def get_available_providers(self) -> List[str]:
        return self.async_client.get_available_providers()
    
    def test_connection(self, provider: str) -> Dict[str, Any]:
        return asyncio.run(self.async_client.test_connection(provider))


if __name__ == "__main__":
    # 簡單測試
    import asyncio
    
    async def test():
        client = AIAPIClients()
        
        # 檢查API金鑰
        keys_status = client.check_api_keys()
        print(f"API keys status: {keys_status}")
        
        available = client.get_available_providers()
        print(f"Available providers: {available}")
        
        # 測試連接（如果有可用的API金鑰）
        if available:
            test_result = await client.test_connection(available[0])
            print(f"Connection test: {json.dumps(test_result, indent=2, ensure_ascii=False)}")
        
        await client.close()
    
    # 運行測試
    # asyncio.run(test())