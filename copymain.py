from flask import Flask, render_template, request, redirect, url_for, session, flash
import pickle, pandas as pd, numpy as np, json, os
import uuid
from models import db, SymptomHistory
from flask import Flask, render_template, request, session, redirect, url_for
from flask import render_template, request
import ast
import json
from werkzeug.security import generate_password_hash,check_password_hash
import os



app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)




# Load model and label encoder
with open("disease_model_with_le.pkl", "rb") as f:
    data = pickle.load(f)
    model = data["model"]
    le = data["label_encoder"]

# Load training data columns to get symptom names
df = pd.read_csv("dataset\Training.csv")
symptoms_list = df.columns[:-1].tolist()
symptoms_dict = {symptom.lower(): idx for idx, symptom in enumerate(symptoms_list)}

# Load description and medication data into dictionaries for fast lookup
desc_df = pd.read_csv("dataset\description.csv")
med_df = pd.read_csv("dataset\medications.csv")

desc_dict = dict(zip(desc_df['Disease'].str.lower(), desc_df['Description']))
med_dict = dict(zip(med_df['Disease'].str.lower(), med_df['Medication']))


@app.route("/predict", methods=["GET", "POST"])
def index():
    predicted_disease = None
    description = None
    medications = None
    error_msg = None

    if request.method == "POST":
        # Get symptoms from user input
        input_symptoms = request.form.get("symptoms", "").lower()
        typed_symptoms = [sym.strip() for sym in input_symptoms.split(",") if sym.strip()]

        input_vector = np.zeros(len(symptoms_list))
        matched_any = False

        for symptom in typed_symptoms:
            if symptom in symptoms_dict:
                input_vector[symptoms_dict[symptom]] = 1
                matched_any = True

        if not matched_any:
            error_msg = "None of the entered symptoms matched the database. Please check spelling or try different symptoms."
        else:
            # Predict disease
            pred_index = model.predict([input_vector])[0]
            predicted_disease = le.inverse_transform([pred_index])[0]
            
            # Lookup description and medications (case insensitive)
            key = predicted_disease.lower()
            description = desc_dict.get(key, "Description not available.")
            medications = med_dict.get(key, "Medications not available.")

            # Medications string cleanup for better display
            # if stored as string representation of list, convert to list
            try:
                import ast
                medications = ast.literal_eval(medications)
            except:
                # if not a list string, just keep as is
                medications = [medications]

            # new_entry = SymptomHistory(user_id=session['user_id'], symptoms=input_symptoms, predicted_disease=predicted_disease)
            # db.session.add(new_entry)
            # db.session.commit()

            return render_template("result.html",
                           prediction=predicted_disease,
                           description=description,
                           medications=medications,
                           symptoms=input_symptoms,
                           error=error_msg)
    return render_template('index.html')



@app.route('/')
def home():
    return render_template('home.html')

@app.route('/save_history', methods=['POST'])
def save_history():
    symptoms = request.form.get("symptoms")
    predicted_disease = request.form.get("predicted_disease")
    user_id = session.get("user_id")
    
    print(f"Received symptoms: {symptoms}")
    print(f"Received predicted_disease: {predicted_disease}")
    print(f"Received user_id: {user_id}")

    new_entry = SymptomHistory(
        user_id=user_id,
        symptoms=symptoms,
        predicted_disease=predicted_disease
    )
    db.session.add(new_entry)
    db.session.commit()

    return redirect(url_for('history'))
# Login route (to authenticate and set session)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            with open('users.json', 'r') as f:
                users = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return "No registered users", 401

        # Find user based on email
        user = next((u for u in users if u['email'] == email), None)

        if user and check_password_hash(user['password'], password):
            session['user'] = user['email']
            session['user_id'] = user['id']  # Store user ID in session
            session['user_data'] = user  # Save user info in session for profile
            return redirect(url_for('dashboard'))  # Redirect to dashboard after successful login
        else:
            return "Invalid email or password", 401

    return render_template('login.html')
# Dashboard route (after login)
@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        user = session['user']
        return render_template('dashboard.html', user=user)  # Pass user data to template
    return redirect(url_for('login'))  # Redirect to login page if not logged in



# Profile route (to display the logged-in user's profile)
@app.route('/profile')
def profile():
    if 'user_data' in session:
        user = session['user_data']  # Retrieve all user data from session
        return render_template('profile.html', user=user)  # Pass user data to template
    return redirect(url_for('login'))  # Redirect to login page if not logged in


# Logout route (to log out the user)
@app.route('/logout')
def logout():
    session.pop('user', None)  # Remove user data from session
    return redirect(url_for('login'))  # Redirect to login page

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        gender = request.form['gender']
        email = request.form['email']
        password = request.form['password']

        # Generate hashed password and user ID
        hashed_password = generate_password_hash(password)
        user_id = str(uuid.uuid4())

        # Load existing users
        try:
            with open('users.json', 'r') as f:
                users = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            users = []

        # Check if user already exists
        for user in users:
            if user['email'] == email:
                flash("User already exists!", "danger")
                return redirect(url_for('signup'))

        # Append new user
        users.append({
            "id": user_id,
            "name": name,
            "dob": dob,
            "gender": gender,
            "email": email,
            "password": hashed_password
        })

        # Save to users.json
        with open('users.json', 'w') as f:
            json.dump(users, f, indent=4)

        flash("Signup successful!", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/history')
def history():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))  # if login required

    history_entries = SymptomHistory.query.filter_by(user_id=user_id).order_by(SymptomHistory.timestamp.desc()).all()
    return render_template('history.html', entries=history_entries)


if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True, port=5000)