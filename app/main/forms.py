from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectMultipleField
from wtforms.fields.choices import SelectField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError
from flask_pagedown.fields import PageDownField
from ..models import Tag

class PostForm(FlaskForm):
    header = StringField("header of your post:", validators=[DataRequired(), Length(1,80)])
    body = PageDownField("post body:", validators=[DataRequired()])
    tagging = SelectMultipleField("tag:", validators=[DataRequired()], coerce=int)
    submit = SubmitField("submit")

    def validate_tagging(form, field):
        if len(form.tagging.data) != 3:
            raise ValidationError("3 tags required")

class CommentForm(FlaskForm):
    body = PageDownField("write your comment:", validators=[DataRequired()])
    submit = SubmitField("submit")

class PostFilterForm(FlaskForm):
    header  = StringField("search by header:", validators=[Length(0,80)])
    tag = SelectField("category:", validators=[DataRequired()], coerce=int)
    time_order = SelectField("order by time:", choices=[(1, "new to old"),(2, "old to new")], validators=[DataRequired()], coerce=int)
    submit = SubmitField("filter")
