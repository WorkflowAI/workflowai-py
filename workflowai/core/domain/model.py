from typing import Literal, Union

Model = Union[
    Literal[
        # --------------------------------------------------------------------------
        # OpenAI Models
        # --------------------------------------------------------------------------
        "gpt-4o-latest",
        "gpt-4o-2024-11-20",
        "gpt-4o-2024-08-06",
        "gpt-4o-2024-05-13",
        "gpt-4o-mini-latest",
        "gpt-4o-mini-2024-07-18",
        "o1-2024-12-17-high",
        "o1-2024-12-17",
        "o1-2024-12-17-low",
        "o1-preview-2024-09-12",
        "o1-mini-latest",
        "o1-mini-2024-09-12",
        "gpt-4o-audio-preview-2024-12-17",
        "gpt-4o-audio-preview-2024-10-01",
        "gpt-4-turbo-2024-04-09",
        "gpt-4-0125-preview",
        "gpt-4-1106-preview",
        "gpt-4-1106-vision-preview",
        "gpt-3.5-turbo-0125",
        "gpt-3.5-turbo-1106",
        # --------------------------------------------------------------------------
        # Gemini Models
        # --------------------------------------------------------------------------
        "gemini-2.0-flash-exp",
        "gemini-2.0-flash-thinking-exp-1219",
        "gemini-1.5-pro-latest",
        "gemini-1.5-pro-002",
        "gemini-1.5-pro-001",
        "gemini-1.5-pro-preview-0514",
        "gemini-1.5-pro-preview-0409",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash-002",
        "gemini-1.5-flash-001",
        "gemini-1.5-flash-8b",
        "gemini-1.5-flash-preview-0514",
        "gemini-exp-1206",
        "gemini-exp-1121",
        "gemini-1.0-pro-002",
        "gemini-1.0-pro-001",
        "gemini-1.0-pro-vision-001",
        # --------------------------------------------------------------------------
        # Claude Models
        # --------------------------------------------------------------------------
        "claude-3-5-sonnet-latest",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-20240620",
        "claude-3-5-haiku-latest",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        # --------------------------------------------------------------------------
        # Llama Models
        # --------------------------------------------------------------------------
        "llama-3.3-70b",
        "llama-3.2-90b",
        "llama-3.2-11b",
        "llama-3.2-11b-vision",
        "llama-3.2-3b",
        "llama-3.2-1b",
        "llama-3.2-90b-vision-preview",
        "llama-3.2-90b-text-preview",
        "llama-3.2-11b-text-preview",
        "llama-3.2-3b-preview",
        "llama-3.2-1b-preview",
        "llama-3.1-405b",
        "llama-3.1-70b",
        "llama-3.1-8b",
        "llama3-70b-8192",
        "llama3-8b-8192",
        # --------------------------------------------------------------------------
        # Mistral AI Models
        # --------------------------------------------------------------------------
        "mixtral-8x7b-32768",
        "mistral-large-2-latest",
        "mistral-large-2-2407",
        "mistral-large-latest",
        "mistral-large-2411",
        "pixtral-large-latest",
        "pixtral-large-2411",
        "pixtral-12b-2409",
        "ministral-3b-2410",
        "ministral-8b-2410",
        "mistral-small-2409",
        "codestral-mamba-2407",
        # --------------------------------------------------------------------------
        # Qwen Models
        # --------------------------------------------------------------------------
        "qwen-v3p2-32b-instruct",
        # --------------------------------------------------------------------------
        # DeepSeek Models
        # --------------------------------------------------------------------------
        "deepseek-v3-2412",
        "deepseek-r1-2501",
    ],
    # Adding string to allow for any model not currently in the SDK but supported by the API
    str,
]
