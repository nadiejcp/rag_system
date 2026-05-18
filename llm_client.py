import json
import httpx
from enum import Enum


class OllamaModel(Enum):
    """Available Ollama models"""
    GANDALF = "GandalfBaum/llama3.1-claude3.7"
    LLAMA_CLAUDE = "incept5/llama3.1-claude"
    GPT35 = "Eomer/gpt-3.5-turbo"
    CODE_GEMMA = "codegemma"
    DEEPSEEK = "deepseek-coder:6.7b"
    LLAMA3 = "llama3"


class LLMClient:
    def __init__(self, model: str = OllamaModel.LLAMA3.value):
        self.model = model
        self.url = "http://localhost:11434/api/chat"

    def ask(self, prompt: str) -> str:
        """
        Send a prompt to Ollama and get the response
        """
        try:
            with httpx.Client(timeout=300.0) as client:
                with client.stream(
                        "POST",
                        self.url,
                        json={
                            "model": self.model,
                            "messages": [{"role": "user", "content": prompt}],
                            "stream": True
                        },
                ) as response:
                    response.raise_for_status()

                    full_content = ""
                    for line in response.iter_lines():
                        if not line:
                            continue

                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            full_content += content
                        except json.JSONDecodeError:
                            continue

                    return full_content

        except Exception as e:
            return f"Error in LLM request: {str(e)}"

    @staticmethod
    def list_models() -> list[str]:
        """List all available model names"""
        return [model.value for model in OllamaModel]


def test_llm():
    """Test function for the LLM client"""
    client = LLMClient()

    print("Available models:", LLMClient.list_models())
    print("\nTesting LLM with a simple prompt...")

    response = client.ask("What is Python?")
    print(f"\nResponse:\n{response}")


if __name__ == "__main__":
    test_llm()
