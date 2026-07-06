from flask import Flask, request, jsonify, Response
import os
import cv2
import numpy as np
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
from wildlife_agent import run_wildlife_agent

warnings.filterwarnings("ignore")
from reportlab.pdfgen import canvas

from stripe_match import identify_tiger
from predict import predict_image

from ai_assistant import (
    ai_chat_answer,
    ai_decision_support,
    generate_camera_ai_summary,
    generate_photo_detection_analysis,
    generate_video_detection_analysis,
    check_ai_status
)

try:
    from ai_assistant import generate_final_report_ai_summary
except Exception:
    def generate_final_report_ai_summary(result, frames, tiger_frames, nontiger_frames):
        return ai_decision_support(
            result,
            "Final Report",
            f"Frames checked: {frames}, Tiger frames: {tiger_frames}, NonTiger frames: {nontiger_frames}"
        )

from database import (
    signup_user,
    login_user,
    change_password,
    save_detection,
    get_history,
    get_stats,
    get_user_stats
)

from server.config import (
    UPLOAD_FOLDER,
    SAVED_TIGER_FOLDER,
    CAPTURED_FRAMES_FOLDER,
    REPORT_FOLDER,
    GRAPH_FOLDER,
    PDF_FOLDER,
    TEMP_FRAMES_FOLDER
)

from server.camera_manager import (
    start_camera,
    stop_camera,
    get_camera_status,
    get_latest_frame,
    final_tiger_detection
)

from server.health_service import get_server_health
from server.storage_service import delete_old_files
from server.alert_service import read_alerts

from sighting_manager import (
    get_recent_sightings,
    get_sightings_by_camera,
    get_sighting_by_id,
    get_sighting_stats,
    clear_sightings,
    format_sightings_text,
    format_stats_text
)


app = Flask(__name__)


def ensure_folders():
    for folder in [
        UPLOAD_FOLDER,
        SAVED_TIGER_FOLDER,
        CAPTURED_FRAMES_FOLDER,
        REPORT_FOLDER,
        GRAPH_FOLDER,
        PDF_FOLDER,
        TEMP_FRAMES_FOLDER
    ]:
        os.makedirs(folder, exist_ok=True)


ensure_folders()


@app.route("/")
def home():
    return "Tiger Detection Server Running"


def process_detection(file_path):
    current_time = datetime.now().strftime("%d-%m-%Y | %I:%M %p")

    result = predict_image(file_path)[0]

    if result == "Tiger":
        tiger_status = identify_tiger(file_path)

        return {
            "result": "Tiger Detected",
            "message": tiger_status,
            "time": current_time
        }

    return {
        "result": "No Tiger Detected",
        "message": "No tiger found",
        "time": current_time
    }


def convert_camera_url(camera_url):
    if camera_url is None or str(camera_url).strip() == "":
        return 0

    camera_url = str(camera_url).strip()

    if camera_url.isdigit():
        return int(camera_url)

    return camera_url


def save_tiger_image(image_path):
    os.makedirs(SAVED_TIGER_FOLDER, exist_ok=True)

    time_name = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    save_path = os.path.join(SAVED_TIGER_FOLDER, f"tiger_{time_name}.jpg")

    image = cv2.imread(image_path)

    if image is not None:
        cv2.imwrite(save_path, image)

    return save_path


def generate_frames(camera_id="CAM_1"):
    while True:
        frame = get_latest_frame(camera_id)

        if frame is None:
            frame = 255 * np.ones((480, 640, 3), dtype=np.uint8)
            cv2.putText(
                frame,
                f"Start {camera_id}",
                (180, 240),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

        ret, buffer = cv2.imencode(".jpg", frame)

        if not ret:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buffer.tobytes()
            + b"\r\n"
        )


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames("CAM_1"),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/video_feed/<camera_id>")
def video_feed_camera(camera_id):
    return Response(
        generate_frames(camera_id),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/snapshot/<camera_id>")
def snapshot(camera_id):
    frame = get_latest_frame(camera_id)

    if frame is None:
        frame = 255 * np.ones((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame, f"Start {camera_id}", (180, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    ret, buffer = cv2.imencode(".jpg", frame)

    if not ret:
        return "Frame error"

    response = Response(buffer.tobytes(), mimetype="image/jpeg")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/start_camera", methods=["POST"])
def start_camera_route():
    camera_id = request.form.get("camera_id", "CAM_1")
    camera_url = convert_camera_url(request.form.get("camera_url", "0"))
    message = start_camera(camera_id, camera_url)

    return jsonify({"success": True, "message": message, "camera_id": camera_id})


@app.route("/stop_camera", methods=["POST"])
def stop_camera_route():
    camera_id = request.form.get("camera_id", "CAM_1")
    message = stop_camera(camera_id)

    return jsonify({"success": True, "message": message, "camera_id": camera_id})


@app.route("/start_multi_camera", methods=["POST"])
def start_multi_camera_route():
    cameras = {
        "CAM_1": request.form.get("cam1", "0"),
        "CAM_2": request.form.get("cam2", ""),
        "CAM_3": request.form.get("cam3", ""),
        "CAM_4": request.form.get("cam4", "")
    }

    messages = {}

    for camera_id, camera_url in cameras.items():
        if camera_url is not None and str(camera_url).strip() != "":
            messages[camera_id] = start_camera(camera_id, convert_camera_url(camera_url))

    return jsonify({"success": True, "messages": messages})


@app.route("/stop_multi_camera", methods=["POST"])
def stop_multi_camera_route():
    messages = {}

    for camera_id in ["CAM_1", "CAM_2", "CAM_3", "CAM_4"]:
        messages[camera_id] = stop_camera(camera_id)

    return jsonify({"success": True, "messages": messages})


@app.route("/camera_status", methods=["GET"])
def camera_status_route():
    return jsonify(get_camera_status())


@app.route("/server_health", methods=["GET"])
def server_health_route():
    return jsonify(get_server_health())


@app.route("/cleanup_storage", methods=["GET"])
def cleanup_storage_route():
    result1 = delete_old_files(TEMP_FRAMES_FOLDER, hours=24)
    result2 = delete_old_files(CAPTURED_FRAMES_FOLDER, hours=24)
    result3 = delete_old_files(UPLOAD_FOLDER, hours=24)

    return jsonify({
        "success": True,
        "temp_frames": result1,
        "captured_frames": result2,
        "uploads": result3
    })


@app.route("/alerts", methods=["GET"])
def alerts_route():
    return read_alerts()


@app.route("/clear_alerts", methods=["POST"])
def clear_alerts_route():
    with open("alerts_log.txt", "w") as file:
        file.write("")
    return "Alerts cleared successfully"


@app.route("/api", methods=["POST"])
def api():
    action = request.form.get("action")

    if action == "signup":
        return signup_user(request.form.get("email"), request.form.get("password"))

    elif action == "login":
        return login_user(request.form.get("email"), request.form.get("password"))

    elif action == "change_password":
        email = request.form.get("email")
        password_data = request.form.get("password", "")

        if "," not in password_data:
            return jsonify({"success": False, "message": "Old and new password required"})

        old_password, new_password = password_data.split(",", 1)
        return change_password(email, old_password, new_password)

    elif action == "detect_photo":
        if "file" not in request.files:
            return jsonify({"result": "No image file received"})

        file = request.files["file"]
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        output = process_detection(file_path)

        saved_path = ""

        if output["result"] == "Tiger Detected":
            saved_path = save_tiger_image(file_path)

        camera_id = request.form.get("camera_id", "CAM_1")

        # FIX: wrap in try/except so agent crash never kills the response
        try:
            agent_result = run_wildlife_agent(
                source_type="Photo",
                result=output["result"],
                message=output["message"],
                file_name=file.filename,
                image_path=saved_path,
                camera_id=camera_id
            )
            # FIX: use correct keys returned by run_wildlife_agent
            output["agent_plan"] = agent_result.get("summary", "")
            output["agent_execution"] = agent_result.get("full_report", "")
            output["ai_report"] = agent_result.get("ai_summary", "")
            # Sighting Intelligence: field-note style story + AI classification
            output["sighting_story"] = agent_result.get("sighting_story", "")
            output["sighting_classification"] = agent_result.get("sighting_classification", {})
            output["identification"] = agent_result.get("sighting_entry", {}).get("identification", "")
        except Exception as e:
            print("Agent error (photo):", e)
            output["agent_plan"] = ""
            output["agent_execution"] = ""
            output["ai_report"] = ""
            output["sighting_story"] = ""
            output["sighting_classification"] = {}
            output["identification"] = ""

        ai_text = ai_decision_support(
            output["result"],
            "Photo Upload",
            output.get("message", "")
        )

        output["ai_decision"] = ai_text
        output["saved_image"] = saved_path

        save_detection(
            username="admin",
            source_type="Photo",
            file_name=file.filename,
            result=output["result"],
            confidence=0,
            image_path=saved_path
        )

        return jsonify(output)

    elif action == "detect_video":
        if "file" not in request.files:
            return jsonify({"result": "No video file received"})

        file = request.files["file"]
        video_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(video_path)

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return jsonify({"result": "Video could not be opened"})

        frame_count = 0
        checked_frames = 0
        tiger_frames = 0
        nontiger_frames = 0
        best_frame_path = ""

        tiger_detected_once = False
        last_result = "None"

        while True:
            success, frame = cap.read()

            if not success:
                break

            frame_count += 1

            if frame_count <= 10 or frame_count % 5 == 0:
                checked_frames += 1

                result = final_tiger_detection(frame, "VIDEO")
                print("VIDEO FRAME RESULT:", result)

                # FIX: accept both "Tiger" and "Tiger Detected" from final_tiger_detection
                if result == "Tiger" or result == "Tiger Detected":
                    tiger_frames += 1
                    tiger_detected_once = True
                    last_result = "Tiger Detected"

                    if best_frame_path == "":
                        temp_path = os.path.join(CAPTURED_FRAMES_FOLDER, "video_best_frame.jpg")
                        cv2.imwrite(temp_path, frame)
                        best_frame_path = save_tiger_image(temp_path)

                else:
                    nontiger_frames += 1

                    if tiger_detected_once:
                        last_result = "Tiger Detected"
                    else:
                        last_result = "No Tiger Detected"

        cap.release()

        final_result = last_result

        if final_result == "None":
            final_result = "No Tiger Detected"

        text_report_path = create_video_report(final_result, checked_frames, tiger_frames, nontiger_frames)
        graph_path = create_video_graph(tiger_frames, nontiger_frames)
        pdf_path = create_pdf_report(final_result, checked_frames, tiger_frames, nontiger_frames, graph_path)

        ai_text = ai_decision_support(
            final_result,
            "Video Upload",
            "Frames checked: "
            + str(checked_frames)
            + ", Tiger frames: "
            + str(tiger_frames)
            + ", NonTiger frames: "
            + str(nontiger_frames)
        )

        final_report_ai = generate_final_report_ai_summary(
            final_result,
            checked_frames,
            tiger_frames,
            nontiger_frames
        )

        # FIX: run wildlife agent for video (was completely missing before)
        agent_summary = ""
        agent_full_report = ""
        agent_ai_summary = ""
        agent_sighting_story = ""
        agent_sighting_classification = {}
        agent_identification = ""

        try:
            confidence_val = round((tiger_frames / checked_frames * 100), 2) if checked_frames > 0 else 0
            agent_result = run_wildlife_agent(
                source_type="Video",
                result=final_result,
                file_name=file.filename,
                image_path=best_frame_path,
                frames_checked=checked_frames,
                tiger_frames=tiger_frames,
                nontiger_frames=nontiger_frames,
                confidence=confidence_val
            )
            agent_summary = agent_result.get("summary", "")
            agent_full_report = agent_result.get("full_report", "")
            agent_ai_summary = agent_result.get("ai_summary", "")
            agent_sighting_story = agent_result.get("sighting_story", "")
            agent_sighting_classification = agent_result.get("sighting_classification", {})
            agent_identification = agent_result.get("sighting_entry", {}).get("identification", "")
        except Exception as e:
            print("Agent error (video):", e)
            agent_sighting_story = ""
            agent_sighting_classification = {}
            agent_identification = ""

        save_detection(
            username="admin",
            source_type="Video",
            file_name=file.filename,
            result=final_result,
            confidence=0,
            image_path=pdf_path
        )

        return jsonify({
            "status": "Completed",
            "result": final_result,
            "last_result": final_result,
            "frames_checked": checked_frames,
            "tiger_frames": tiger_frames,
            "nontiger_frames": nontiger_frames,
            "saved_image": best_frame_path,
            "text_report": text_report_path,
            "pdf_report": pdf_path,
            "ai_decision": ai_text,
            "final_report_ai": final_report_ai,
            # FIX: these fields are now included in video response
            "agent_plan": agent_summary,
            "agent_execution": agent_full_report,
            "ai_report": agent_ai_summary,
            "sighting_story": agent_sighting_story,
            "sighting_classification": agent_sighting_classification,
            "identification": agent_identification,
            "time": datetime.now().strftime("%d-%m-%Y %I:%M %p")
        })

    elif action == "live_camera":
        return jsonify({"success": True, "message": "Use /start_camera and /snapshot/CAM_1 for live camera preview"})

    elif action == "history":
        return get_history()

    elif action == "stats":
        return get_stats()

    elif action == "user_stats":
        return get_user_stats(request.form.get("username"))

    elif action == "start_cctv_server":
        camera_id = request.form.get("camera_id", "CAM_1")
        camera_url = convert_camera_url(request.form.get("camera_url", "0"))
        message = start_camera(camera_id, camera_url)
        return jsonify({"success": True, "message": message})

    elif action == "stop_cctv_server":
        camera_id = request.form.get("camera_id", "CAM_1")
        message = stop_camera(camera_id)
        return jsonify({"success": True, "message": message})

    elif action == "camera_status":
        return jsonify(get_camera_status())

    elif action == "server_health":
        return jsonify(get_server_health())

    elif action == "cleanup_storage":
        result1 = delete_old_files(TEMP_FRAMES_FOLDER, hours=24)
        result2 = delete_old_files(CAPTURED_FRAMES_FOLDER, hours=24)
        result3 = delete_old_files(UPLOAD_FOLDER, hours=24)

        return jsonify({
            "success": True,
            "temp_frames": result1,
            "captured_frames": result2,
            "uploads": result3
        })

    elif action == "alerts":
        return read_alerts()

    elif action == "sightings":
        camera_id = request.form.get("camera_id", "")
        limit = request.form.get("limit", "20")

        try:
            limit = int(limit)
        except ValueError:
            limit = 20

        if camera_id:
            sightings = get_sightings_by_camera(camera_id, limit=limit)
        else:
            sightings = get_recent_sightings(limit=limit)

        return format_sightings_text(sightings)

    elif action == "sighting_stats":
        return format_stats_text(get_sighting_stats())

    elif action == "clear_sightings":
        return clear_sightings()

    else:
        return jsonify({"success": False, "message": "Invalid action"})


def create_video_report(final_result, checked_frames, tiger_frames, nontiger_frames):
    time_name = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(REPORT_FOLDER, "report_" + time_name + ".txt")

    with open(report_path, "w") as f:
        f.write("Tiger Detection Video Report\n")
        f.write("----------------------------\n")
        f.write("Date Time: " + time_name + "\n")
        f.write("Result: " + final_result + "\n")
        f.write("Frames Checked: " + str(checked_frames) + "\n")
        f.write("Tiger Frames: " + str(tiger_frames) + "\n")
        f.write("NonTiger Frames: " + str(nontiger_frames) + "\n")
        f.write("Saved Tiger Screenshots: " + str(tiger_frames) + "\n")

    with open("report.txt", "w") as f:
        f.write("Latest Text Report: " + report_path)

    return report_path


def create_video_graph(tiger_frames, nontiger_frames):
    graph_path = os.path.join(GRAPH_FOLDER, "video_result_graph.png")

    labels = ["Tiger Frames", "NonTiger Frames"]
    values = [tiger_frames, nontiger_frames]

    plt.figure()
    plt.bar(labels, values)
    plt.title("Video Detection Result")
    plt.ylabel("Number of Frames")
    plt.savefig(graph_path)
    plt.close()

    return graph_path


def create_pdf_report(final_result, checked_frames, tiger_frames, nontiger_frames, graph_path):
    time_name = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = os.path.join(PDF_FOLDER, "report_" + time_name + ".pdf")

    c = canvas.Canvas(pdf_path)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, 780, "Tiger Detection Report")

    c.setFont("Helvetica", 12)
    c.drawString(100, 730, "Date Time: " + time_name)
    c.drawString(100, 700, "Result: " + final_result)
    c.drawString(100, 670, "Frames Checked: " + str(checked_frames))
    c.drawString(100, 640, "Tiger Frames: " + str(tiger_frames))
    c.drawString(100, 610, "NonTiger Frames: " + str(nontiger_frames))
    c.drawString(100, 580, "Saved Tiger Screenshots: " + str(tiger_frames))

    if os.path.exists(graph_path):
        c.drawImage(graph_path, 100, 300, width=350, height=220)

    c.save()
    return pdf_path


@app.route("/sightings", methods=["GET"])
def sightings_route():
    """
    Returns the structured sighting log as plain text (matches /history, /stats style).
    Optional query params:
      - camera_id: filter by a specific camera
      - limit: max number of entries (default 20)
    """
    camera_id = request.args.get("camera_id", "")
    limit = request.args.get("limit", "20")

    try:
        limit = int(limit)
    except ValueError:
        limit = 20

    if camera_id:
        sightings = get_sightings_by_camera(camera_id, limit=limit)
    else:
        sightings = get_recent_sightings(limit=limit)

    return format_sightings_text(sightings)


@app.route("/sightings/<sighting_id>", methods=["GET"])
def sighting_detail_route(sighting_id):
    sighting = get_sighting_by_id(sighting_id)

    if sighting is None:
        return "Sighting not found"

    return format_sightings_text([sighting])


@app.route("/sighting_stats", methods=["GET"])
def sighting_stats_route():
    return format_stats_text(get_sighting_stats())


@app.route("/clear_sightings", methods=["POST"])
def clear_sightings_route():
    return clear_sightings()


@app.route("/ai_status", methods=["GET"])
def ai_status_route():
    """
    Quick way to check whether the AI (Ollama/Llama) layer is actually
    live, without running the Java frontend or triggering a detection.
    Hit this directly: GET http://127.0.0.1:5000/ai_status
    """
    status = check_ai_status()

    if status["connected"]:
        return (
            "AI STATUS: CONNECTED\n"
            f"Model: {status['model']}\n"
            f"Sample Reply: {status['sample_reply']}\n"
            "\nReal Llama responses are being used across the app."
        )

    return (
        "AI STATUS: NOT CONNECTED\n"
        f"Model: {status['model']}\n"
        f"Reason: {status['error']}\n"
        "\nThe app is currently using rule-based FALLBACK text for all "
        "AI Summary / Suggestion / Decision / Sighting Story fields. "
        "Fallback text is the fixed wording hard-coded in ai_assistant.py "
        "(e.g. 'Continue routine monitoring', 'DECISION: Continue routine "
        "monitoring...') — if you see that exact phrasing repeat identically "
        "across different detections, that confirms fallback mode."
    )


@app.route("/ai_chat", methods=["POST"])
def ai_chat():
    return ai_chat_answer(request.form.get("question", ""))


@app.route("/ai_decision", methods=["POST"])
def ai_decision():
    result = request.form.get("result", "")
    camera_id = request.form.get("camera_id", "System")
    message = request.form.get("message", "")
    return ai_decision_support(result, camera_id, message)


@app.route("/camera_ai_summary", methods=["POST"])
def camera_ai_summary():
    camera_id = request.form.get("camera_id", "")
    status = request.form.get("status", "")
    result = request.form.get("result", "")
    frames = request.form.get("frames", "")
    same_tiger = request.form.get("same_tiger", "")

    return generate_camera_ai_summary(
        camera_id=camera_id,
        status=status,
        result=result,
        frames=frames,
        same_tiger=same_tiger
    )


@app.route("/final_report_ai", methods=["POST"])
def final_report_ai():
    result = request.form.get("result", "")
    frames = request.form.get("frames", "0")
    tiger_frames = request.form.get("tiger_frames", "0")
    nontiger_frames = request.form.get("nontiger_frames", "0")

    return generate_final_report_ai_summary(
        result,
        frames,
        tiger_frames,
        nontiger_frames
    )


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        threaded=True,
        use_reloader=False
    )