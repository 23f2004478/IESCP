from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

app = Flask(__name__)

load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')

db = SQLAlchemy(app)

class testDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(64))
    passhash = db.Column(db.String(256))

with app.app_context():
    db.create_all()

@app.route("/")
def test():
    # test_db = testDB(username='sample_username', passhash='sample_passhash')
    # db.session.add(test_db)
    # db.session.commit()
    test_db_get = testDB.query.get(1)

    return "<p>Flask run test passed. <br> Dotenv working. <br><br> Username: {} <br> Password: {} <br> testDB passed.</p>".format(test_db_get.username, test_db_get.passhash)