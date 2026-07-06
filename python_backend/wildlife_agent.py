import os
import json
from datetime import datetime
from ai_assistant import (
    ai_decision_support,
    ollama_answer,
    generate_camera_ai_summary,
    generate_sighting_story,
    classify_sighting
)
from sighting_manager import add_sighting


class WildlifeAgent:
    """
    Enhanced Wildlife Intelligence Officer using Llama/Ollama
    Provides AI-driven analysis for tiger detections across:
    - Live camera streams
    - Photo uploads
    - Video uploads
    """

    def __init__(
        self,
        source_type="Unknown",
        result="",
        message="",
        file_name="",
        image_path="",
        username="admin",
        camera_id="",
        frames_checked=0,
        tiger_frames=0,
        nontiger_frames=0,
        confidence=0.0
    ):
        self.source_type = source_type
        self.result = result
        self.message = message
        self.file_name = file_name
        self.image_path = image_path
        self.username = username
        self.camera_id = camera_id

        self.frames_checked = frames_checked
        self.tiger_frames = tiger_frames
        self.nontiger_frames = nontiger_frames
        self.confidence = confidence

        self.ai_summary = ""
        self.ai_suggestions = ""
        self.ai_decision = ""
        self.ai_report = ""
        self.plan = []
        self.execution_log = []
        self.memory_file = "agent_memory.json"

        self.sighting_story = ""
        self.sighting_classification = {}
        self.sighting_entry = {}

    # ============= STEP 1: LOAD AGENT MEMORY =============
    def load_memory(self):
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Memory load error: {e}")

        return {"detections": [], "patterns": {}}

    # ============= STEP 2: SAVE AGENT MEMORY =============
    def save_memory(self, memory):
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(memory, f, indent=2)
        except Exception as e:
            print(f"Memory save error: {e}")

    # ============= STEP 3: VALIDATE DETECTION =============
    def validate_detection(self):
        validation_report = {
            "is_valid": True,
            "confidence_score": self.confidence,
            "issues": []
        }

        if self.result == "Tiger Detected":
            if self.confidence < 20:
                validation_report["issues"].append("Low confidence score")
            if not self.image_path or not os.path.exists(self.image_path):
                validation_report["issues"].append("Image path invalid")

        if len(validation_report["issues"]) > 0:
            validation_report["is_valid"] = False

        return validation_report

    # ============= STEP 4: IDENTIFY TIGER PROFILE =============
    def identify_tiger_profile(self):
        if "Same Tiger" in self.message:
            return {
                "identification": "Same Tiger Seen Again",
                "profile": "Existing tiger profile updated",
                "action": "UPDATE_PROFILE"
            }

        if "Tiger Detected" in self.result:
            return {
                "identification": "New Tiger Recorded",
                "profile": "New tiger profile created",
                "action": "CREATE_PROFILE"
            }

        return {
            "identification": "No Tiger",
            "profile": "N/A",
            "action": "NONE"
        }

    # ============= STEP 5: ANALYZE BEHAVIOR & RISK =============
    def analyze_behavior_and_risk(self):
        analysis_prompt = f"""
You are a Wildlife Expert AI analyzing tiger detection data.

Detection Summary:
- Source: {self.source_type}
- Result: {self.result}
- Frames Analyzed: {self.frames_checked}
- Tiger Frames: {self.tiger_frames}
- Confidence: {self.confidence}%
- Additional Info: {self.message}

Analyze and provide:

1. BEHAVIOR ASSESSMENT:
   - Activity level (High/Medium/Low)
   - Threat level (Critical/High/Medium/Low/None)
   - Recommended action

2. RISK FACTORS:
   - List 2-3 risk factors if tiger detected
   - Proximity to infrastructure
   - Time of activity

3. MONITORING PRIORITY:
   - Should this camera/location be prioritized? (Yes/No)
   - Recommended monitoring frequency

Keep response concise and actionable.
"""

        try:
            response = ollama_answer(analysis_prompt)
            return response if response else self._fallback_behavior_analysis()
        except Exception as e:
            print(f"Behavior analysis error: {e}")
            return self._fallback_behavior_analysis()

    def _fallback_behavior_analysis(self):
        if "Tiger Detected" in self.result:
            return """
BEHAVIOR ASSESSMENT:
- Activity: High
- Threat Level: High
- Recommended Action: Increase monitoring frequency

RISK FACTORS:
- Tiger presence confirmed in monitoring area
- May indicate territory establishment
- Monitor nearby cameras for movement

MONITORING PRIORITY:
- Yes, prioritize this camera
- Increase check frequency to every 2-4 hours
"""
        return "No tiger activity detected. Continue routine monitoring."

    # ============= STEP 6: AUTONOMOUS DATABASE OPERATIONS =============
    def execute_database_operations(self):
        ops = []

        if self.result == "Tiger Detected":
            ops.append({
                "operation": "INSERT_DETECTION",
                "table": "detection_history",
                "data": {
                    "username": self.username,
                    "source_type": self.source_type,
                    "result": self.result,
                    "confidence": self.confidence,
                    "image_path": self.image_path
                }
            })

            ops.append({
                "operation": "INSERT_ALERT",
                "table": "alerts",
                "data": {
                    "camera_id": self.camera_id,
                    "alert_type": "TIGER_DETECTED",
                    "confidence": self.confidence,
                    "timestamp": datetime.now().isoformat()
                }
            })

        return ops

    # ============= STEP 7: GENERATE AI SUMMARY =============
    def generate_ai_summary(self):
        summary_prompt = f"""
You are Tiger AI Assistant summarizing a detection event.

DETECTION DATA:
- Source: {self.source_type}
- Camera: {self.camera_id}
- Result: {self.result}
- Frames Checked: {self.frames_checked}
- Tiger Frames: {self.tiger_frames}
- Non-Tiger Frames: {self.nontiger_frames}
- Confidence: {self.confidence}%

Generate a 2-3 line SUMMARY that:
1. States the detection result clearly
2. Mentions key statistics
3. Indicates action status

Example: "Tiger detected in CAM_1 with 75% confidence. Analyzed 45 frames, 8 tiger detections. Alert generated and monitoring intensified."
"""

        try:
            self.ai_summary = ollama_answer(summary_prompt)
            if not self.ai_summary:
                self.ai_summary = f"Detection: {self.result} | Frames: {self.frames_checked} | Tigers: {self.tiger_frames}"
            return self.ai_summary
        except Exception as e:
            self.ai_summary = f"Detection: {self.result} | Frames: {self.frames_checked} | Tigers: {self.tiger_frames}"
            return self.ai_summary

    # ============= STEP 8: PROVIDE SUGGESTIONS =============
    def generate_suggestions(self):
        suggestion_prompt = f"""
You are a Wildlife Monitoring Expert. Based on this detection, provide 3 specific, actionable suggestions.

SITUATION:
- Detection: {self.result}
- Source: {self.source_type}
- Location: {self.camera_id}
- Frames Analyzed: {self.frames_checked}

Provide exactly 3 suggestions as bullet points.

Example format:
• Increase monitoring frequency on CAM_1 for next 48 hours
• Review video footage for tiger movement patterns
• Check proximity to human settlements

Keep each suggestion under 15 words.
"""

        try:
            self.ai_suggestions = ollama_answer(suggestion_prompt)
            if not self.ai_suggestions:
                self.ai_suggestions = self._fallback_suggestions()
            return self.ai_suggestions
        except Exception as e:
            self.ai_suggestions = self._fallback_suggestions()
            return self.ai_suggestions

    def _fallback_suggestions(self):
        if self.result == "Tiger Detected":
            return (
                "• Increase monitoring frequency on camera for next 48 hours\n"
                "• Review saved tiger image for stripe pattern identification\n"
                "• Check nearby cameras for additional tiger sightings"
            )
        return (
            "• Continue routine monitoring\n"
            "• Maintain current camera configuration\n"
            "• Archive detection record for historical analysis"
        )

    # ============= STEP 9: CREATE DECISION SUPPORT =============
    def generate_decision_support(self):
        decision_prompt = f"""
You are an AI Decision Support System for Tiger Monitoring.

Given this scenario, provide a clear decision framework:

SCENARIO:
- Result: {self.result}
- Camera: {self.camera_id}
- Confidence: {self.confidence}%
- Message: {self.message}

Provide:
1. DECISION: (What action should user take?)
2. CONFIDENCE: (How confident is this recommendation?)
3. ALTERNATIVE: (What if this detection is false?)
4. ESCALATION: (Should this be escalated? To whom?)

Keep response concise and practical.
"""

        try:
            self.ai_decision = ollama_answer(decision_prompt)
            if not self.ai_decision:
                self.ai_decision = self._fallback_decision()
            return self.ai_decision
        except Exception as e:
            self.ai_decision = self._fallback_decision()
            return self.ai_decision

    def _fallback_decision(self):
        if self.result == "Tiger Detected":
            return (
                "DECISION: Immediate alert. Review footage and increase monitoring.\n"
                "CONFIDENCE: High\n"
                "ALTERNATIVE: If false alarm, recalibrate detection model\n"
                "ESCALATION: Yes, alert wildlife authority if real tiger"
            )
        return (
            "DECISION: Continue routine monitoring\n"
            "CONFIDENCE: Medium\n"
            "ALTERNATIVE: Review for missed detections\n"
            "ESCALATION: No escalation needed"
        )

    # ============= STEP 10: GENERATE SIGHTING LOG ENTRY =============
    def generate_sighting_entry(self):
        """
        Builds a structured sighting log entry: AI narrative story +
        AI classification (activity/risk/time-of-day), then persists it
        to sightings_log.json via sighting_manager. Only confirmed tiger
        detections are logged as sightings.
        """
        tiger_id = self.identify_tiger_profile()

        self.sighting_story = generate_sighting_story(
            camera_id=self.camera_id,
            source_type=self.source_type,
            result=self.result,
            confidence=self.confidence,
            message=self.message,
            tiger_id_status=tiger_id["identification"]
        )

        self.sighting_classification = classify_sighting(
            camera_id=self.camera_id,
            result=self.result,
            confidence=self.confidence,
            frames_checked=self.frames_checked,
            tiger_frames=self.tiger_frames
        )

        entry = {
            "camera_id": self.camera_id,
            "source_type": self.source_type,
            "username": self.username,
            "result": self.result,
            "confidence": self.confidence,
            "identification": tiger_id["identification"],
            "image_path": self.image_path,
            "file_name": self.file_name,
            "story": self.sighting_story,
            "activity": self.sighting_classification.get("activity", "Unknown"),
            "risk": self.sighting_classification.get("risk", "Medium"),
            "time_context": self.sighting_classification.get("time_context", "Unknown")
        }

        if self.result == "Tiger Detected":
            entry = add_sighting(entry)

        self.sighting_entry = entry
        return entry

    # ============= ORCHESTRATE: 10-STEP PIPELINE =============
    def execute_pipeline(self):
        results = {
            "step_1_memory_loaded": self.load_memory(),
            "step_2_validation": self.validate_detection(),
            "step_3_tiger_identification": self.identify_tiger_profile(),
            "step_4_behavior_analysis": self.analyze_behavior_and_risk(),
            "step_5_db_operations": self.execute_database_operations(),
            "step_6_ai_summary": self.generate_ai_summary(),
            "step_7_suggestions": self.generate_suggestions(),
            "step_8_decision_support": self.generate_decision_support(),
            "step_9_memory_saved": "Agent memory updated",
            "step_10_sighting_log": self.generate_sighting_entry()
        }

        memory = self.load_memory()
        memory["detections"].append({
            "timestamp": datetime.now().isoformat(),
            "result": self.result,
            "camera": self.camera_id,
            "confidence": self.confidence
        })
        self.save_memory(memory)

        return results

    # ============= DISPLAY FUNCTIONS =============
    def show_summary(self):
        return (
            f"\n========== WILDLIFE AGENT SUMMARY ==========\n"
            f"Source: {self.source_type}\n"
            f"Camera: {self.camera_id}\n"
            f"Result: {self.result}\n\n"
            f"AI SUMMARY:\n{self.ai_summary}\n\n"
            f"AI SUGGESTIONS:\n{self.ai_suggestions}\n\n"
            f"AI DECISION:\n{self.ai_decision}\n"
            f"=========================================\n"
        )

    def show_full_report(self):
        validation = self.validate_detection()
        behavior = self.analyze_behavior_and_risk()
        tiger_id = self.identify_tiger_profile()

        return (
            f"\n========== COMPREHENSIVE WILDLIFE AGENT REPORT ==========\n\n"
            f"1. VALIDATION\n"
            f"   Is Valid: {validation['is_valid']}\n"
            f"   Confidence: {validation['confidence_score']}%\n"
            f"   Issues: {', '.join(validation['issues']) if validation['issues'] else 'None'}\n\n"
            f"2. TIGER IDENTIFICATION\n"
            f"   Status: {tiger_id['identification']}\n"
            f"   Action: {tiger_id['action']}\n\n"
            f"3. BEHAVIOR ANALYSIS\n{behavior}\n\n"
            f"4. AI SUMMARY\n{self.ai_summary}\n\n"
            f"5. SUGGESTIONS\n{self.ai_suggestions}\n\n"
            f"6. DECISION SUPPORT\n{self.ai_decision}\n\n"
            f"7. DATABASE OPERATIONS\n{json.dumps(self.execute_database_operations(), indent=2)}\n\n"
            f"========================================================\n"
        )


# ============= CONVENIENCE FUNCTION =============
def run_wildlife_agent(**kwargs):
    """
    Main entry point for agent execution.

    Returns dict with keys:
        agent_name, pipeline, summary, full_report,
        ai_summary, ai_suggestions, ai_decision
    
    app.py should read:
        agent_result.get("summary")       -> short summary text
        agent_result.get("full_report")   -> comprehensive report text
        agent_result.get("ai_summary")    -> AI-generated summary string
    """
    agent = WildlifeAgent(**kwargs)
    pipeline_result = agent.execute_pipeline()

    return {
        "agent_name": "Wildlife Intelligence Officer",
        "pipeline": pipeline_result,
        # FIX: these are the correct keys — app.py must use these
        "summary": agent.show_summary(),
        "full_report": agent.show_full_report(),
        "ai_summary": agent.ai_summary,
        "ai_suggestions": agent.ai_suggestions,
        "ai_decision": agent.ai_decision,
        # Sighting Intelligence: AI story + AI classification + saved log entry
        "sighting_story": agent.sighting_story,
        "sighting_classification": agent.sighting_classification,
        "sighting_entry": agent.sighting_entry
    }