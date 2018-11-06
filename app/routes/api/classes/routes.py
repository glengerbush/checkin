from app import db
from app.models.main import Student, Teacher, Class, teachers_classes, students_classes
from app.models.gradebook import Assignment, Score, Attendance, AssignmentCategory, LearningGoal
from app.routes.api.classes import api_v1
from flask_user import roles_required, current_user
from flask import url_for, jsonify, redirect, request, render_template, render_template_string
from sqlalchemy import and_, asc, desc
from sqlalchemy.sql import func
import datetime


def owns_class(class_id):
    teacher_id = db.session.query(Teacher).with_entities(Teacher.id).filter(
        Teacher.user_id == current_user.id).one_or_none()
    if db.session.query(teachers_classes).with_entities(teachers_classes.c.teacher_id). \
            filter(and_(teachers_classes.c.class_id == class_id, teachers_classes.c.teacher_id == teacher_id)).first():
        return True
    else:
        return False


def in_class(class_id):
    if db.session.query(students_classes).with_entities(students_classes.c.student_id).filter(
            students_classes.c.class_id == class_id).one_or_none() == db.session.query(Student).with_entities(
            Student.id).filter(Student.user_id == current_user.id).one_or_none():
        return True
    else:
        return False


@api_v1.route('/classes', methods=['GET'])
@roles_required(['services'])
def all_classes():
    if current_user.is_authenticated:
        if current_user.has_roles('services'):
            allclasses = list()
            for i in db.session.query(Class).all():
                allclasses.append(i.serialize())
            return jsonify(allclasses)
    return redirect(url_for('auth.login'))


@api_v1.route('/classes/<int:class_id>', methods=['GET'])
@roles_required(['services', 'teacher', 'student'])
def class_by_id(class_id):
    if current_user.is_authenticated:
        if owns_class(class_id) or in_class(class_id) or current_user.has_roles('services'):
            return jsonify(db.session.query(Class).filter(Class.id == class_id).one_or_none().serialize())
    return redirect(url_for('auth.login'))


@api_v1.route('/class_details/<int:class_id>')
@roles_required(['services', 'teacher'])
def class_details(class_id):
    class_ = db.session.query(Class).filter(Class.id == class_id).one_or_none()
    assignment_categories = db.session.query(AssignmentCategory).filter(AssignmentCategory.class_id == class_id).all()
    assignments = db.session.query(Assignment).filter(Assignment.class_id == class_id).all()
    student_list = db.session.query(students_classes).with_entities(students_classes.c.student_id).filter(
        students_classes.c.class_id == class_id).all()
    assignment_list = db.session.query(Assignment).with_entities(Assignment.id).filter(
        Assignment.class_id == class_id).order_by(asc(Assignment.date)).all()
    scores = db.session.query(Score).filter(Score.assignment_id.in_(assignment_list)).all()
    enrollment = len(student_list)
    if current_user.has_roles('services') or owns_class(class_id):
        return render_template('teacher/class.html', class_=class_, assignment_categories=assignment_categories,
                               assignments=assignments, scores=scores,
                               assignment_categories_col=[("Category:", "category"), ("Weight:", "weight")],
                               learning_goals_col=[("Name:", "name")],
                               enrollment=enrollment)


####################################
#           Scores(Grades)         #
####################################
assignment_label = "Assignment"
score_label = "score"


@api_v1.route('/classes/<int:class_id>/grades', methods=['GET'])
@roles_required(['services', 'teacher'])
def get_grades_json(class_id):
    if owns_class(class_id) or current_user.has_roles('services'):
        student_ids_list = db.session.query(students_classes).with_entities(students_classes.c.student_id).filter(
            students_classes.c.class_id == class_id).all()
        student_ids_list = [i[0] for i in student_ids_list]
        student_info = db.session.query(Student).with_entities(Student.id, Student.last, Student.first).filter(
            Student.id.in_(student_ids_list)).all()
        assignment_info = db.session.query(Assignment).filter(Assignment.class_id == class_id).order_by(
            asc(Assignment.date)).all()
        assignment_list = db.session.query(Assignment).with_entities(Assignment.id).filter(
            Assignment.class_id == class_id).all()
        assignment_list = [i[0] for i in assignment_list]
        scores = db.session.query(Score).filter(Score.assignment_id.in_(assignment_list)).all()
        overall = overall_score(student_ids_list, assignment_list, class_id)
        return render_template('json/data_grades.json', objects=[student_info, assignment_info, scores],
                               object_types=["Student", "Assignment", "Score"],
                               column_lists=[['id', 'last', 'first'], ['id', 'name', 'date']], overall_score=overall,
                               pick_dict=learning_goals_pick(class_id))
    else:
        return redirect(url_for('auth.login'))


@api_v1.route('/classes/<int:class_id>/grades/<string:ids_string>', methods=['PUT'])
@roles_required(['services', 'teacher'])
def update_grades_json(class_id, ids_string):
    if owns_class(class_id) or current_user.has_roles('services'):
        id_list = ids_string.split(",")
        data = request.get_json()
        for id_ in id_list:
            scores = db.session.query(Score).filter(
                and_(Score.student_id == int(id_), Score.assignment_id.in_(data[id_][assignment_label].keys()))).all()
            for score_object in scores:
                score = data[str(score_object.student_id)][assignment_label][str(score_object.assignment_id)][
                    score_label]
                if score == '':
                    score = None
                else:
                    score = int(score)
                setattr(score_object, score_label, score)
        db.session.commit()

        # convert string list to integers for filtering
        id_list = map(int, id_list)
        student_info = db.session.query(Student).with_entities(Student.id, Student.last, Student.first).filter(
            Student.id.in_(id_list)).all()
        assignment_info = db.session.query(Assignment).with_entities(
            Assignment.id, Assignment.name, Assignment.date).filter(Assignment.class_id == class_id).all()
        assignment_list = db.session.query(Assignment).with_entities(Assignment.id).filter(
            Assignment.class_id == class_id).all()
        scores = db.session.query(Score).filter(Score.assignment_id.in_(assignment_list)).all()
        overall = overall_score(id_list, assignment_list, class_id)
        return render_template('json/data_grades.json', objects=[student_info, assignment_info, scores],
                               object_types=["Student", "Assignment", "Score"],
                               column_lists=[['id', 'last', 'first'], ['id', 'name', 'date']], overall_score=overall,
                               pick_dict=learning_goals_pick(class_id))
    else:
        return redirect(url_for('auth.login'))


def overall_score(student_list, assignment_list, class_id):
    # makes a dictionary that where the AssignmentCategory.id is the key to the AssignmentCategory.weight
    weight_cat_dict = db.session.query(AssignmentCategory).with_entities(AssignmentCategory.id,
                                                                         AssignmentCategory.weight).filter(
        AssignmentCategory.class_id == class_id).all()
    weight_cat_dict = dict(weight_cat_dict)
    assignments_cat_dict = db.session.query(Assignment).with_entities(Assignment.id,
                                                                      Assignment.assignment_category_id).filter(
        Assignment.id.in_(assignment_list)).all()
    assignments_cat_dict = dict(assignments_cat_dict)
    assignments = db.session.query(Assignment).filter(Assignment.id.in_(assignment_list)).all()

    # make a dictionary of overall scores, where the student id's are the keys
    # initialize grades which will be dict of dict, takes [student id][assignment category]
    scores = dict()
    grades = {}
    assignment_cat_total_possible = {}
    total_weight = {}
    for id_ in student_list:
        scores[id_] = db.session.query(Score).filter(
            and_(Score.student_id == id_, Score.assignment_id.in_(assignment_list))).all()
        grades[id_] = {}
        assignment_cat_total_possible[id_] = {}
        total_weight[id_] = 0
        for key in weight_cat_dict:
            assignment_cat_total_possible[id_][key] = 0
        for assignment in assignments:
            if assignment.assignment_category_id and assignment.total_points:
                if db.session.query(Score.score).filter(Score.assignment_id == assignment.id).filter(Score.student_id == id_).first()[0] is not None:
                    assignment_cat_total_possible[id_][assignment.assignment_category_id] += assignment.total_points
        for key in weight_cat_dict:
            if assignment_cat_total_possible[id_][key]:
                total_weight[id_] += weight_cat_dict[key]

    for key in scores:
        for score in scores[key]:
            assignment_category = assignments_cat_dict[score.assignment_id]
            if not grades[score.student_id].get(assignment_category):
                grades[score.student_id][assignment_category] = 0
            if score.score:
                grades[score.student_id][assignment_category] += score.score
            else:
                grades[score.student_id][assignment_category] += 0

    overall = dict()

    for id_ in student_list:
        if total_weight[id_]:
            overall[id_] = 0.0
            for key in weight_cat_dict:
                if grades[id_].get(key) and assignment_cat_total_possible[id_][key]:
                    grade_in_this_cat = float(grades[id_][key])
                    weight = float(weight_cat_dict[key])
                    overall[id_] += (grade_in_this_cat / float(assignment_cat_total_possible[id_][key])) * weight
            overall[id_] = round(overall[id_] / total_weight[id_], 2)
        else:
            overall[id_] = 0.0
    return overall



####################################
#       Projects(Assignments)      #
####################################

def assignment_cat_pick(class_id):
    return dict(db.session.query(AssignmentCategory).with_entities(
        AssignmentCategory.id, AssignmentCategory.category).filter(AssignmentCategory.class_id == class_id).all())


def learning_goals_pick(class_id):
    return dict(db.session.query(LearningGoal).with_entities(LearningGoal.id, LearningGoal.name).filter(
        LearningGoal.class_id == class_id).all())


pick_what = [["AssignmentCategory", "category", "assignment_category_id"], ["LearningGoal", "name", "learning_goal_id"]]

assignment_obj_type = "Assignment"


@api_v1.route('/classes/<int:class_id>/assignments', methods=['GET'])
@roles_required(['services', 'teacher'])
def get_assignments_json(class_id):
    if owns_class(class_id) or current_user.has_roles('services'):
        object_list = db.session.query(Assignment).filter(Assignment.class_id == class_id).all()
        return render_template('json/data_dropdown.json', objects=object_list, object_type=assignment_obj_type,
                               column_list=Assignment.__mapper__.c.keys(),
                               pick_dict=[assignment_cat_pick(class_id), learning_goals_pick(class_id)],
                               pick_what=pick_what, send_pick_list=True)
    else:
        return redirect(url_for('auth.login'))


@api_v1.route('/classes/<int:class_id>/assignments', methods=['POST'])
@roles_required(['services', 'teacher'])
def create_assignments_json(class_id):
    if owns_class(class_id) or current_user.has_roles('services'):
        data = request.get_json()
        new_row = Assignment()
        for key, value in data["0"][assignment_obj_type].iteritems():
            if value == '':
                value = None
            setattr(new_row, key, value)
        setattr(new_row, "class_id", class_id)
        db.session.add(new_row)
        db.session.commit()
        object_list = list()
        object_list.append(new_row)
        return render_template('json/data_dropdown.json', objects=object_list, object_type=assignment_obj_type,
                               column_list=Assignment.__mapper__.c.keys(),
                               pick_dict=[assignment_cat_pick(class_id), learning_goals_pick(class_id)],
                               pick_what=pick_what)
    else:
        return redirect(url_for('auth.login'))


@api_v1.route('/classes/<int:class_id>/assignments/<string:ids_string>', methods=['PUT'])
@roles_required(['services', 'teacher'])
def update_assignment_json(class_id, ids_string):
    if owns_class(class_id) or current_user.has_roles('services'):
        # for really large bulk edits, a more efficient solution should be used
        # create list of strings containing all ids being updated
        id_list = ids_string.split(",")
        data = request.get_json()
        for id_ in id_list:
            assignment = db.session.query(Assignment).filter(Assignment.id == id_).one_or_none()
            for key, value in data[id_][assignment_obj_type].iteritems():
                setattr(assignment, key, value)
        db.session.commit()
        # convert string list to integers for filtering
        id_list = map(int, id_list)
        object_list = db.session.query(Assignment).filter(Assignment.id.in_(id_list)).all()
        return render_template('json/data_dropdown.json', objects=object_list, object_type=assignment_obj_type,
                               column_list=Assignment.__mapper__.c.keys(),
                               pick_dict=[assignment_cat_pick(class_id), learning_goals_pick(class_id)],
                               pick_what=pick_what)
    else:
        return redirect(url_for('auth.login'))


@api_v1.route('/classes/<int:class_id>/assignments/<string:ids_string>', methods=['DELETE'])
@roles_required(['services', 'teacher'])
def delete_assignments_json(class_id, ids_string):
    if owns_class(class_id) or current_user.has_roles('services'):
        # create list of strings containing all ids being deleted and then convert to integers for filtering
        id_list = ids_string.split(",")
        id_list = map(int, id_list)
        db.session.query(Assignment).filter(Assignment.id.in_(id_list)).delete(synchronize_session=False)
        db.session.commit()
        return render_template_string("{}")
    else:
        return redirect(url_for('auth.login'))


####################################
# Categories(AssignmentCategories) #
####################################

@api_v1.route('/classes/<int:class_id>/assignment_categories', methods=['GET'])
@roles_required(['services', 'teacher'])
def get_assignment_categories_json(class_id):
    if owns_class(class_id) or current_user.has_roles('services'):
        object_list = db.session.query(AssignmentCategory).filter(AssignmentCategory.class_id == class_id).all()
        extra = cat_class_avg(object_list)
        return render_template('json/data.json', objects=object_list,
                               column_list=AssignmentCategory.__mapper__.c.keys(), extra_name="class_avg", extra=extra)
    else:
        return redirect(url_for('auth.login'))


@api_v1.route('/classes/<int:class_id>/assignment_categories', methods=['POST'])
@roles_required(['services', 'teacher'])
def create_assignment_categories_json(class_id):
    if owns_class(class_id) or current_user.has_roles('services'):
        data = request.get_json()
        new_row = AssignmentCategory()
        for key, value in data["0"].iteritems():
            if value == '':
                value = None
            if key == "weight":
                if safe_add_to_total_weight(value, class_id):
                    setattr(new_row, key, value)
                else:
                    db.session.rollback()
                    return render_template('json/error_message/too_much_weight.json')
            else:
                setattr(new_row, key, value)
        setattr(new_row, "class_id", class_id)
        db.session.add(new_row)
        db.session.commit()
        object_list = list()
        object_list.append(new_row)
        extra = dict()
        extra[new_row.id] =  "0%"
        return render_template('json/data.json', objects=object_list,
                               column_list=AssignmentCategory.__mapper__.c.keys(), extra_name="class_avg", extra=extra)
    else:
        return redirect(url_for('auth.login'))


@api_v1.route('/classes/<int:class_id>/assignment_categories/<string:ids_string>', methods=['PUT'])
@roles_required(['services', 'teacher'])
def update_assignment_categories_json(class_id, ids_string):
    if owns_class(class_id) or current_user.has_roles('services'):
        # for really large bulk edits, a more efficient solution should be used
        # create list of strings containing all ids being updated
        id_list = ids_string.split(",")
        data = request.get_json()
        for id_ in id_list:
            assignment_category = db.session.query(AssignmentCategory).filter(
                AssignmentCategory.id == id_).one_or_none()
            for key, value in data[id_].iteritems():
                if key == "weight":
                    if safe_add_to_total_weight(value, class_id):
                        setattr(assignment_category, key, value)
                    else:
                        db.session.rollback()
                        return render_template('json/too_much_weight.json')
                else:
                    setattr(assignment_category, key, value)
        db.session.commit()
        # convert string list to integers for filtering
        id_list = map(int, id_list)
        object_list = db.session.query(AssignmentCategory).filter(AssignmentCategory.id.in_(id_list)).all()
        extra = cat_class_avg(object_list)
        return render_template('json/data.json', objects=object_list,
                               column_list=AssignmentCategory.__mapper__.c.keys(), extra_name="class_avg", extra=extra)
    else:
        return redirect(url_for('auth.login'))


@api_v1.route('/classes/<int:class_id>/assignment_categories/<string:ids_string>', methods=['DELETE'])
@roles_required(['services', 'teacher'])
def delete_assignment_categories_json(class_id, ids_string):
    if owns_class(class_id) or current_user.has_roles('services'):
        # create list of strings containing all ids being deleted and then convert to integers for filtering
        id_list = ids_string.split(",")
        id_list = map(int, id_list)
        db.session.query(AssignmentCategory).filter(AssignmentCategory.id.in_(id_list)).delete(
            synchronize_session=False)
        db.session.commit()
        return render_template_string("{}")
    else:
        return redirect(url_for('auth.login'))


def safe_add_to_total_weight(new_weight, class_id):
    current_total = db.session.query(func.sum(AssignmentCategory.weight).label("current_total")).filter(
        AssignmentCategory.class_id == class_id).all()
    if long(current_total[0][0]) + long(new_weight) > 100:
        return False
    else:
        return True


def cat_class_avg(all_cats):
    extra = {}
    total_cat_points = {}
    total_cat_score = {}
    for cat in all_cats:
        all_assignments = db.session.query(Assignment).filter(Assignment.assignment_category_id == cat.id).all()
        total_cat_points[cat.id] = 0
        total_cat_score[cat.id] = 0
        extra[cat.id] = "0%"
        for assignment in all_assignments:
            total_cat_points[cat.id] += assignment.total_points
            temp_scores = db.session.query(func.sum(Score.score).label("total_scored"),
                                           func.count(Score.score).label("scores_count")).filter(
                Score.assignment_id == assignment.id).all()
            if temp_scores:
                total_cat_score[cat.id] += temp_scores[0][0] / temp_scores[0][1]

    for key in total_cat_points:
        if total_cat_points[key]:
            temp_avg = (float(total_cat_score[key]) / float(total_cat_points[key])) * 100
            extra[key] = str(int(round(temp_avg, 0))) + "%"
    return extra

####################################
#          Learning Goals          #
####################################
@api_v1.route('/classes/<int:class_id>/learning_goals', methods=['GET'])
@roles_required(['services', 'teacher'])
def get_learning_goals_json(class_id):
    if owns_class(class_id) or current_user.has_roles('services'):
        object_list = db.session.query(LearningGoal).filter(LearningGoal.class_id == class_id).all()
        extra = {}
        assignment_cat_list = db.session.query(AssignmentCategory).filter(AssignmentCategory.class_id == class_id).all()
        lg_total = {}
        for object_ in object_list:
            extra[object_.id] = 0
            for category in assignment_cat_list:
                if category.weight is not None and category.weight is not 0:
                    assignment_list = db.session.query(Assignment).with_entities(Assignment.id).filter(
                        Assignment.class_id == class_id).filter(Assignment.learning_goal_id == object_.id).filter(
                        Assignment.assignment_category_id == category.id).all()
                    lg_total[category.id] = db.session.query(
                        func.sum(Assignment.total_points).label("total_score_in_lg_for_cat")).filter(
                        Assignment.class_id == class_id).filter(Assignment.learning_goal_id == object_.id).filter(
                        Assignment.assignment_category_id == category.id).all()
                    scores_and_count_total = db.session.query(func.count(Score.score).label("score_count"),
                                                              func.sum(Score.score).label("sum_of_scores")).filter(
                        Score.assignment_id.in_(assignment_list))
                    if scores_and_count_total[0][0] and scores_and_count_total[0][1]:
                        score_average = scores_and_count_total[0][1] / scores_and_count_total[0][0]
                    else:
                        score_average = 0
                    if lg_total[category.id][0][0] is not None:
                        extra[object_.id] += (float(score_average) / float(lg_total[category.id][0][0])) * (
                            float(category.weight))
        for key in extra:
            extra[key] = str(int(round(extra[key], 2))) + "%"
        return render_template('json/data.json', objects=object_list, column_list=LearningGoal.__mapper__.c.keys(),
                               extra_name="class_avg", extra=extra)
    else:
        return redirect(url_for('auth.login'))


@api_v1.route('/classes/<int:class_id>/learning_goals', methods=['POST'])
@roles_required(['services', 'teacher'])
def create_learning_goals_json(class_id):
    if owns_class(class_id) or current_user.has_roles('services'):
        data = request.get_json()
        new_row = LearningGoal()
        for key, value in data["0"].iteritems():
            if value == '':
                value = None
            setattr(new_row, key, value)
        setattr(new_row, "class_id", class_id)
        db.session.add(new_row)
        db.session.commit()
        object_list = list()
        object_list.append(new_row)
        extra = {}
        for object_ in object_list:
            extra[object_.id] = "0%"
        return render_template('json/data.json', objects=object_list, column_list=LearningGoal.__mapper__.c.keys(),
                               extra_name="class_avg", extra=extra)
    else:
        return redirect(url_for('auth.login'))


@api_v1.route('/classes/<int:class_id>/learning_goals/<string:ids_string>', methods=['PUT'])
@roles_required(['services', 'teacher'])
def update_learning_goals_json(class_id, ids_string):
    if owns_class(class_id) or current_user.has_roles('services'):
        # for really large bulk edits, a more efficient solution should be used
        # create list of strings containing all ids being updated
        id_list = ids_string.split(",")
        data = request.get_json()
        for id_ in id_list:
            learning_goal = db.session.query(LearningGoal).filter(
                LearningGoal.id == id_).one_or_none()
            for key, value in data[id_].iteritems():
                setattr(learning_goal, key, value)
        db.session.commit()
        # convert string list to integers for filtering
        id_list = map(int, id_list)
        object_list = db.session.query(LearningGoal).filter(LearningGoal.id.in_(id_list)).all()
        extra = {}
        for object_ in object_list:
            extra[object_.id] = "0%"
        return render_template('json/data.json', objects=object_list, column_list=LearningGoal.__mapper__.c.keys(),
                               extra_name="class_avg", extra=extra)
    else:
        return redirect(url_for('auth.login'))


@api_v1.route('/classes/<int:class_id>/learning_goals/<string:ids_string>', methods=['DELETE'])
@roles_required(['services', 'teacher'])
def delete_learning_goals_json(class_id, ids_string):
    if owns_class(class_id) or current_user.has_roles('services'):
        # create list of strings containing all ids being deleted and then convert to integers for filtering
        id_list = ids_string.split(",")
        id_list = map(int, id_list)
        db.session.query(LearningGoal).filter(LearningGoal.id.in_(id_list)).delete(
            synchronize_session=False)
        db.session.commit()
        return render_template_string("{}")
    else:
        return redirect(url_for('auth.login'))


####################################
#            Attendance            #
####################################

# ADVISORY ONLY
# currently this route is for teachers leading advisory classes only!
@api_v1.route('/classes/<int:class_id>/attendance', methods=['GET'])
@roles_required(['services', 'teacher'])
def get_attendance_json(class_id):
    if owns_class(class_id) or current_user.has_roles('services'):
        now = datetime.datetime.now()
        today_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
        student_ids = db.session.query(students_classes).with_entities(students_classes.c.student_id).filter(
            students_classes.c.class_id == class_id).all()
        student_ids_list = [i[0] for i in student_ids]
        if not db.session.query(Attendance).filter(
                and_(Attendance.class_id == class_id, Attendance.start_time == today_start)).first():
            max_session = db.session.query(Attendance).order_by(desc(Attendance.session)).filter(
                Attendance.class_id == class_id).first()
            if max_session is not None:
                new_session = max_session.session + 1
            else:
                new_session = 1
            for each_student_id in student_ids_list:
                newAttendanceRow = Attendance()
                setattr(newAttendanceRow, "start_time", today_start)
                setattr(newAttendanceRow, "class_id", class_id)
                setattr(newAttendanceRow, "student_id", each_student_id)
                setattr(newAttendanceRow, "session", new_session)
                db.session.add(newAttendanceRow)
            db.session.commit()
        student_info = db.session.query(Student).with_entities(Student.id, Student.last, Student.first,
                                                               Student.phone).filter(
            Student.id.in_(student_ids_list)).all()
        attendance_info = db.session.query(Attendance).filter(
            and_(Attendance.class_id == class_id, Attendance.start_time == today_start)).all()
        return render_template('json/data_daily_attendance.json', objects=[student_info, attendance_info],
                               object_types=["Student", "Attendance"],
                               column_lists=[['id', 'last', 'first'], ['id', 'name', 'date']])
    else:
        return redirect(url_for('auth.login'))


# currently this route is for teachers leading advisory classes only!
@api_v1.route('/classes/<int:class_id>/attendance/<string:ids_string>', methods=['PUT'])
@roles_required(['services', 'teacher'])
def update_attendance_json(class_id, ids_string):
    if owns_class(class_id) or current_user.has_roles('services'):
        id_list = ids_string.split(",")
        now = datetime.datetime.now()
        today_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
        for student_id in id_list:
            attendance_row = db.session.query(Attendance).filter(Attendance.student_id == student_id).filter(
                Attendance.class_id == class_id).filter(Attendance.start_time == today_start).first()
            if attendance_row is not None:
                setattr(attendance_row, "arrived", now)
        db.session.commit()
        student_info = db.session.query(Student).with_entities(Student.id, Student.last, Student.first,
                                                               Student.phone).filter(
            Student.id.in_(id_list)).all()
        attendance_info = db.session.query(Attendance).filter(Attendance.class_id == class_id).filter(
            Attendance.start_time == today_start).filter(Attendance.student_id.in_(id_list)).all()
        return render_template('json/data_daily_attendance.json', objects=[student_info, attendance_info],
                               object_types=["Student", "Attendance"],
                               column_lists=[['id', 'last', 'first'], ['id', 'name', 'date']])
    else:
        return redirect(url_for('auth.login'))


# WHOLE GRADE
# currently this route is only for receptionists to take attendance for the whole grade!
@api_v1.route('/grade/<int:grade>/attendance', methods=['GET'])
@roles_required(['services', 'receptionist'])
def get_attendance_for_receptionist_json(grade):
    if current_user.has_roles('services') or current_user.has_roles('receptionist'):
        now = datetime.datetime.now()
        today_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
        student_ids = db.session.query(Student).with_entities(Student.id).filter(Student.grade_band == grade).all()
        student_ids_list = [i[0] for i in student_ids]
        if not db.session.query(Attendance).filter(
                and_(Attendance.student_id.in_(student_ids_list), Attendance.start_time == today_start)).first():
            max_session = db.session.query(Attendance).order_by(desc(Attendance.session)).filter(
                Attendance.student_id.in_(student_ids_list)).first()
            if max_session is not None:
                new_session = max_session.session + 1
            else:
                new_session = 1
            for each_student_id in student_ids_list:
                newAttendanceRow = Attendance()
                setattr(newAttendanceRow, "start_time", today_start)
                setattr(newAttendanceRow, "student_id", each_student_id)
                setattr(newAttendanceRow, "session", new_session)
                db.session.add(newAttendanceRow)
            db.session.commit()
        student_info = db.session.query(Student).with_entities(Student.id, Student.last, Student.first,
                                                               Student.phone).filter(
            Student.id.in_(student_ids_list)).all()
        attendance_info = db.session.query(Attendance).filter(
            and_(Attendance.student_id.in_(student_ids_list), Attendance.start_time == today_start)).all()
        return render_template('json/data_daily_attendance.json', objects=[student_info, attendance_info],
                               object_types=["Student", "Attendance"],
                               column_lists=[['id', 'last', 'first'], ['id', 'name', 'date']])
    else:
        return redirect(url_for('auth.login'))


# currently this route is only for receptionists to take attendance for the whole grade!
@api_v1.route('/grade/<int:grade>/attendance/<string:ids_string>', methods=['PUT'])
@roles_required(['services', 'receptionist'])
def update_attendance_for_receptionist_json(grade, ids_string):
    if current_user.has_roles('services') or current_user.has_roles('receptionist'):
        id_list = ids_string.split(",")
        id_list = map(int, id_list)
        student_ids = db.session.query(Student).with_entities(Student.id).filter(
            Student.grade_band == grade).all()
        student_ids_list = [i[0] for i in student_ids]
        if not all(elem in student_ids_list for elem in id_list):
            return render_template('/json/error_message/whole_student_attendance_error.json')
        now = datetime.datetime.now()
        today_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
        for student_id in id_list:
            attendance_row = db.session.query(Attendance).filter(Attendance.student_id == student_id).filter(
                Attendance.student_id.in_(student_ids_list)).filter(Attendance.start_time == today_start).first()
            if attendance_row is not None:
                setattr(attendance_row, "arrived", now)
        db.session.commit()
        student_info = db.session.query(Student).with_entities(Student.id, Student.last, Student.first,
                                                               Student.phone).filter(Student.id.in_(id_list)).all()
        attendance_info = db.session.query(Attendance).filter(Attendance.student_id.in_(student_ids_list)).filter(
            Attendance.start_time == today_start).filter(Attendance.student_id.in_(id_list)).all()
        return render_template('json/data_daily_attendance.json', objects=[student_info, attendance_info],
                               object_types=["Student", "Attendance"],
                               column_lists=[['id', 'last', 'first'], ['id', 'name', 'date']])
    else:
        return redirect(url_for('auth.login'))


@api_v1.route('/grade_attendance/<int:grade>', methods=['GET'])
@roles_required(['services', 'receptionist'])
def whole_grade_attendance(grade):
    enrollment = db.session.query(func.count(Student.id)).filter(Student.grade_band == grade).all()
    enrollment = enrollment[0][0]
    return render_template('receptionist/whole_grade_attendance.html', grade=grade, enrollment=enrollment)
