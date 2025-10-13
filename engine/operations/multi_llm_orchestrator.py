"""
Multi-LLM Orchestrator for Parallel Analysis and Debugging

This module orchestrates multiple LLM providers to analyze bugs and propose fixes
in parallel. It supports GPT-4, Claude 3.5, Qwen Coder, and DeepSeek R1 with
configurable weights and timeouts.

Architecture:
- Parallel API calls to multiple LLM providers
- Provider-specific prompt optimization
- Error handling and fallback strategies
- Response parsing and confidence scoring
- Integration with secrets management

Usage:
    orchestrator = MultiLLMOrchestrator()
    responses = await orchestrator.analyze_bug(
        bug_description="Error in file_editor.py",
        code_context={"file_editor.py": "..."},
        test_failures=["test_edit_file failed"]
    )
"""

import asyncio
import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import aiohttp
from pathlib import Path

# Debug flag
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""
    GPT4 = "gpt4"
    CLAUDE = "claude"
    QWEN = "qwen"
    DEEPSEEK = "deepseek"


@dataclass
class LLMResponse:
    """Response from an LLM provider"""
    provider: LLMProvider
    analysis: str
    proposed_fix: str
    confidence: float  # 0.0 to 1.0
    reasoning: str
    error: Optional[str] = None
    response_time: float = 0.0


@dataclass
class LLMConfig:
    """Configuration for an LLM provider"""
    provider: LLMProvider
    model: str
    weight: float
    api_key_file: str
    api_endpoint: str
    timeout: int = 60
    max_tokens: int = 4000


class MultiLLMOrchestrator:
    """Orchestrates multiple LLM providers for parallel bug analysis"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the orchestrator
        
        Args:
            config_path: Path to multi_llm_debug.yaml config file
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), '../../config/services/multi_llm_debug.yaml'
        )
        self.providers_config = self._load_config()
        self.api_keys = self._load_api_keys()
        
        if DEBUG:
            logger.debug(f"🔍 MultiLLMOrchestrator initialized with {len(self.providers_config)} providers")
    
    def _load_config(self) -> Dict[LLMProvider, LLMConfig]:
        """Load LLM provider configurations"""
        # Default configuration
        default_config = {
            LLMProvider.GPT4: LLMConfig(
                provider=LLMProvider.GPT4,
                model="gpt-4-turbo-preview",
                weight=1.0,
                api_key_file="secrets/keys/openai.key",
                api_endpoint="https://api.openai.com/v1/chat/completions",
                timeout=60,
                max_tokens=4000
            ),
            LLMProvider.CLAUDE: LLMConfig(
                provider=LLMProvider.CLAUDE,
                model="claude-3-5-sonnet-20241022",
                weight=0.9,
                api_key_file="secrets/keys/anthropic.key",
                api_endpoint="https://api.anthropic.com/v1/messages",
                timeout=60,
                max_tokens=4000
            ),
            LLMProvider.QWEN: LLMConfig(
                provider=LLMProvider.QWEN,
                model="qwen/qwen-2.5-coder-32b-instruct",
                weight=0.7,
                api_key_file="secrets/keys/openrouter.key",
                api_endpoint="https://openrouter.ai/api/v1/chat/completions",
                timeout=45,
                max_tokens=3000
            ),
            LLMProvider.DEEPSEEK: LLMConfig(
                provider=LLMProvider.DEEPSEEK,
                model="deepseek/deepseek-r1",
                weight=0.8,
                api_key_file="secrets/keys/openrouter.key",
                api_endpoint="https://openrouter.ai/api/v1/chat/completions",
                timeout=45,
                max_tokens=3000
            )
        }
        
        # Load from YAML if exists
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                import yaml
                with open(config_file, 'r') as f:
                    yaml_config = yaml.safe_load(f)
                
                if DEBUG:
                    logger.debug(f"✅ Loaded config from {config_file}")
                
                # Override defaults with YAML config
                for provider_name, provider_config in yaml_config.get('providers', {}).items():
                    try:
                        provider_enum = LLMProvider(provider_name)
                        if provider_enum in default_config:
                            config = default_config[provider_enum]
                            # Update with YAML values
                            for key, value in provider_config.items():
                                if hasattr(config, key):
                                    setattr(config, key, value)
                    except (ValueError, KeyError) as e:
                        logger.warning(f"⚠️ Invalid provider config: {provider_name}: {e}")
                        
            except Exception as e:
                logger.warning(f"⚠️ Failed to load config from {config_file}: {e}")
                logger.info("📊 Using default configuration")
        else:
            if DEBUG:
                logger.debug(f"🔍 Config file not found: {config_file}, using defaults")
        
        return default_config
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from secrets directory"""
        keys = {}
        secrets_dir = Path(os.path.dirname(__file__)).parent.parent / 'secrets' / 'keys'
        
        key_files = {
            'openai': secrets_dir / 'openai.key',
            'anthropic': secrets_dir / 'anthropic.key',
            'openrouter': secrets_dir / 'openrouter.key'
        }
        
        for key_name, key_file in key_files.items():
            if key_file.exists():
                try:
                    with open(key_file, 'r') as f:
                        key_value = f.read().strip()
                        keys[key_name] = key_value
                        if DEBUG:
                            logger.debug(f"✅ Loaded {key_name} API key")
                except Exception as e:
                    logger.error(f"❌ Failed to load {key_name} API key: {e}")
            else:
                logger.warning(f"⚠️ API key file not found: {key_file}")
        
        return keys
    
    def _get_api_key(self, config: LLMConfig) -> Optional[str]:
        """Get API key for a provider"""
        # Map key file paths to loaded keys
        if 'openai.key' in config.api_key_file:
            return self.api_keys.get('openai')
        elif 'anthropic.key' in config.api_key_file:
            return self.api_keys.get('anthropic')
        elif 'openrouter.key' in config.api_key_file:
            return self.api_keys.get('openrouter')
        return None
    
    def _build_prompt(
        self,
        provider: LLMProvider,
        bug_description: str,
        code_context: Dict[str, str],
        test_failures: List[str],
        previous_attempts: Optional[List[str]] = None
    ) -> str:
        """Build provider-specific prompt"""
        
        # Format code context
        context_str = "\n\n".join([
            f"File: {filename}\n```python\n{content}\n```"
            for filename, content in code_context.items()
        ])
        
        # Format test failures
        failures_str = "\n".join([f"- {failure}" for failure in test_failures])
        
        # Format previous attempts if any
        attempts_str = ""
        if previous_attempts:
            attempts_str = "\n\nPrevious fix attempts that failed:\n" + "\n".join([
                f"Attempt {i+1}:\n{attempt}"
                for i, attempt in enumerate(previous_attempts)
            ])
        
        # Base prompt
        base_prompt = f"""You are a senior software engineer debugging a critical issue in the Agent-Forge multi-agent platform.

**Bug Description:**
{bug_description}

**Test Failures:**
{failures_str}

**Code Context:**
{context_str}{attempts_str}

**Your Task:**
1. Analyze the bug thoroughly
2. Identify the root cause
3. Propose a specific fix with exact code changes
4. Explain your reasoning
5. Estimate your confidence (0.0 to 1.0)

**Response Format (JSON):**
{{
    "analysis": "Your detailed analysis of the bug",
    "root_cause": "The underlying cause of the issue",
    "proposed_fix": "Exact code changes needed (use diff format)",
    "reasoning": "Why this fix will work",
    "confidence": 0.85,
    "alternative_approaches": ["Other possible fixes if confidence is low"]
}}

Provide ONLY the JSON response, no other text.
"""
        
        # Provider-specific optimizations
        if provider == LLMProvider.GPT4:
            # GPT-4: Focus on complex reasoning and architecture
            return base_prompt + "\nFocus on architectural issues and complex logic bugs."
        
        elif provider == LLMProvider.CLAUDE:
            # Claude: Focus on code understanding and API usage
            return base_prompt + "\nFocus on API usage patterns and code structure."
        
        elif provider == LLMProvider.QWEN:
            # Qwen: Focus on fast iteration and syntax
            return base_prompt + "\nFocus on syntax errors and quick fixes. Be concise."
        
        elif provider == LLMProvider.DEEPSEEK:
            # DeepSeek: Focus on edge cases and bug detection
            return base_prompt + "\nFocus on edge cases and subtle bugs."
        
        return base_prompt
    
    async def _call_provider(
        self,
        config: LLMConfig,
        prompt: str
    ) -> LLMResponse:
        """Call a single LLM provider"""
        import time
        start_time = time.time()
        
        api_key = self._get_api_key(config)
        if not api_key:
            error_msg = f"API key not found for {config.provider.value}"
            logger.error(f"❌ {error_msg}")
            return LLMResponse(
                provider=config.provider,
                analysis="",
                proposed_fix="",
                confidence=0.0,
                reasoning="",
                error=error_msg
            )
        
        try:
            if DEBUG:
                logger.debug(f"🔍 Calling {config.provider.value} ({config.model})")
            
            # Build request based on provider
            if config.provider == LLMProvider.CLAUDE:
                # Anthropic API format
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
                payload = {
                    "model": config.model,
                    "max_tokens": config.max_tokens,
                    "messages": [{"role": "user", "content": prompt}]
                }
            else:
                # OpenAI-compatible format (GPT-4, Qwen, DeepSeek via OpenRouter)
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": config.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": config.max_tokens,
                    "temperature": 0.7
                }
                
                # OpenRouter-specific headers
                if 'openrouter' in config.api_endpoint:
                    headers["HTTP-Referer"] = "https://github.com/agent-forge"
                    headers["X-Title"] = "Agent-Forge Multi-LLM Debug"
            
            # Make API call
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    config.api_endpoint,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=config.timeout)
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status != 200:
                        error_text = await response.text()
                        error_msg = f"API error {response.status}: {error_text}"
                        logger.error(f"❌ {config.provider.value}: {error_msg}")
                        return LLMResponse(
                            provider=config.provider,
                            analysis="",
                            proposed_fix="",
                            confidence=0.0,
                            reasoning="",
                            error=error_msg,
                            response_time=response_time
                        )
                    
                    result = await response.json()
                    
                    # Extract content based on provider
                    if config.provider == LLMProvider.CLAUDE:
                        content = result['content'][0]['text']
                    else:
                        content = result['choices'][0]['message']['content']
                    
                    # Parse JSON response
                    try:
                        # Extract JSON from markdown code blocks if present
                        if '```json' in content:
                            content = content.split('```json')[1].split('```')[0].strip()
                        elif '```' in content:
                            content = content.split('```')[1].split('```')[0].strip()
                        
                        parsed = json.loads(content)
                        
                        if DEBUG:
                            logger.debug(f"✅ {config.provider.value} responded in {response_time:.2f}s")
                        
                        return LLMResponse(
                            provider=config.provider,
                            analysis=parsed.get('analysis', ''),
                            proposed_fix=parsed.get('proposed_fix', ''),
                            confidence=float(parsed.get('confidence', 0.5)),
                            reasoning=parsed.get('reasoning', ''),
                            response_time=response_time
                        )
                    
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ {config.provider.value}: Failed to parse JSON: {e}")
                        logger.debug(f"🐛 Raw response: {content[:500]}...")
                        
                        # Return partial response
                        return LLMResponse(
                            provider=config.provider,
                            analysis=content,
                            proposed_fix="",
                            confidence=0.3,
                            reasoning="Failed to parse structured response",
                            error=f"JSON parse error: {str(e)}",
                            response_time=response_time
                        )
        
        except asyncio.TimeoutError:
            error_msg = f"Timeout after {config.timeout}s"
            logger.error(f"❌ {config.provider.value}: {error_msg}")
            return LLMResponse(
                provider=config.provider,
                analysis="",
                proposed_fix="",
                confidence=0.0,
                reasoning="",
                error=error_msg,
                response_time=time.time() - start_time
            )
        
        except Exception as e:
            logger.error(f"❌ {config.provider.value}: {str(e)}")
            return LLMResponse(
                provider=config.provider,
                analysis="",
                proposed_fix="",
                confidence=0.0,
                reasoning="",
                error=str(e),
                response_time=time.time() - start_time
            )
    
    async def analyze_bug(
        self,
        bug_description: str,
        code_context: Dict[str, str],
        test_failures: List[str],
        previous_attempts: Optional[List[str]] = None,
        providers: Optional[List[LLMProvider]] = None
    ) -> List[LLMResponse]:
        """
        Analyze a bug using multiple LLMs in parallel
        
        Args:
            bug_description: Description of the bug
            code_context: Dictionary of {filename: content}
            test_failures: List of test failure messages
            previous_attempts: Previous fix attempts that failed
            providers: Specific providers to use (default: all)
        
        Returns:
            List of LLMResponse objects
        """
        if DEBUG:
            logger.debug(f"🐛 Starting multi-LLM bug analysis")
            logger.debug(f"🔍 Bug: {bug_description[:100]}...")
            logger.debug(f"📊 Code context: {len(code_context)} files")
            logger.debug(f"❌ Test failures: {len(test_failures)}")
        
        # Select providers
        if providers is None:
            providers = list(self.providers_config.keys())
        
        # Build prompts for each provider
        prompts = {}
        for provider in providers:
            if provider in self.providers_config:
                prompt = self._build_prompt(
                    provider,
                    bug_description,
                    code_context,
                    test_failures,
                    previous_attempts
                )
                prompts[provider] = prompt
        
        # Call all providers in parallel
        tasks = [
            self._call_provider(self.providers_config[provider], prompts[provider])
            for provider in prompts.keys()
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and convert to list
        valid_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                provider = list(prompts.keys())[i]
                logger.error(f"❌ {provider.value} raised exception: {response}")
                # Create error response
                valid_responses.append(LLMResponse(
                    provider=provider,
                    analysis="",
                    proposed_fix="",
                    confidence=0.0,
                    reasoning="",
                    error=str(response)
                ))
            else:
                valid_responses.append(response)
        
        # Log summary
        successful = [r for r in valid_responses if not r.error]
        if DEBUG:
            logger.debug(f"📊 Analysis complete: {len(successful)}/{len(valid_responses)} providers succeeded")
            for response in successful:
                logger.debug(f"  - {response.provider.value}: confidence {response.confidence:.2f} ({response.response_time:.2f}s)")
        
        return valid_responses
    
    def get_provider_weights(self) -> Dict[LLMProvider, float]:
        """Get configured weights for each provider"""
        return {
            provider: config.weight
            for provider, config in self.providers_config.items()
        }


# CLI for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Multi-LLM Orchestrator")
    parser.add_argument("--bug", required=True, help="Bug description")
    parser.add_argument("--file", required=True, help="File with buggy code")
    parser.add_argument("--test-failure", required=True, help="Test failure message")
    parser.add_argument("--providers", nargs="+", choices=["gpt4", "claude", "qwen", "deepseek"], help="Specific providers to use")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
        os.environ['DEBUG'] = 'true'
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Load code context
    code_context = {}
    if os.path.exists(args.file):
        with open(args.file, 'r') as f:
            code_context[args.file] = f.read()
    
    # Convert provider names to enums
    providers = None
    if args.providers:
        providers = [LLMProvider(p) for p in args.providers]
    
    # Run analysis
    async def main():
        orchestrator = MultiLLMOrchestrator()
        responses = await orchestrator.analyze_bug(
            bug_description=args.bug,
            code_context=code_context,
            test_failures=[args.test_failure],
            providers=providers
        )
        
        print("\n" + "="*80)
        print("MULTI-LLM ANALYSIS RESULTS")
        print("="*80 + "\n")
        
        for response in responses:
            print(f"Provider: {response.provider.value}")
            print(f"Confidence: {response.confidence:.2f}")
            print(f"Response Time: {response.response_time:.2f}s")
            if response.error:
                print(f"Error: {response.error}")
            else:
                print(f"\nAnalysis:\n{response.analysis}\n")
                print(f"Proposed Fix:\n{response.proposed_fix}\n")
                print(f"Reasoning:\n{response.reasoning}\n")
            print("-" * 80 + "\n")
    
    asyncio.run(main())
