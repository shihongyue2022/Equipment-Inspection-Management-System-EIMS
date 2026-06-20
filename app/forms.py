from flask_wtf import FlaskForm


class CsrfForm(FlaskForm):
    """HTML forms keep their fields in templates; this form supplies CSRF."""

