import os
import tempfile
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import speech_recognition as sr

app = FastAPI(
    title="Speech to Text API",
    description="An API that transcribes speech to text using SpeechRecognition",
    version="1.0.1",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.post("/transcribe/", summary="Transcribe speech to text")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("bg-BG")  # Set default to Bulgarian
):
    """
    Transcribe the uploaded audio file to text.
    
    - **file**: An audio file to be transcribed (supported formats: WAV, AIFF, AIFF-C, FLAC)
    - **language**: The language code for transcription (default: bg-BG)
    
    Returns the transcribed text.
    """
    try:
        # Create a temporary file to store the uploaded audio
        with tempfile.NamedTemporaryFile(delete=False) as temp_audio:
            temp_audio.write(await file.read())
            temp_audio_path = temp_audio.name

        # Initialize the recognizer
        recognizer = sr.Recognizer()

        # Load the audio file
        with sr.AudioFile(temp_audio_path) as source:
            audio = recognizer.record(source)

        # Perform the transcription
        text = recognizer.recognize_google(audio, language=language)

        # Remove the temporary file
        os.unlink(temp_audio_path)

        return JSONResponse(content={"transcription": text}, status_code=200)

    except sr.UnknownValueError:
        return JSONResponse(content={"error": "Speech Recognition could not understand the audio"}, status_code=400)
    except sr.RequestError as e:
        return JSONResponse(content={"error": f"Could not request results from Speech Recognition service; {str(e)}"}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
