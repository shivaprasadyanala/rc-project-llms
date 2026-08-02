import subprocess
import sys

# Per-model --think setting for agentic_approach2.py:
#   - gemma4:26b is a reasoning model whose tool-calling lives in its thinking
#     channel -> MUST use --think true (think=False breaks its tool calls).
#   - gpt-oss:20b -> --think false keeps the thinking channel off for lower
#     latency while tool calls still work.
#   - everything else -> --think default (omit the param; server decides).
MODEL_THINK_FLAGS = {
    "gemma4:26b": "--think true",
    "gpt-oss:20b": "--think false",
    "qwen3:8b": "--think false"
}

models = [
    "gpt-oss:20b",
    "llama3.1:8b",
    # "qwen2.5:7b",
    "qwen3:8b",
    # "qwen3.6:27b",
    # "glm-4.7-flash:q4_K_M",
    # "nemotron3:33b",
    # "gemma4:e4b",
    "gemma4:26b",
    "nemotron-3-nano:4b"
]

NUM_RUNS = 1

for model in models:
    think_flag = MODEL_THINK_FLAGS.get(model, "--think default")
    for i in range(NUM_RUNS):
        print(f"{model} (flag: {think_flag}) - run {i+1}/{NUM_RUNS}")

        subprocess.run(
            [
                sys.executable,
                "agentic_approach2.py",
                "--model",
                model,
                think_flag
            ],
            check=True
        )

print("All models completed.")
