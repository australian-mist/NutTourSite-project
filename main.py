import datetime
import requests

from flask import Flask, request, redirect, abort
from flask import render_template, make_response, session
from flask_login import LoginManager, login_user, login_required
from flask_login import logout_user, current_user

from data import db_session
from data.news import News
from data.users import User
from forms.add_news import NewsForm
from forms.user import RegisterForm
from loginform import LoginForm

import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)

app.config['SECRET_KEY'] = 'too short key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/news.sqlite'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)  # год


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/forest')
def forest():
    return render_template('forest.html')


@app.route('/rivers')
def rivers():
    return render_template('rivers.html')


@app.route('/sea')
def sea():
    return render_template('sea.html')


@app.route('/map')
def map():
    return render_template('map.html')


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        return render_template('login.html', title='Повторная авторизация',
                               message='Неверный логин или пароль',
                               form=form)
    return render_template('login.html',
                           title='Авторизация',
                           form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html',
                                   title='Проблемы с регистрацией',
                                   message='Пароли не совпадают',
                                   form=form)
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html',
                                   title='Проблемы с регистрацией',
                                   message='Такой пользователь уже есть',
                                   form=form)
        user = User(name=form.name.data,
                    email=form.email.data,
                    about=form.about.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/mail', methods=['GET', 'POST'])
def mail():
    if request.method == 'GET':
        return render_template('mail.html', title='e-mail')

    elif request.method == 'POST':
        email = 'NextProDanceHall@yandex.ru'
        password = 'pxtpfondojwvfsod'

        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = request.form.get('email')
        msg['Subject'] = 'nutTour'
        text = 'Вы зарегистрировались на туристический поход'
        msg.attach(MIMEText(text, 'plain'))

        server = smtplib.SMTP_SSL(host='smtp.yandex.ru', port=465)
        server.login(email, password)
        server.send_message(msg)
        server.quit()
        return render_template('success.html')


@app.errorhandler(404)
def http_404_error():
    return render_template('error.html', title='error')


@app.route('/success')
def success():
    return render_template('success.html', title='--code--')


if __name__ == '__main__':
    db_session.global_init('db/news.sqlite')
    app.run(host='127.0.0.1', port=5000, debug=True)
