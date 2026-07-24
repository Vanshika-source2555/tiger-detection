import cv2
import os
import time
import threading
from datetime import datetime

from server.config import (
    TEMP_FRAMES_FOLDER,
    SAVED_TIGER_FOLDER,
    CAPTURED_FRAMES_FOLDER,
    FRAME_INTERVAL_SECONDS
)

from server.detector_service import detect_tiger
from server.alert_service import create_alert
from database import save_detection
from ai_assistant import generate_sighting_story, classify_sighting
from sighting_manager import add_sighting
from stripe_match import identify_tiger

camera_threads = {}
camera_status = {}
latest_frames = {}

ALERT_COOLDOWN_SECONDS = 10


def save_frame(frame, folder, camera_id):
    os.makedirs(folder, exist_ok=True)

    file_name = f"{camera_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
    file_path = os.path.join(folder, file_name)

    cv2.imwrite(file_path, frame)
    return file_path


def open_camera(camera_url):
    camera_url = str(camera_url).strip()

    if camera_url.isdigit():
        cap = cv2.VideoCapture(int(camera_url), cv2.CAP_DSHOW)

    elif os.path.exists(camera_url):
        cap = cv2.VideoCapture(camera_url)

    else:
        cap = cv2.VideoCapture(camera_url)

    # Reduce camera buffering
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    # Optional: Lower resolution for smoother processing
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    return cap


def detect_tiger_full_frame(frame, camera_id):
    frame_path = os.path.join(
    TEMP_FRAMES_FOLDER,
    camera_id + "_full.jpg"
)

    cv2.imwrite(frame_path, frame)
    prediction = detect_tiger(frame_path)

    print("Full Frame Prediction:", prediction)

    if prediction["result"] == "Tiger":
        return "Tiger"

    return "No Tiger Detected"


def detect_tiger_multi_crop(frame, camera_id):
    h, w, _ = frame.shape

    crops = [
        frame,
        frame[h // 4: 3 * h // 4, w // 4: 3 * w // 4],
        frame[h // 4: 3 * h // 4, 0: w // 2],
        frame[h // 4: 3 * h // 4, w // 2: w],
        frame[h // 2: h, 0: w // 2],
        frame[h // 2: h, w // 2: w],
        frame[0: h // 2, 0: w // 2],
        frame[0: h // 2, w // 2: w]
    ]

    for i, crop in enumerate(crops):
        if crop is None or crop.size == 0:
            continue

        crop_path = os.path.join(
    TEMP_FRAMES_FOLDER,
    f"{camera_id}_crop_{i}.jpg"
)

        cv2.imwrite(crop_path, crop)

        prediction = detect_tiger(crop_path)

        print("Crop", i, "Prediction:", prediction)

        if prediction["result"] == "Tiger":
            return "Tiger"

    return "No Tiger Detected"


def final_tiger_detection(frame, camera_id):
    full_result = detect_tiger_full_frame(frame, camera_id)

    if full_result == "Tiger":
        return "Tiger"

    crop_result = detect_tiger_multi_crop(frame, camera_id)

    if crop_result == "Tiger":
        return "Tiger"

    return "No Tiger Detected"


def process_tiger_sighting(camera_id, frame, checked_frames, tiger_frame_count):
    """
    Called once per alert cooldown window when a tiger is confirmed live.

    - Saves the frame
    - Identifies whether this is a NEW tiger or the SAME tiger seen before
      (stripe matching via stripe_match.identify_tiger)
    - Generates an AI field-note "sighting story" + AI classification
      (activity / risk / time-of-day)
    - Updates camera_status so the result area reflects it immediately
    - Writes a structured entry to sightings_log.json
    - Fires the existing alert + detection-history save

    Returns the saved image path.
    """
    saved_path = save_frame(frame, SAVED_TIGER_FOLDER, camera_id)

    identification = identify_tiger(saved_path)  # "New Tiger Recorded" / "Same Tiger Seen Again"

    story = generate_sighting_story(
        camera_id=camera_id,
        source_type="Live Camera",
        result="Tiger Detected",
        confidence=0,
        message=identification,
        tiger_id_status=identification
    )

    classification = classify_sighting(
        camera_id=camera_id,
        result="Tiger Detected",
        confidence=0,
        frames_checked=checked_frames,
        tiger_frames=tiger_frame_count
    )

    camera_status[camera_id]["identification"] = identification
    camera_status[camera_id]["sighting_story"] = story
    camera_status[camera_id]["activity"] = classification.get("activity", "Unknown")
    camera_status[camera_id]["risk"] = classification.get("risk", "Medium")
    camera_status[camera_id]["time_context"] = classification.get("time_context", "Unknown")

    add_sighting({
        "camera_id": camera_id,
        "source_type": "Live Camera",
        "username": "admin",
        "result": "Tiger Detected",
        "confidence": 0,
        "identification": identification,
        "image_path": saved_path,
        "file_name": camera_id,
        "story": story,
        "activity": classification.get("activity", "Unknown"),
        "risk": classification.get("risk", "Medium"),
        "time_context": classification.get("time_context", "Unknown")
    })

    create_alert(
        camera_id=camera_id,
        confidence=0,
        image_path=saved_path
    )

    save_detection(
        username="admin",
        source_type="Live Camera",
        file_name=camera_id,
        result="Tiger Detected",
        confidence=0,
        image_path=saved_path
    )

    return saved_path


def camera_worker(camera_id, camera_url):
    camera_status[camera_id] = {
        "status": "Starting",
        "source": str(camera_url),
        "last_result": "None",
        "frames_checked": 0,
        "last_alert_time": "No alert yet",
        "ai_summary": "Monitoring not started yet.",
        "ai_suggestion": "Start camera to begin live tiger detection.",
        "ai_decision": "User should monitor the result.",
        "identification": "No Tiger Yet",
        "sighting_story": "No tiger detected yet. Live monitoring active.",
        "activity": "Idle",
        "risk": "Low",
        "time_context": "Live"
    }

    cap = open_camera(camera_url)

    if not cap.isOpened():
        camera_status[camera_id]["status"] = "Offline"
        camera_status[camera_id]["last_result"] = "Camera Offline"
        camera_status[camera_id]["ai_summary"] = "Camera could not be opened."
        camera_status[camera_id]["ai_suggestion"] = "Check camera source, permissions, IP/RTSP URL, and backend logs."
        camera_status[camera_id]["ai_decision"] = "Restart camera after fixing the source."
        print(camera_id, "camera could not open:", camera_url)
        return

    camera_status[camera_id]["status"] = "Online"
    camera_status[camera_id]["ai_summary"] = "Live monitoring is active."
    camera_status[camera_id]["ai_suggestion"] = "Continue monitoring camera feed."
    camera_status[camera_id]["ai_decision"] = "No action required right now."

    last_processed_time = 0
    last_alert_time = 0
    checked_frames = 0
    tiger_frame_count = 0

    while camera_status[camera_id]["status"] == "Online":
        success, frame = cap.read()

        if not success:
            if isinstance(camera_url, str) and os.path.exists(camera_url):
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                success, frame = cap.read()

            if not success:
                camera_status[camera_id]["status"] = "Disconnected"
                camera_status[camera_id]["last_result"] = "Camera Disconnected"
                camera_status[camera_id]["ai_summary"] = "Camera stream disconnected."
                camera_status[camera_id]["ai_suggestion"] = "Check camera connection, source URL, and restart the camera."
                camera_status[camera_id]["ai_decision"] = "User should verify the camera source."
                print(camera_id, "disconnected")
                break

        latest_frames[camera_id] = frame.copy()
        current_time = time.time()

        if current_time - last_processed_time >= FRAME_INTERVAL_SECONDS:
            last_processed_time = current_time

            captured_path = save_frame(frame, CAPTURED_FRAMES_FOLDER, camera_id)

            checked_frames += 1
            camera_status[camera_id]["frames_checked"] = checked_frames

            print("Frame checked:", camera_id, captured_path)

            try:
                result = final_tiger_detection(frame, camera_id)
                print("Final Result:", camera_id, result)

            except Exception as e:
                print("Detection error:", camera_id, e)
                result = "Error"

            if result == "Tiger":
                tiger_frame_count += 1
                camera_status[camera_id]["last_result"] = "Tiger Detected"
                camera_status[camera_id]["ai_summary"] = "Tiger detected successfully."
                camera_status[camera_id]["ai_suggestion"] = "Review saved image and check nearby cameras."
                camera_status[camera_id]["ai_decision"] = "Continue monitoring. Final action should be taken by user."

                if current_time - last_alert_time >= ALERT_COOLDOWN_SECONDS:
                    last_alert_time = current_time
                    camera_status[camera_id]["last_alert_time"] = str(datetime.now())

                    try:
                        process_tiger_sighting(camera_id, frame, checked_frames, tiger_frame_count)
                        print(camera_id, "Tiger Detected - Sighting Saved (with AI story + identification)")
                    except Exception as e:
                        print("Sighting processing error:", camera_id, e)

            elif result == "No Tiger Detected":
                # Do not overwrite Tiger Detected once it happened this session
                if camera_status[camera_id].get("last_result") != "Tiger Detected":
                    camera_status[camera_id]["last_result"] = "No Tiger Detected"
                    camera_status[camera_id]["ai_summary"] = "No tiger detected in the current frame."
                    camera_status[camera_id]["ai_suggestion"] = "Continue monitoring."
                    camera_status[camera_id]["ai_decision"] = "No immediate action required."
                    camera_status[camera_id]["identification"] = "No Tiger Currently"
                    camera_status[camera_id]["sighting_story"] = (
                        "No tiger detected in the current frame. Monitoring remains active."
                    )
                    camera_status[camera_id]["activity"] = "Idle"
                    camera_status[camera_id]["risk"] = "Low"
                    camera_status[camera_id]["time_context"] = "Live"

            else:
                camera_status[camera_id]["last_result"] = result
                camera_status[camera_id]["ai_summary"] = "Detection issue occurred."
                camera_status[camera_id]["ai_suggestion"] = "Check backend logs and model status."
                camera_status[camera_id]["ai_decision"] = "User should verify the system."

            print(
                camera_id,
                "Status:",
                camera_status[camera_id]["last_result"],
                "Frames:",
                checked_frames
            )

    cap.release()

    if camera_id in camera_status:
        camera_status[camera_id]["status"] = "Stopped"

        if camera_status[camera_id].get("last_result", "") in ["None", ""]:
            camera_status[camera_id]["last_result"] = "Stopped"

        camera_status[camera_id]["ai_summary"] = camera_status[camera_id].get(
            "ai_summary",
            "Camera stopped."
        )

        camera_status[camera_id]["ai_suggestion"] = camera_status[camera_id].get(
            "ai_suggestion",
            "Review last result."
        )

        camera_status[camera_id]["ai_decision"] = camera_status[camera_id].get(
            "ai_decision",
            "User should verify final result."
        )


def start_camera(camera_id, camera_url):
    if camera_id in camera_status:
        camera_status[camera_id]["status"] = "Stopped"
        time.sleep(1)

    thread = threading.Thread(
        target=camera_worker,
        args=(camera_id, camera_url),
        daemon=True
    )

    camera_threads[camera_id] = thread
    thread.start()

    return f"{camera_id} started"


def stop_camera(camera_id):
    if camera_id not in camera_status:
        return f"{camera_id} not found"

    camera_status[camera_id]["status"] = "Stopped"

    if camera_status[camera_id].get("last_result", "") in ["", "None"]:
        camera_status[camera_id]["last_result"] = "Stopped"

    if camera_status[camera_id].get("ai_summary", "") == "":
        camera_status[camera_id]["ai_summary"] = "Camera stopped."

    if camera_status[camera_id].get("ai_suggestion", "") == "":
        camera_status[camera_id]["ai_suggestion"] = "Review last camera result."

    if camera_status[camera_id].get("ai_decision", "") == "":
        camera_status[camera_id]["ai_decision"] = "User should verify final status."

    if camera_id in latest_frames:
        del latest_frames[camera_id]

    return f"{camera_id} stopped successfully"


def get_camera_status():
    return camera_status


def get_latest_frame(camera_id="CAM_1"):
    return latest_frames.get(camera_id)