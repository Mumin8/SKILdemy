from learning_platform import app, db, login_manager, bcrypt
from flask_login import UserMixin
from sqlalchemy import func
from datetime import datetime
import uuid


@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(user_id)


# join user and course
user_course = db.Table('user_course',
                       db.Column('user_id', db.String(36), db.ForeignKey(
                           'user.id'), primary_key=True),
                       db.Column('course_id', db.String(36), db.ForeignKey(
                           'course.id'), primary_key=True)
                       )


# join couse and topics
course_topics = db.Table('course_topics',
                         db.Column('course_id', db.String(36), db.ForeignKey(
                             'course.id'), primary_key=True),
                         db.Column('topic_id', db.String(36), db.ForeignKey(
                             'topic.id'), primary_key=True)
                         )


class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.String(36), primary_key=True, default= lambda: str(uuid.uuid4()))
    fullname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    profile = db.Column(db.String(200), unique=False, default='')
    created_at = db.Column(db.DateTime(timezone=True),
                           nullable=False, default=datetime.now)
    reset_token = db.Column(db.String(120), nullable=True)

    authenticated = db.Column(db.Boolean, default=False)
    moderator = db.Column(db.Boolean, default=False)

    enrolling = db.relationship(
        'Course', secondary='user_course', backref='enrollers')

    time_task = db.relationship('TimeTask', backref='user', lazy='dynamic')

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

    id = db.Column(db.String(36), primary_key=True, default= lambda: str(uuid.uuid4()))
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    rate = db.Column(db.Numeric(10, 2), nullable=False, default=1.00)
    enrolled_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now())
    duration = db.Column(db.Integer, nullable=False, default=3)
    discount = db.Column(db.Integer, nullable=True)

    def update(self, update_):
        self.updated_at = update_

    def get_updated(self):
        return self.updated_at
    

    def update_enrolled_at(self, enrolled):
        self.enrolled_at = enrolled
        db.session.commit()

    topics = db.relationship('Topic', secondary=course_topics,
                             lazy='subquery', backref=db.backref('courses', lazy=True))



class Topic(db.Model):
    __tablename__ = "topic"

    id = db.Column(db.String(36), primary_key=True, default= lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    desc = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    sub_topics = db.relationship('SubTopic', backref='topic', lazy='dynamic')
    


class SubTopic(db.Model):
    __tablename__ = "subtopic"

    id = db.Column(db.String(36), primary_key=True, default= lambda: str(uuid.uuid4()))
    name = db.Column(db.String(80), nullable=False)
    desc = db.Column(db.String(250), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    topic_id = db.Column(db.String(36), db.ForeignKey('topic.id'))


class TimeTask(db.Model):
    __tablename__ = "timetask"
    id = db.Column(db.String(36), primary_key=True, default= lambda: str(uuid.uuid4()))
    usertask = db.Column(db.String(80), nullable=True)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'))
    



class Video(db.Model):
    '''
    this is the model to allow videos to be 
    added and approved
    '''
    __tablename__ = "video"
    id = db.Column(db.String(36), primary_key=True, default= lambda: str(uuid.uuid4()))
    video_id = db.Column(db.String(255))
    video_path = db.Column(db.String(255))
    course = db.Column(db.String(20))
    topic = db.Column(db.String(20))
    status = db.Column(db.String(20), default='pending')

    def __repr__(self):
        return f"<Video {self.topic}>"


with app.app_context():
    db.create_all()
