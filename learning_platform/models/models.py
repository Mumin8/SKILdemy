from learning_platform import app, db, login_manager, bcrypt
from flask_login import UserMixin
from sqlalchemy import func
from datetime import datetime
import json
# from ../paystack import Paystack


@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(user_id)


# join user and course
user_course = db.Table('user_course',
                       db.Column('user_id', db.Integer, db.ForeignKey(
                           'user.id'), primary_key=True),
                       db.Column('course_id', db.Integer, db.ForeignKey(
                           'course.id'), primary_key=True)
                       )


# join course and subjects
course_subjects = db.Table('course_subjects',
                           db.Column('course_id', db.Integer, db.ForeignKey(
                               'course.id'), primary_key=True),
                           db.Column('subject_id', db.Integer, db.ForeignKey(
                               'subject.id'), primary_key=True)
                           )


# join couse and topics
course_topics = db.Table('course_topics',
                         db.Column('course_id', db.Integer, db.ForeignKey(
                             'course.id'), primary_key=True),
                         db.Column('topic_id', db.Integer, db.ForeignKey(
                             'topic.id'), primary_key=True)
                         )


# join subject and topics
subject_topics = db.Table('subject_topics',
                          db.Column('subject_id', db.Integer, db.ForeignKey(
                              'subject.id'), primary_key=True),
                          db.Column('topic_id', db.Integer, db.ForeignKey(
                              'topic.id'), primary_key=True)
                          )


class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    profile = db.Column(db.String(200), unique=False, default='')
    created_at = db.Column(db.DateTime(timezone=True),
                           nullable=False, default=datetime.utcnow)
    reset_token = db.Column(db.String(120), nullable=True)

    # login manager things
    authenticated = db.Column(db.Boolean, default=False)
    moderator = db.Column(db.Boolean, default=False)

    # relationship thing
    enrolling = db.relationship(
        'Course', secondary='user_course', backref='enrollers')

    time_task = db.relationship('TimeTask', backref='user', lazy='dynamic')

    # wallet = db.relationship('UserWallet', backref='user', uselist=False)

    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.email

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

    def get_id(self):
        return str(self.id)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def __repr__(self):
        return f'<User {self.fullname} {self.email}  {self.username}>'


class Course(db.Model):
    __tablename__ = "course"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    subjects = db.relationship(
        'Subject', secondary=course_subjects, backref=db.backref('courses', lazy=True))

    topics = db.relationship('Topic', secondary=course_topics,
                             lazy='subquery', backref=db.backref('courses', lazy=True))


class Topic(db.Model):
    __tablename__ = "topic"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    desc = db.Column(db.String(500), nullable=True)
    sub_topics = db.relationship('SubTopic', backref='topic', lazy='dynamic')


class SubTopic(db.Model):
    __tablename__ = "subtopic"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    desc = db.Column(db.String(250), nullable=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))


class Subject(db.Model):
    __tablename__ = "subject"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    topics = db.relationship(
        'Topic', secondary=subject_topics, backref=db.backref('subjects', lazy=True))


class TimeTask(db.Model):
    __tablename__ = "timetask"
    id = db.Column(db.Integer, primary_key=True)
    usertask = db.Column(db.String(80), nullable=True)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


# class UserWallet(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     currency = db.Column(db.String(50), default='NGN')
#     created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

#     def __repr__(self):
#         return f"UserWallet('{self.currency}', '{self.created_at}')"



# class Payment(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     # user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     # amount = db.Column(db.Integer, nullable=False)
#     # ref = db.Column(db.String(200), unique=True, nullable=False)
#     # email = db.Column(db.String(120), nullable=False)
#     verified = db.Column(db.Boolean, default=False, nullable=False)
#     date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


#     def __repr__(self):
#         return f"Payment: {self.amount}"

    # def save(self, *args, **kwargs):
    #     while not self.ref:
    #         ref = secrets.token_urlsafe(50)
    #         object_with_similar_ref = Payment.query.filter_by(ref=ref).first()
    #         if not object_with_similar_ref:
    #             self.ref = ref
    #     db.session.add(self)
    #     db.session.commit()

#     def amount_value(self):
#         return int(self.amount)*100

    
#     def verify_payment():
#         paystack = Paystack()
#         status, result = paystack.verify_payment(self.ref, self.amount)
#         if status:
#             if result['amount'] / 100 == self.amount:
#                 self.verified = True
#                 self.save()
#         if self.verified:
#             return True
#         else:
#             return False
    

class Video(db.Model):
    '''
    this is the model to allow videos to be 
    added and approved
    '''
    __tablename__ = "video"
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.String(255))
    video_path = db.Column(db.String(255))
    course = db.Column(db.String(20))
    topic = db.Column(db.String(20))
    status = db.Column(db.String(20), default='pending')

    def __repr__(self):
        return f"<Video {self.topic}>"


with app.app_context():
    db.create_all()
