
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

analyzeButton.addEventListener("click", () => {
  const text = requestText.value.trim();
  const selectedFile = audioFile.files[0];
  const hasAudio = Boolean(selectedFile || recordedAudio);

  if (!text && !hasAudio) {
    decisionTitle.textContent = "Input required";
    decisionDescription.textContent =
      "Enter a request, record audio, or select an audio file.";

    addLog("Assessment not started",
      "No request or audio was provided.");
    return;
  }

  resetAssessment();

  setStatus(deepfakeStatus, "Not connected");
  setStatus(speakerStatus, "Not connected");
  setStatus(policyStatus, "Demo only");

  const action = actionType.value;
  const sensitiveActions = [
    "account_update",
    "file_transfer",
    "payment"
  ];

  if (sensitiveActions.includes(action)) {
    decisionTitle.textContent = "Blocked in demo mode";
    decisionDescription.textContent =
      "This action requires real backend authorization. " +
      "No action was executed.";
    setStatus(policyStatus, "Blocked", "blocked");
  } else {
    decisionTitle.textContent = "Simulation only";
    decisionDescription.textContent =
      "Input received, but no AI verification or authorization " +
      "was performed. Connect the backend for a real assessment.";
  }

  const inputType = hasAudio
    ? "Audio supplied"
    : "Text supplied";

  addLog("Demo assessment created",
    `${inputType}. Deepfake detection and speaker verification ` +
    "were not performed. No sensitive action was executed.");
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
