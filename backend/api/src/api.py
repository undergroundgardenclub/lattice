from sanic import Sanic
from sanic.response import json
from sanic_cors import CORS
import env
from middleware.error_handler import APIErrorHandler
from intake.routes import blueprint_intake


# INIT
api_app = Sanic('api')


# MIDDLEWARE
# --- cors
CORS(api_app)
# --- error handler
api_app.error_handler = APIErrorHandler()


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
        auto_reload=True, # auto-reload only for dev. done via watchdog pkg in docker-compose file
        dev=False,
        host=env.env_get_api_host(),
        port=env.env_get_api_port(),
        workers=1)
