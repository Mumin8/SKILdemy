from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user, logout_user, login_user
from learning_platform import bcrypt, db
from learning_platform.forms.form import Registration, LoginForm, ResetForm
from learning_platform.models.models import User

user_bp = Blueprint('users', __name__, static_folder='static', template_folder='templates')

@user_bp.route("/auth")
def register_auth():
    return render_template('user/home_page.html')


@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = Registration(request.form)
    if form.validate_on_submit():
        fullname = form.fullname.data
        username = form.username.data
        email = form.email.data
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        user = User(fullname=fullname, username=username, email=email,
                    password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Thank you for Registering", category='success')
        return redirect(url_for('users.register_auth'))
    return render_template('user/register.html', form=form)


@user_bp.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            user.authenticated = True
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash('Happy Coding!  😊', category='success')
            return redirect(url_for('users.userprofile'))
        flash("Invalid Credentials", category='warning')
        return redirect(url_for('users.login', user_id=user.id))
    return render_template('user/login.html', form=form)


@user_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ResetForm()
    if form.validate_on_submit():
        email = form.email.data
        # check if password exists in the database first
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_reset_token()
            user.reset_token = token
            db.session.commit()
            msg = Message('Password Reset Request',
                          sender='masschusse@gmail.com',
                          recipients=[email])
            msg.body = f'''
            Click this link to reset your password:
            {url_for('reset_password', token=token, _external=True)}
            '''
            mail.send(msg)

            flash('Check your email for the password reset link.',
                  category='success')
        else:
            flash('Email not found', category='danger')
            return redirect(url_for('users.login'))
    return render_template('user/reset_password.html', form=form, title='Reset Password')