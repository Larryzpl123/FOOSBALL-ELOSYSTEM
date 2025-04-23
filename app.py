#import Flask
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from ai_modules.adaptive_engine import AdaptiveEngine
from ai_modules.content_generator import ContentGenerator
from ai_modules.assessment_analyzer import AssessmentAnalyzer
import numpy as np

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    learning_style = db.Column(db.String(50))
    knowledge_level = db.Column(db.Float)
    progress = db.Column(db.JSON)

# AI Modules
adaptive_engine = AdaptiveEngine()
content_gen = ContentGenerator()
assess_analyzer = AssessmentAnalyzer()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        new_user = User(username=username)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/assessment')
    return render_template('register.html')

@app.route('/assessment', methods=['GET', 'POST'])
def learning_assessment():
    if request.method == 'POST':
        responses = []
        for i in range(1, 11):
            responses.append(int(request.form[f'q{i}']))
        
        learning_style, knowledge_gap = assess_analyzer.analyze(responses)
        
        user = User.query.filter_by(username=session['username']).first()
        user.learning_style = learning_style
        user.knowledge_level = knowledge_gap
        db.session.commit()
        
        return redirect('/dashboard')
    
    return render_template('assessment.html')

@app.route('/dashboard')
def dashboard():
    user = User.query.get(session['user_id'])
    recommended_content = adaptive_engine.recommend_content(user)
    return render_template('dashboard.html', 
                         content=recommended_content,
                         user=user)

@app.route('/learn/<topic_id>')
def learning_interface(topic_id):
    user = User.query.get(session['user_id'])
    content = content_gen.generate_content(topic_id, user.learning_style)
    return render_template('learning_interface.html',
                          content=content,
                          topic_id=topic_id)

@app.route('/ask', methods=['POST'])
def ai_assistant():
    user_question = request.form['question']
    context = request.form['context']
    answer = content_gen.generate_answer(user_question, context)
    return {'answer': answer}

@app.route('/quiz/<topic_id>')
def generate_quiz(topic_id):
    user = User.query.get(session['user_id'])
    quiz = content_gen.generate_quiz(topic_id, user.knowledge_level)
    return render_template('quiz.html', quiz=quiz)

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
