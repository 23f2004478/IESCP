from flask import Flask

app = Flask(__name__)

@app.route("/")
def test():
    return "<p>Test Passed.</p>"