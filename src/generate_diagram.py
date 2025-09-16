from eralchemy2 import render_er

# Import the Flask-SQLAlchemy Model base
from models import db

if __name__ == "__main__":
    # Generate the ER diagram using Flask-SQLAlchemy's declarative base (db.Model)
    # The output will be saved as 'diagram.png' in the project root
    render_er(db.Model, 'diagram.png')
    print("Database diagram generated: diagram.png")
