import speech_recognition as sr
import requests
r = sr.Recognizer()
import time

url = "http://hal9000.skim.th-owl.de:8003/transcribe"
audio_text = ""
while True:
    try:
        with sr.Microphone() as source:
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
            text = response.json()["text"]
            text = text.lower()+" stop"  
            print("You said:", text)
            audio_text = text
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



# recognize speech using whisper
# try:
#     print("Whisper thinks you said " + r.recognize_whisper(audio, language="english"))
# except sr.UnknownValueError:
#     print("Whisper could not understand audio")
# except sr.RequestError as e:
#     print(f"Could not request results from Whisper; {e}")


# with open("microphone-results.wav", "wb") as f:
#     f.write(audio.get_wav_data())