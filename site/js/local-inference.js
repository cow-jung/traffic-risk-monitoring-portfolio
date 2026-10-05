document.addEventListener("DOMContentLoaded", () => {
  const fileInput = document.getElementById("media-file");
  const runButton = document.getElementById("run-local-detect");
  const stage = document.getElementById("media-stage");
  const state = document.getElementById("local-model-state");
  const resultText = document.getElementById("local-detect-result");
  const confInput = document.getElementById("detect-conf");

  fetch("/local_model_status").then(r => r.json()).then(data => {
    state.textContent = data.ready ? "로컬 AI 모델 준비됨" : "models/best.pt 필요";
  }).catch(() => { state.textContent = "로컬 AI 모델 상태 확인 실패"; });

  if (!runButton) return;
  runButton.addEventListener("click", async () => {
    const file = fileInput && fileInput.files ? fileInput.files[0] : null;
    if (!file) {
      resultText.textContent = "먼저 탐지할 사진 또는 영상 파일을 선택하세요.";
      return;
    }
    runButton.disabled = true;
    runButton.textContent = "탐지 처리 중...";
    resultText.textContent = "YOLO11n으로 파일을 분석하고 있습니다.";
    const form = new FormData();
    form.append("file", file);
    form.append("conf", confInput ? confInput.value : "0.30");
    try {
      const response = await fetch("/detect_media", { method: "POST", body: form });
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.error || "탐지에 실패했습니다.");
      if (data.kind === "image") {
        stage.innerHTML = "";
        const img = document.createElement("img");
        img.src = data.url + "?t=" + Date.now();
        img.alt = "YOLO 낙하물 탐지 결과";
        img.style.maxWidth = "100%";
        stage.appendChild(img);
        const summary = (data.detections || []).map(x => x.class + " " + Math.round(x.confidence * 100) + "%").join(", ");
        resultText.textContent = "탐지 " + data.count + "건" + (summary ? " · " + summary : "");
      } else {
        stage.innerHTML = "";
        const video = document.createElement("video");
        video.src = data.url + "?t=" + Date.now();
        video.controls = true;
        video.style.maxWidth = "100%";
        stage.appendChild(video);
        const cc = data.class_counts || {};
        resultText.textContent = "프레임 기준 탐지 합계 " + data.count + "건 · wood " + (cc.wood || 0) + " / box " + (cc.box || 0) + " / pet " + (cc.pet || 0);
      }
    } catch (error) {
      resultText.textContent = error.message;
    } finally {
      runButton.disabled = false;
      runButton.textContent = "AI 탐지 실행";
    }
  });
});
