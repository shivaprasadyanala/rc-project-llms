**Models with reliable/good tool calling (function calling) support in vLLM** (as of March 2026) are those with dedicated parsers, guided decoding via structured outputs (Outlines), and community/user confirmation of consistency in production/agentic use cases.

vLLM's tool calling works via **--enable-auto-tool-choice** + a **--tool-call-parser** flag (e.g., `hermes`, `llama3_json`, `mistral`, `openai`, etc.). It leverages structured outputs for enforcement, making it more reliable on models trained/fine-tuned for JSON-like or Hermes-style tool formats.

### Models that work well / are explicitly supported and reliable

| Model Family                  | Specific Examples (Hugging Face IDs)                          | Tool Parser Flag              | Reliability Notes                                                                 | Sources |
|-------------------------------|----------------------------------------------------------------|--------------------------------|-----------------------------------------------------------------------------------|---------|
| **Llama 3.1 / 3.2 / 4**       | meta-llama/Meta-Llama-3.1-8B-Instruct<br>meta-llama/Meta-Llama-3.1-70B-Instruct<br>meta-llama/Meta-Llama-3.2-* <br>meta-llama/Llama-4-* | `llama3_json` (JSON mode)<br>`pythonic` or `llama4_pythonic` (for newer variants) | Very good; JSON-based is solid, parallel calls supported in Llama-4. Widely used in agents. | vLLM docs (latest): https://docs.vllm.ai/en/latest/features/tool_calling.html |
| **Hermes / NousResearch**     | NousResearch/Hermes-3-*<br>Hermes-2-Pro-*, Hermes-2-Theta-*   | `hermes`                      | Excellent for multi-turn & parallel tool calls; community favorite for reliability. (Theta variants slightly degraded post-merge.) | vLLM docs; user reports in Reddit / GitHub |
| **Mistral**                   | mistralai/Mistral-7B-Instruct-v0.3<br>Other Mistral function-calling variants | `mistral`                     | Good, especially with custom chat templates; some issues with parallel calls on 7B. | vLLM docs; examples/tool_chat_template_mistral_parallel.jinja |
| **Qwen / Qwen2.5**            | Qwen/Qwen2.5-*<br>Qwen/QwQ-32B                                | `hermes` (uses Hermes-style in tokenizer) | Strong; good reasoning + tool integration, especially QwQ series for agent workflows. | vLLM docs; Qwen official docs on function calling with vLLM |
| **DeepSeek**                  | DeepSeek-V3 / V3.2 / R1 series                                | Often `hermes` or custom       | Emerging as top for agentic/tool-use; built-in thinking + tool modes. | Community blogs (e.g., BentoML 2026 overview); vLLM recipes |

### Models with partial / problematic support
- **gpt-oss-20b / 120b** (OpenAI's open-weight MoE models): Supported via `--tool-call-parser openai` (or `openai_gptoss` in newer builds) + `--reasoning-parser openai`.  
  Tool calling often fails or is inconsistent on the standard `/v1/chat/completions` endpoint (leaked tokens like `<|channel|>commentary`, malformed args, streaming bugs). It works much better on the Harmony-specific `/v1/responses` endpoint with openai-harmony parser. Many open GitHub issues (#32587, #22578, #26083) confirm ongoing bugs even in early 2026. → Not "works well" compared to the above.

### Why some work better than others
- Models with native JSON/Hermes-style training + matching chat templates in tokenizer_config.json → vLLM can enforce structured outputs reliably.
- Older/niche/custom formats (like gpt-oss Harmony channels) → require extra parsers and still have parsing/streaming edge cases.

### Sources / References (primary & up-to-date as of March 2026)
- Official vLLM Tool Calling documentation: https://docs.vllm.ai/en/latest/features/tool_calling.html (lists supported models, parsers, known issues, and chat template examples)
- vLLM Supported Models page (cross-referenced): https://docs.vllm.ai/en/latest/models/supported_models.html
- GitHub issues/PRs (e.g., gpt-oss bugs): https://github.com/vllm-project/vllm/issues/32587, #22578, #26083
- Community discussions (Reddit r/LocalLLaMA): Threads on reliable function calling with vLLM, Hermes/Qwen/Llama praised frequently.
- Model-specific notes: Qwen docs on vLLM function calling; DeepSeek agent/tool focus in 2026 reviews.

**Bottom line**: For reliable tool calling in vLLM right now, go with Llama-3.1/3.2/4, Hermes-3, Mistral-Instruct, or Qwen2.5/QwQ series. These have the most mature parser integration and fewest reported issues. Avoid relying on gpt-oss variants for production tool agents via the standard chat completions API unless using the Harmony endpoint workaround.