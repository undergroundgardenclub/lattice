from sanic import json, Request
from sanic.handlers import ErrorHandler

class APIErrorHandler(ErrorHandler):
    def default(self, request: Request, exception: Exception):
        # --- print errors for now
        print('[api] Unhandled Error: ', str(exception))
        # --- respond
        return json(
            { "status": "failure", "error": str(exception) },
            status=getattr(exception, 'status_code', 500))
