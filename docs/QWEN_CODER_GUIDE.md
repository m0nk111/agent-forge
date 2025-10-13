# Using Qwen3 Coder 480B in Your Copilot Workflow

This guide shows you how to use the free Qwen3 Coder 480B model from OpenRouter in various Copilot setups.

## 🔑 Prerequisites

Your OpenRouter API key is already stored at:
- Development: `secrets/keys/openrouter.key`
- Production: `/opt/agent-forge/secrets/keys/openrouter.key`

## 📋 Quick Reference

**Model ID**: `qwen/qwen3-coder:free`
**Context Length**: 262,144 tokens (262K)
**Cost**: FREE
**Best For**: Code generation, debugging, refactoring, code review

## 🎯 Method 1: Continue Extension (Recommended)

### Setup Steps:

1. **Install Continue Extension** in VS Code:
   ```
   code --install-extension continue.continue
   ```

2. **Open Continue Config**:
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Continue: Open config.json"
   - Press Enter

3. **Add OpenRouter Configuration**:
   ```json
   {
     "models": [
       {
         "title": "Qwen3 Coder 480B (Free)",
         "provider": "openrouter",
         "model": "qwen/qwen3-coder:free",
         "apiKey": "sk-or-v1-YOUR_KEY_HERE",
         "apiBase": "https://openrouter.ai/api/v1"
       }
     ],
     "tabAutocompleteModel": {
       "title": "Qwen3 Coder Autocomplete",
       "provider": "openrouter",
       "model": "qwen/qwen3-coder:free",
       "apiKey": "sk-or-v1-YOUR_KEY_HERE"
     }
   }
   ```

4. **Replace API Key**:
   - Copy your API key from `secrets/keys/openrouter.key`
   - Replace `sk-or-v1-YOUR_KEY_HERE` with your actual key

5. **Use It**:
   - Press `Ctrl+L` (or `Cmd+L`) to open Continue chat
   - Select "Qwen3 Coder 480B (Free)" from model dropdown
   - Start coding!

### Features with Continue:

- **Chat**: Ask coding questions inline
- **Edit**: Select code and ask for modifications
- **Autocomplete**: Tab completion powered by Qwen3 Coder
- **Context**: Automatically includes relevant files

## 🎯 Method 2: Direct Python Usage

### Test Script

Run the provided test script:
```bash
python3 scripts/test_qwen_coder.py
```

### Use in Your Code

```python
from pathlib import Path
import requests

def load_api_key() -> str:
    """Load OpenRouter API key."""
    return Path('secrets/keys/openrouter.key').read_text().strip()

def ask_qwen(prompt: str) -> str:
    """Ask Qwen3 Coder a question."""
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {load_api_key()}",
            "HTTP-Referer": "https://github.com/m0nk111/agent-forge",
            "X-Title": "Agent-Forge"
        },
        json={
            "model": "qwen/qwen3-coder:free",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    return response.json()['choices'][0]['message']['content']

# Example usage
code = ask_qwen("Write a Python function to sort a list using quicksort")
print(code)
```

## 🎯 Method 3: LangChain Integration

```python
from langchain_openai import ChatOpenAI
from pathlib import Path

api_key = Path('secrets/keys/openrouter.key').read_text().strip()

llm = ChatOpenAI(
    model="qwen/qwen3-coder:free",
    openai_api_key=api_key,
    openai_api_base="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "https://github.com/m0nk111/agent-forge",
        "X-Title": "Agent-Forge"
    }
)

# Use it
response = llm.invoke("Explain how async/await works in Python")
print(response.content)
```

## 🎯 Method 4: Cursor Editor

If you use Cursor (VS Code fork):

1. **Open Settings**: `Ctrl+,` (or `Cmd+,`)
2. **Search**: "cursor rules"
3. **Add Model**:
   - Provider: OpenRouter
   - Model: `qwen/qwen3-coder:free`
   - API Key: Your OpenRouter key

## 💡 Best Practices

### 1. Optimize Prompts for Code

**Good Prompt**:
```
Write a Python function that:
- Takes a list of integers
- Returns the sum of even numbers
- Include type hints and docstring
- Add error handling
```

**Better Prompt**:
```
Create a robust Python function with these specs:

Function name: sum_even_numbers
Input: List[int]
Output: int
Logic: Sum only even numbers from the list
Requirements:
  - Type hints (Python 3.10+)
  - Google-style docstring
  - Handle empty lists (return 0)
  - Handle None values in list (skip them)
  - Include 3 test cases in docstring

Example usage:
>>> sum_even_numbers([1, 2, 3, 4, 5, 6])
12
```

### 2. Use Context Effectively

Qwen3 Coder has 262K token context - use it!

```python
# Include relevant code in your prompt
prompt = f"""
Here's my existing code:

{existing_function_code}

Now improve it by:
1. Adding type hints
2. Improving error handling
3. Adding docstrings
4. Making it more efficient
"""
```

### 3. Leverage Streaming

For long responses, use streaming:

```python
def stream_response(prompt: str):
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={...},
        json={
            "model": "qwen/qwen3-coder:free",
            "messages": [{"role": "user", "content": prompt}],
            "stream": True
        },
        stream=True
    )
    
    for line in response.iter_lines():
        if line:
            # Process streaming response
            ...
```

### 4. Compare with Other Free Models

Try different models for different tasks:

| Task | Best Model | Reason |
|------|-----------|--------|
| Code Generation | `qwen/qwen3-coder:free` | Specialized for code |
| Debugging | `deepseek/deepseek-r1:free` | Strong reasoning |
| Documentation | `google/gemini-2.0-flash-exp:free` | Large context (1M) |
| Code Review | `meta-llama/llama-3.3-70b-instruct:free` | Balanced |

## 📊 Performance Tips

1. **Temperature**: Lower (0.3-0.5) for precise code, higher (0.7-0.9) for creative solutions
2. **Max Tokens**: Set appropriate limits to avoid timeout
3. **System Prompt**: Add role definition for better results:
   ```json
   {
     "messages": [
       {
         "role": "system",
         "content": "You are an expert Python developer specializing in clean, efficient code."
       },
       {
         "role": "user",
         "content": "Your actual prompt here"
       }
     ]
   }
   ```

## 🐛 Troubleshooting

### Rate Limits
Free models may have rate limits during peak hours. If you hit limits:
- Wait a few minutes
- Switch to another free model temporarily
- Use smaller prompts

### Timeout Errors
For long generations:
- Increase timeout: `timeout=120`
- Use streaming instead of blocking
- Break into smaller requests

### Quality Issues
If responses aren't good enough:
- Be more specific in prompts
- Provide more context/examples
- Try a different model (DeepSeek R1 for reasoning)

## 🔄 Alternative Free Models

If Qwen3 Coder is busy, try:

1. **DeepSeek R1**: `deepseek/deepseek-r1:free` (reasoning)
2. **Gemini 2.0 Flash**: `google/gemini-2.0-flash-exp:free` (1M context)
3. **Llama 3.3 70B**: `meta-llama/llama-3.3-70b-instruct:free` (balanced)

## 📚 Resources

- OpenRouter Docs: https://openrouter.ai/docs
- Model Rankings: https://openrouter.ai/rankings
- Pricing: https://openrouter.ai/models?q=free
- API Reference: https://openrouter.ai/docs/api-reference

## ✅ Quick Test

Run this to verify everything works:

```bash
python3 scripts/test_qwen_coder.py
```

You should see:
- Fibonacci function generation
- Code review example
- Token usage stats

Happy coding with Qwen3 Coder! 🚀
