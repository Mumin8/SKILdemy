
from learning_platform import app
from learning_platform.views.home import home_bp
from learning_platform.views.users import user_bp
from learning_platform.views.admin import admin_bp



app.register_blueprint(admin_bp)
app.register_blueprint(home_bp)
app.register_blueprint(user_bp)

if __name__ == '__main__':
    app.run(debug=True)
