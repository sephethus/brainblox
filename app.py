from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_wtf import FlaskForm
from flask_migrate import Migrate
from wtforms import TextAreaField, SubmitField, FieldList, FormField, StringField, BooleanField
from wtforms.validators import DataRequired, Optional
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect
import bleach
import os

import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flashcards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

class Flashcard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    choices = db.relationship('Choice', backref='flashcard', lazy=True)
    explanation = db.Column(db.Text, nullable=False)
    additional_content = db.Column(db.Text, nullable=True)
    choices = db.relationship('Choice', backref='flashcard', lazy=True, cascade='all, delete-orphan')

class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    flashcard_id = db.Column(db.Integer, db.ForeignKey('flashcard.id'), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    flashcard_id = db.Column(db.Integer, db.ForeignKey('flashcard.id'), nullable=False)
    

class ChoiceForm(FlaskForm):
    content = StringField('Choice')
    is_correct = BooleanField('Correct')

    class Meta:
        csrf = False

class FlashcardForm(FlaskForm):
    question = TextAreaField('Question', validators=[DataRequired()])
    choice_1 = StringField('Choice 1', validators=[DataRequired()])
    choice_1_correct = BooleanField('Correct?')

    choice_2 = StringField('Choice 2', validators=[DataRequired()])
    choice_2_correct = BooleanField('Correct?')

    choice_3 = StringField('Choice 3', validators=[DataRequired()])
    choice_3_correct = BooleanField('Correct?')

    # Define additional choices as optional
    choice_4 = StringField('Choice 4', validators=[Optional()])
    choice_4_correct = BooleanField('Correct?')

    choice_5 = StringField('Choice 5', validators=[Optional()])
    choice_5_correct = BooleanField('Correct?')

    choice_6 = StringField('Choice 6', validators=[Optional()])
    choice_6_correct = BooleanField('Correct?')

    choice_7 = StringField('Choice 7', validators=[Optional()])
    choice_7_correct = BooleanField('Correct?')
    explanation = TextAreaField('Explanation', validators=[DataRequired()])
    additional_content = TextAreaField('Additional Content', validators=[Optional()])
    submit = SubmitField('')

@app.route('/')
def index():
    flashcards = Flashcard.query.all()
    return render_template('index.html', flashcards=flashcards)

@app.route('/submit_answer/<int:id>', methods=['POST'])
def submit_answer(id):
    flashcard = Flashcard.query.get_or_404(id)
    user_answer = request.form.get('user_answer')

    correct_choice = next((choice for choice in flashcard.choices if choice.is_correct), None)

    feedback = 'correct' if correct_choice and str(correct_choice.id) == user_answer else 'incorrect'

    # Make sure you are passing all flashcards or just the relevant ones
    flashcards = Flashcard.query.all()  # This could be one card or all, depending on your logic

    return render_template(
        'index.html',
        flashcards=flashcards,  # Pass the list of flashcards back
        selected_card_id=flashcard.id, 
        feedback=feedback,
        correct_choice=correct_choice,
        user_answer=user_answer,
        show_explanation=True 
    )

@app.route('/add', methods=['GET', 'POST'])
def add():
    form = FlashcardForm()
    form.submit.label.text = 'Add Card'
    
    if form.validate_on_submit():
        cleaned_question = bleach.clean(form.question.data, tags=['p'], strip=True)
        cleaned_explanation = bleach.clean(form.explanation.data, tags=[], strip=True)
        cleaned_additional_content = bleach.clean(form.additional_content.data, tags=['p'], strip=True)

        # Create flashcard with sanitized data
        flashcard = Flashcard(
            question=cleaned_question,
            explanation=cleaned_explanation,
            additional_content=cleaned_additional_content
        )
        db.session.add(flashcard)
        db.session.commit()

        choices = [
            (form.choice_1.data, form.choice_1_correct.data),
            (form.choice_2.data, form.choice_2_correct.data),
            (form.choice_3.data, form.choice_3_correct.data),
            (form.choice_4.data, form.choice_4_correct.data),
            (form.choice_5.data, form.choice_5_correct.data),
            (form.choice_6.data, form.choice_6_correct.data),
            (form.choice_7.data, form.choice_7_correct.data),
        ]
        
        for content, is_correct in choices:
            if content:
                choice = Choice(
                    content=content,
                    is_correct=is_correct,
                    flashcard_id=flashcard.id
                )
                db.session.add(choice)

        db.session.commit()
        print(request.form)
        return redirect(url_for('index') + f'#flashcard-{flashcard.id}')
    else:
        print(form.errors)
    return render_template('add.html', form=form)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    flashcard = Flashcard.query.get_or_404(id)
    form = FlashcardForm(obj=flashcard)
    form.submit.label.text = 'Update'
    if form.validate_on_submit():
        flashcard.question = form.question.data
        flashcard.choices=form.choices.data
        flashcard.explanation = form.explanation.data
        flashcard.additional_content = form.additional_content.data
        db.session.commit()
        flash('Flashcard updated successfully')
        return redirect(url_for('index') + f'#flashcard-{flashcard.id}')
    return render_template('edit.html', form=form, flashcard=flashcard)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    flashcard = Flashcard.query.get_or_404(id)
    db.session.delete(flashcard)
    db.session.commit()
    flash('Flashcard deleted successfully')
    return redirect(url_for('index') + f'#flashcard-{flashcard.id}')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file_url = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        return jsonify({'location': file_url})
    return jsonify({'error': 'File type not allowed'}), 400

@app.context_processor
def utility_processor():
    return dict(str=str)

if __name__ == '__main__':
    app.run(debug=True)