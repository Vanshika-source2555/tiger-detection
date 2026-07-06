"""
sighting_manager.py

Structured "Sighting Log" storage for the Tiger Detection Monitoring System.

Every confirmed tiger detection becomes a Sighting Entry containing:
- basic detection metadata (camera, source, confidence, image path)
- tiger identity status (New Tiger Recorded / Same Tiger Seen Again)
- an AI-generated narrative "sighting story" (field-note style)
- an AI classification (activity, risk level, time-of-day context)

This file only handles STORAGE. AI generation lives in ai_assistant.py
(generate_sighting_story, classify_sighting) so it can reuse the same
Ollama/Llama pipeline as the rest of the app.
"""

import os
import json
from datetime import datetime

SIGHTING_LOG_FILE = "sightings_log.json"


# ============= LOAD =============
def load_sightings():
    if not os.path.exists(SIGHTING_LOG_FILE):
        return []

    try:
        with open(SIGHTING_LOG_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception as e:
        print("Sighting log load error:", e)
        return []


# ============= SAVE =============
def save_sightings(sightings):
    try:
        with open(SIGHTING_LOG_FILE, "w") as f:
            json.dump(sightings, f, indent=2)
    except Exception as e:
        print("Sighting log save error:", e)


# ============= ADD A NEW SIGHTING =============
def add_sighting(entry):
    """
    entry should be a dict. A unique id + timestamp are added automatically
    if not already present.
    """
    sightings = load_sightings()

    if "id" not in entry:
        entry["id"] = f"SGT-{len(sightings) + 1:05d}"

    if "timestamp" not in entry:
        entry["timestamp"] = datetime.now().isoformat()

    sightings.append(entry)
    save_sightings(sightings)

    return entry


# ============= FETCH RECENT SIGHTINGS =============
def get_recent_sightings(limit=20):
    sightings = load_sightings()
    return sightings[-limit:][::-1]  # most recent first


# ============= FETCH SIGHTINGS FOR ONE CAMERA =============
def get_sightings_by_camera(camera_id, limit=20):
    sightings = [s for s in load_sightings() if s.get("camera_id") == camera_id]
    return sightings[-limit:][::-1]


# ============= FETCH A SINGLE SIGHTING BY ID =============
def get_sighting_by_id(sighting_id):
    for s in load_sightings():
        if s.get("id") == sighting_id:
            return s
    return None


# ============= STATS =============
def get_sighting_stats():
    sightings = load_sightings()

    total = len(sightings)
    new_tigers = sum(1 for s in sightings if s.get("identification") == "New Tiger Recorded")
    same_tiger = sum(1 for s in sightings if s.get("identification") == "Same Tiger Seen Again")

    risk_counts = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    for s in sightings:
        risk = str(s.get("risk", "")).strip().capitalize()
        if risk in risk_counts:
            risk_counts[risk] += 1

    camera_counts = {}
    for s in sightings:
        cam = s.get("camera_id", "Unknown") or "Unknown"
        camera_counts[cam] = camera_counts.get(cam, 0) + 1

    return {
        "total_sightings": total,
        "new_tigers": new_tigers,
        "same_tiger_sightings": same_tiger,
        "risk_breakdown": risk_counts,
        "sightings_by_camera": camera_counts
    }


# ============= CLEAR LOG (admin utility) =============
def clear_sightings():
    save_sightings([])
    return "Sighting log cleared"


# ============= PLAIN TEXT FORMATTERS (match rest of app's text-based routes) =============
def format_sightings_text(sightings):
    if not sightings:
        return "No sightings found"

    lines = []
    for s in sightings:
        lines.append("===== SIGHTING =====")
        lines.append(f"ID: {s.get('id', '')}")
        lines.append(f"Time: {s.get('timestamp', '')}")
        lines.append(f"Camera: {s.get('camera_id', '')}")
        lines.append(f"Source: {s.get('source_type', '')}")
        lines.append(f"Result: {s.get('result', '')}")
        lines.append(f"Confidence: {s.get('confidence', '')}%")
        lines.append(f"Identification: {s.get('identification', '')}")
        lines.append(f"Activity: {s.get('activity', '')}")
        lines.append(f"Risk: {s.get('risk', '')}")
        lines.append(f"Time Context: {s.get('time_context', '')}")
        lines.append(f"Image: {s.get('image_path', '')}")
        lines.append("Story:")
        lines.append(str(s.get('story', '')))
        lines.append("=====================")
        lines.append("")

    return "\n".join(lines)


def format_stats_text(stats):
    lines = []
    lines.append(f"Total Sightings: {stats.get('total_sightings', 0)}")
    lines.append(f"New Tigers: {stats.get('new_tigers', 0)}")
    lines.append(f"Same Tiger Sightings: {stats.get('same_tiger_sightings', 0)}")
    lines.append("")
    lines.append("Risk Breakdown:")
    for risk, count in stats.get("risk_breakdown", {}).items():
        lines.append(f"  {risk}: {count}")
    lines.append("")
    lines.append("Sightings By Camera:")
    for cam, count in stats.get("sightings_by_camera", {}).items():
        lines.append(f"  {cam}: {count}")

    return "\n".join(lines)