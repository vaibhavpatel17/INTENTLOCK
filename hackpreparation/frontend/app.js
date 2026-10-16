
const recordButton = document.getElementById("recordButton");
const recordStatus = document.getElementById("recordStatus");
const audioFile = document.getElementById("audioFile");
const fileStatus = document.getElementById("fileStatus");
const requestText = document.getElementById("requestText");
const actionType = document.getElementById("actionType");
const analyzeButton = document.getElementById("analyzeButton");
const resetButton = document.getElementById("resetButton");

const deepfakeStatus = document.getElementById("deepfakeStatus");
const speakerStatus = document.getElementById("speakerStatus");
const policyStatus = document.getElementById("policyStatus");
const decisionTitle = document.getElementById("decisionTitle");
const decisionDescription = document.getElementById("decisionDescription");
const activityLog = document.getElementById("activityLog");

let mediaRecorder = null;
let audioStream = null;
let audioChunks = [];
let recordedAudio = null;
let isRecording = false;

function setStatus(element, text, type = "pending") {
  element.textContent = text;
  element.className = `result-pill ${type}`;
}

function addLog(message, detail) {
  const emptyMessage = activityLog.querySelector(".empty-log");

  if (emptyMessage) {
    emptyMessage.remove();
  }

  const entry = document.createElement("div");
  entry.className = "log-entry";

  const content = document.createElement("div");
  const title = document.createElement("p");
  const description = document.createElement("small");
  const time = document.createElement("time");

  title.textContent = message;
  description.textContent = detail;
  time.textContent = new Date().toLocaleTimeString();

  content.append(title, description);
  entry.append(content, time);
  activityLog.prepend(entry);
}

function resetAssessment() {
  setStatus(deepfakeStatus, "Not checked");
  setStatus(speakerStatus, "Not checked");
  setStatus(policyStatus, "Not checked");

  decisionTitle.textContent = "Awaiting input";
  decisionDescription.textContent =
    "Submit a request to see a clearly labelled demonstration.";
}

function stopMicrophone() {
  if (audioStream) {
    audioStream.getTracks().forEach(track => track.stop());
    audioStream = null;
  }
}

recordButton.addEventListener("click", async () => {
  if (isRecording && mediaRecorder) {
    if (mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
    return;
  }

  if (!navigator.mediaDevices?.getUserMedia ||
      typeof MediaRecorder === "undefined") {
    recordStatus.textContent =
      "Recording is unavailable in this browser or page context.";
    addLog("Recording unavailable",
      "Try a supported browser on localhost or HTTPS.");
    return;
  }

  try {
    audioStream = await navigator.mediaDevices.getUserMedia({
      audio: true
    });

    audioChunks = [];
    recordedAudio = null;

    mediaRecorder = new MediaRecorder(audioStream);

    mediaRecorder.addEventListener("dataavailable", event => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    });

    mediaRecorder.addEventListener("stop", () => {
      recordedAudio = new Blob(audioChunks, {
        type: mediaRecorder.mimeType || "audio/webm"
      });

      isRecording = false;
      recordButton.textContent = "Start Recording";
      recordStatus.textContent =
        `Recording captured (${Math.ceil(recordedAudio.size / 1024)} KB).`;

      stopMicrophone();

      addLog("Voice recording captured",
        "Stored in this page's memory; not sent to a backend.");
    });

    mediaRecorder.start();
    isRecording = true;
    recordButton.textContent = "Stop Recording";
    recordStatus.textContent = "Recording in progress...";

    addLog("Recording started",
      "Microphone permission was granted.");
  } catch (error) {
    stopMicrophone();
    isRecording = false;
    recordButton.textContent = "Start Recording";
    recordStatus.textContent =
      "Microphone permission denied or unavailable.";

    addLog("Recording could not start",
      "Check browser microphone permissions.");
  }
});

audioFile.addEventListener("change", () => {
  const file = audioFile.files[0];

  if (!file) {
    fileStatus.textContent = "No file selected.";
    return;
  }

  recordedAudio = null;
  fileStatus.textContent =
    `${file.name} — ${Math.ceil(file.size / 1024)} KB selected.`;

  addLog("Audio file selected",
    "The file has not been analyzed by an AI model.");
});


analyzeButton.addEventListener("click", async () => {
  const text = requestText.value.trim();
  const selectedFile = audioFile.files[0];
  const audio = selectedFile || recordedAudio;

  if (!audio) {
    decisionTitle.textContent = "Audio required";
    decisionDescription.textContent =
      "Record or upload audio before running real verification.";
    addLog("Assessment not started", "No audio was provided.");
    return;
  }

  const speakerId =
    document.getElementById("speakerId")?.value.trim();

  if (!speakerId) {
    decisionTitle.textContent = "Speaker ID required";
    decisionDescription.textContent =
      "Enroll a trusted speaker and enter their speaker ID.";
    return;
  }

  analyzeButton.disabled = true;
  analyzeButton.textContent = "Analyzing...";
  setStatus(deepfakeStatus, "Checking...");
  setStatus(speakerStatus, "Checking...");
  setStatus(policyStatus, "Checking...");
  decisionTitle.textContent = "Verification in progress";
  decisionDescription.textContent =
    "Waiting for DetectifAI. No sensitive action will be executed.";

  try {
    const form = new FormData();
    form.append("speaker_id", speakerId);
    form.append("action_type", actionType.value);
    form.append("request_text", text);

    if (selectedFile) {
      form.append("audio", selectedFile);
    } else {
      form.append("audio", audio, "recording.webm");
    }

    const response = await fetch("http://127.0.0.1:8000/api/analyze", {
      method: "POST",
      body: form
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.detail || "Verification request failed.");
    }

    const deepfake = result.deepfake_verdict || "not_sure";
    const speaker = result.speaker_decision || "unknown";
    const policy = result.policy || {};
    const decision = policy.decision || "BLOCK";

    setStatus(
      deepfakeStatus,
      deepfake,
      deepfake === "real" ? "success" : "blocked"
    );

    setStatus(
      speakerStatus,
      speaker,
      speaker === "match" ? "success" : "blocked"
    );

    setStatus(
      policyStatus,
      decision,
      decision === "REQUIRES_CONFIRMATION" ||
      decision === "REVIEW" ? "pending" : "blocked"
    );

    decisionTitle.textContent = decision.replaceAll("_", " ");
    decisionDescription.textContent =
      `${policy.reason || "No policy explanation returned."} ` +
      "No real payment or sensitive action was executed.";

    addLog(
      "Real verification response received",
      `Speaker: ${speaker}; deepfake: ${deepfake}; policy: ${decision}`
    );
  } catch (error) {
    setStatus(deepfakeStatus, "Unavailable", "blocked");
    setStatus(speakerStatus, "Unavailable", "blocked");
    setStatus(policyStatus, "Blocked", "blocked");
    decisionTitle.textContent = "Verification failed";
    decisionDescription.textContent =
      `${error.message} No sensitive action was executed.`;
    addLog("Verification failed", error.message);
  } finally {
    analyzeButton.disabled = false;
    analyzeButton.textContent = "Analyze Request";
  }
});


resetButton.addEventListener("click", () => {
  if (isRecording && mediaRecorder &&
      mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  }

  requestText.value = "";
  audioFile.value = "";
  recordedAudio = null;

  fileStatus.textContent = "No file selected.";
  recordStatus.textContent = "Ready to record";

  resetAssessment();

  addLog("Assessment reset",
    "The displayed assessment has been cleared.");
});

window.addEventListener("beforeunload", stopMicrophone);
