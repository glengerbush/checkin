from app.routes.main import main
from flask import render_template, flash
from flask import redirect, url_for, request
from app import db

###############################
#        Landing Page         #
###############################


@main.route('/')
@main.route('/index')
def index():
    return render_template()


###############################
#        Checkin      #
###############################

@main.route('/checkin')
def user_home():
    guid = request.args.get("id")
    if not guid:
        redirect(url_for('main.index'))

# teacher_id = db.session.query(Teacher).with_entities(Teacher.id).filter(
# Teacher.user_id == current_user.id).one_or_none()
# class_ids = db.session.query(teachers_classes).with_entities(teachers_classes.c.class_id).filter(
# teachers_classes.c.teacher_id == teacher_id).all()
# class_list = db.session.query(Class).filter(and_(Class.id.in_(class_ids), Class.in_session == True)).all()
