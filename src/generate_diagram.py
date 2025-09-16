from eralchemy2 import render_er

# Import Base from your models
from models import Base

if __name__ == "__main__":
    # Generate the ER diagram from SQLAlchemy's Base metadata
    # The output will be saved as 'diagram.png' in the project root
    render_er(Base, 'diagram.png')
    print("Database diagram generated: diagram.png")
