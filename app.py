from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# DB Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
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
    students = Student.query.all()
    return render_template('index.html', students=students)


# this is the create route
@app.route('/student/create', methods=['GET', 'POST'])
def create_student():
    if request.method == 'GET':
        return render_template('create.html')

    # POST method: form submitted
    roll = request.form['roll']
    f_name = request.form['f_name']
    l_name = request.form['l_name']
    selected_courses = request.form.getlist('courses')

    # Check if roll number already exists
    existing_student = Student.query.filter_by(roll_number=roll).first()
    if existing_student:
        return render_template('already_exists.html')

    # Add new student
    new_student = Student(roll_number=roll, first_name=f_name, last_name=l_name)
    db.session.add(new_student)
    db.session.commit()

    # Add enrollments
    for course_id in selected_courses:
        enrollment = Enrollments(estudent_id=new_student.student_id, ecourse_id=int(course_id))
        db.session.add(enrollment)
    db.session.commit()

    return redirect(url_for('index'))

# this is update route

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

    # POST - update values
    student.first_name = request.form['f_name']
    student.last_name = request.form['l_name']

    # Remove old enrollments
    Enrollments.query.filter_by(estudent_id=student_id).delete()

    # Add new ones
    selected_courses = request.form.getlist('courses')
    for course_id in selected_courses:
        new_enroll = Enrollments(estudent_id=student_id, ecourse_id=int(course_id))
        db.session.add(new_enroll)

    db.session.commit()
    return redirect(url_for('index'))


# this is the delete route
@app.route('/student/<int:student_id>/delete', methods=['GET'])
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)

    # Delete enrollments first
    Enrollments.query.filter_by(estudent_id=student_id).delete()

    # Delete the student
    db.session.delete(student)
    db.session.commit()

    return redirect(url_for('index'))

# this is student detail ka route
@app.route('/student/<int:student_id>')
def student_detail(student_id):
    # Get the student by ID or show 404 if not found
    student = Student.query.get_or_404(student_id)

    # Get the course IDs the student is enrolled in
    enrollment_links = Enrollments.query.filter_by(estudent_id=student_id).all()
    course_ids = [e.ecourse_id for e in enrollment_links]

    # Fetch the actual course details using the course IDs
    courses = Course.query.filter(Course.course_id.in_(course_ids)).all()

    # DEBUG (optional): Print what's fetched
    print(f"Student ID: {student_id}")
    print("Enrolled course IDs:", course_ids)
    print("Courses found:", [c.course_name for c in courses])

    # Send the data to the template
    return render_template('student_detail.html', student=student, courses=courses)

# Run only
if __name__ == '__main__':
    app.run(debug=True)
