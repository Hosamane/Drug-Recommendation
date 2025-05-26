from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

db = SQLAlchemy()

# Define IST timezone
IST = pytz.timezone('Asia/Kolkata')

class SymptomHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)
    predicted_disease = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(IST))

