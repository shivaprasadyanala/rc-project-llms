from faster_whisper import WhisperModel
model = WhisperModel("small",compute_type="float32")
segments, info = model.transcribe("record_game.m4a", word_timestamps=True)
print("part 1")
for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

audio = "record_game.m4a"

segments, info = model.transcribe(
    audio,
    beam_size=5,
    vad_filter=True,
    task="translate",  # direct translation
    condition_on_previous_text=True
)
print("part 2")
# for segment in segments:
#     for word in segment.words:
#         print("[%.2fs -> %.2fs] %s" % (word.start, word.end, word.word))
for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
# print(segments)



