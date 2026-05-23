import tensorflow as tf

from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras import Input, Model


def build_acoustic_model(num_features, num_hidden, num_phonemes):
    input_features = Input(shape=(None, num_features))
    x = LSTM(num_hidden, return_sequences=True)(input_features)
    output_phonemes = Dense(num_phonemes, activation='softmax')(x)
    model = Model(inputs=input_features, outputs=output_phonemes)
    return model

# Instantiate the model
num_features = 13  # Typically the number of MFCCs
num_hidden = 128   # Number of LSTM units
num_phonemes = 40  # Depends on the phoneme set being used
model = build_acoustic_model(num_features, num_hidden, num_phonemes)

# Compile the model
model.compile(
    optimizer='adam',  # Optimizer
    loss='sparse_categorical_crossentropy',  # Loss function
    metrics=['accuracy'],  # Metric to monitor
)

# Print the model summary to check the architecture
model.summary()



sample_mfcc_features = tf.random.normal((1, 100, num_features))  

# Forward pass through the model
output = model(sample_mfcc_features)

print(output.shape)


### use of the librosa library.
# import librosa
# import matplotlib.pyplot as plt
# file_path = 'sample.wav'
# y, sr = librosa.load(file_path, sr=22050)  # sr is the sample rate, default is 22050 Hz
# print(f"Sample Rate: {sr}")
# print(f"Audio Array Shape: {y.shape}")
# plt.figure(figsize=(12, 4))
# librosa.display.waveshow(y, sr=sr)
# plt.title("Waveform of Audio")
# plt.xlabel("Time (s)")
# plt.ylabel("Amplitude")
# plt.show()

# mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
# plt.figure(figsize=(10, 4))
# librosa.display.specshow(mfccs, sr=sr, x_axis='time')
# plt.colorbar()
# plt.title("MFCC")
# plt.show()

####### with a sample audio #####
import librosa
import numpy as np


# Load an audio file (mono)
audio_path = "sample.wav"
signal, sr = librosa.load(audio_path, sr=16000)

# Extract MFCC features
num_features = 13
mfcc = librosa.feature.mfcc(y=signal, sr=sr, n_mfcc=num_features)

# Transpose to shape: (time, features)
mfcc = mfcc.T

# Add batch dimension: (1, time, features)
mfcc = np.expand_dims(mfcc, axis=0)

# Run through the model
output = model(mfcc)

print("Input shape:", mfcc.shape)
print("Output shape:", output.shape)
