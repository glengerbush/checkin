from app import db
from app.models.main import Services
from app.routes.main import main
from flask import render_template
from flask import redirect, url_for, request


###############################
#        Landing Page         #
###############################


@main.route('/')
@main.route('/index')
def index():
    return render_template("services_table.html")


###############################
#        Checkin      #
###############################

@main.route('/checkin', methods=['GET'])
def checkin():
    _id = request.args.get("id")

    # UUID for checkin is not included
    if db.session.query(Services).filter(Services.uuid == _id).one_or_none():
        return render_template('checkin.html', uuid=_id)
    else:
        return render_template('no_id.html')


@main.route('/checkin', methods=['POST'])
def submit_checkin():
    available = request.form.get("available")
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")
    uuid = request.form.get("uuid")

    if available is not None:
        # load stuff into the database here
        service = db.session.query(Services).filter(Services.uuid == uuid).one_or_none()
        service.checked_in = bool(available)
        if longitude and latitude:
            service.longitude = longitude
            service.latitude = latitude
        db.session.commit()
        return render_template('thank_you.html', available=available)
    else:
        return render_template('checkin_failure.html')
