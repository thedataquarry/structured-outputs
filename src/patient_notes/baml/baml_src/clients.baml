// Learn more about clients at https://docs.boundaryml.com/docs/snippets/clients/overview

client<llm> OpenRouterGPT4oMini {
  provider "openai-generic"
  options {
    base_url "https://openrouter.ai/api/v1"
    api_key env.OPENROUTER_API_KEY
    model "openai/gpt-4o-mini"
    temperature 0.0
    headers {
      "HTTP-Referer" "https://thedataquarry.com" // Optional
      "X-Title" "Structured Outputs" // Optional
    }
  }
}

client<llm> OpenRouterGPT41Mini {
  provider "openai-generic"
  options {
    base_url "https://openrouter.ai/api/v1"
    api_key env.OPENROUTER_API_KEY
    model "openai/gpt-4.1-mini"
    temperature 0.0
    headers {
      "HTTP-Referer" "https://thedataquarry.com" // Optional
      "X-Title" "Structured Outputs" // Optional
    }
  }
}

client<llm> OpenRouterGPT41Nano {
  provider "openai-generic"
  options {
    base_url "https://openrouter.ai/api/v1"
    api_key env.OPENROUTER_API_KEY
    model "openai/gpt-4.1-nano"
    temperature 0.0
    headers {
      "HTTP-Referer" "https://thedataquarry.com" // Optional
      "X-Title" "Structured Outputs" // Optional
    }
  }
}

client<llm> OpenRouterGemma3_27b {
  provider "openai-generic"
  options {
    base_url "https://openrouter.ai/api/v1"
    api_key env.OPENROUTER_API_KEY
    model "google/gemma-3-27b-it"
    temperature 0.0
    headers {
      "HTTP-Referer" "https://thedataquarry.com" // Optional
      "X-Title" "Structured Outputs" // Optional
    }
  }
}

client<llm> OpenRouterGemma3_4b {
  provider "openai-generic"
  options {
    base_url "https://openrouter.ai/api/v1"
    api_key env.OPENROUTER_API_KEY
    model "google/gemma-3-4b-it"
    temperature 0.0
    headers {
      "HTTP-Referer" "https://thedataquarry.com" // Optional
      "X-Title" "Structured Outputs" // Optional
    }
  }
}

client<llm> OpenRouterGoogleGemini25Flash {
  provider "openai-generic"
  options {
    base_url "https://openrouter.ai/api/v1"
    api_key env.OPENROUTER_API_KEY
    model "google/gemini-2.5-flash"
    temperature 0.0
    headers {
      "HTTP-Referer" "https://thedataquarry.com" // Optional
      "X-Title" "Structured Outputs" // Optional
    }
  }
}


client<llm> OpenRouterGoogleGemini2Flash {
  provider "openai-generic"
  options {
    base_url "https://openrouter.ai/api/v1"
    api_key env.OPENROUTER_API_KEY
    model "google/gemini-2.0-flash-001"
    temperature 0.0
    headers {
      "HTTP-Referer" "https://thedataquarry.com" // Optional
      "X-Title" "Structured Outputs" // Optional
    }
  }
}

client<llm> OpenRouterMistralDevstralMedium {
  provider "openai-generic"
  options {
    base_url "https://openrouter.ai/api/v1"
    api_key env.OPENROUTER_API_KEY
    model "mistralai/devstral-medium"
    temperature 0.0
    headers {
      "HTTP-Referer" "https://thedataquarry.com" // Optional
      "X-Title" "Structured Outputs" // Optional
    }
  }
}

client<llm> OllamaLlama3 {
  provider "openai-generic"
  options {
    base_url "http://localhost:11434/v1"
    model "llama3:latest"
  }
}

client<llm> OllamaGemma3_12b {
  provider "openai-generic"
  options {
    base_url "http://localhost:11434/v1"
    model "gemma3:12b"
  }
}

client<llm> Gemini2Flash {
  provider google-ai
  options {
    model "gemini-2.0-flash"
    api_key env.GOOGLE_API_KEY
    generationConfig {
      temperature 0.0
    }
  }
}

client<llm> Gemini25Flash {
  provider google-ai
  options {
    model "gemini-2.5-flash"
    api_key env.GOOGLE_API_KEY
    generationConfig {
      temperature 0.0
    }
  }
}

client<llm> GTP4oMiniExtract {
  provider openai
  options {
    model "gpt-4o-mini"
    api_key env.OPENAI_API_KEY
    temperature 0.0
  }
}

client<llm> GTP4oMiniGenerate {
  provider openai
  options {
    model "gpt-4o-mini"
    api_key env.OPENAI_API_KEY
    temperature 0.3
  }
}

client<llm> GPT4o {
  provider openai
  options {
    model "gpt-4o"
    api_key env.OPENAI_API_KEY
    temperature 0.0
  }
}

client<llm> FastOpenAI {
  provider openai
  options {
    model "gpt-4o-mini"
    api_key env.OPENAI_API_KEY
  }
}

client<llm> Fast {
  provider round-robin
  options {
    // This will alternate between the two clients
    // Learn more at https://docs.boundaryml.com/docs/snippets/clients/round-robin
    strategy [OpenRouterGPT4oMini, FastOpenAI]
  }
}

client<llm> OpenaiFallback {
  provider fallback
  options {
    // This will try the clients in order until one succeeds
    // Learn more at https://docs.boundaryml.com/docs/snippets/clients/fallback
    strategy [GTP4oMiniGenerate, GPT4o]
  }
}