import os
import wave
import struct
import math
import numpy as np

def generate_wav(filepath, duration_sec, sample_rate=44100, generator_fn=None):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    num_samples = int(duration_sec * sample_rate)
    
    with wave.open(filepath, 'w') as wav_file:
        nchannels = 1
        sampwidth = 2
        wav_file.setparams((nchannels, sampwidth, sample_rate, num_samples, 'NONE', 'not compressed'))
        
        samples = generator_fn(num_samples, sample_rate)
        # Normalize and convert to 16-bit PCM
        samples = np.clip(samples, -1.0, 1.0)
        pcm = (samples * 32767).astype(np.int16)
        wav_file.writeframes(pcm.tobytes())
    print(f"Generated audio: {filepath} ({os.path.getsize(filepath)/1024:.1f} KB, {duration_sec}s)")

def make_wind_ambience(n, sr):
    # Pink / brown filtered noise with slow resonant modulation
    noise = np.random.normal(0, 0.3, n)
    t = np.linspace(0, n/sr, n)
    envelope = 0.5 + 0.3 * np.sin(2 * math.pi * 0.2 * t) + 0.2 * np.cos(2 * math.pi * 0.07 * t)
    # Low pass filter via rolling mean
    window = 100
    filtered = np.convolve(noise, np.ones(window)/window, mode='same')
    return filtered * envelope

def make_rain_audio(n, sr):
    # Dense high-frequency clicks and white noise shower
    white = np.random.normal(0, 0.25, n)
    clicks = np.zeros(n)
    click_indices = np.random.randint(0, n, size=int(n * 0.05))
    clicks[click_indices] = np.random.uniform(0.3, 0.8, size=len(click_indices))
    # Filter
    window = 15
    f_white = np.convolve(white, np.ones(window)/window, mode='same')
    return (f_white * 0.7 + clicks * 0.3)

def make_thunder_audio(n, sr):
    t = np.linspace(0, n/sr, n)
    decay = np.exp(-t * 0.8)
    sub = np.sin(2 * math.pi * 45 * t) * decay * 0.8
    rumble = np.random.normal(0, 0.3, n) * decay
    window = 80
    f_rumble = np.convolve(rumble, np.ones(window)/window, mode='same')
    return np.clip(sub + f_rumble * 1.5, -1.0, 1.0)

def make_indoor_ambience(n, sr):
    # Very gentle hum and room resonance
    t = np.linspace(0, n/sr, n)
    hum = np.sin(2 * math.pi * 60 * t) * 0.08
    air = np.random.normal(0, 0.05, n)
    window = 120
    f_air = np.convolve(air, np.ones(window)/window, mode='same')
    return hum + f_air

def make_footstep(surface_type, n, sr):
    t = np.linspace(0, n/sr, n)
    decay = np.exp(-t * 40.0) # Sharp tap decay
    if surface_type == 'concrete':
        impact = np.sin(2 * math.pi * 180 * t) * decay * 0.6 + np.random.normal(0, 0.4, n) * decay
    elif surface_type == 'wood':
        impact = np.sin(2 * math.pi * 95 * t) * decay * 0.8 + np.sin(2 * math.pi * 190 * t) * decay * 0.3
    else: # grass
        noise = np.random.normal(0, 0.35, n) * decay
        window = 30
        impact = np.convolve(noise, np.ones(window)/window, mode='same')
    return impact

def make_ui_sound(sound_type, n, sr):
    t = np.linspace(0, n/sr, n)
    if sound_type == 'click':
        decay = np.exp(-t * 80.0)
        return np.sin(2 * math.pi * 1200 * t) * decay * 0.5
    else: # transition
        decay = np.exp(-t * 10.0)
        freq = 300 + 400 * np.sin(2 * math.pi * 2 * t)
        return np.sin(2 * math.pi * freq * t) * decay * 0.4

def generate_all_soundtrack():
    base = "assets/audio"
    generate_wav(f"{base}/ambience_outdoor.wav", 4.0, generator_fn=make_wind_ambience)
    generate_wav(f"{base}/ambience_indoor.wav", 3.0, generator_fn=make_indoor_ambience)
    generate_wav(f"{base}/weather_rain.wav", 4.0, generator_fn=make_rain_audio)
    generate_wav(f"{base}/weather_wind.wav", 4.0, generator_fn=make_wind_ambience)
    generate_wav(f"{base}/weather_thunder.wav", 3.0, generator_fn=make_thunder_audio)
    
    generate_wav(f"{base}/footstep_concrete.wav", 0.25, generator_fn=lambda n, sr: make_footstep('concrete', n, sr))
    generate_wav(f"{base}/footstep_wood.wav", 0.25, generator_fn=lambda n, sr: make_footstep('wood', n, sr))
    generate_wav(f"{base}/footstep_grass.wav", 0.25, generator_fn=lambda n, sr: make_footstep('grass', n, sr))
    
    generate_wav(f"{base}/ui_click.wav", 0.1, generator_fn=lambda n, sr: make_ui_sound('click', n, sr))
    generate_wav(f"{base}/ui_transition.wav", 0.5, generator_fn=lambda n, sr: make_ui_sound('transition', n, sr))
    print("All environmental audio samples successfully generated.")

if __name__ == "__main__":
    generate_all_soundtrack()
