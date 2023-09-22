from flask import Flask, render_template , json, redirect, url_for, request, flash, session, request
from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField, ValidationError, DateField
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from forms import PrintRequestBW, PrintRequestColor, LoginForm
from datetime import datetime
import auth
import os
from db import db

# Get the config so configuration errors can be caught immediately on server start
import config
cfg = config.get_config()

app = Flask(__name__ , template_folder="templates", static_folder="static")
app.config['SECRET_KEY'] = cfg.secret_key

# triple slash needed for absolute path ¯\_(ツ)_/¯
sqlite_uri = 'sqlite:///' + os.path.abspath(cfg.sqlite_db)
app.config['SQLALCHEMY_DATABASE_URI'] = sqlite_uri
print(f'sqlite db will be stored at {sqlite_uri}')
db.init_app(app)

loginManager = LoginManager()
loginManager.init_app(app)
loginManager.login_view = 'login'

@loginManager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

def getdbconnection():
    conn = sqlite3.connect('printlogs.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    #here will be the home page and nav links
    return render_template("home.html")

@app.route("/login", methods = ["GET", "POST"])
#login page will recieve authentication from citadel to authorize user to print to cif printers
def login():
    form = LoginForm()
    form.validate()
    if current_user.is_authenticated:
        return redirect(url_for('printselection'))
    else:
        netid = None
        password = None
        if form.validate_on_submit():
            #only using auth() for testing purposes, will be replaced with auth_citadel() later, which only runs on linux
            #user = auth.auth_citadel(form.netid.data, form.password.data)
            user = auth.auth(form.netid.data, form.password.data)

            if user:
                login_user(user)
                return redirect(url_for('printselection'))
            else:
                flash("NetID not found. Please try again. Don't have a lab account? Register here.")
        else:
            flash("Invalid information, please try again.")

    netid = ''
    password = ''
    return render_template("login.html", form = form)

@login_required
@app.route("/logout")
def logout():
    logout_user()
    if session.get('was_once_logged_in'):
        del session['was_once_logged_in']
        flash("Logout Successful")

    return redirect(url_for('login'))

#@login_required
@app.route("/printerselection")
def printselection():
    return render_template("printerselection.html")

#@login_required
@app.route("/printbw", methods=['GET', 'POST'])
def printbw():
    form = PrintRequestBW()
    if request.method == "POST" and form.validate():
        if form.validate_on_submit:
            print(form.printall.data)
            print(form.startpage.data)
            print(form.endpage.data)
            return redirect(url_for('printsent'))
        else: 
            return "Form invalid"
    return render_template("printbw.html", form = form)

#@login_required
@app.route("/printcolor", methods=['GET', 'POST'])
def printcolor():
    form = PrintRequestColor()
    if request.method == "POST" and form.validate():
        if form.validate_on_submit:
            return redirect(url_for('printsent'))
        else: 
            return "Form invalid"
        #uncomment this for form.validate_on_submit once database is initialized
        #conn = getdbconnection()
        #conn.execute("INSERT INTO PrintLogs (filename, printer, datetime, copies) VALUES (?, ?, ?, ?);", (os.path.basename((form.file.data).name)), "Color", (datetime.now().strftime("%m/%d/%Y %H:%M:%S"), form.copies.data))
        #conn.close()
    #here will be the print form that will send print information to the print server
    return render_template("printcolor.html", form = form)

@app.route("/printsent")
def printsent():
    return "Print Job Recieved"


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run()
