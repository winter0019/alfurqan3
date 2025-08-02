# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    """A simple form for user login."""
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=2, max=50)]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired()]
    )
    submit = SubmitField('Login')

class CreateUserForm(FlaskForm):
    """A form for creating new users."""
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=2, max=50)]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6)]
    )
    role = StringField(
        'Role',
        validators=[DataRequired()]
    )
    submit = SubmitField('Create User')
