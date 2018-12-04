from flask import render_template, jsonify
from sqlalchemy import func

from accounting import app, db
from models import Contact, Invoice, Policy

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/policies")
def policies():
    return render_template('policies.html', policies = populatePolicies())

def populatePolicies(): # Grab all policies and return them in a JSON format
    rawPolicies = Policy.query.all()
    policies = []

    for i in range(Policy.query.count()):
        policy = jsonify(rawPolicies[i].to_json()) # Convert the JSON readable format to actual JSON
        policies.append(policy.data)

    return policies

@app.route("/policyInvoices")
@app.route("/policyInvoices/<policyNumber>")
def policyInvoices(policyNumber):
    policyNumber = policyNumber.replace("_", " ")
    return render_template('policyInvoices.html', invoices = populateInvoices(policyNumber))

def populateInvoices(policyNumber): #TODO add date variable
    # func.lower() allows for case-insensitive searching of the database
    policy = Policy.query.filter(func.lower(Policy.policy_number) == func.lower(policyNumber)).first_or_404()

    query = Invoice.query.filter_by(policy_id=policy.id)
    rawInvoices = query.all()
    invoices = []

    for i in range(query.count()):
        invoice = jsonify(rawInvoices[i].to_json())
        invoices.append(invoice.data)

    return invoices

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404