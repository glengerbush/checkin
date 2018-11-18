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
    services = db.session.query(Services).limit(10).all()
    return render_template("services_table.html", columnHeaders=Services.__mapper__.c.keys(), services=services)


###############################
#        Checkin      #
###############################

@main.route('/checkin', methods=['GET'])
def getcheckin():
    _id = request.args.get("id")

    # UUID for checkin is not included
    if db.session.query(Services).filter(Services.checkin_token == _id).one_or_none():
        return render_template('checkin/checkin.html', checkin_token=_id)
    else:
        return render_template('checkin/no_id.html')


@main.route('/checkin', methods=['POST'])
def createCheckin():
    available = request.form.get("available")
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")
    checkinToken = request.form.get("checkinToken")

    if available is not None:
        # load stuff into the database here
        service = db.session.query(Services).filter(Services.checkin_token == checkinToken).one_or_none()
        service.checked_in = bool(available)
        if longitude and latitude:
            service.longitude = longitude
            service.latitude = latitude
        db.session.commit()
        return render_template('checkin/thank_you.html', available=available, latitude=latitude, longitude=longitude, checkinToken=checkinToken)
    else:
        return render_template('checkin/failure.html', checkinToken=checkinToken)
