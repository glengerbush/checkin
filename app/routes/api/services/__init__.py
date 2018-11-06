from flask import Blueprint

api_v1 = Blueprint('services-api', __name__)

from app.routes.api.services import routes