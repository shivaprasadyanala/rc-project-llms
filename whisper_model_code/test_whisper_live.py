from whisper_live.client import TranscriptionClient
client = TranscriptionClient(
    host="localhost",
    port=9090,
    model="small",
    lang="en",
    save_output_recording=True,
    output_recording_filename="./output_recording.wav",
    output_transcription_path = "test.srt"
)
transcript_array = []

client()