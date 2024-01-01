class ActorTools:
    def __init__(self):
        self.tools = {
            "help_manual_about_tool": {
                "name": "help_manual_about_tool",
                "description": "Learn about this device's functionality and what spoken commands it accepts.",
                "schema": { "type": "object", "properties": {} }
            },
            "other": {
                "name": "other",
                "description": "Catch all category for unclear intents",
                "schema": { "type": "object", "properties": {} }
            },
            "question_answer": {
                "name": "question_answer",
                "description": "Get answers to general questions, excluding device settings and functionality.",
                "schema": { "type": "object", "properties": {} }
            },
            "recording_annotation": {
                "name": "recording_annotation",
                "description": "During a recording, make note of important information such as the start of a new step or a reminder for a task later.",
                "schema": {
                    "type": "object",
                    "properties": {
                        # doing just to assist tool deciding func. this is going to be processed by follow up processor so it can utilize image/video, not just transcription text
                        "type": { "type": "string", "enum": ["step", "reminder", "observation.gel_electrophoresis", "observation.plate_colonies"] },
                        # not doing text, because we'll just pass through transcript text, not some regurgitated LLM output
                    },
                }
            },
            "send_recording_series_summary_email": {
                "name": "send_recording_series_summary_email",
                "description": "Get an email sent to you about recordings you've done today or yesterday.",
                "schema": {
                    "type": "object",
                    "properties": {
                        "interval_unit": { "type": "string", "enum": ["days"], "default": "days" },
                        "interval_num": { "type": "integer", "default": 0 },
                    },
                }
            },
            "send_recording_clip": {
                "name": "send_recording_clip",
                "description": "Get a recording for some step/task of work or some explicit number of minutes or hours. Do not assume times.",
                "schema": {
                    "type": "object",
                    "properties": {
                        "type": { "type": "string", "enum": ["step", "interval"] },
                        "interval_unit": { "type": "string", "enum": ["minutes", "hours", "days"] },
                        "interval_num": { "type": "integer" },
                    },
                }
            },
        }
    def get_tools_names(self):
        return list(self.tools.keys())
