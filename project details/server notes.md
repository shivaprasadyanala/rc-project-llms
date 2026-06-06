e158763509cb  ollama continaer

ff83eae80205 whisper container whisper\_server\_whisper-api(image)



containers

ff83  whisper\_server\_file\_api 8003/transcribe

e15 ollama 11435

sudo docker run -p 11435:11434 --gpus "device=5" -d ollama/ollama:latest

8b08  inco\_robotics  live whisper 

bbe4  llama.cpp server   8085



sudo docker run --gpus='"device=0"' -p 8003:8000 --name whisper-server whisper\_server\_whisper-api:latest

use compose file to build whisper contianer



&#x20;sudo docker run -d   --name llama-gpu   --gpus '"device=0"'   -p 8085:8080   -v \~/models:/models   ghcr.io/ggerganov/llama.cpp:server-cuda-b4719   --model /models/mistral-7b-instruct-v0.3.Q4\_K\_M.gguf   --host 0.0.0.0   --port 8080   --ctx-size 4096   --n-gpu-layers 99   --threads 4



docker exec -it <container> nvidia-smi

sudo docker run -d agentic\_ir:latest

&#x20;sudo docker build -t agentic\_ir:latest .

wc -l



models



gpt-oss:20b  fast but inaccurate

gemma4:31b  accurate but slow



add for which points are gained.



#### **fixing the issues:-** 



1. if the crop is planted first before water collecting, the crop gets removed due to water available false.



##### **next working:-**



pydantic for return type validation

