
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.policy import assess_request
from app.verifier import enroll_speaker, verify_speaker

from pydantic import BaseModel
from app.agent import change_registered_number, demo_account

app = FastAPI(title="INTENTLOCK API")

# Development only: allow the local frontend to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def save_upload(upload: UploadFile) -> Path:
    """Save an uploaded recording temporarily for verification."""

    suffix = Path(upload.filename or "recording.webm").suffix
    temp = tempfile.NamedTemporaryFile(
        delete=False, suffix=suffix
    )
    path = Path(temp.name)

    try:
        with temp:
            shutil.copyfileobj(upload.file, temp)
        if path.stat().st_size == 0:
            raise HTTPException(400, "The audio file is empty.")
        if path.stat().st_size > 100 * 1024 * 1024:
            raise HTTPException(413, "Audio file exceeds 100 MB.")
        return path
    except Exception:
        path.unlink(missing_ok=True)
        raise


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "INTENTLOCK"}


@app.post("/api/enroll")
def enroll(
    speaker_id: str = Form(...),
    display_name: str = Form("Family member"),
    audio: UploadFile = File(...),
):
    path = save_upload(audio)

    try:
        result = enroll_speaker(
            path, speaker_id, display_name=display_name
        )
        return {
            "status": "enrolled",
            "speaker_id": speaker_id,
            "result": result,
        }
    except (RuntimeError, FileNotFoundError) as exc:
        raise HTTPException(502, str(exc)) from exc
    finally:
        path.unlink(missing_ok=True)


@app.post("/api/analyze")
def analyze(
    speaker_id: str = Form(...),
    action_type: str = Form("general"),
    request_text: str = Form(""),
    audio: UploadFile = File(...),
):
    path = save_upload(audio)

    try:
        result = verify_speaker(
            path, speaker_id, detect_deepfake=True
        )

        data = result.get("result", result)
        speaker_decision = data.get("decision", "unknown")

        deepfake = data.get("deepfake") or {}
        deepfake_verdict = deepfake.get("verdict", "not_sure")

        policy = assess_request(
            action_type, speaker_decision, deepfake_verdict
        )

        return {
            "speaker_decision": speaker_decision,
            "deepfake_verdict": deepfake_verdict,
            "similarity": data.get("similarity"),
            "action_type": action_type,
            "request_text": request_text,
            "policy": policy,
            "request_id": result.get("request_id"),
            "note": (
                "Voice checks are signals, not proof. "
                "No real payment or sensitive action was executed."
            ),
        }

    except (RuntimeError, FileNotFoundError) as exc:
        # A failed verification must never authorize an action.
        raise HTTPException(502, str(exc)) from exc
    finally:
        path.unlink(missing_ok=True)
class ChangeNumberRequest(BaseModel):
    new_number: str
    confirmation_complete: bool = False


@app.get("/api/demo-account")
def get_demo_account():
    return {"phone": demo_account["phone"]}


@app.post("/api/change-number")
def change_number(request: ChangeNumberRequest):
    # Sensitive changes require independent confirmation.
    if not request.confirmation_complete:
        raise HTTPException(
            status_code=403,
            detail="Independent confirmation is required."
        )

    result = change_registered_number(
        request.new_number,
        authorized=True
    )

    if result["status"] == "BLOCKED":
        raise HTTPException(status_code=403, detail=result["message"])

    if result["status"] == "ERROR":
        raise HTTPException(status_code=400, detail=result["message"])

    return result