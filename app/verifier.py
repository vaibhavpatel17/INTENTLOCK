import os
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load the .env file from the INTENTLOCK project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

BASE_URL = "https://platform.detectif.ai/v1"
TIMEOUT = 300


def _upload_audio(endpoint, audio_path, fields, idempotency_key=None):
    """Upload an audio file to DetectifAI and return its JSON response."""

    api_key = os.getenv("DETECTIFAI_API_KEY")

    if not api_key or api_key == "replace_with_your_real_api_key":
        raise RuntimeError("DetectifAI API key is missing.")

    audio_path = Path(audio_path)

    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Idempotency-Key": idempotency_key or str(uuid.uuid4()),
    }

    with audio_path.open("rb") as audio_file:
        response = requests.post(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            data=fields,
            files={"file": (audio_path.name, audio_file)},
            timeout=TIMEOUT,
        )

    try:
        result = response.json()
    except ValueError:
        result = {"message": "DetectifAI returned a non-JSON response."}

    if not response.ok:
        error = result.get("error", {})
        code = error.get("code", "request_failed")
        message = error.get(
            "message", result.get("message", "Unknown error")
        )
        raise RuntimeError(
            f"DetectifAI request failed ({response.status_code}): "
            f"{code} - {message}"
        )

    return result


def enroll_speaker(
    audio_path, speaker_id, display_name=None, idempotency_key=None
):
    """Enroll a 15–60 second reference voice recording."""

    fields = {"speaker_id": speaker_id}

    if display_name:
        fields["display_name"] = display_name

    return _upload_audio(
        "/speakers/enroll",
        audio_path,
        fields,
        idempotency_key,
    )


def verify_speaker(
    audio_path, speaker_id, detect_deepfake=True, idempotency_key=None
):
    """Verify an enrolled speaker and optionally check for deepfake audio."""

    fields = {
        "speaker_id": speaker_id,
        "detect_deepfake": str(detect_deepfake).lower(),
    }

    return _upload_audio(
        "/speakers/verify",
        audio_path,
        fields,
        idempotency_key,
    )
