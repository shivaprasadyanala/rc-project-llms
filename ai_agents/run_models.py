import subprocess
import sys

models = [
    "gpt-oss:20b",
    "llama3.1:8b",
    # "mistral:7b",
    # "qwen2.5:7b",
    "qwen3:8b",
    # "llama3.3:latest",
    # "qwen3.6:27b",
    # "glm-4.7-flash:q4_K_M",
    # "nemotron3:33b",
    "nemotron-3-nano:4b",
    "gemma4:26b"
]

NUM_RUNS = 1

for model in models:
    for i in range(NUM_RUNS):
        print(f"{model} - run {i+1}/{NUM_RUNS}")

        subprocess.run(
            [
                sys.executable,
                "deps_prompting.py",
                "--model",
                model
            ],
            check=True
        )

print("All models completed.")