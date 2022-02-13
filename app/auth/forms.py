from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,PasswordField
from wtforms.fields.simple import BooleanField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo, ValidationError
from ..models import User

class LoginForm(FlaskForm):
    email = StringField("username:", validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField("password:", validators=[DataRequired()])
    remember_me = BooleanField("keep me logged in")
    submit  = SubmitField("log in")

class RegistrationForm(FlaskForm):
    email = StringField("email", validators=[DataRequired(), Length(1,64), Email()])
    username = StringField("username", validators=[DataRequired(), Length(1,64), Regexp("^[A-Za-z][A-Za-z0-9_.]*$",0,"only letters, numbers, underscores, dots")])
    password = PasswordField("password", validators=[DataRequired(), EqualTo("password2","passwords must match")])
    password2 = PasswordField("confirm password", validators=[DataRequired()])
    submit  = SubmitField("sign up")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("email already registered")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("username already taken")