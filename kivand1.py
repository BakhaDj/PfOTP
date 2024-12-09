import psycopg2
import random
import requests
from datetime import datetime, timedelta
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock

# PostgreSQL настройки
DB_HOST = '192.168.1.13'
DB_NAME = 'otp_data'
DB_USER = 'otp'
DB_PASSWORD = 'myotp2207'

# Telegram Bot API Token и чат администратора
TELEGRAM_BOT_TOKEN = "7884636536:AAF57CwCyyy-u8yywBxmcQga1FLGURkwuH4"
TELEGRAM_CHAT_ID = "5750719490"

# Подключение к базе данных
def connect_db():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# Проверка учетных данных пользователя
def check_user_credentials(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE username_name = %s AND password_hash = %s", (username, password))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None

# Генерация нового OTP
def generate_otp(user_id):
    otp_code = str(random.randint(1000, 9999))
    expires_at = datetime.now() + timedelta(seconds=30)
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO OTP (user_id, otp_code, created_at, expires_at) VALUES (%s, %s, NOW(), %s)",
        (user_id, otp_code, expires_at)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return otp_code

# Удаление устаревших OTP
def delete_expired_otp():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM OTP WHERE expires_at <= NOW()")
    conn.commit()
    cursor.close()
    conn.close()

# Экран авторизации
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        title = Label(text="OTPsec", font_size=32, bold=True)
        layout.add_widget(title)

        self.username_input = TextInput(hint_text="Login", multiline=False)
        layout.add_widget(self.username_input)

        self.password_input = TextInput(hint_text="Password", multiline=False, password=True)
        layout.add_widget(self.password_input)

        login_button = Button(text="Connect", size_hint=(0.6, None), height=50)
        login_button.bind(on_press=self.on_button_press)
        layout.add_widget(login_button)

        self.add_widget(layout)

    def on_button_press(self, instance):
        username = self.username_input.text
        password = self.password_input.text

        if check_user_credentials(username, password):
            self.manager.get_screen("main").set_user(username)
            self.manager.current = "main"
        else:
            self.username_input.hint_text = "Invalid login"
            self.password_input.hint_text = "Try again"
            self.username_input.text = ""
            self.password_input.text = ""

# Главный экран
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_user = None
        self.role = None
        self.code_generation_allowed = True
        self.time_left_for_code = 0
        self.time_left_for_next_code = 0
        self.timer_event = None
        self.timer_next_code_event = None

        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        # Профиль пользователя
        self.profile_label = Label(text="", font_size=16)
        self.layout.add_widget(self.profile_label)

        # Код
        self.otp_label = Label(text="Press Generate", font_size=40, bold=True)
        self.layout.add_widget(self.otp_label)

        # Таймеры
        self.timer_label = Label(text="Code valid for: -- seconds", font_size=16)
        self.layout.add_widget(self.timer_label)
        self.next_code_label = Label(text="Next code available in: -- seconds", font_size=16)
        self.layout.add_widget(self.next_code_label)

        # Кнопка "Создать код"
        generate_button = Button(text="Generate Code", size_hint=(0.6, None), height=50)
        generate_button.bind(on_press=self.generate_new_code)
        self.layout.add_widget(generate_button)

        # Поле ввода сообщения
        self.message_input = TextInput(hint_text="Enter message to admin", multiline=True, size_hint=(1, None), height=100)
        self.layout.add_widget(self.message_input)

        # Кнопка "Отправить сообщение"
        send_button = Button(text="Send to Admin", size_hint=(0.6, None), height=50)
        send_button.bind(on_press=self.send_message_to_admin)
        self.layout.add_widget(send_button)

        # Кнопка "Выйти"
        logout_button = Button(text="Logout", size_hint=(0.6, None), height=50)
        logout_button.bind(on_press=self.logout)
        self.layout.add_widget(logout_button)

        self.add_widget(self.layout)

    def set_user(self, username):
        self.current_user = username
        self.profile_label.text = f"Profile: {username}"

    def generate_new_code(self, instance):
        if not self.code_generation_allowed:
            self.otp_label.text = "Wait before generating!"
            return

        user_id = self.get_user_id()
        delete_expired_otp()
        new_code = generate_otp(user_id)
        self.otp_label.text = new_code

        self.time_left_for_code = 30
        self.time_left_for_next_code = 60
        self.code_generation_allowed = False

        self.timer_event = Clock.schedule_interval(self.update_code_timer, 1)
        self.timer_next_code_event = Clock.schedule_interval(self.update_next_code_timer, 1)

    def get_user_id(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM Users WHERE username_name = %s", (self.current_user,))
        user_id = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return user_id

    def update_code_timer(self, dt):
        self.time_left_for_code -= 1
        if self.time_left_for_code > 0:
            self.timer_label.text = f"Code valid for: {self.time_left_for_code} seconds"
        else:
            self.timer_label.text = "Code expired"
            self.otp_label.text = "Press Generate"
            Clock.unschedule(self.timer_event)

    def update_next_code_timer(self, dt):
        self.time_left_for_next_code -= 1
        if self.time_left_for_next_code > 0:
            self.next_code_label.text = f"Next code available in: {self.time_left_for_next_code} seconds"
        else:
            self.next_code_label.text = "You can generate a new code!"
            self.code_generation_allowed = True
            Clock.unschedule(self.timer_next_code_event)

    def send_code_to_admin(self, code):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"User: {self.current_user}\nRole: {self.role}\nTime: {timestamp}\nGenerated Code: {code}"

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}

        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                print("Code sent successfully!")
            else:
                print("Failed to send code.")
        except Exception as e:
            print(f"Error sending code: {e}")

    def send_message_to_admin(self, instance):
        user_message = self.message_input.text
        if not user_message.strip():
            print("Message is empty.")
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"User: {self.current_user}\nRole: {self.role}\nTime: {timestamp}\nMessage: {user_message}"

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                print("Message sent successfully!")
                self.message_input.text = ""
            else:
                print("Failed to send message.")
        except Exception as e:
            print(f"Error sending message: {e}")

    def logout(self, instance):
        self.manager.current = "login"

# Приложение
class LoginApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(MainScreen(name="main"))
        return sm


if __name__ == "__main__":
    LoginApp().run()