from sanic import json, Request
from sanic.handlers import ErrorHandler

class APIErrorHandler(ErrorHandler):
    def default(self, request: Request, exception: Exception):
        return json(
            { "status": "failure", "error": str(exception) },
            status=getattr(exception, 'status_code', 500))
