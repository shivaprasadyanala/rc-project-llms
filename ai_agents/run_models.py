import subprocess
import sys

models = [
    "gpt-oss:20b",
    "llama3.1:8b",
    "mistral:7b",
    "qwen2.5:7b",
    "qwen3:8b",
    "qwen3.6:27b",
    "glm-4.7-flash:q4_K_M",
    "nemotron3:33b",
    "gemma4:e4b",
    "gemma4:26b",
    "nemotron-3-nano:4b",
    "gemma4:e4b"
]

NUM_RUNS = 20

for model in models:
    for i in range(NUM_RUNS):
        print(f"{model} - run {i+1}/{NUM_RUNS}")

        subprocess.run(
            [
                sys.executable,
                "experiment_baseline_agentic.py",
                "--model",
                model
            ],
            check=True
        )

print("All models completed.")