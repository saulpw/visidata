from flask import Flask, send_from_directory
from flask_cors import CORS

app = Flask(__name__)

CORS(app, resources={r'/*': {'origins': '*'}})

# Catch all possible routes
@app.route("/", defaults={"path": ""})
@app.route("/<string:path>")
@app.route("/<path:path>")
def index(path):
    return send_from_directory("./spa/dist/", path)

# Support SPA routing. If a route doesn't refer to a static file then it is
# likely JS app route and if it isn't then the JS app will handle the 404.
@app.errorhandler(404)
def not_found(_):
    return send_from_directory("./spa/dist/", "index.html")

