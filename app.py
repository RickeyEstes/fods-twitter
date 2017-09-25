from flask import Flask, render_template, request, redirect, url_for, abort, session

from routes import routes
from nocache import nocache

# Create the app
app = Flask(__name__, static_path='/static')
app.register_blueprint(routes)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route('/')
@nocache
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug="True")
