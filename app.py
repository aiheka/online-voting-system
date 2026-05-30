from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= MODELS =================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    role = db.Column(db.String(20), default='user')


class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    status = db.Column(db.String(20), default='Active')


class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    election_id = db.Column(db.Integer)


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    election_id = db.Column(db.Integer)
    candidate_id = db.Column(db.Integer)


# ================= ROUTES =================

@app.route('/')
def home():
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = generate_password_hash(
            request.form['password']
        )

        user = User(
            username=username,
            password=password
        )

        db.session.add(user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
                user.password,
                password):

            session['user_id'] = user.id
            session['role'] = user.role

            return redirect('/dashboard')

        return "Invalid Login"

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.route('/dashboard')
def dashboard():

    elections = Election.query.all()

    return render_template(
        'dashboard.html',
        elections=elections
    )


@app.route('/admin', methods=['GET', 'POST'])
def admin():

    if session.get('role') != 'admin':
        return "Access Denied"

    if request.method == 'POST':

        election = Election(
            title=request.form['title']
        )

        db.session.add(election)
        db.session.commit()

    elections = Election.query.all()

    return render_template(
        'admin.html',
        elections=elections
    )


@app.route('/add_candidate/<int:election_id>',
           methods=['GET', 'POST'])
def add_candidate(election_id):

    if session.get('role') != 'admin':
        return "Access Denied"

    if request.method == 'POST':

        candidate = Candidate(
            name=request.form['name'],
            election_id=election_id
        )

        db.session.add(candidate)
        db.session.commit()

        return redirect('/admin')

    return render_template(
        'add_candidate.html',
        election_id=election_id
    )


@app.route('/vote/<int:election_id>',
           methods=['GET', 'POST'])
def vote(election_id):

    candidates = Candidate.query.filter_by(
        election_id=election_id
    ).all()

    if request.method == 'POST':

        existing_vote = Vote.query.filter_by(
            user_id=session['user_id'],
            election_id=election_id
        ).first()

        if existing_vote:
            return "You already voted"

        vote = Vote(
            user_id=session['user_id'],
            election_id=election_id,
            candidate_id=request.form['candidate']
        )

        db.session.add(vote)
        db.session.commit()

        return redirect('/results')

    return render_template(
        'vote.html',
        candidates=candidates
    )


@app.route('/results')
def results():

    candidates = Candidate.query.all()

    results_data = []

    for candidate in candidates:

        total = Vote.query.filter_by(
            candidate_id=candidate.id
        ).count()

        results_data.append({
            "name": candidate.name,
            "votes": total
        })

    return render_template(
        'results.html',
        results=results_data
    )


if __name__ == '__main__':

    with app.app_context():

        db.create_all()

        admin = User.query.filter_by(
            username='admin'
        ).first()

        if not admin:

            admin = User(
                username='admin',
                password=generate_password_hash(
                    'admin123'
                ),
                role='admin'
            )

            db.session.add(admin)
            db.session.commit()

    app.run(debug=True)