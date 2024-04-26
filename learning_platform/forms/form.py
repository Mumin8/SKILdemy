from wtforms import (
    Form, BooleanField, StringField, PasswordField,
    validators, SubmitField, ValidationError, SelectField,
    TextAreaField, DecimalField, SubmitField
)
from flask_wtf.file import (
    FileRequired, FileAllowed, FileField
)
from flask_wtf import FlaskForm
from ..models.models import User


class TopicForm(FlaskForm):
    name = StringField('Topic', [validators.DataRequired("Topic is required")])
    submit = SubmitField('Add Topic')


class SubTopicForm(FlaskForm):
    name = StringField(
        'Sub topic', [validators.DataRequired("Topic is required")])
    submit = SubmitField('Add Topic')


class SubjectForm(FlaskForm):
    name = StringField('Subject or Language', [
                       validators.DataRequired("Topic is required")])
    submit = SubmitField('Add Sub Topic')


class CourseForm(FlaskForm):
    name = StringField('Course Name', [validators.DataRequired(
        "The name of the course is required")])
    description = TextAreaField('Description', [validators.DataRequired(
        "Write a brief description of the course")])
    price = DecimalField(
        'Price', [validators.DataRequired("Enter the price for the course")])
    submit = SubmitField('Create Course')


class LanguageForm(FlaskForm):
    LANGUAGES_CHOICES = [('python', 'Python'), ('javascript', 'JavaScript')]
    language = SelectField('Select Language', choices=LANGUAGES_CHOICES)


class LoginForm(FlaskForm):
    email = StringField(
        'Email', [validators.Length(min=6, max=35), validators.Email()])
    password = PasswordField(
        'Password', [validators.DataRequired("please enter password to please")])


class ResetForm(FlaskForm):
    email = StringField(
        'Email', [validators.Length(min=6, max=35), validators.Email()])


class NewPasswordForm(FlaskForm):
    password = PasswordField(
        'Password', [validators.DataRequired("please enter password to please")])


class Registration(FlaskForm):
    fullname = StringField('Full name', [validators.Length(min=4, max=25)])
    username = StringField('User name', [validators.Length(min=4, max=25)])
    email = StringField(
        'Email', [validators.Length(min=6, max=35), validators.Email()])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    profile = FileField('Profile ', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'],
                                                            "Image only please")])
    submit = SubmitField('Register')

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError("This username is already taken")

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError("This email is already taken")

# class PaymentForm(FlaskForm):
#     amount = IntegerField('Amount', validators=[DataRequired()])
#     email = StringField('Email', validators=[DataRequired(), Email()])
#     verified = BooleanField('Verified')
