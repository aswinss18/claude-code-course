from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

# Test different model names
models_to_test = [
    "claude-3-haiku-20240307",
    "claude-3-sonnet-20240229",
    "claude-3-opus-20240229",
    "claude-3-5-sonnet-20240620",
    "claude-3-5-sonnet-20241022"
]

for model in models_to_test:
    try:
        response = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        print(f"SUCCESS: {model} - WORKS")
        break
    except Exception as e:
        print(f"FAILED: {model} - {str(e)}")