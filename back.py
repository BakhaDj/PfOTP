from flask import Flask, render_template, request, redirect, url_for, session, make_response, flash
import psycopg2
# from psycopg2.extras import DictCursor
# import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Убедитесь, что это безопасно

# # Функция для подключения к базе данных PostgreSQL
def get_db_connection():
    return psycopg2.connect(
        host='95.165.70.18',       # Адрес сервера
        database='otp_data',     # Имя базы данных
        user='otp',       # Имя пользователя
        password='myotp2207',  # Пароль
    )

# Главная страница
@app.route('/')
def intro():
    user_cookie = request.cookies.get('user_cookie')
    if user_cookie:
        return f"Добро пожаловать, пользователь с cookie: {user_cookie}"
    return render_template('intro.html')

# О нас
@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

# Связаться с нами
@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        

        # Проверка учетных данных в БД
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = %s AND password = %s', (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['authenticated'] = True  # Пометка авторизации
            session['user_id'] = user[0]  # Сохраняем ID пользователя
            return redirect(url_for('code_enter'))
        else:
            return render_template('login.html', error="Неверный логин или пароль")    
    return render_template('login.html')


@app.route('/code_enter', methods=['GET', 'POST'])
def code_enter():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        user_code = request.form.get('code')

        # Проверка кода в базе данных
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT code FROM users WHERE id = %s', (session.get('user_id'),))
        correct_code = cursor.fetchone()
        conn.close()

        if correct_code and  user_code == correct_code[0]:
            return redirect(url_for('dashboard'))
        else:
            flash("Неверный код. Попробуйте снова.")
    
    return render_template('code_enter.html')


# Страница после авторизации
@app.route('/dashboard')
def dashboard():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    return render_template('dashboard.html')

# Мои задачи
@app.route('/duty')
def duty():
    return render_template('duty.html')

# Зарплата
@app.route('/sal')
def sal():
    return render_template('sal.html')

# Встречи
@app.route('/meetups')
def meetups():
    return render_template('meetups.html')



# Обработчик кнопок
@app.route('/button_action', methods=['POST'])
def button_action():
    button_id = request.form['button_id']  # ID кнопки из фронт-энда
    if button_id == 'example_button':
        return "Действие для кнопки выполнено!"
    return "Неизвестная кнопка", 400

# Выход из аккаунта
@app.route('/logout')
def logout():
    return render_template('intro.html')

if __name__ == '__main__':
    app.run(debug=True)
