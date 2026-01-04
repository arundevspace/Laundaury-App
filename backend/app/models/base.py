from flask_sqlalchemy import SQLAlchemy

# Initialize the SQLAlchemy instance
db = SQLAlchemy()
# Use the declarative base from SQLAlchemy
Base = db.Model