from flask import Flask, jsonify

app = Flask(__name__)

import config

import models

import api

import routes