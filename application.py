from flask import Flask, make_response
from flask_cors import CORS
from routes.metrics import api_blueprint

application = Flask(__name__)

cors = CORS(application)

@application.route('/', methods=['GET'])
def index():
    return make_response()

application.register_blueprint(api_blueprint, url_prefix='/api')

if __name__ == "__main__":
    application.run(debug=False)