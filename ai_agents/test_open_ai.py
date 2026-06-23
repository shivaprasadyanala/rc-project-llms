from openai import OpenAI

# Create a client pointing to your vLLM server
# The API key can be any string since vLLM doesn't require real authentication by default
client = OpenAI(
    base_url="http://hal9000.skim.th-owl.de:1951/v1/",  # vLLM server endpoint
    api_key="EMPTY"  # or any placeholder
)

try:
    # Send a chat completion request
    response = client.chat.completions.create(
        model="qwen3.6-27b",  # Must match a model loaded in vLLM
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "what is a apple?"}
        ],
        temperature=0.7,
        max_tokens=20000
    )

    # Print the model's reply
    print(dir(response.choices[0]))
    print((response.choices[0]))
    print("Assistant:", response.choices[0].message.content)

except Exception as e:
    print("Error communicating with vLLM server:", e)
