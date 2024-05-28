
from flask import Flask, render_template, request, redirect, session, flash, jsonify
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from cs50 import SQL

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///water.db")

def initialize_genders():
    genders = ['Male', 'Female', 'Non binary']
    existing_genders = db.execute("SELECT * FROM gender WHERE name IN (?, ?, ?)", *genders)
    existing_genders = [gender['name'] for gender in existing_genders]
    for gender in genders:
        if gender not in existing_genders:
            db.execute("INSERT INTO gender (name) VALUES (?)", gender)

initialize_genders()

@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('user_id'):
        return redirect('/login')
    if request.method == 'GET':
        water = db.execute("SELECT daily_water_intake FROM user WHERE id_user = ?", session['user_id'])
        total_volume = db.execute("SELECT SUM(volume) as total_volume FROM water WHERE id_user = ?", session['user_id'])
        return render_template('index.html', water=water[0]['daily_water_intake'], total_volume=total_volume[0]['total_volume'])
    elif request.method == 'POST':
        if 'plus-ml' in request.form:
            return handle_plus_ml()
        elif 'water-intake' in request.form:
            return handle_water_intake()
        elif 'return' in request.form:
            return return_water()

def handle_plus_ml():
    new_volume = 100
    add_water(session['user_id'], new_volume)
    return redirect('/')

def handle_water_intake():
    try:
        new_volume = int(request.form['water-intake'])
        if 50 <= new_volume <= 7000:
            add_water(session['user_id'], new_volume)
        else:
            flash('Enter in the range from 50 ml to 7 l')
            return redirect('/')
    except ValueError:
        flash('Invalid input!')
    return redirect('/')

def return_water():
    db.execute("DELETE FROM water WHERE id_water IN (SELECT id_water FROM water WHERE id_user = ? ORDER BY datetime DESC LIMIT 1)",session['user_id'])
    return redirect('/')

def add_water(user_id, volume):
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.execute("INSERT INTO water (id_user, datetime, volume) VALUES (?, ?, ?)", user_id, time, volume)

@app.route('/choice1', methods=['GET', 'POST'])
def choice1():
    if not session.get('user_id'):
        return redirect('/login')
    if request.method == 'GET':
        return render_template('choice1.html')
    elif request.method == 'POST':
        choice1 = request.form.get('choice1')
        if choice1 == 'yes':
            return redirect('/choice2')
        elif choice1 == 'no':
            return redirect('/')

@app.route('/choice2', methods=['GET', 'POST'])
def choice2():
    if not session.get('user_id'):
        return redirect('/login')

    if request.method == 'GET':
        return render_template('choice2.html')
    elif request.method == 'POST':
        gender = request.form.get('gender')
        weight = request.form.get('weight')

        if gender and weight:
            try:
                weight = int(weight)
                if gender == 'Male':
                    daily_water_intake = weight * 40
                elif gender == 'Female' or gender == 'Non binary':
                    daily_water_intake = weight * 30
                else:
                    flash('Invalid gender selected. Please choose your gender.')
                    return redirect('/choice2')

                gender_id = db.execute("SELECT id_gender FROM gender WHERE name = ?", gender)[0]['id_gender']

                if 'go' in request.form:
                    db.execute("UPDATE user SET id_gender = ?, weight = ?, daily_water_intake = ? WHERE id_user = ?",
                               gender_id, weight, daily_water_intake, session['user_id'])
                    return redirect('/')
            except ValueError:
                flash('Invalid weight entered. Please enter a number.')
                return redirect('/choice2')
        else:
            flash('Please fill out all fields.')
            return redirect('/choice2')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session.get('user_id'):
        return redirect('/login')

    if request.method == 'GET':
        user_login = db.execute("SELECT login FROM user WHERE id_user = ?", session['user_id'])
        user_weight = db.execute("SELECT weight FROM user WHERE id_user = ?", session['user_id'])
        user_gender = db.execute("SELECT name FROM gender WHERE id_gender = (SELECT id_gender FROM user WHERE id_user = ?)", session['user_id'])
        return render_template('profile.html', user_login=user_login[0]['login'], user_weight=user_weight[0]['weight'], user_gender=user_gender[0]['name'])
    if request.method == 'POST':
        if 'change' in request.form:
            return redirect('/choice2')

@app.route('/chart', methods=['GET'])
def chart():
    return render_template('chart.html')

@app.route('/chart_data_daily', methods=['GET'])
def chart_data_daily():

    # Fake
    water_statistic = [
        {'day_of_week': '0', 'total_volume': 100},
        {'day_of_week': '1', 'total_volume': 150},
        {'day_of_week': '2', 'total_volume': 200},
        {'day_of_week': '3', 'total_volume': 250},
        {'day_of_week': '4', 'total_volume': 300},
        {'day_of_week': '5', 'total_volume': 350},
        {'day_of_week': '6', 'total_volume': 400}
    ]
    # Fake

    # Real
    # water_statistic = db.execute(
    #     "SELECT strftime('%w', datetime) as day_of_week, SUM(volume) as total_volume FROM water WHERE id_user = ? GROUP BY day_of_week ORDER BY day_of_week",
    #     session['user_id'])

    # Real

    day_map = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    labels = [day_map[int(data['day_of_week'])] for data in water_statistic]
    data_points = [data['total_volume'] for data in water_statistic]

    data = {
        'labels': labels,
        'datasets': [
            {
                'label': 'Total Volume by Day of Week',
                'data': data_points,
                'fill': False,
                'backgroundColor': 'rgba(41, 82, 155, 0.8)',
                'lineTension': 0.1
            }
        ]
    }
    return jsonify(data)

@app.route('/chart_data_montly', methods=['GET'])
def chart_data_montly():
    #Fake
    water_statistic = [
        {'month': 'January', 'total_volume': 500},
        {'month': 'February', 'total_volume': 600},
        {'month': 'March', 'total_volume': 700},
        {'month': 'April', 'total_volume': 800},
        {'month': 'May', 'total_volume': 900},
        {'month': 'June', 'total_volume': 1000},
        {'month': 'July', 'total_volume': 1100},
        {'month': 'August', 'total_volume': 1200},
        {'month': 'September', 'total_volume': 1300},
        {'month': 'October', 'total_volume': 1400},
        {'month': 'November', 'total_volume': 1500},
        {'month': 'December', 'total_volume': 1600}
    ]

    labels = [data['month'] for data in water_statistic]
    data_points = [data['total_volume'] for data in water_statistic]
    # Fake

    #Real
    # water_statistic = db.execute(
    #     "SELECT strftime('%m', datetime) as month, SUM(volume) as total_volume FROM water WHERE id_user = ? GROUP BY month ORDER BY month",
    #     session.get('user_id'))
    #
    # # Map months for display
    # month_map = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
    #              'November', 'December']
    #
    # labels = [month_map[int(data['month']) - 1] for data in water_statistic]
    # data_points = [data['total_volume'] for data in water_statistic]
    #Real

    data = {
        'labels': labels,
        'datasets': [
            {
                'label': 'Total Volume by Month',
                'data': data_points,
                'fill': False,
                'backgroundColor': 'rgb(41, 82, 155)',
                'borderColor': 'rgb(41, 82, 155)',
                'lineTension': 0.1
            }
        ]
    }
    return jsonify(data)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        repassword = request.form.get('repassword')
        if not login or not password or not repassword:
            flash('Provide login, password and repeat password!')
            return redirect('/signup')
        if password != repassword:
            flash('Passwords are different! Try again!')
            return redirect('/signup')
        user = db.execute("SELECT * FROM user WHERE login = ?", login)
        if len(user) == 1:
            flash('You already have an account! Please log in!')
            return redirect('/login')
        password = generate_password_hash(password)

        db.execute("INSERT INTO user (login, password) VALUES(?, ?)", login, password)
        flash('You successfully registered!')
        user = db.execute("SELECT * FROM user WHERE login = ?", login)
        session['user_id'] = user[0]['id_user']
        return redirect('/choice1')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        if not login or not password:
            flash('Provide login and password! Try again!')
            return redirect('/login')
        user = db.execute("SELECT * FROM user WHERE login = ?", login)
        if len(user) != 1:
            flash('No such login! Try again!')
            return redirect('/login')
        if not check_password_hash(user[0]['password'], password):
            flash('Wrong password! Try again!')
            return redirect('/login')
        else:
            session['user_id'] = user[0]['id_user']
            return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
