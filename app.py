from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# DB Config (fix path)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/database.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Student(db.Model):
    __tablename__ = 'student'
    student_id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String, unique=True, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String)

class Course(db.Model):
    __tablename__ = 'course'
    course_id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String, unique=True, nullable=False)
    course_name = db.Column(db.String, nullable=False)
    course_description = db.Column(db.String)

class Enrollments(db.Model):
    __tablename__ = 'enrollments'
    enrollment_id = db.Column(db.Integer, primary_key=True)
    estudent_id = db.Column(db.Integer, db.ForeignKey('student.student_id'), nullable=False)
    ecourse_id = db.Column(db.Integer, db.ForeignKey('course.course_id'), nullable=False)

@app.route('/')
def index():
    students = Student.query.order_by(Student.student_id).all()
    return render_template('index.html', students=students)

@app.route('/student/create', methods=['GET', 'POST'])
def create_student():
    if request.method == 'GET':
        courses = Course.query.all()
        return render_template('create.html', courses=courses)

    roll = request.form['roll']
    f_name = request.form['f_name']
    l_name = request.form['l_name'] if request.form['l_name'] else ""
    selected_courses = request.form.getlist('courses')

    existing_student = Student.query.filter_by(roll_number=roll).first()
    if existing_student:
        return render_template('already_exists.html')

    new_student = Student(roll_number=roll, first_name=f_name, last_name=l_name)
    db.session.add(new_student)
    db.session.flush()  # get student_id

    for course_id in selected_courses:
        enrollment = Enrollments(estudent_id=new_student.student_id, ecourse_id=int(course_id))
        db.session.add(enrollment)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/student/<int:student_id>/update', methods=['GET', 'POST'])
def update_student(student_id):
    student = Student.query.get_or_404(student_id)
    courses = Course.query.all()
    enrolled_course_ids = [e.ecourse_id for e in Enrollments.query.filter_by(estudent_id=student_id)]

    if request.method == 'GET':
        return render_template('update.html',
                               student=student,
                               courses=courses,
                               enrolled_course_ids=enrolled_course_ids)

    student.roll_number = request.form['roll']  # <-- add this line
    student.first_name = request.form['f_name']
    student.last_name = request.form['l_name'] if request.form['l_name'] else ""

    Enrollments.query.filter_by(estudent_id=student_id).delete()
    db.session.flush()

    selected_courses = request.form.getlist('courses')
    for course_id in selected_courses:
        new_enroll = Enrollments(estudent_id=student_id, ecourse_id=int(course_id))
        db.session.add(new_enroll)

    db.session.commit()
    return redirect(url_for('index'))

@app.route('/student/<int:student_id>/delete', methods=['GET'])
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    Enrollments.query.filter_by(estudent_id=student_id).delete()
    db.session.delete(student)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/student/<int:student_id>')
def student_detail(student_id):
    student = Student.query.get_or_404(student_id)
    enrollment_links = Enrollments.query.filter_by(estudent_id=student_id).all()
    course_ids = [e.ecourse_id for e in enrollment_links]
    courses = Course.query.filter(Course.course_id.in_(course_ids)).all() if course_ids else []
    return render_template('student_detail.html', student=student, courses=courses)

if __name__ == '__main__':
    app.run(debug=True)
