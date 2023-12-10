from contextvars import ContextVar
from sanic import Sanic
from sanic.response import json
from sanic_cors import CORS
import env
from devices.routes import blueprint_devices
from intake.routes import blueprint_intake
from middleware.error_handler import APIErrorHandler
from orm import sa_sessionmaker


# INIT
api_app = Sanic('api')


# MIDDLEWARE
# --- cors
CORS(api_app)
# --- error handler
api_app.error_handler = APIErrorHandler()
# --- db session
_base_model_session_ctx = ContextVar('session')
# --- db session: request hook
@api_app.middleware('request')
async def inject_session(request):
    request.ctx.session = sa_sessionmaker()
    request.ctx.session_ctx_token = _base_model_session_ctx.set(request.ctx.session)
# --- db session: response hook
@api_app.middleware('response')
async def close_session(request, response):
    if hasattr(request.ctx, "session_ctx_token"):
        _base_model_session_ctx.reset(request.ctx.session_ctx_token)
        await request.ctx.session.close()


# ROUTES
# --- health
@api_app.route('/health', methods=['GET'])
def app_route_health(_):
    return json({ 'status': 'success' })
# --- intake (streams/recordings)
api_app.blueprint(blueprint_intake)


# RUN
def start_api():
    api_app.run(
        auto_reload=False, # auto-reload only for dev. done via watchdog pkg in docker-compose file
        dev=False,
        host=env.env_api_host(),
        port=env.env_api_port(),
        workers=1)
