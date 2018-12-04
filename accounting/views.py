# Necessary functions from libraries/frameworks
from flask import render_template, jsonify
from sqlalchemy import func
from datetime import datetime

# Necessary functions from code framework
from accounting import app, db

# Necessary models from database for the view
from models import Contact, Invoice, Policy

# Necessary functions for program utility
from utils import PolicyAccounting

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
@app.route("/policyInvoices/<policyNumber>/<date>")
def policyInvoices(policyNumber, date):
    policyNumber = policyNumber.replace("_", " ")
    date = date.replace("_", " ")

    # func.lower() allows for case-insensitive searching of the database
    policy = Policy.query.filter(func.lower(Policy.policy_number) == func.lower(policyNumber)).first_or_404() 

    # Pass policyNumber to the HTML so the page can be properly labeled
    return render_template('policyInvoices.html', 
        invoices = populateInvoices(policy, date), 
        accountBalance = PolicyAccounting(policy.id).return_account_balance(date),
        policyNumber = policyNumber.title()
    )

def populateInvoices(policy, date):
    # Parse a date to datetime from the input date string
    date_cursor = datetime.strptime(date, "%Y-%m-%d")

    # Grab invoices for the policy before and on the given date
    # One variable here allows use by two different statements down below
    query = Invoice.query.filter_by(policy_id=policy.id).filter(Invoice.bill_date <= date_cursor)

    # Return all the invoices
    rawInvoices = query.all()
    invoices = []

    # Get a count of all invoices found
    for i in range(query.count()):
        invoice = jsonify(rawInvoices[i].to_json())
        invoices.append(invoice.data)

    return invoices

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404