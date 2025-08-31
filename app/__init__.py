# ticketing/app/__init__.py

from flask import Flask
from flask_login import LoginManager

# ۱. نمونه اپلیکیشن همینجا یک بار برای همیشه ساخته می‌شود
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key-that-you-should-change'

# ۲. لاگین منیجر روی همین نمونه app تنظیم می‌شود
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "برای دسترسی به این صفحه، لطفاً وارد شوید."
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(user_id):
    from .services import get_user_by_id
    return get_user_by_id(int(user_id))

# ۳. در انتها، فایل routes را وارد می‌کنیم تا مسیرها روی همین نمونه app ثبت شوند
# این خط باید بعد از ساختن app باشد
from . import routes