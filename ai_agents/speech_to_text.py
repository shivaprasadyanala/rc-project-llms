import speech_recognition as sr
import requests
r = sr.Recognizer()
import time
import yaml,os,sys
def read_config(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)  # safe_load prevents code execution
            return config
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error reading file: {e}")
        sys.exit(1)

config_data = read_config("config.yaml")
url = "http://hal9000.skim.th-owl.de:8003/transcribe"
audio_text = ""
while True and config_data["speech"]["user_input"]:
    try:
        with sr.Microphone() as source:
            print("give a task to the llm agent:")
            print("Listening...")
            
            r.adjust_for_ambient_noise(source, duration=0.2)
            audio = r.listen(source)
            
            st_time = time.time()
            # text = r.recognize_google(audio)
            with open("mic.wav", "wb") as f:
                f.write(audio.get_wav_data())
            print("time taken for audio processing: "+str(time.time()-st_time))
            response = ""
            with open("mic.wav", "rb") as f:
                response = requests.post(url, files={"file": f})
            
            print("time taken for model: "+str(response.json()["time_taken"]))
            main_text = response.json()["text"]
            text = main_text.lower()+" stop"  
            print("You said:", text)
            audio_text = main_text
            print("say STOP to stop giving commands")
            if "stop" in text:
                print("Exiting program...")
                break

    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))

    except sr.UnknownValueError:
        print("Could not understand audio")

    except KeyboardInterrupt:
        print("Program terminated by user")
        break
