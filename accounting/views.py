# Necessary functions from libraries/frameworks
from flask import render_template, jsonify
from sqlalchemy import func
from sqlalchemy.orm import aliased
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

# Grab all policies and return them in a JSON format
def populatePolicies(): 
    # For use in query to query the contacts table twice for names
    Contact_Alias = aliased(Contact) 

    query = db.session.query(Policy.policy_number,
        Policy.status,
        Policy.annual_premium,
        Policy.effective_date,
        Policy.billing_schedule,
        Contact.name,
        Contact_Alias.name)\
        .join(Contact, Policy.named_insured == Contact.id)\
        .join(Contact_Alias, Policy.agent == Contact_Alias.id)

    tuples = query.all()
    policies = []
    
    for i in range(query.count()):
        policy = list(tuples[i]) # Variable assignment from tuple to list
        policy = jsonify(return_json(policy))

        policies.append(policy.data)

    return policies

# Returns JSON parseable output from the query
def return_json(policy):
    return {
        'policy_number': policy[0],
        'status': policy[1],
        'annual_premium': policy[2],
        'effective_date': str(policy[3]),
        'billing_schedule': policy[4],
        'named_insured': policy[5],
        'agent': policy[6]
    }

@app.route("/policyInvoices")
@app.route("/policyInvoices/<policyNumber>/<date>")
def policyInvoices(policyNumber, date):
    policyNumber = policyNumber.replace("_", " ")
    date = date.replace("_", " ")

    # func.lower() allows for case-insensitive searching of the database
    policy = Policy.query.filter(func.lower(Policy.policy_number) == func.lower(policyNumber)).first_or_404() 

    accountBalance = PolicyAccounting(policy.id).return_account_balance(date)

    # If the accountBalance is returned as -1, then we know a date before the effective date was entered
    if(accountBalance == -1): 
        return render_template("404.html", code=404)

    # Pass policyNumber to the HTML so the page can be properly labeled
    return render_template('policyInvoices.html', 
        invoices = populateInvoices(policy, date), 
        accountBalance = accountBalance,
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