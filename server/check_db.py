from flask import Flask
from models.niche import Niche
from extensions import db

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:overwatch23562@localhost:5432/ig_story_checker_dev'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def check_niches():
    app = create_app()
    with app.app_context():
        niches = Niche.query.all()
        if niches:
            print("Niches in the database:")
            for niche in niches:
                print(f"ID: {niche.id}, Name: {niche.name}, Order: {niche.order}")
        else:
            print("No niches found in the database.")

if __name__ == "__main__":
    check_niches()
