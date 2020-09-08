import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Configuration:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ["true", "on", 1]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

    FLASKY_MAIL_SUBJECT_PREFIX = "[Flasky]"
    FLASKY_MAIL_SENDER = "Flasky Admin <flasky@example.com>"
    FLASKY_ADMIN = os.environ.get("FLASKY_ADMIN")
    FLASKY_POSTS_PER_PAGE = 10
    FLASKY_FOLLOWERS_PER_PAGE = 10
    FLASKY_COMMENTS_PER_PAGE = 15

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        pass


class Development(Configuration):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URI"
    ) or "sqlite:///" + os.path.join(basedir, "data-dev.sqlite")


class Testing(Configuration):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URI") or "sqlite:///"


class Production(Configuration):
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URI"
    ) or "sqlite:///" + os.path.join(basedir, "data.sqlite")


config = {
    "development": Development,
    "testing": Testing,
    "production": Production,
    "default": Development,
}
