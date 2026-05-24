from enum import Enum


class GroqModel(str, Enum):
    """Supported models from the Groq API."""

    LLAMA_70B = "llama-3.3-70b-versatile"
    DEEPSEEK_R1 = "deepseek-r1-distill-llama-70b"
