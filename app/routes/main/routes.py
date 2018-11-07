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

@main.route('/checkin')
def user_home():
    guid = request.args.get("id")

    if not guid:
        redirect(url_for('main.index'))

    return render_template("checkin.html")