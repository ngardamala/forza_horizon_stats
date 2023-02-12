from flask import Flask, render_template, request


app = Flask(__name__)


@app.route('/')
def index():
	return render_template('cars.html')


@app.route('/cars/')
def cars():
	return render_template('cars.html')


@app.route('/road/')
def road():
	return render_template('road.html')


@app.route('/dirt/')
def dirt():
	return render_template('dirt.html')


@app.route('/offroad/')
def offroad():
	return render_template('offroad.html')


@app.route('/tracks/')
def tracks():
	return render_template('tracks.html')


@app.route('/championships/')
def championships():
	return render_template('championships.html')


@app.route('/generate/')
def generate():
	return render_template('generate.html')