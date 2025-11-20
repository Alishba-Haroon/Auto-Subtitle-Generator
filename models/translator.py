from transformers import pipeline
import whisper
import ffmpeg
import torch
import os
from typing import List, Dict
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hugging Face token (optional)
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
if HUGGINGFACE_TOKEN:
    try:
        from huggingface_hub import login
        login(token=HUGGINGFACE_TOKEN)
        logger.info("Hugging Face login successful")
    except Exception as e:
        logger.warning(f"Login failed: {str(e)}")
else:
    logger.info("No token found. Public models only.")

# Supported languages & models
SUPPORTED_LANGUAGES = {
    "en": None, 
    "fr": "Helsinki-NLP/opus-mt-en-fr",
    "de": "Helsinki-NLP/opus-mt-en-de",
    "es": "Helsinki-NLP/opus-mt-en-es",
    "ur": "facebook/mbart-large-50-many-to-many-mmt",  
}
# MBART language codes
MBART_LANG_CODES = {
    "en": "en_XX",
    "ur": "ur_PK",
    "pt": "pt_XX"
}
# Global variables
translation_pipelines = {}
whisper_model = None

def load_models():
    """Load Whisper and translation models."""
    global whisper_model, translation_pipelines

    if not whisper_model:
        logger.info("Loading Whisper model...")
        whisper_model = whisper.load_model("base")
    for lang, model_name in SUPPORTED_LANGUAGES.items():
        if model_name and lang not in translation_pipelines:
            if HUGGINGFACE_TOKEN is None and lang in ["ur", "pt"]:
                logger.warning(f"Skipping {lang} translation: needs token")
                translation_pipelines[lang] = None
                continue
            try:
                logger.info(f"Loading translation model for {lang}")
                if lang in ["ur", "pt"]:
                    translation_pipelines[lang] = pipeline(
                        "translation",
                        model=model_name,
                        token=HUGGINGFACE_TOKEN,
                        src_lang="en_XX",
                        tgt_lang=MBART_LANG_CODES[lang]
                    )
                else:
                    translation_pipelines[lang] = pipeline(
                        "translation",
                        model=model_name,
                        token=HUGGINGFACE_TOKEN
                    )
            except Exception as e:
                logger.error(f"Failed to load {lang}: {str(e)}")
                translation_pipelines[lang] = None

def extract_audio(video_path: str, output_audio_path: str) -> str:
    """Extract audio from video."""
    try:
        logger.info(f"Extracting audio from {video_path}")
        os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
        (
            ffmpeg.input(video_path)
            .output(output_audio_path, ac=1, ar=16000)
            .run(overwrite_output=True, quiet=True)
        )
        return output_audio_path
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg error: {e.stderr.decode('utf8')}")
        raise

def transcribe_audio(audio_path: str, source_lang: str = "en") -> List[Dict]:
    """Transcribe audio using Whisper."""
    if not whisper_model:
        load_models()
    try:
        logger.info(f"Transcribing {audio_path}")
        result = whisper_model.transcribe(audio_path, language=None if source_lang == "auto" else source_lang)
        return [
            {"start": seg["start"], "end": seg["end"], "text": seg["text"].strip()}
            for seg in result["segments"]
        ]
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise


def translate_segments(segments: List[Dict], target_lang: str) -> List[Dict]:
    """Translate transcribed text."""
    if target_lang == "en":
        return segments
    if target_lang not in SUPPORTED_LANGUAGES:
        logger.warning(f"Unsupported language: {target_lang}")
        return segments
    if not translation_pipelines.get(target_lang):
        load_models()
    translator = translation_pipelines.get(target_lang)
    if not translator:
        logger.warning(f"No model for {target_lang}")
        return segments
    try:
        texts = [s["text"] for s in segments]

        if target_lang in ["ur", "pt"]:  # MBART
            translations = translator(texts, src_lang="en_XX", tgt_lang=MBART_LANG_CODES[target_lang])
            return [
                {"start": seg["start"], "end": seg["end"],
                 "text": trans[0]["translation_text"] if isinstance(trans, list) else trans["translation_text"]}
                for seg, trans in zip(segments, translations)
            ]
        else:
            translations = translator(texts)
            return [
                {"start": seg["start"], "end": seg["end"], "text": trans["translation_text"]}
                for seg, trans in zip(segments, translations)
            ]
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return segments

def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp."""
    hours, rem = divmod(seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{milliseconds:03}"


def generate_srt(segments: List[Dict], srt_path: str) -> str:
    """Save segments as SRT file."""
    try:
        logger.info(f"Generating SRT at {srt_path}")
        os.makedirs(os.path.dirname(srt_path), exist_ok=True)
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments, 1):
                f.write(f"{i}\n")
                f.write(f"{format_timestamp(seg['start'])} --> {format_timestamp(seg['end'])}\n")
                f.write(f"{seg['text']}\n\n")
        return srt_path
    except Exception as e:
        logger.error(f"SRT generation failed: {str(e)}")
        raise

def embed_subtitles(video_path: str, srt_path: str, output_path: str):
    """Embed SRT into video."""
    try:
        logger.info(f"Embedding subtitles: {video_path} → {output_path}")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        if not os.path.exists(srt_path):
            raise FileNotFoundError(f"SRT not found: {srt_path}")

        def escape_path(path):
            return path.replace('\\', '/').replace(':', '\\:')
        (
            ffmpeg.input(escape_path(video_path))
            .output(
                escape_path(output_path),
                vf=f"subtitles='{escape_path(srt_path)}'",
                acodec="copy",
                vcodec="libx264",
                crf=23,
                preset="fast"
            )
            .run(overwrite_output=True, quiet=True)
        )
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg error: {e.stderr.decode('utf8')}")
        raise
    except Exception as e:
        logger.error(f"Embedding error: {str(e)}")
        raise

def cleanup_files(*files):
    """Delete temporary files."""
    for file in files:
        try:
            if os.path.exists(file):
                os.remove(file)
                logger.info(f"Deleted {file}")
        except Exception as e:
            logger.warning(f"Could not delete {file}: {str(e)}")

# Initialize models safely
load_models() 
