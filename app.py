from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'edututor_secret_key'

# Sample study content for each subject
study_materials = {
    "Science": "Science is the study of the natural world through observation and experiments. Photosynthesis is a process by which phototrophs convert light energy into chemical energy, which is later used to fuel cellular activities. The chemical energy is stored in the form of sugars, which are created from water and carbon dioxide.",
    "Math": "Math is the study of numbers, shapes, and patterns. For example, Pi is approximately 3.14 and represents the ratio of a circle's circumference to its diameter.",
    "English": "English involves reading, writing, and understanding language. A noun is a person, place, or thing."
}

# DB Initialization
def init_db():
    with sqlite3.connect('edu_users.db') as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                subject TEXT,
                level TEXT,
                learning_style TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                quiz_subject TEXT,
                quiz_score INTEGER,
                teach_back_feedback TEXT
            )
        ''')
        conn.commit()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        subject = request.form['subject']
        level = request.form['level']
        style = request.form['style']
        try:
            with sqlite3.connect('edu_users.db') as conn:
                c = conn.cursor()
                c.execute("INSERT INTO users (name, email, password, subject, level, learning_style) VALUES (?, ?, ?, ?, ?, ?)",
                          (name, email, password, subject, level, style))
                conn.commit()
        except sqlite3.IntegrityError:
            return "Email already registered!"
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        with sqlite3.connect('edu_users.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
            user = c.fetchone()
        if user:
            session['user'] = user[1]
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials!"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return render_template('dashboard.html', name=session['user'])
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    quiz_questions = {
        "Science": [
            {"question": "What is the main source of energy for the Earth?", "options": ["Sunlight", "Water", "Coal", "Wind"]},
            {"question": "Which organelle performs photosynthesis?", "options": ["Chloroplast", "Mitochondria", "Nucleus", "Ribosome"]},
            {"question": "What gas do plants absorb from the air?", "options": ["Carbon Dioxide", "Oxygen", "Nitrogen", "Hydrogen"]},
            {"question": "What is the chemical formula for water?", "options": ["H2O", "CO2", "O2", "NaCl"]},
            {"question": "What process converts sunlight into energy?", "options": ["Photosynthesis", "Respiration", "Transpiration", "Fermentation"]}
        ],
        "Math": [
            {"question": "What is the value of Pi (approx)?", "options": ["3.14", "2.72", "1.61", "1.41"]},
            {"question": "How many sides does a triangle have?", "options": ["3", "4", "5", "6"]},
            {"question": "What is 7 multiplied by 6?", "options": ["42", "36", "48", "56"]},
            {"question": "What shape has all sides equal?", "options": ["Square", "Rectangle", "Triangle", "Circle"]},
            {"question": "What is the square root of 64?", "options": ["8", "6", "7", "9"]}
        ],
        "English": [
            {"question": "What part of speech is a noun?", "options": ["Person, place or thing", "Action", "Describing word", "Connective"]},
            {"question": "What is a simile?", "options": ["Comparison using like or as", "Opposite meaning", "A question", "An exclamation"]},
            {"question": "Which tense describes actions that happened in the past?", "options": ["Past tense", "Present tense", "Future tense", "Perfect tense"]},
            {"question": "What does an adjective do?", "options": ["Describes a noun", "Shows action", "Connects clauses", "Expresses emotion"]},
            {"question": "What is the verb in the sentence: She runs fast?", "options": ["Runs", "She", "Fast", "None"]}
        ]
    }

    if request.method == 'POST':
        subject = request.form['subject']
        questions = quiz_questions.get(subject, [])
        return render_template("quiz.html", subject=subject, questions=questions)
    return render_template("quiz.html", subject=None)

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    subject = request.form['subject']
    correct_answers = {
        "Science": ['Sunlight', 'Chloroplast', 'Carbon Dioxide', 'H2O', 'Photosynthesis'],
        "Math": ['3.14', '3', '42', 'Square', '8'],
        "English": ['Person, place or thing', 'Comparison using like or as', 'Past tense', 'Describes a noun', 'Runs']
    }

    user_answers = [request.form.get(f'q{i+1}') for i in range(5)]
    score = sum(1 for ua, ca in zip(user_answers, correct_answers.get(subject, [])) if ua == ca)

    if score == 5:
        feedback = "Excellent! You mastered this topic!"
    elif score >= 3:
        feedback = "Good job! Some room for improvement."
    else:
        feedback = "Needs improvement. Try revising the topic again."

    username = session.get('user', 'guest')
    with sqlite3.connect('edu_users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO progress (username, quiz_subject, quiz_score, teach_back_feedback) VALUES (?, ?, ?, ?)",
                       (username, subject, score, feedback))
        conn.commit()

    return render_template("score.html", score=score, subject=subject, feedback=feedback)

@app.route('/choose_teach_back')
def choose_teach_back():
    subjects = list(study_materials.keys())
    return render_template('choose_teach_back.html', subjects=subjects)

@app.route('/teach_back/<subject>', methods=['GET'])
def teach_back(subject):
    material = study_materials.get(subject)
    if not material:
        return "Invalid subject", 404
    return render_template('teach_back.html', subject=subject, material=material)

@app.route('/submit_teach_back/<subject>', methods=['POST'])
def submit_teach_back(subject):
    explanation = request.form['explanation']
    if len(explanation.strip()) < 20:
        feedback = "Your explanation is too short. Try to be more detailed."
    else:
        feedback = "Good job! Your explanation covers the main points."

    username = session.get('user', 'guest')
    with sqlite3.connect('edu_users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO progress (username, quiz_subject, quiz_score, teach_back_feedback) VALUES (?, ?, ?, ?)",
                       (username, subject, 0, feedback))
        conn.commit()

    return render_template('teach_back_result.html', explanation=explanation, feedback=feedback, subject=subject)

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    response = None
    if request.method == 'POST':
        question = request.form.get('question', '').lower()

        if 'photosynthesis' in question:
            response = "Photosynthesis is the process where plants convert sunlight into chemical energy."
        elif 'pi' in question or 'circle' in question:
            response = "Pi is approximately 3.14 and represents the ratio of a circle's circumference to its diameter."
        elif 'noun' in question:
            response = "A noun is a word that refers to a person, place, or thing."
        elif 'triangle' in question:
            response = "A triangle has 3 sides."
        elif 'simile' in question:
            response = "A simile is a figure of speech comparing two unlike things using 'like' or 'as'."
        elif 'square root of 64' in question:
            response = "The square root of 64 is 8."
        elif 'verb' in question:
            response = "A verb is a word that expresses an action or a state of being."
        else:
            response = "I'm not sure, but try checking your study material or ask your teacher for more help."

    return render_template('chatbot.html', response=response, hide_nav=True)

@app.route('/progress')
def view_progress():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = session['user']
    with sqlite3.connect('edu_users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT quiz_subject, quiz_score, teach_back_feedback FROM progress WHERE username = ?", (user,))
        records = cursor.fetchall()
    return render_template("view_progress.html", records=records)


@app.route('/topic/<subject>')
def topic(subject):
    material = study_materials.get(subject)
    if not material:
        return "Topic not found", 404
    return render_template('topic.html', subject=subject, material=material)

@app.route('/test_url_build')
def test_url_build():
    try:
        link = url_for('teach_back')
    except Exception as e:
        return str(e)
    return link

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
