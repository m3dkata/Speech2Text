import logging
import os
import tempfile
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import speech_recognition as sr
from pydub import AudioSegment

templates = Jinja2Templates(directory="templates")

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

@app.get("/pypa", response_class=HTMLResponse)
async def pypa_page(request: Request):
    return templates.TemplateResponse("pypa.html", {"request": request})

@app.post("/pypa/transcribe")
async def pypa_transcribe(file: UploadFile = File(...)):
    try:
        logging.info(f"Received file: {file.filename}, content_type: {file.content_type}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            content = await file.read()
            temp_audio.write(content)
            temp_audio_path = temp_audio.name
        
        logging.info(f"Temporary file created: {temp_audio_path}")

        # Convert to WAV using pydub
        audio = AudioSegment.from_file(temp_audio_path)
        audio = audio.set_channels(1)  # Convert to mono
        audio = audio.set_frame_rate(16000)  # Set frame rate to 16kHz
        audio.export(temp_audio_path, format="wav")

        logging.info("Audio converted to WAV format")

        recognizer = sr.Recognizer()

        try:
            with sr.AudioFile(temp_audio_path) as source:
                audio_data = recognizer.record(source)
            logging.info("Audio file read successfully")
        except Exception as e:
            logging.error(f"Error reading audio file: {str(e)}", exc_info=True)
            raise ValueError(f"Error reading audio file: {str(e)}")

        try:
            text = recognizer.recognize_google(audio_data, language="bg-BG")
            logging.info("Transcription completed")
        except sr.RequestError as e:
            logging.error(f"Could not request results from Google Speech Recognition service; {e}")
            raise
        except sr.UnknownValueError:
            logging.error("Google Speech Recognition could not understand audio")
            raise

        os.unlink(temp_audio_path)
        return JSONResponse(content={"transcription": text}, status_code=200)

    except Exception as e:
        logging.error(f"Transcription error: {str(e)}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)

    
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
    uvicorn.run(app, host="0.0.0.0", port=8004)
