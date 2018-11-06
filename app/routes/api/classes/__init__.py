from flask import Blueprint

api_v1 = Blueprint('classes-api', __name__)

from app.routes.api.classes import routes
