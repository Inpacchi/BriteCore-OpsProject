from flask import render_template, jsonify
from accounting import app, db

from models import Contact, Invoice, Policy

@app.route("/")
def index():
    return render_template('policies.html', policies = populatePolicies(),policies_count = Policy.query.count())

def populatePolicies(): # Grab all policies and return them in a JSON format
    rawPolicies = Policy.query.all()
    policies = []

    for i in range(Policy.query.count()):
        policy = jsonify(rawPolicies[i].to_json()) # Convert the JSON readable format to actual JSON
        policies.append(policy.data)

    return policies