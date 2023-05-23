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
client = MongoClient(os.environ.get('MONGODB_URI'))
db = client.forza_stats

def generate_unique_id():
	unique_id = ''
	for n in range(32):
		unique_id = unique_id + random.choice(string.ascii_letters)
	return unique_id


track = {
	'_id': generate_unique_id(),
	'name': "HORIZON OVAL CIRCUIT",
	'car_type': 'ROAD',
	'track_type': 'CIRCUIT',
	'small_image': 'https://i.ibb.co/P17YJtn/horizon-oval-circuit-small.png',
	'big_image': 'https://i.ibb.co/12XW3pZ/horizon-oval-circuit-big.png',
}

result = db.tracks.insert_one(track)
print(result)