import os
import random
import string
import pprint
import datetime
import math
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash

load_dotenv()

app = Flask(__name__)
client = MongoClient(os.environ.get('MONGODB_URI'))
app.db = client.forza_stats
app.secret_key = b'afkljfkljfskl239293jflskdjGDHGHDGHDfslkdfj'


POINTS = {
	1: 25,
	2: 18,
	3: 15,
	4: 12,
	5: 10,
	6: 8,
	7: 6,
	8: 4,
	9: 2,
	10: 1,
	11: 0,
	12: 0
}


def championship_completed(championship_id):
	championship = app.db.championships.find_one({'_id': championship_id})
	for n, track in enumerate(championship['tracks']):
			for track_id in track.keys():
				for car_id in championship['tracks'][n][track_id]['cars'].keys():
					if championship['tracks'][n][track_id]['cars'][car_id]['time'] == 0.0:
						return False
	points_championship = []
	time_championship = []
	cars = {}
	all_cars = list(app.db.cars.find({}))
	for n, track in enumerate(championship['tracks']):
		for track_id in track.keys():
			for car_id in championship['tracks'][n][track_id]['cars'].keys():
				car = {}
				if car_id not in cars.keys():
					cars[car_id] = {}
					cars[car_id]['time'] = 0.0
					cars[car_id]['points'] = 0
				cars[car_id]['time'] += championship['tracks'][n][track_id]['cars'][car_id]['time']
				cars[car_id]['points'] += championship['tracks'][n][track_id]['cars'][car_id]['points']
	for car_id in cars.keys():
		car_points = {}
		car_points['car_id'] = car_id
		car_points['points'] = cars[car_id]['points']
		car_points['time'] = cars[car_id]['time']
		points_championship.append(car_points)
		car_time = {}
		car_time['car_id'] = car_id
		car_time['time'] = cars[car_id]['time']
		car_time['time_str'] = convert_from_seconds(car_time['time'])
		time_championship.append(car_time)
	points_championship.sort(key=lambda x: (-x.get('points'), x.get('time')))
	time_championship.sort(key=lambda x: x.get('time'))
	championship['completed'] = True
	championship['winners'].append(points_championship[0]['car_id'])
	championship['winners'].append(time_championship[0]['car_id'])
	championship['podiums'].append((points_championship[1]['car_id']))
	championship['podiums'].append((points_championship[2]['car_id']))
	championship['podiums'].append((time_championship[1]['car_id']))
	championship['podiums'].append((time_championship[2]['car_id']))
	championship_query = {'_id': championship_id}
	championship_update = {'$set': championship}
	result = app.db.championships.update_one(championship_query, championship_update, upsert=True)
	for completed_car in points_championship:
		car = {}
		for single_car in all_cars:
			if completed_car['car_id'] == single_car['_id']:
				car['championships'] = single_car['championships'] + 2
				car_query = {'_id': completed_car['car_id']}
				car_update = {'$set': car}
				result = app.db.cars.update_one(car_query, car_update, upsert=True)
				break
	for winner in championship['winners']:
		car = {}
		for single_car in all_cars:
			if winner == single_car['_id']:
				car_info = app.db.cars.find_one({'_id': winner})
				car['championships_wins'] = car_info['championships_wins'] + 1
				car_query = {'_id': winner}
				car_update = {'$set': car}
				result = app.db.cars.update_one(car_query, car_update, upsert=True)
				break
	for podium in championship['podiums']:
		car = {}
		for single_car in all_cars:
			if podium == single_car['_id']:
				car_info = app.db.cars.find_one({'_id': podium})
				car['championships_podiums'] = car_info['championships_podiums'] + 1
				car_query = {'_id': podium}
				car_update = {'$set': car}
				result = app.db.cars.update_one(car_query, car_update, upsert=True)
				break
	return True
	

def generate_track_details():
	RACE_TYPES = ['VENDOR', 'COUNTRY', 'CAR FAMILY', 'DECADE', 'ANYTHING GOES']
	SEASONS = ['SUMMER - WET SEASON', 'AUTUMN - STORM SEASON', 'WINTER - DRY SEASON', 'SPRING - HOT SEASON']
	TIME = [
		'DAWN', 'DAWN',
		'SUNRISE', 'SUNRISE',
		'MORNING', 'MORNING', 'MORNING',
		'EARLY AFTERNOON', 'EARLY AFTERNOON', 'EARLY AFTERNOON', 'EARLY AFTERNOON', 'EARLY AFTERNOON',
		'LATE AFTERNOON', 'LATE AFTERNOON', 'LATE AFTERNOON', 'LATE AFTERNOON', 'LATE AFTERNOON',
		'SUNSET', 'SUNSET', 'SUNSET',
		'EVENING', 'EVENING',
		'NIGHT',
	]
	WEATHER = [
		'CLOUDY', 'CLOUDY', 'CLOUDY', 'CLOUDY',
		'CLEAR', 'CLEAR', 'CLEAR', 'CLEAR', 'CLEAR', 'CLEAR',
		'OVERCAST', 'OVERCAST',
	]
	return random.choice(SEASONS), random.choice(TIME), random.choice(WEATHER), random.choice(RACE_TYPES)


def generate_unique_id():
	unique_id = ''
	for n in range(32):
		unique_id = unique_id + random.choice(string.ascii_letters)
	return unique_id


def convert_to_seconds(time_str):
    time_str = time_str.replace(',', '.')
    minutes = time_str.split(':')[0]
    minutes = float(minutes)
    seconds = float(time_str.split(':')[1].split('.')[0])
    if 0.0 <= seconds < 60.0:
        milliseconds = time_str.split(':')[1].split('.')[1]
        milliseconds = '0.' + milliseconds
        milliseconds = float(milliseconds)
        result_time = float(minutes * 60) + seconds + milliseconds
        result_time = round(result_time, 3)
    else:
        raise Exception('Wrong seconds value.')
    return result_time


def convert_from_seconds(time_float):
    # Split time for seconds and milliseconds
    milliseconds, seconds = math.modf(time_float)
    milliseconds = round(milliseconds, 3)
    seconds = int(seconds)
    milliseconds = str(milliseconds).split('.')[1]
    minutes = str(seconds // 60)
    seconds = str(seconds % 60)
    if minutes == '0':
        minutes = '00'
    if seconds == '0':
        seconds = '00'
    if len(minutes) == 1:
        minutes = '0' + minutes
    if len(seconds) == 1:
        seconds = '0' + seconds
    return '{}:{}.{}'.format(minutes, seconds, milliseconds)



@app.route('/')
@app.route('/cars/')
def cars():
	search_str = request.args.get('search_str')
	sort_by = request.args.get('cars_sort_by')
	if not sort_by:
		sort_by = 'added'
	cars = app.db.cars.find({}).sort(sort_by, DESCENDING)
	if search_str:
		search_str = search_str.upper()
		cars_with_search = []
		for car in cars:
			if search_str in car['vendor']:
				cars_with_search.append(car)
				continue
			elif search_str in car['model']:
				cars_with_search.append(car)
				continue
			elif search_str in str(car['year']):
				cars_with_search.append(car)
				continue
			elif search_str in car['class']:
				cars_with_search.append(car)
				continue
			elif search_str in car['type']:
				cars_with_search.append(car)
				continue
			elif search_str in car['drivetrain']:
				cars_with_search.append(car)
				continue
		cars = cars_with_search
	return render_template('cars.html', cars=cars, title='Forza Horizon 5 stats - Cars')


@app.route('/cars/<string:car_id>')
def car(car_id):
	car = app.db.cars.find_one({'_id': car_id})
	car_races = app.db.races.find({'car_id': car_id})
	car_rivals = app.db.rivals.find({'car_id': car_id})
	races = []
	for car_race in car_races:
		race = {}
		track = app.db.tracks.find_one({'_id': car_race['track_id']})
		race['track_name'] = track['name']
		race['car_type'] = track['car_type']
		race['track_id'] = track['_id']
		race['lap_time'] = car_race['lap_time_str']
		race['overall_time'] = car_race['overall_time_str']
		race['place'] = car_race['place']
		races.append(race)
	rivals = []
	for car_rival in car_rivals:
		rival = {}
		track = app.db.tracks.find_one({'_id': car_rival['track_id']})
		rival['track_name'] = track['name']
		rival['car_type'] = track['car_type']
		rival['track_id'] = track['_id']
		rival['time'] = car_rival['time_str']
		rivals.append(rival)
	return render_template('car.html', car=car, races=races, rivals=rivals, title='Forza Horizon 5 stats - {}'.format(car['model']))


@app.route('/cars/add_mastery/<string:car_id>')
def add_mastery(car_id):
	car_query = {'_id': car_id}
	car_update = {'$set': {'mastery': True}}
	result = app.db.cars.update_one(car_query, car_update, upsert=True)
	return redirect(url_for('car', car_id=car_id))


@app.route('/cars/add-car/', methods=['GET', 'POST'])
def add_car():
	if request.method == 'POST':
		car = {}
		car['vendor'] = request.form['vendor'].strip().upper()
		if len(car['vendor']) == 0:
			flash('Please, specify car vendor')
			return redirect(url_for('add_car'))
		car['model'] = request.form['model'].strip().upper()
		if len(car['model']) == 0:
			flash('Please, specify car model')
			return redirect(url_for('add_car'))
		try:
			car['year'] = int(request.form['year'].strip())
		except Exception as e:
			flash('Please, specify valid car manufactured year')
			return redirect(url_for('add_car'))
		if (car['year'] < 1900) or (car['year'] > 2023):
			flash('Please, specify valid car manufactured year')
			return redirect(url_for('add_car'))
		car['class'] = request.form['class']
		car['type'] = request.form['type']
		try:
			car['power'] = int(request.form['power'].strip())
		except Exception as e:
			flash('Please, specify valid car power in hp')
			return redirect(url_for('add_car'))
		if car['power'] < 1:
			flash('Please, specify valid car power in hp')
			return redirect(url_for('add_car'))
		try:
			car['mass'] = int(request.form['mass'].strip())
		except Exception as e:
			flash('Please, specify valid car mass in kg')
			return redirect(url_for('add_car'))
		if car['mass'] < 1:
			flash('Please, specify valid car mass in kg')
			return redirect(url_for('add_car'))
		try:
			car['max_speed'] = float(request.form['max_speed'].strip())
		except Exception as e:
			flash('Please, specify valid car max speed in km/h')
			return redirect(url_for('add_car'))
		if car['mass'] < 1.0:
			flash('Please, specify valid car max speed in km/h')
			return redirect(url_for('add_car'))
		car['drivetrain'] = request.form['drivetrain']
		try:
			car['test_track'] = convert_to_seconds(request.form['test_track'].strip().replace(',', '.'))
		except Exception as e:
			flash('Please, specify valid test track time (mm:ss.ms)')
			return redirect(url_for('add_car'))
		car['test_track_str'] = request.form['test_track'].strip().replace(',', '.')
		car['image'] = request.form['image'].strip()
		if len(car['image']) == 0:
			flash('Please, specify valid car image link')
			return redirect(url_for('add_car'))
		car['_id'] = generate_unique_id()
		car['races'] = 0
		car['wins'] = 0
		car['podiums'] = 0
		car['championships'] = 0
		car['championships_wins'] = 0
		car['championships_podiums'] = 0
		car['added'] = datetime.datetime.now()
		car['mastery'] = False
		result = app.db.cars.insert_one(car)
		flash('New car successfully added')
		return redirect(url_for('cars'))
	return render_template('add_car.html', title='Forza Horizon 5 stats - Add car')


@app.route('/cars/edit-car/<string:car_id>', methods=['GET', 'POST'])
def edit_car(car_id):
	if request.method == 'POST':
		car = {}
		car['vendor'] = request.form['vendor'].strip().upper()
		if len(car['vendor']) == 0:
			flash('Please, specify car vendor')
			return redirect(url_for('edit_car', car_id=car_id))
		car['model'] = request.form['model'].strip().upper()
		if len(car['model']) == 0:
			flash('Please, specify car model')
			return redirect(url_for('edit_car', car_id=car_id))
		try:
			car['year'] = int(request.form['year'].strip())
		except Exception as e:
			flash('Please, specify valid car manufactured year')
			return redirect(url_for('edit_car', car_id=car_id))
		if (car['year'] < 1900) or (car['year'] > 2023):
			flash('Please, specify valid car manufactured year')
			return redirect(url_for('edit_car', car_id=car_id))
		car['class'] = request.form['class']
		car['type'] = request.form['type']
		try:
			car['power'] = int(request.form['power'].strip())
		except Exception as e:
			flash('Please, specify valid car power in hp')
			return redirect(url_for('edit_car', car_id=car_id))
		if car['power'] < 1:
			flash('Please, specify valid car power in hp')
			return redirect(url_for('edit_car', car_id=car_id))
		try:
			car['mass'] = int(request.form['mass'].strip())
		except Exception as e:
			flash('Please, specify valid car mass in kg')
			return redirect(url_for('edit_car', car_id=car_id))
		if car['mass'] < 1:
			flash('Please, specify valid car mass in kg')
			return redirect(url_for('edit_car', car_id=car_id))
		try:
			car['max_speed'] = float(request.form['max_speed'].strip())
		except Exception as e:
			flash('Please, specify valid car max speed in km/h')
			return redirect(url_for('edit_car', car_id=car_id))
		if car['mass'] < 1.0:
			flash('Please, specify valid car max speed in km/h')
			return redirect(url_for('edit_car', car_id=car_id))
		car['drivetrain'] = request.form['drivetrain']
		try:
			car['test_track'] = convert_to_seconds(request.form['test_track'].strip())
		except Exception as e:
			flash('Please, specify valid test track time (mm:ss.ms)')
			return redirect(url_for('edit_car', car_id=car_id))
		car['test_track_str'] = request.form['test_track'].strip()
		car['image'] = request.form['image'].strip()
		if len(car['image']) == 0:
			flash('Please, specify valid car image link')
			return redirect(url_for('edit_car', car_id=car_id))
		car_query = {'_id': car_id}
		car_update = {'$set': car}
		result = app.db.cars.update_one(car_query, car_update, upsert=True)
		flash('Car successfully updated')
		return redirect(url_for('cars'))
	else:
		car = app.db.cars.find_one({'_id': car_id})
		return render_template('edit_car.html', car=car, title='Forza Horizon 5 stats - Edit car')


@app.route('/cars/delete-car/<string:car_id>', methods=['GET', 'POST'])
def delete_car(car_id):
	if request.method == 'POST':
		result = app.db.cars.delete_one({'_id': car_id})
		flash('Car deleted')
		return redirect(url_for('cars'))
	car = app.db.cars.find_one({'_id': car_id})
	return render_template('delete_car.html', car=car, title='Forza Horizon 5 stats - Delete car')


@app.route('/type/<string:car_type>')
def type_car(car_type):
	search_str = request.args.get('search_str')
	sort_by = request.args.get('cars_sort_by')
	if not sort_by:
		sort_by = 'test_track'
		cars = app.db.cars.find({'type': car_type.upper()}).sort(sort_by, ASCENDING)
	else:
		cars = app.db.cars.find({'type': car_type.upper()}).sort(sort_by, DESCENDING)
	if search_str:
		search_str = search_str.upper()
		cars_with_search = []
		for car in cars:
			if search_str in car['vendor']:
				cars_with_search.append(car)
				continue
			elif search_str in car['model']:
				cars_with_search.append(car)
				continue
			elif search_str in str(car['year']):
				cars_with_search.append(car)
				continue
			elif search_str in car['class']:
				cars_with_search.append(car)
				continue
			elif search_str in car['type']:
				cars_with_search.append(car)
				continue
			elif search_str in car['drivetrain']:
				cars_with_search.append(car)
				continue
		cars = cars_with_search
	return render_template('road.html', cars=cars, title='Forza Horizon 5 stats - {}'.format(car_type.upper()))


@app.route('/tracks/')
def tracks():
	search_str = request.args.get('search_str')
	tracks = app.db.tracks.find({})
	if search_str:
		search_str = search_str.upper()
		tracks_with_search = []
		for track in tracks:
			if search_str in track['name']:
				tracks_with_search.append(track)
				continue
			elif search_str in track['car_type']:
				tracks_with_search.append(track)
				continue
			elif search_str in track['track_type']:
				tracks_with_search.append(track)
				continue
		tracks = tracks_with_search
	return render_template('tracks.html', tracks=tracks, title='Forza Horizon 5 stats - Tracks')


@app.route('/tracks/<string:track_id>')
def track(track_id):
	track = app.db.tracks.find_one({'_id': track_id})
	track_races = app.db.races.find({'track_id': track_id}).sort('lap_time', ASCENDING)
	track_rivals = app.db.rivals.find({'track_id': track_id}).sort('time', ASCENDING)
	races = []
	for track_race in track_races:
		race = {}
		car = app.db.cars.find_one({'_id': track_race['car_id']})
		race['car'] = '{} - {}'.format(car['vendor'], car['model'])
		race['car_class'] = car['class']
		race['car_type'] = car['type']
		race['car_id'] = car['_id']
		race['lap_time'] = track_race['lap_time_str']
		race['overall_time'] = track_race['overall_time_str']
		race['place'] = track_race['place']
		races.append(race)
	rivals = []
	for track_rival in track_rivals:
		rival = {}
		car = app.db.cars.find_one({'_id': track_rival['car_id']})
		rival['car'] = '{} - {}'.format(car['vendor'], car['model'])
		rival['car_class'] = car['class']
		rival['car_id'] = car['_id']
		rival['time'] = track_rival['time_str']
		rivals.append(rival)
	return render_template('track.html', track=track, races=races, rivals=rivals, title='Forza Horizon 5 stats - {}'.format(track['name']))


@app.route('/races/')
def races():
	all_races = app.db.races.find({}).sort('added', DESCENDING)
	all_tracks = list(app.db.tracks.find({}))
	all_cars = list(app.db.cars.find({}))
	races = []
	for single_race in all_races:
		race = {}
		race['race_id'] = single_race['_id']
		for single_track in all_tracks:
			if single_track['_id'] == single_race['track_id']:
				race['track'] = single_track['name']
				race['track_id'] = single_race['track_id']
				break
		for single_car in all_cars:
			if single_car['_id'] == single_race['car_id']:
				race['car'] = '{} - {}'.format(single_car['vendor'], single_car['model'])
				race['car_type'] = single_car['type']
				race['car_class'] = single_car['class']
				break
		race['car_id'] = single_race['car_id']
		race['place'] = single_race['place']
		race['lap_time'] = single_race['lap_time_str']
		race['overall_time'] = single_race['overall_time_str']
		races.append(race)
	return render_template('races.html', races=races, title='Forza Horizon 5 stats - Races')


@app.route('/races/delete_race/<string:race_id>', methods=['GET', 'POST'])
def delete_race(race_id):
	if request.method == 'POST':
		race = app.db.races.find_one({'_id': race_id})
		if race['championship']:
			championship = app.db.championships.find_one({'_id': race['championship']})
			if championship['completed']:
				flash('Cannot delete race from completed championship')
				return redirect(url_for('races'))
			for n, championship_track in enumerate(championship['tracks']):
				for track_id in championship_track.keys():
					if track_id == race['track_id']:
						for car_id in championship_track[track_id]['cars'].keys():
							if car_id == race['car_id']:
								championship['tracks'][n][track_id]['cars'][car_id]['time'] = 0.0
								championship['tracks'][n][track_id]['cars'][car_id]['points'] = 0
								championship_query = {'_id': race['championship']}
								championship_update = {'$set': championship}
								result = app.db.championships.update_one(championship_query, championship_update, upsert=True)
		car = {}
		car['races'] = app.db.cars.find_one({'_id': race['car_id']})['races'] - 1
		if race['place'] == 1:
			car['wins'] = app.db.cars.find_one({'_id': race['car_id']})['wins'] - 1
		if (race['place'] == 2) or (race['place'] == 3) :
			car['podiums'] = app.db.cars.find_one({'_id': race['car_id']})['podiums'] - 1
		car_query = {'_id': race['car_id']}
		car_update = {'$set': car}
		result = app.db.cars.update_one(car_query, car_update, upsert=True)
		result = app.db.races.delete_one({'_id': race_id})
		flash('Race deleted')
		return redirect(url_for('races'))
	return render_template('delete_race.html', title='Forza Horizon 5 stats - Delete race result')


@app.route('/races/add_race/', methods=['GET', 'POST'])
def add_race():
	selected_track = {}
	selected_car = {}
	if request.method == 'GET':
		championships = app.db.championships.find({}).sort('added', DESCENDING)
		cars = app.db.cars.find({}).sort('vendor', ASCENDING)
		tracks = app.db.tracks.find({})
		track_id = request.args.get('track_id')
		if track_id:
			selected_track = app.db.tracks.find_one({'_id': track_id})
		car_id = request.args.get('car_id')
		if car_id:
			selected_car = app.db.cars.find_one({'_id': car_id})
		return render_template('add_race.html',
				selected_track=selected_track, selected_car=selected_car,
				tracks=tracks, cars=cars, championships=championships,
				title='Forza Horizon 5 stats - Add race result')
	if request.method == 'POST':
		race = {}
		race['track_id'] = request.form['track']
		race['car_id'] = request.form['car']
		race['place'] = int(request.form['place'])
		try:
			race['lap_time'] = convert_to_seconds(request.form['lap_time'].strip().replace(',', '.'))
		except Exception as e:
			flash('Please, specify valid lap time (mm:ss.ms)')
			return redirect(url_for('add_race'))
		try:
			race['overall_time'] = convert_to_seconds(request.form['overall_time'].strip().replace(',', '.'))
		except Exception as e:
			flash('Please, specify valid overall time (mm:ss.ms)')
			return redirect(url_for('add_race'))
		if race['lap_time'] > race['overall_time']:
			flash('Lap time cannot be larger then overall time. Please, specify valid lap time and overall time')
			return redirect(url_for('add_race'))
		race['lap_time_str'] = request.form['lap_time'].strip().replace(',', '.')
		race['overall_time_str'] = request.form['overall_time'].strip().replace(',', '.')
		race['_id'] = generate_unique_id()
		race['added'] = datetime.datetime.now()
		if request.form['championship'] == 'NO':
			race['championship'] = ''
		else:
			found = False
			championship = app.db.championships.find_one({'_id': request.form['championship']})
			for n, championship_track in enumerate(championship['tracks']):
				for track_id in championship_track.keys():
					if track_id == race['track_id']:
						for car_id in championship_track[track_id]['cars'].keys():
							if car_id == race['car_id']:
								found = True
								race['championship'] = request.form['championship']
								championship['tracks'][n][track_id]['cars'][car_id]['time'] = race['overall_time']
								championship['tracks'][n][track_id]['cars'][car_id]['points'] = POINTS[race['place']]
								championship_query = {'_id':request.form['championship']}
								championship_update = {'$set': championship}
								result = app.db.championships.update_one(championship_query, championship_update, upsert=True)
			if not found:
				flash('The specified car or track are not present in selected championship')
				return redirect(url_for('add_race'))
			if championship_completed(request.form['championship']):
				flash("You've completed the championship!")
		result = app.db.races.insert_one(race)
		car = {}
		car['races'] = app.db.cars.find_one({'_id': race['car_id']})['races'] + 1
		if race['place'] == 1:
			car['wins'] = app.db.cars.find_one({'_id': race['car_id']})['wins'] + 1
		if (race['place'] == 2) or (race['place'] == 3) :
			car['podiums'] = app.db.cars.find_one({'_id': race['car_id']})['podiums'] + 1
		car_query = {'_id': race['car_id']}
		car_update = {'$set': car}
		result = app.db.cars.update_one(car_query, car_update, upsert=True)
		flash('Race added')
		return redirect(url_for('races'))


@app.route('/rivals/')
def rivals():
	all_rivals = app.db.rivals.find({}).sort('added', DESCENDING)
	all_tracks = list(app.db.tracks.find({}))
	all_cars = list(app.db.cars.find({}))
	rivals = []
	for single_rival in all_rivals:
		rival = {}
		rival['rival_id'] = single_rival['_id']
		for single_track in all_tracks:
			if single_track['_id'] == single_rival['track_id']:
				rival['track'] = single_track['name']
				rival['track_id'] = single_rival['track_id']
				break
		for single_car in all_cars:
			if single_car['_id'] == single_rival['car_id']:
				rival['car'] = '{} - {}'.format(single_car['vendor'], single_car['model'])
				rival['car_type'] = single_car['type']
				rival['car_class'] = single_car['class']
				break
		rival['car_id'] = single_rival['car_id']
		rival['time'] = single_rival['time_str']
		rivals.append(rival)
	return render_template('rivals.html', rivals=rivals, title='Forza Horizon 5 stats - Rivals')


@app.route('/rivals/delete-rival/<string:rival_id>', methods=['GET', 'POST'])
def delete_rival(rival_id):
	if request.method == 'POST':
		result = app.db.rivals.delete_one({'_id': rival_id})
		flash('Rival deleted')
		return redirect(url_for('rivals'))
	return render_template('delete_rival.html', title='Forza Horizon 5 stats - Delete rival result')


@app.route('/rivas/add_rival/', methods=['GET', 'POST'])
def add_rival():
	selected_track = {}
	selected_car = {}
	if request.method == 'GET':
		cars = app.db.cars.find({}).sort('vendor', ASCENDING)
		tracks = app.db.tracks.find({})
		track_id = request.args.get('track_id')
		if track_id:
			selected_track = app.db.tracks.find_one({'_id': track_id})
		car_id = request.args.get('car_id')
		if car_id:
			selected_car = app.db.cars.find_one({'_id': car_id})
		return render_template('add_rival.html',
			selected_track=selected_track, selected_car=selected_car,
			tracks=tracks, cars=cars,
			title='Forza Horizon 5 stats - Add rivals result')
	if request.method == 'POST':
		rival = {}
		rival['track_id'] = request.form['track']
		rival['car_id'] = request.form['car']
		try:
			rival['time'] = convert_to_seconds(request.form['rivals_result'].strip().replace(',', '.'))
		except Exception as e:
			flash('Please, specify valid rivals result time (mm:ss.ms)')
			return redirect(url_for('add_rival'))
		all_rivals = app.db.rivals.find({})
		for single_rival in all_rivals:
			if single_rival['track_id'] == rival['track_id']:
					if single_rival['car_id'] == rival['car_id']:
						if rival['time'] < single_rival['time']:
							result = app.db.rivals.delete_one({'_id': single_rival['_id']})
						else:
							flash('New rivals result is worse then current. Please, try again.')
							return redirect(url_for('rivals'))
						break
		rival['time_str'] = request.form['rivals_result'].strip().replace(',', '.')
		rival['_id'] = generate_unique_id()
		rival['added'] = datetime.datetime.now()
		result = app.db.rivals.insert_one(rival)
		flash('Rivals result added')
		return redirect(url_for('rivals'))


@app.route('/championships/')
def championships():
	all_championships = app.db.championships.find({})
	all_cars = list(app.db.cars.find({}))
	championships = []
	for single_championship in all_championships:
		championship = {}
		championship['id'] = single_championship['_id']
		championship['name'] = single_championship['name']
		championship['conditions'] = single_championship['conditions']
		championship['completed'] = single_championship['completed']
		championship['winners'] = single_championship['winners']
		championship['podiums'] = single_championship['podiums']
		championship['points_championship'] = []
		championship['time_championship'] = []
		cars = {}
		for n, track in enumerate(single_championship['tracks']):
			for track_id in track.keys():
				for car_id in single_championship['tracks'][n][track_id]['cars'].keys():
					car = {}
					for single_car in all_cars:
						if single_car['_id'] == car_id:
							car = single_car
					if car_id not in cars.keys():
						cars[car_id] = {}
						cars[car_id]['name'] = '{} - {}'.format(car['vendor'], car['model'])
						cars[car_id]['time'] = 0.0
						cars[car_id]['points'] = 0
					cars[car_id]['time'] += single_championship['tracks'][n][track_id]['cars'][car_id]['time']
					cars[car_id]['points'] += single_championship['tracks'][n][track_id]['cars'][car_id]['points']
		for car_id in cars.keys():
			car_points = {}
			car_points['car_id'] = car_id
			car_points['name'] = cars[car_id]['name']
			car_points['points'] = cars[car_id]['points']
			car_points['time'] = cars[car_id]['time']
			championship['points_championship'].append(car_points)
			car_time = {}
			car_time['car_id'] = car_id
			car_time['name'] = cars[car_id]['name']
			car_time['time'] = cars[car_id]['time']
			car_time['time_str'] = convert_from_seconds(car_time['time'])
			championship['time_championship'].append(car_time)
		championship['points_championship'].sort(key=lambda x: (-x.get('points'), x.get('time')))
		championship['time_championship'].sort(key=lambda x: x.get('time'))
		championships.append(championship)
	return render_template('championships.html', championships=championships, title='Forza Horizon 5 stats - Championships')


@app.route('/championships/<string:championship_id>')
def championship(championship_id):
	all_cars = list(app.db.cars.find({}))
	all_tracks = list(app.db.tracks.find({}))
	current_championship = app.db.championships.find_one({'_id': championship_id})
	championship = {}
	championship['id'] = current_championship['_id']
	championship['name'] = current_championship['name']
	championship['conditions'] = current_championship['conditions']
	championship['completed'] = current_championship['completed']
	championship['winners'] = current_championship['winners']
	championship['podiums'] = current_championship['podiums']
	championship['points_championship'] = []
	championship['time_championship'] = []
	cars = {}
	for n, track in enumerate(current_championship['tracks']):
		for track_id in track.keys():
			for car_id in current_championship['tracks'][n][track_id]['cars'].keys():
				car = {}
				for single_car in all_cars:
					if single_car['_id'] == car_id:
						car = single_car
				if car_id not in cars.keys():
					cars[car_id] = {}
					cars[car_id]['name'] = '{} - {}'.format(car['vendor'], car['model'])
					cars[car_id]['time'] = 0.0
					cars[car_id]['points'] = 0
				cars[car_id]['time'] += current_championship['tracks'][n][track_id]['cars'][car_id]['time']
				cars[car_id]['points'] += current_championship['tracks'][n][track_id]['cars'][car_id]['points']
	for car_id in cars.keys():
		car_points = {}
		car_points['car_id'] = car_id
		car_points['name'] = cars[car_id]['name']
		car_points['points'] = cars[car_id]['points']
		car_points['time'] = cars[car_id]['time']
		championship['points_championship'].append(car_points)
		car_time = {}
		car_time['car_id'] = car_id
		car_time['name'] = cars[car_id]['name']
		car_time['time'] = cars[car_id]['time']
		car_time['time_str'] = convert_from_seconds(car_time['time'])
		championship['time_championship'].append(car_time)
	championship['points_championship'].sort(key=lambda x: (-x.get('points'), x.get('time')))
	championship['time_championship'].sort(key=lambda x: x.get('time'))
	championship['tracks'] = []
	for n, track in enumerate(current_championship['tracks']):
		for track_id in track.keys():
			current_track = {}
			for single_track in all_tracks:
				if track_id == single_track['_id']:
					current_track['id'] = single_track['_id']
					current_track['name'] = single_track['name']
					current_track['cars_points'] = []
					current_track['cars_time'] = []
					for car_id in current_championship['tracks'][n][track_id]['cars'].keys():
						car = {}
						for single_car in all_cars:
							if car_id == single_car['_id']:
								car['id'] = single_car['_id']
								car['name'] = '{} - {}'.format(single_car['vendor'], single_car['model'])
								car['points'] = current_championship['tracks'][n][track_id]['cars'][car_id]['points']
								car['time'] = current_championship['tracks'][n][track_id]['cars'][car_id]['time']
								car['time_str'] = convert_from_seconds(car['time'])
								current_track['cars_points'].append(car)
								current_track['cars_time'].append(car)
					current_track['cars_points'].sort(key=lambda x: (-x.get('points'), x.get('time')))
					current_track['cars_time'].sort(key=lambda x: x.get('time'))
		championship['tracks'].append(current_track)
	return render_template('championship.html', championship=championship, title='Forza Horizon 5 stats - Championship')


@app.route('/generate/')
def generate():
	return render_template('generate.html', title='Forza Horizon 5 stats - Generate')


@app.route('/generated-race/', methods=['POST'])
def generated_race():
	car = {}
	track = {}
	car_type = request.form['race_type']
	try:
		car_class = request.form['car_class']
		if car_class == 'ANY':
			if car_type == 'ANY':
				cars = app.db.cars.find({})
			else:
				cars = app.db.cars.find({'type': car_type})
		else:
			if car_type == 'ANY':
				cars =  app.db.cars.find({})
			else:
				cars =  app.db.cars.find({'class': car_class, 'type': car_type})
		car = random.choice(list(cars))
		if car_type == 'ANY':
			car_type = car['type']
	except Exception as e:
		pass
	if car_type == 'ANY':
		tracks = app.db.tracks.find({})
	else:
		tracks = app.db.tracks.find({'car_type': car_type})
	track = random.choice(list(tracks))
	track_season, track_time, track_weather, track_competition = generate_track_details()
	return render_template('generated_race.html', track=track, car=car, track_competition=track_competition,
			track_season = track_season, track_time = track_time, track_weather=track_weather,
			title='Forza Horizon 5 stats - Race Generation')


@app.route('/generated-championship/', methods=['POST'])
def generated_championship():
	car_type = request.form['race_type']
	car_class = request.form['car_class']
	all_tracks = list(app.db.tracks.find({'car_type': car_type}))
	all_cars = list(app.db.cars.find({'class': car_class, 'type': car_type}).sort('championships', ASCENDING))
	if len(all_cars) < 6:
		flash("It's not enough cars to create the championship.")
		return redirect(url_for('generate'))
	tracks = []
	cars = []
	for n in range(8):
		while True:
			selected_track = random.choice(all_tracks)
			if selected_track['_id'] in tracks:
				continue
			else:
				tracks.append(selected_track['_id'])
				break
	for car in all_cars:
		if len(cars) < 11:
			cars.append(car['_id'])
	championship = {}
	championship['_id'] = generate_unique_id()
	season, time, weather, race_type = generate_track_details()
	championship['name'] = '{} | {} | {}'.format(car_class, car_type, race_type)
	championship['conditions'] = '{} | {} | {}'.format(season, time, weather)
	championship['completed'] = False
	championship['winners'] = []
	championship['podiums'] = []
	championship['tracks'] = []
	for track_id in tracks:
		track = {}
		track[track_id] = {}
		track[track_id]['cars'] = {}
		for car_id in cars:
			track[track_id]['cars'][car_id] = {}
			track[track_id]['cars'][car_id]['points'] = 0
			track[track_id]['cars'][car_id]['time'] = 0.0
		championship['tracks'].append(track)
	result = app.db.championships.insert_one(championship)
	flash('New championship is created')
	return render_template('generated_championship.html', championship=championship, tracks=tracks, cars=cars, title='Forza Horizon 5 stats - Championship Generation')