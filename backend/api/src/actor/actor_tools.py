class ActorTools:
    def __init__(self):
        self.tools = {
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
            "send_video_series_slice": {
                "name": "send_video_series_slice",
                "description": "Get a recording that covers some number of minutes or hours.",
                "schema": {
                    "type": "object",
                    "properties": {
                        "interval_unit": { "type": "string", "enum": ["minutes", "hours"], "default": "minutes" },
                        "interval_num": { "type": "integer", "default": 15 },
                    },
                }
            },
            "question_answer": {
                "name": "question_answer",
                "description": "Get answers to general questions, excluding device settings and functionality.",
                "schema": { "type": "object", "properties": {} }
            },
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
        }
    def get_tools_names(self):
        return list(self.tools.keys())