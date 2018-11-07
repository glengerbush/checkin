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
    if not _id:
        return render_template('no_id.html')

    return render_template('checkin.html')


@main.route('/checkin', methods=['POST'])
def submit_checkin():

    if request.args.get("latitude"):
        return render_template('thank_you.html')
    else:
        return render_template('checkin_failure.html')

    return render_template('checkin.html')
