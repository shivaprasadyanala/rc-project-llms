**gpt-oss:20b** (the ~21B MoE model from OpenAI, released mid-2025) performs reliably with tool calling / function calling when run via **Ollama**, but frequently fails or behaves inconsistently when served via **vLLM**. Here's why this happens and the current state as of early 2026.

### Ollama handles it "out of the box" better for most users
Ollama applies model-specific post-processing, chat templates, and output parsing tailored to gpt-oss. It uses the model's native "Harmony" format (with channels like `<|channel|>reasoning`, `<|channel|>tool_call`, etc.) and cleanly converts tool calls into the standard OpenAI-compatible structure (`tool_calls` array in the response).

- In Ollama, tool calling usually "just works" for basic to medium-complexity agents — especially with the default or OpenAI-compatible API endpoint (`/v1/chat/completions`).
- Many users report excellent agentic behavior (multi-step reasoning + reliable tool selection) precisely because Ollama does the heavy lifting on parsing and prompt formatting.
- It defaults to a reasonable context size (often 128k for gpt-oss tags) and reasoning effort level.

### vLLM's tool calling support for gpt-oss is still partial / buggy
vLLM is designed for high-throughput serving (PagedAttention, continuous batching, multi-GPU), but its tool-calling integration for gpt-oss has lagged behind Ollama. Key reasons it often doesn't work well:

- **Format mismatch & parser issues**  
  gpt-oss uses a custom structured output format ("Harmony") with tagged channels for reasoning vs. tool calls. vLLM requires explicit `--tool-call-parser openai` (or sometimes `gptoss` / `openai_gptoss` in newer builds) + `--reasoning-parser openai` flags.  
  Even with correct flags, many users see:
  - Tool calls leaking into `content` / `reasoning_content` instead of a clean `tool_calls` field.
  - Malformed JSON arguments.
  - Special tokens (`<|channel|>commentary`, etc.) leaking into tool names or responses.
  - Streaming tool calls randomly failing (tool args dumped into reasoning text).
  - Chat completions endpoint (`/v1/chat/completions`) being less reliable than the Harmony `/v1/responses` endpoint (which requires manual parsing via openai-harmony lib).

- **Work-in-progress status**  
  Multiple GitHub issues (vLLM repo #22337, #22578, #24076, #27641, #32587, etc.) from Aug 2025–Jan 2026 show ongoing bugs with tool calling on both 20b and 120b variants. Some were fixed in later vLLM releases (0.10.x+ with gpt-oss wheels), but problems persist — especially in streaming, parallel tool calls, or long contexts.

- **Prompt / system message sensitivity**  
  vLLM is stricter about exact prompt formatting. If tools aren't described perfectly in the system prompt (or if the client library mangles them), the model falls back to text reasoning instead of structured tool calls.

### Quick comparison table

| Aspect                  | Ollama (gpt-oss:20b)                          | vLLM (openai/gpt-oss-20b)                          |
|-------------------------|-----------------------------------------------|-----------------------------------------------------|
| **Tool calling reliability** | High – usually works without extra config    | Medium-low – requires flags, still buggy in many cases |
| **API style**           | OpenAI-compatible chat + good parsing        | OpenAI-compatible, but /chat/completions often broken; /responses better but needs extra parsing |
| **Streaming tools**     | Usually fine                                 | Frequently dumps tool args into reasoning text     |
| **Best for**            | Local dev, agents, quick prototyping         | High-throughput serving, multi-user, production (when it works) |
| **Hardware focus**      | CPU / modest GPU                             | High-end GPU(s), optimized for throughput          |
| **Fix level (early 2026)** | Mature for gpt-oss                           | Improving, but many open issues remain             |

### What to do if you want tools + vLLM
- Use latest vLLM with gpt-oss extras:  
  `uv pip install --pre vllm --extra-index-url https://wheels.vllm.ai/gpt-oss/`  
  Then serve with: `--tool-call-parser openai --reasoning-parser openai` (check exact flags in current docs).
- Prefer the `/v1/responses` Harmony endpoint + openai-harmony parser library if /chat/completions keeps failing.
- Test with very explicit system prompts that repeat tool schemas.
- If reliability > speed → stick with Ollama (or LM Studio, which also handles gpt-oss well).
- For production agents → many switched back to Ollama or waited for vLLM patches.

**Bottom line in March 2026**: Ollama's tighter integration and post-processing make tool use feel "plug-and-play" for gpt-oss-20b, while vLLM's more general-purpose (and ambitious) tool-calling layer still has rough edges for this specific model. If your setup allows, Ollama remains the safer bet for consistent tool-calling behavior right now.