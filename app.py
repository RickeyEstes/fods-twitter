from flask import Flask, render_template

from routes import routes

# Create the app
app = Flask(__name__, static_path='/static')
app.register_blueprint(routes)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug="True")
