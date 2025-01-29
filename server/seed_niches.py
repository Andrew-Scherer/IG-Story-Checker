from flask import Flask
from models.niche import Niche
from extensions import db

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:overwatch23562@localhost:5432/ig_story_checker_dev'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def seed_niches():
    app = create_app()
    with app.app_context():
        # Check if niches already exist
        existing_niches = Niche.query.all()
        if existing_niches:
            print("Niches already exist in the database. Skipping seeding.")
            return

        # Create initial niches
        niches = [
            Niche(name="Golf", order=0),
            Niche(name="Tennis", order=1),
            Niche(name="Football", order=2),
            Niche(name="Basketball", order=3),
        ]

        # Add niches to the database
        for niche in niches:
            db.session.add(niche)

        # Commit the changes
        db.session.commit()

        print("Niches have been successfully added to the database.")

if __name__ == "__main__":
    seed_niches()