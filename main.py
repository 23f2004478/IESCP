from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = '23f2004478'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

    return "<p>Flask run test passed. <br><br> Username: {} <br> Password: {} <br> testDB passed.</p>".format(test_db_get.username, test_db_get.passhash)