from flask import Flask, render_template, Response, request, jsonify, send_from_directory
from pathlib import Path
import os
import requests
import uuid
import cv2

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

BASE_DIR = Path(__file__).resolve().parent
SITE_DIR = BASE_DIR.parent / "site"

app = Flask(
    __name__,
    template_folder=str(SITE_DIR / "html"),
    static_folder=str(SITE_DIR),
    static_url_path="/static",
)

CAMERAS = ("cam1", "cam2")
AI_SERVER_BASE = os.environ.get("AI_SERVER_BASE", "http://192.168.2.100:5000").rstrip("/")
HTTP_TIMEOUT = 3
MODEL_PATH = Path(os.environ.get("FALLEN_MODEL_PATH", BASE_DIR.parent / "models" / "best.pt"))
UPLOAD_DIR = BASE_DIR.parent / "runtime" / "uploads"
OUTPUT_DIR = BASE_DIR.parent / "runtime" / "outputs"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
_model = None


def _get_local_model():
    global _model
    if _model is None:
        if YOLO is None:
            raise RuntimeError("ultralytics가 설치되지 않았습니다.")
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"모델 파일이 없습니다: {MODEL_PATH}")
        _model = YOLO(str(MODEL_PATH))
    return _model



@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/control")
def control():
    return render_template("control.html")


@app.route("/history")
def history():
    return render_template("history.html")


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "ai_server": AI_SERVER_BASE,
    })


def _valid_camera(cam_id):
    return cam_id in CAMERAS


@app.route("/video_feed")
def video_feed():
    """Proxy the processed MJPEG stream from the remote Traffic AI server."""
    cam_id = request.args.get("cam_id", "cam1")
    if not _valid_camera(cam_id):
        return "unknown camera", 404

    upstream_url = f"{AI_SERVER_BASE}/video_feed"
    try:
        upstream = requests.get(
            upstream_url,
            params={"cam_id": cam_id},
            stream=True,
            timeout=(HTTP_TIMEOUT, None),
        )
        upstream.raise_for_status()
    except requests.RequestException as exc:
        return f"AI camera server unavailable: {exc}", 502

    content_type = upstream.headers.get(
        "Content-Type",
        "multipart/x-mixed-replace; boundary=frame",
    )

    def generate():
        try:
            for chunk in upstream.iter_content(chunk_size=64 * 1024):
                if chunk:
                    yield chunk
        finally:
            upstream.close()

    return Response(
        generate(),
        content_type=content_type,
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@app.route("/camera_status")
def camera_status():
    """Translate the remote AI server debug status into dashboard camera state."""
    try:
        response = requests.get(f"{AI_SERVER_BASE}/debug_status", timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        remote = response.json()
    except (requests.RequestException, ValueError):
        return jsonify({
            cam: {"connected": False, "last_seen_seconds": None}
            for cam in CAMERAS
        }), 200

    result = {}
    for cam in CAMERAS:
        info = remote.get(cam, {}) if isinstance(remote, dict) else {}
        # The AI server reports frame shapes after receiving/processing a frame.
        connected = bool(info.get("raw_shape") or info.get("normalized_shape"))
        result[cam] = {
            "connected": connected,
            "last_seen_seconds": None,
            "detections": info.get("detections", 0),
            "tracked": info.get("tracked", 0),
            "last_error": info.get("last_error", ""),
        }
    return jsonify(result)


@app.route("/event_history")
def event_history():
    """Proxy stored historical detection records from the remote AI server."""
    try:
        upstream = requests.get(
            f"{AI_SERVER_BASE}/event_history",
            params={"limit": request.args.get("limit", "100")},
            timeout=HTTP_TIMEOUT,
        )
        upstream.raise_for_status()
        return Response(
            upstream.content,
            status=upstream.status_code,
            content_type=upstream.headers.get("Content-Type", "application/json"),
        )
    except requests.RequestException as exc:
        return jsonify({"events": [], "count": 0, "error": str(exc)}), 502


@app.route("/event_media/<cam_id>/<media_type>/<path:filename>")
def event_media(cam_id, media_type, filename):
    """Proxy saved event images/videos from the remote Traffic AI server."""
    if not _valid_camera(cam_id) or media_type not in ("images", "videos"):
        return "invalid event media path", 400

    upstream_url = f"{AI_SERVER_BASE}/event_media/{cam_id}/{media_type}/{filename}"
    headers = {}
    if request.headers.get("Range"):
        headers["Range"] = request.headers["Range"]

    try:
        upstream = requests.get(
            upstream_url,
            headers=headers,
            stream=True,
            timeout=(HTTP_TIMEOUT, None),
        )
    except requests.RequestException as exc:
        return f"AI event media unavailable: {exc}", 502

    response_headers = {
        "Cache-Control": "no-store",
        "Accept-Ranges": upstream.headers.get("Accept-Ranges", "bytes"),
    }
    for name in ("Content-Length", "Content-Range"):
        if upstream.headers.get(name):
            response_headers[name] = upstream.headers[name]

    def generate():
        try:
            for chunk in upstream.iter_content(chunk_size=64 * 1024):
                if chunk:
                    yield chunk
        finally:
            upstream.close()

    return Response(
        generate(),
        status=upstream.status_code,
        content_type=upstream.headers.get("Content-Type", "application/octet-stream"),
        headers=response_headers,
    )


@app.route("/stream_alerts")
def stream_alerts():
    """Proxy real-time SSE alerts from the remote Traffic AI server."""
    try:
        upstream = requests.get(
            f"{AI_SERVER_BASE}/stream_alerts",
            stream=True,
            timeout=(HTTP_TIMEOUT, None),
            headers={"Accept": "text/event-stream"},
        )
        upstream.raise_for_status()
    except requests.RequestException as exc:
        return jsonify({"ok": False, "error": str(exc)}), 502

    def generate():
        try:
            for line in upstream.iter_lines(decode_unicode=True):
                if line is not None:
                    yield line + "\n"
        finally:
            upstream.close()

    return Response(
        generate(),
        content_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/ai_status")
def ai_status():
    """Expose the remote debug payload for dashboard diagnostics."""
    try:
        response = requests.get(f"{AI_SERVER_BASE}/debug_status", timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type", "application/json"),
        )
    except requests.RequestException as exc:
        return jsonify({"ok": False, "error": str(exc)}), 502


@app.route("/local_model_status")
def local_model_status():
    return jsonify({
        "ready": YOLO is not None and MODEL_PATH.exists(),
        "model_path": str(MODEL_PATH),
        "classes": ["wood", "box", "pet"],
    })


@app.route("/detect_media", methods=["POST"])
def detect_media():
    if "file" not in request.files or not request.files["file"].filename:
        return jsonify({"ok": False, "error": "사진 또는 영상 파일을 선택하세요."}), 400
    if YOLO is None:
        return jsonify({"ok": False, "error": "ultralytics가 설치되지 않았습니다."}), 503
    if not MODEL_PATH.exists():
        return jsonify({"ok": False, "error": f"models/best.pt가 필요합니다. 현재 경로: {MODEL_PATH}"}), 503

    uploaded = request.files["file"]
    suffix = Path(uploaded.filename).suffix.lower()
    allowed = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".mp4", ".avi", ".mov", ".mkv"}
    if suffix not in allowed:
        return jsonify({"ok": False, "error": "지원하지 않는 파일 형식입니다."}), 400

    token = uuid.uuid4().hex
    source = UPLOAD_DIR / f"{token}{suffix}"
    uploaded.save(source)
    conf = min(max(float(request.form.get("conf", "0.30")), 0.05), 0.95)
    model = _get_local_model()

    try:
        if suffix in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
            result = model.predict(source=str(source), conf=conf, imgsz=640, verbose=False)[0]
            output_name = f"{token}.jpg"
            output_path = OUTPUT_DIR / output_name
            cv2.imwrite(str(output_path), result.plot())
            detections = []
            for box in result.boxes:
                cls_id = int(box.cls[0].item())
                detections.append({"class": result.names[cls_id], "confidence": round(float(box.conf[0].item()), 3)})
            return jsonify({"ok": True, "kind": "image", "url": f"/local_output/{output_name}", "detections": detections, "count": len(detections)})

        cap = cv2.VideoCapture(str(source))
        if not cap.isOpened():
            raise RuntimeError("영상을 열 수 없습니다.")
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        output_name = f"{token}.mp4"
        output_path = OUTPUT_DIR / output_name
        writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
        total = 0
        class_counts = {"wood": 0, "box": 0, "pet": 0}
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            result = model.predict(source=frame, conf=conf, imgsz=640, verbose=False)[0]
            writer.write(result.plot())
            total += len(result.boxes)
            for box in result.boxes:
                name = result.names[int(box.cls[0].item())]
                if name in class_counts:
                    class_counts[name] += 1
        cap.release()
        writer.release()
        return jsonify({"ok": True, "kind": "video", "url": f"/local_output/{output_name}", "count": total, "class_counts": class_counts})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/local_output/<path:filename>")
def local_output(filename):
    return send_from_directory(OUTPUT_DIR, filename, conditional=True)


if __name__ == "__main__":
    print(f"Dashboard -> Traffic AI server: {AI_SERVER_BASE}")
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=True)
