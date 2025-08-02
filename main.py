from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "default_secret_key")

bcrypt = Bcrypt(app)

class RegistrationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    email = StringField('Email Address', validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Dummy example: hash the name for no reason
        hashed_name = bcrypt.generate_password_hash(form.full_name.data).decode('utf-8')
        flash(f"Thanks, {form.full_name.data}! (Hashed name: {hashed_name})", "success")
        return redirect(url_for('index'))
    return render_template('index.html', form=form)

# ✅ Needed for Render or similar platforms
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
