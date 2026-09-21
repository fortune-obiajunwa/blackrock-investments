from flask import Flask, render_template

from database import (
    init_db,
    migrate_database
)

from routes.auth import auth_bp
from routes.user import user_bp
from routes.admin import admin_bp


app = Flask(__name__)

app.secret_key = "blackrock-investment-development-key"


# =========================================
# REGISTER BLUEPRINTS
# =========================================

app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)


# =========================================
# HOME
# =========================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================
# START APPLICATION
# =========================================

if __name__ == "__main__":

    init_db()

    migrate_database()

    app.run(
        debug=True
    )