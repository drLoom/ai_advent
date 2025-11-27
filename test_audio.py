import requests
import json
import base64
import os
from dotenv import load_dotenv

load_dotenv()

def encode_audio_to_base64(audio_path):
    with open(audio_path, "rb") as audio_file:
        return base64.b64encode(audio_file.read()).decode('utf-8')

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
    "Content-Type": "application/json"
}

# Read and encode the audio file
audio_path = input("Enter path to WAV or MP3 file: ").strip()

if not os.path.exists(audio_path):
    print(f"Error: File {audio_path} does not exist")
    exit(1)

print("Encoding audio to base64...")
base64_audio = encode_audio_to_base64(audio_path)

# Determine format from file extension
audio_format = "wav" if audio_path.endswith(".wav") else "mp3"
print(f"Detected format: {audio_format}")

messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "Please transcribe this audio file. Only return the transcribed text, nothing else."
            },
            {
                "type": "input_audio",
                "input_audio": {
                    "data": base64_audio,
                    "format": audio_format
                }
            }
        ]
    }
]

payload = {
    "model": "google/gemini-2.0-flash-exp:free",
    "messages": messages
}

print("Sending request to OpenRouter...")
response = requests.post(url, headers=headers, json=payload)

print(f"\nStatus Code: {response.status_code}")
print(f"\nResponse:")
result = response.json()
print(json.dumps(result, indent=2))

if response.status_code == 200:
    transcript = result.get('choices', [{}])[0].get('message', {}).get('content', '')
    print(f"\n=== TRANSCRIPTION ===")
    print(transcript)
