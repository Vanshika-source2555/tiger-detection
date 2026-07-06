import os
import re
import openpyxl
import warnings
from dotenv import load_dotenv
import httpx
import ollama



QA_FILE = "qa_dataset.xlsx"



def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s_.]", " ", text)
    return text.strip()


def load_qa_dataset():
    data = []

    if not os.path.exists(QA_FILE):
        return data

    wb = openpyxl.load_workbook(QA_FILE, data_only=True)
    sheet = wb.active

    for row in sheet.iter_rows(min_row=3, values_only=True):
        if len(row) < 6:
            continue

        question = row[4]
        answer = row[5]

        if question and answer:
            data.append({
                "question": str(question),
                "answer": str(answer),
                "clean_question": clean_text(question)
            })

    return data


def dataset_answer(user_question):
    q = clean_text(user_question)
    words = set(q.split())

    best_score = 0
    best_answer = None

    for item in load_qa_dataset():
        dataset_words = set(item["clean_question"].split())
        score = len(words.intersection(dataset_words))

        if item["clean_question"] == q:
            score += 30

        if q in item["clean_question"]:
            score += 15

        if score > best_score:
            best_score = score
            best_answer = item["answer"]

    if best_score >= 2:
        return best_answer

    return None


def ollama_answer(question, system_prompt=None):
    try:
        if system_prompt is None:
            system_prompt = """

You are Tiger AI Assistant.

You are an intelligent AI assistant for the Tiger Detection Monitoring System.

Your job is to help users understand, operate, troubleshoot, and improve the complete wildlife monitoring system.

=========================
YOUR KNOWLEDGE AREAS
=========================

You can answer questions about:

----------------------------------------------------
1. Tiger Detection
----------------------------------------------------
- Tiger Detection
- Tiger Identification
- Tiger Recognition
- Tiger Classification
- Tiger Species
- Tiger Behaviour
- Tiger Movement
- Tiger Tracking
- Tiger Presence
- Tiger Activity
- Tiger Sighting
- Tiger Monitoring

----------------------------------------------------
2. Wildlife Monitoring
----------------------------------------------------
- Wildlife Monitoring
- Forest Surveillance
- Wildlife Conservation
- Protected Forest
- National Parks
- Animal Detection
- Animal Classification
- Animal Tracking
- Animal Behaviour
- Human-Wildlife Conflict
- Forest Safety

----------------------------------------------------
3. Computer Vision
----------------------------------------------------
- Object Detection
- Image Classification
- Image Segmentation
- Feature Extraction
- Bounding Boxes
- Confidence Score
- Non-Max Suppression
- Deep Learning Vision
- OpenCV
- Image Processing

----------------------------------------------------
4. MOdel Training & Evaluation
----------------------------------------------------

-  Model
- Model Training
- Model Validation
- Dataset Preparation
- Image Annotation
- Label Files
- Detection Accuracy
- Precision
- Recall
- mAP
- Inference
- Prediction

----------------------------------------------------
5. Llama & Ollama
----------------------------------------------------
- Llama
- Llama 3.2
- Ollama
- Local LLM
- Prompt Engineering
- AI Summary
- AI Suggestion
- AI Decision Support
- AI Reports
- AI Recommendations
- AI Reasoning

----------------------------------------------------
6. Images
----------------------------------------------------
- Uploaded Images
- Image Detection
- Saved Images
- Captured Frames
- Tiger Screenshots
- Latest Tiger Image
- Image Quality
- Image Resolution
- Image Formats

----------------------------------------------------
7. Videos
----------------------------------------------------
- Uploaded Videos
- Video Detection
- Video Processing
- Frame Extraction
- Frame Analysis
- FPS
- Video Preview
- Saved Video Results

----------------------------------------------------
8. Live Camera
----------------------------------------------------
- Live Camera
- Webcam
- CCTV
- IP Camera
- Camera Feed
- Camera Monitoring
- Camera Health
- Camera Status
- Camera Restart
- Camera Preview
- Camera Snapshot
- Camera Frames
- Live Detection

----------------------------------------------------
9. Same Tiger Identification
----------------------------------------------------
- Stripe Matching
- Stripe Comparison
- Same Tiger Detection
- Tiger Re-identification
- Similarity Score
- Feature Matching
- Visual Comparison

----------------------------------------------------
10. Alerts
----------------------------------------------------
- Alert System
- Popup Alerts
- Email Alerts
- Notifications
- Alarm
- Warning
- Emergency Alert
- Detection Alert

----------------------------------------------------
11. Reports
----------------------------------------------------
- PDF Reports
- Text Reports
- Detection Reports
- Summary Reports
- AI Reports
- Report Generation
- Report Download

----------------------------------------------------
12. Dashboard
----------------------------------------------------
- Dashboard
- Status Cards
- Result Panel
- Live Monitoring
- Camera Panels
- Dashboard Controls
- Analytics
- Statistics

----------------------------------------------------
13. Analytics
----------------------------------------------------
- Detection Count
- Tiger Count
- Camera Statistics
- Detection History
- Daily Report
- Weekly Report
- Monthly Report
- Graphs
- Charts

----------------------------------------------------
14. Dataset
----------------------------------------------------
- Dataset
- Dataset Collection
- Image Dataset
- Video Dataset
- YOLO Dataset
- Annotation
- LabelImg
- Dataset Augmentation
- Dataset Split

----------------------------------------------------
15. Machine Learning
----------------------------------------------------
- Artificial Intelligence
- Machine Learning
- Deep Learning
- CNN
- Neural Networks
- Transfer Learning
- Training
- Testing
- Validation
- Model Evaluation

----------------------------------------------------
16. Backend
----------------------------------------------------
- Flask
- Python
- REST API
- JSON
- HTTP Requests
- API Response
- API Endpoints
- Server
- Backend Processing

----------------------------------------------------
17. Frontend
----------------------------------------------------
- Java Swing
- Dashboard UI
- JTextArea
- JPanel
- JFrame
- Buttons
- Camera Window
- Preview
- Java Programming

----------------------------------------------------
18. Database & Storage
----------------------------------------------------
- Saved Images
- Saved Videos
- Reports Folder
- Logs
- JSON Files
- Storage
- Cleanup Storage
- File Management

----------------------------------------------------
19. System Features
----------------------------------------------------
- Login
- Registration
- Authentication
- Account
- User Profile
- Camera Control
- Analytics
- Alerts
- Reports
- Settings

----------------------------------------------------
20. Troubleshooting
----------------------------------------------------
- Flask Errors
- Python Errors
- Java Errors
- Camera Offline
- Camera Not Working
- API Errors
- JSON Errors
- YOLO Errors
- Ollama Errors
- Llama Errors
- Model Loading Errors
- Detection Failure
- Installation Problems

----------------------------------------------------
21. Project Documentation
----------------------------------------------------
- Project Architecture
- Project Workflow
- System Design
- Data Flow
- Technology Stack
- Advantages
- Limitations
- Future Scope
- Project Demonstration
- Viva Questions

----------------------------------------------------
22. Generative AI
----------------------------------------------------
- Generative AI
- Agentic AI
- LLM
- NLP
- Prompt Engineering
- AI Agents
- AI Assistant
- Chatbot
- AI Integration

----------------------------------------------------
23. Git & Development
----------------------------------------------------
- Git
- GitHub
- Version Control
- Branch
- Commit
- Push
- Pull
- Merge
- Repository

----------------------------------------------------
24. Deployment
----------------------------------------------------
- Windows
- Linux
- Docker
- Virtual Environment
- Requirements.txt
- Pip
- Python Packages

----------------------------------------------------
25. Performance
----------------------------------------------------
- Detection Speed
- FPS
- Optimization
- GPU
- CPU
- RAM Usage
- Processing Time
- Performance Improvement

=========================
HOW TO ANSWER
=========================

Always:

• Answer in simple English.
• Keep answers practical.
• Give step-by-step guidance when needed.
• Explain technical terms simply.
• Suggest solutions for errors.
• Recommend best practices.
• Mention possible causes before solutions.
• Use bullet points when useful.
• Never invent information.
• If unsure, clearly say you don't know.

You are a professional AI assistant dedicated to the Tiger Detection Monitoring System."""

        # ✅ FIX: Use explicit httpx client so the socket is properly
        #         closed after each call — stops the ResourceWarning:
        #         "unclosed <socket.socket ... raddr=('127.0.0.1', 11434)>"
        #
        # ⚠️ COMPATIBILITY NOTE: different versions of the `ollama` PyPI
        # package have changed whether ollama.Client() accepts a custom
        # `httpx_client=` kwarg. Some versions raise:
        #   TypeError: Client.__init__() got an unexpected keyword argument 'httpx_client'
        # so we try the explicit-client version first, and transparently
        # fall back to the plain client if that kwarg isn't supported.
        try:
            with httpx.Client() as http_client:
                client = ollama.Client(host="http://localhost:11434", httpx_client=http_client)
                response = client.chat(
                    model="llama3.2",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question}
                    ]
                )
        except TypeError as version_mismatch:
            print("OLLAMA CLIENT COMPAT FALLBACK (httpx_client kwarg unsupported):", version_mismatch)
            client = ollama.Client(host="http://localhost:11434")
            response = client.chat(
                model="llama3.2",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ]
            )

        return response["message"]["content"]

    except Exception as e:
        print("OLLAMA ERROR:", e)
        return None


def fallback_answer(question):

    q = question.lower()

    if "camera" in q:
        return """
Summary:
Camera monitoring checks the live camera feed.

Explanation:
The system continuously captures frames and performs tiger detection.

Suggestion:
Verify the camera connection and preview.

Decision:
Continue monitoring.
"""

    elif "video" in q:
        return """
Summary:
Video detection analyses uploaded videos frame by frame.

Explanation:
Each frame is checked for tiger presence.

Suggestion:
Use clear and stable videos.

Decision:
Review detected frames.
"""

    elif "image" in q or "photo" in q:
        return """
Summary:
Image detection checks a single uploaded image.

Explanation:
The AI identifies whether a tiger is present.

Suggestion:
Use high-quality images.

Decision:
Verify saved results.
"""

    elif "tiger" in q:
        return """
Summary:
Tiger detection completed.

Explanation:
The model searched for tiger features in the media.

Suggestion:
Review saved screenshots.

Decision:
Continue monitoring nearby cameras.
"""

    elif "error" in q:
        return """
Summary:
A system error occurred.

Explanation:
This may be due to Flask, camera, or model issues.

Suggestion:
Check backend logs and restart the server.

Decision:
Fix the error before continuing.
"""

    return """
Summary:
I can help with the Tiger Detection Monitoring System.

Explanation:
Ask me about cameras, videos, photos, reports, alerts, datasets, AI, YOLO, Llama, Flask, Java, GitHub, analytics, troubleshooting, and project documentation.

Suggestion:
Ask a specific question.

Decision:
Ready to assist.
"""


def ai_chat_answer(question):

    # Priority 1: Llama 3.2
    answer = ollama_answer(question)

    if answer:
        return answer

    # Priority 2: Dataset
    answer = dataset_answer(question)

    if answer:
        return answer

    # Priority 3: Rule based fallback
    return fallback_answer(question)

def local_camera_ai_summary(camera_id, status, result, frames, same_tiger=""):
    r = (result or "").lower()
    s = (status or "").lower()

    if "tiger" in r and "no tiger" not in r:
        return (
            "AI Summary:\n"
            f"Tiger activity detected on {camera_id}.\n\n"
            "AI Suggestion:\n"
            "Review saved image and check nearby cameras.\n\n"
            "AI Decision Support:\n"
            "Important detection. User should verify and continue monitoring."
        )

    if "no tiger" in r:
        return (
            "AI Summary:\n"
            f"No tiger activity detected on {camera_id}.\n\n"
            "AI Suggestion:\n"
            "Continue monitoring.\n\n"
            "AI Decision Support:\n"
            "No immediate action required."
        )

    if "offline" in r or "disconnect" in r or "offline" in s:
        return (
            "AI Summary:\n"
            "Camera feed is unavailable.\n\n"
            "AI Suggestion:\n"
            "Check camera source, network, and restart camera.\n\n"
            "AI Decision Support:\n"
            "Restore camera connection before relying on monitoring."
        )

    return (
        "AI Summary:\n"
        "Camera status reviewed.\n\n"
        "AI Suggestion:\n"
        "Continue monitoring.\n\n"
        "AI Decision Support:\n"
        "User should verify final action."
    )


def generate_camera_ai_summary(camera_id, status, result, frames, same_tiger=""):
    
    print("ENTERED generate_camera_ai_summary")
    print("OLLAMA:", "FOUND" if ollama else "MISSING")

    if not ollama:
        print("USING LOCAL AI: OLLAMA missing")
        return local_camera_ai_summary(camera_id, status, result, frames, same_tiger)

    try:
        print("USING OLLAMA AI for", camera_id)

        prompt = f"""
You are an AI Wildlife Monitoring Assistant.

Analyze the following detection result.

Camera ID: {camera_id}
Camera Status: {status}
Detection Result: {result}
Frames Checked: {frames}
Same Tiger Status: {same_tiger}

Generate ONLY the following format.

AI Summary:
(2-3 lines describing what happened.)

AI Suggestion:
(Practical recommendation for the forest officer.)

AI Decision Support:
(Explain whether immediate action is needed.)

Risk Level:
(Low / Medium / High)

Confidence:
(High / Medium / Low)

Recommended Action:
(One short action.)

Keep the response below 120 words.
Do not use markdown.
Do not add introductions.
"""

        response = ollama_answer(prompt)

        print("OLLAMA RESPONSE:", response)

        return response

    except Exception as e:
        print("OLLAMA ERROR:", e)
        return local_camera_ai_summary(camera_id, status, result, frames, same_tiger)


def ai_decision_support(result, camera_id="System", message=""):
    """
    Generate decision support for any detection
    """

    prompt = f"""
You are providing decision support for a wildlife monitoring system.

Result: {result}
Source: {camera_id}
Context: {message}

Provide ONLY:

ASSESSMENT: What happened?
URGENCY: Low / Medium / High / Critical
ACTION: What should be done now?
NEXT: What happens next?

Keep it very short (max 4 lines).
"""

    try:
        response = ollama_answer(prompt)
        if response:
            return response
    except Exception as e:
        print("Ollama error:", e)

    # fallback ONLY if LLM fails
    if "tiger" in result.lower():
        return (
            "ASSESSMENT: Tiger detected\n"
            "URGENCY: High\n"
            "ACTION: Start alert protocol\n"
            "NEXT: Monitor nearby cameras"
        )
    else:
        return (
            "ASSESSMENT: No threat\n"
            "URGENCY: Low\n"
            "ACTION: Continue monitoring\n"
            "NEXT: Resume normal schedule"
        )
def generate_photo_detection_analysis(result, confidence, filename):
    prompt = f"""
You are an AI Wildlife Monitoring Assistant.

Photo Detection Result:
File: {filename}
Result: {result}
Confidence: {confidence}

Generate ONLY:

AI Summary:
(2-3 lines about what happened)

AI Suggestion:
(practical action for forest officer)

AI Decision Support:
(is action needed or not)

Risk Level:
(Low / Medium / High)

Confidence:
(Low / Medium / High)

Recommended Action:
(one clear action)
"""

    try:
        return ollama_answer(prompt)
    except:
        return f"""
AI Summary:
Photo analyzed for tiger detection.

AI Suggestion:
Check image clarity and re-run detection if needed.

AI Decision Support:
No critical issue detected.

Risk Level: Medium

Confidence: Low

Recommended Action:
Review image manually.
"""


def generate_video_detection_analysis(result, frames_checked, tiger_frames, filename):
    prompt = f"""
You are an AI Wildlife Monitoring Assistant.

Video Detection Result:
Video: {filename}
Result: {result}
Frames Checked: {frames_checked}
Tiger Frames: {tiger_frames}

Generate ONLY:

AI Summary:
AI Suggestion:
AI Decision Support:
Risk Level:
Confidence:
Recommended Action:
"""

    try:
        return ollama_answer(prompt)
    except:
        return f"""
AI Summary:
Video analyzed successfully.

AI Suggestion:
Review detected frames.

AI Decision Support:
Continue monitoring.

Risk Level: Medium

Confidence: Low

Recommended Action:
Check saved frames.
"""

# =========================================================
# SIGHTING INTELLIGENCE: AI STORY + AI CLASSIFICATION
# =========================================================

def generate_sighting_story(camera_id, source_type, result, confidence, message="", tiger_id_status="New Tiger Recorded"):
    """
    Generates a short, natural, field-note style narrative describing a
    tiger sighting, as if written by a forest ranger reviewing camera data.
    """
    prompt = f"""
You are a wildlife field officer writing a short sighting log entry.

DETECTION DETAILS:
- Camera/Location: {camera_id}
- Source: {source_type}
- Result: {result}
- Confidence: {confidence}%
- Tiger Identity Status: {tiger_id_status}
- Additional Info: {message}

Write a short, natural field-note style story (3-5 sentences) describing this
sighting as if logged by a forest ranger. Mention:
- what was observed and how confident the detection is
- whether this appears to be a new tiger or a returning individual, and why that matters
- one practical implication for monitoring this location

Write in plain narrative prose. Do not use markdown, headings, or bullet points.
"""

    try:
        story = ollama_answer(prompt)
        if story:
            return story.strip()
    except Exception as e:
        print("Sighting story error:", e)

    return _fallback_sighting_story(camera_id, result, tiger_id_status)


def _fallback_sighting_story(camera_id, result, tiger_id_status):
    r = (result or "").lower()

    if "tiger" in r and "no tiger" not in r:
        if "Same Tiger" in tiger_id_status:
            return (
                f"A tiger was sighted again at {camera_id}, with stripe patterns matching a "
                f"previously recorded individual. This repeat appearance suggests the animal is "
                f"maintaining territory in this zone. Field staff should log this as continued "
                f"activity for behavioral tracking rather than a new arrival."
            )
        return (
            f"A tiger was recorded at {camera_id} whose stripe pattern did not match any tiger "
            f"currently in the database, indicating a previously unlogged individual may be entering "
            f"the area. This location should be prioritized for follow-up monitoring over the next "
            f"few days to confirm the animal's presence."
        )

    return (
        f"Routine review at {camera_id} completed with no tiger activity detected during this check. "
        f"No action is required beyond continuing the standard monitoring schedule."
    )


def classify_sighting(camera_id, result, confidence, frames_checked=0, tiger_frames=0):
    """
    Uses the LLM to classify a sighting into structured categories that can be
    stored alongside the sighting log entry (activity type, risk level, and
    likely time-of-day context based on detection pattern).
    Always returns a dict, even if the AI call fails.
    """
    prompt = f"""
You are classifying a wildlife camera sighting for a structured log.

Camera: {camera_id}
Result: {result}
Confidence: {confidence}%
Frames Checked: {frames_checked}
Tiger Frames: {tiger_frames}

Respond ONLY in this exact format, one value per line, no extra commentary:
ACTIVITY: (Resting/Walking/Hunting/Territorial Marking/Unknown)
RISK: (Low/Medium/High/Critical)
TIME_CONTEXT: (Day/Night/Dusk/Dawn/Unknown)
"""

    classification = {
        "activity": "Unknown",
        "risk": "Medium" if "tiger" in (result or "").lower() and "no tiger" not in (result or "").lower() else "Low",
        "time_context": "Unknown"
    }

    try:
        response = ollama_answer(prompt)
        if response:
            for line in response.splitlines():
                line = line.strip()
                upper = line.upper()

                if upper.startswith("ACTIVITY:"):
                    classification["activity"] = line.split(":", 1)[1].strip()
                elif upper.startswith("RISK:"):
                    classification["risk"] = line.split(":", 1)[1].strip()
                elif upper.startswith("TIME_CONTEXT:"):
                    classification["time_context"] = line.split(":", 1)[1].strip()
    except Exception as e:
        print("Sighting classification error:", e)

    return classification


# =========================================================
# AI CONNECTIVITY CHECK (verify Ollama is really answering,
# not silently using fallback text)
# =========================================================

def check_ai_status():
    """
    Runs the SAME ollama_answer() function every real AI feature in this
    app uses (chat, decision support, camera summary, photo/video analysis,
    sighting stories) — not a separate simplified call. This guarantees
    the health check reflects what users actually experience, instead of
    potentially reporting CONNECTED via a different code path while the
    real feature functions still silently fail and fall back.
    """
    test_reply = ollama_answer("Reply with exactly one word: OK")

    if test_reply:
        return {
            "connected": True,
            "model": "llama3.2",
            "sample_reply": test_reply.strip()[:200]
        }

    return {
        "connected": False,
        "model": "llama3.2",
        "error": (
            "ollama_answer() returned no response. Check the server console "
            "for a line starting with 'OLLAMA ERROR:' printed at the moment "
            "this check ran — that line has the real underlying exception."
        )
    }