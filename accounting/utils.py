#!/user/bin/env python2.7

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from accounting import db
from models import Contact, Invoice, Payment, Policy, Cancelled_Policy

"""
#######################################################
This is the base code for the engineer project.
#######################################################
"""

class PolicyAccounting(object):
    """
     Each policy has its own instance of accounting.
    """

    def __init__(self, policy_id): # Executed on class initiailization, setting the global class policy and creating invoices if there are none
        print "Initializing PolicyAccouting class..."
        self.policy = Policy.query.filter_by(id=policy_id).one()

        if not self.policy.invoices:
            print "No invoices are made. Making invoices..."
            self.make_invoices()
            print "Invoices made!"
        else:
            print "Invoices are already made."
        
        print "PolicyAccouting intialized!\n"

    def return_account_balance(self, date_cursor=None): # Take in a date and return the corresponding account balance according to invoices and payments
        if not date_cursor: # If date_cursor is equal to the default value (None) or null, set it equal to the current date
            print "No date has been set. Setting date to current date."
            date_cursor = datetime.now().date()
        else: # Convert the date_cursor to a datetime.date() variable
            date_cursor = datetime.strptime(date_cursor, "%Y-%m-%d").date()

        if(date_cursor <= self.policy.effective_date): # If a date is given before the effective date, there should be no account balance
            return -1 # return -1 so our Flask server can handle the routing

        billing_schedules = {'Annual': 1, 'Two-Pay': 2, 'Quarterly': 4, 'Monthly': 12}

        # Access the database to grab invoices according to the current policy. Filter them by looking for all invoices whose billing date is on or before 
        # the date_cursor, then order them by the billing date. The .all() method returns all matched invoices.
        invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
                                .filter(Invoice.bill_date <= date_cursor)\
                                .order_by(Invoice.bill_date)\
                                .all()

        due_now = 0 # Set our due_now variable to 0 as it is to be modified by invoices and payments

        if len(invoices) != 0: # If invoices is empty, don't bother executing code on it as we are wasting time
            if len(invoices) == 1:
                if invoices[0].amount_due > 0: # Check if the invoice has a remaining balance
                    print "1 invoice is present. Listing..."
                    print "The current invoice has a balance due of $", invoices[0].amount_due
                    due_now = invoices[0].amount_due
            else:
                print len(invoices), "invoices, listing..."
                for invoice in invoices:
                    if invoice.amount_due > 0: # Check if the invoice has a remaining balance
                        print "The current invoice has a balance due of $", invoice.amount_due
                        due_now += invoice.amount_due # Increase due_now for each invoice found

            print "The current amount due is $", due_now, "\n"
        else:
            print "No invoices are present.\n"

        # Same logic as invoices above
        payments = Payment.query.filter_by(policy_id=self.policy.id)\
                                .filter(Payment.transaction_date <= date_cursor)\
                                .all()

        if len(invoices) == 0 and len(payments) == 0: # If there are no payments or invoices, the account balance has not been paid
            # If that's the case, set due_now equal to the annual premium divided by the billing schedule
            due_now = self.policy.annual_premium / billing_schedules.get(self.policy.billing_schedule) #
            print "Since no invoices are present and as such, no payments have been made, the current amount due is $", due_now, "\n"

        if due_now < 0: # If due_now is less than 0, this means the payments satisfied the invoices due to our checking of the deleted status
            due_now = 0 # So set it equal to 0 as there is no balance due
        return due_now

    def make_payment(self, contact_id=None, date_cursor=None, amount=0):
        if not date_cursor: # If date_cursor is equal to the default value (None) or null, set it equal to the current date
            date_cursor = datetime.now().date()

        if not contact_id: # If there is no contact_id or it is equal to the default value (None), set it equal to the named insured of the policy
            try:
                contact_id = self.policy.named_insured
            except:
                pass

        payment = Payment(self.policy.id, # Create a payment using the method parameters
                          contact_id,
                          amount,
                          date_cursor)
        
        invoices = Invoice.query.filter_by(policy_id=self.policy.id).all() # Get a list of invoices

        for invoice in invoices: # For each invoice...
            if invoice.amount_due != 0: # That is not paid (i.e not equal to 0)...
               invoice.amount_due -= amount # Subtract the amount paid from the invoice amount due
               break # We want to execute the break statement because we found our invoice that was decremented and don't want to modify any other ones

        db.session.add(payment) # Add the payment to the database
        db.session.commit() # Commit the changes (save)

        return payment

    def evaluate_cancellation_pending_due_to_non_pay(self, date_cursor=None):
        if not date_cursor: # If date_cursor is equal to the default value (None) or null, set it equal to the current date
            date_cursor = datetime.now().date()

        invoice = Invoice.query.filter_by(policy_id=self.policy.id)\
            .filter_by(amount_due > 0)\
            .first() # Check and grab the first invoice that hasn't been paid

        if invoice == None: # If no invoice was queried from the database, check the account balance to make sure all payments have been made
            if return_account_balance == 0: # If return_account_balance returns 0, that means all invoices have been paid
                return False

        if date_cursor > invoice.due_date and date_cursor <= invoice.cancel_date:
            policy.status = 'Cancellation Pending due to non-pay'
            return True
        
        return False

    def evaluate_cancel(self, date_cursor=None):
        if not date_cursor: # If date_cursor is equal to the default value (None) or null, set it equal to the current date
            date_cursor = datetime.now().date()

        # Access the database to grab invoices according to the current policy. Filter them by looking for all invoices whose billing date is on or before 
        # the date_cursor, then order them by the billing date. The .all() method returns all matched invoices.
        invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
                                .filter(Invoice.cancel_date <= date_cursor)\
                                .order_by(Invoice.bill_date)\
                                .all()

        for invoice in invoices: # For each invoice...
            if not self.return_account_balance(invoice.cancel_date): # If there is no account balance on the cancel date...
                continue # Continue on to the next iteration of the for loop
            else:
                print "THIS POLICY SHOULD BE CANCELED\n" # Otherwise the policy should be cancelled'
                self.cancel_policy() # Invoke and cancel it
                return True
        else:
            print "THIS POLICY SHOULD NOT CANCEL" # This is where you end up if invoices returns continue
            return False

    def cancel_policy(self, date_cursor=None, cancellation_reason='No payment received'):
        if not date_cursor: # If no date is given, set the cancellation date to today
            date_cursor = datetime.now().date()

        self.policy.status = 'Cancelled' # Change the status of the policy in the database
        
        print "Policy Number:", self.policy.policy_number
        print "Status:", self.policy.status
        print "Reason:", cancellation_reason, "\n"

        policy = Cancelled_Policy(self.policy.id, self.policy.policy_number, date_cursor, cancellation_reason)
        db.session.add(policy)
        db.session.commit()

    def make_invoices(self):
        billing_schedules = {'Annual': None, 'Two-Pay': 2, 'Quarterly': 4, 'Monthly': 12}

        invoices = []

        first_invoice = Invoice(self.policy.id, # Create an invoice based on the policy
                                self.policy.effective_date, # bill_date
                                self.policy.effective_date + relativedelta(months=1), # due_date
                                self.policy.effective_date + relativedelta(months=1, days=14), # cancel_date
                                self.policy.annual_premium)

        invoices.append(first_invoice) # Add first_invoice to the invoices[] array

        if self.policy.billing_schedule == "Annual":
            pass # An annual billing policy allows us to simply use the above first_invoice because the values don't change
        elif self.policy.billing_schedule == "Two-Pay":
            # Set the invoice amount equal to itself divided by the billing schedule
            first_invoice.amount_due = first_invoice.amount_due / billing_schedules.get(self.policy.billing_schedule)

            for i in range(1, billing_schedules.get(self.policy.billing_schedule)): # For each bill in the billing schedule...
                # Based on the billing schedule, get the next time the customer has to pay and set that as the billing date. 
                months_after_eff_date = i*6

                bill_date = self.policy.effective_date + relativedelta(months=months_after_eff_date)

                invoice = Invoice(self.policy.id,
                                  bill_date,
                                  bill_date + relativedelta(months=1),
                                  bill_date + relativedelta(months=1, days=14),
                                  self.policy.annual_premium / billing_schedules.get(self.policy.billing_schedule))

                invoices.append(invoice)
        elif self.policy.billing_schedule == "Quarterly":
            first_invoice.amount_due = first_invoice.amount_due / billing_schedules.get(self.policy.billing_schedule)

            for i in range(1, billing_schedules.get(self.policy.billing_schedule)):
                months_after_eff_date = i*3

                bill_date = self.policy.effective_date + relativedelta(months=months_after_eff_date)

                invoice = Invoice(self.policy.id,
                                  bill_date,
                                  bill_date + relativedelta(months=1),
                                  bill_date + relativedelta(months=1, days=14),
                                  self.policy.annual_premium / billing_schedules.get(self.policy.billing_schedule))

                invoices.append(invoice)
        elif self.policy.billing_schedule == "Monthly":
            first_invoice.amount_due = first_invoice.amount_due / billing_schedules.get(self.policy.billing_schedule)

            for i in range(1, billing_schedules.get(self.policy.billing_schedule)):
                months_after_eff_date = i

                bill_date = self.policy.effective_date + relativedelta(months=months_after_eff_date)

                invoice = Invoice(self.policy.id,
                                  bill_date,
                                  bill_date + relativedelta(months=1),
                                  bill_date + relativedelta(months=1, days=14),
                                  self.policy.annual_premium / billing_schedules.get(self.policy.billing_schedule))

                invoices.append(invoice)
        else:
            print "You have chosen a bad billing schedule."

        for invoice in invoices: # For every invoice created, add it to the database.
            db.session.add(invoice)
            
        db.session.commit() # Commit the changes (save)

    def change_billing_schedule(self, billing_schedule='Annual'):
        invoices_paid = 0 # Paid invoices tracker variable
        new_amount_due = 0 # Calculate the new amount due based on invoices that haven't been paid yet
        old_billing_date = None # Old billing date will determine how the payments are divided up

        invoices = Invoice.query.filter_by(policy_id=self.policy.id).all() # Grab all invoices for the policy

        for invoice in invoices: # For each invoice...
            if invoice.amount_due == 0: # If it has been paid...
                invoices_paid += 1 # Increment our paid invoices tracker variable
            else: # Otherwise...
                invoice.deleted = True # Mark the invoice as deleted...
                new_amount_due += invoice.amount_due # And add the invoice amount due to our new amount due
        
        print "Invoices paid:", invoices_paid
        print "New amount due:", new_amount_due
        
        for invoice in invoices: # Get the oldest billing date to determine how the new payments will be divided up
            if invoice.deleted: # If the invoice has been marked as deleted...
                old_billing_date = invoice.bill_date # Set the old billing date to the oldest deleted invoice
                break # Break out of the for loop as we want the oldest date and nothing more
        
        invoices = [] # Clear invoices as we don't need the old ones anymore
        print "Old billing date:", old_billing_date

        next_effective_date = self.policy.effective_date + relativedelta(years=1) # Get next year's effective date
        print "Next effective date:", next_effective_date, "\n"

        months_in_between = relativedelta(next_effective_date, old_billing_date).months # Get the months in-between the two dates

        # return months_in_between # This was my temporary return value for testing

        first_invoice = Invoice(self.policy.id, # Create an invoice based on the policy
                                old_billing_date, # bill_date
                                old_billing_date + relativedelta(months=1), # due_date
                                old_billing_date + relativedelta(months=1, days=14), # cancel_date
                                self.policy.annual_premium)

        if billing_schedule != 'Annual': # If the billing schedule isn't Annual, append the invoice.
            invoices.append(first_invoice) # Otherwise if it is, we want to check something first.

        if billing_schedule == 'Annual': # If it is Annual, and the new amount due isn't equal to 0, we need to subtract that from
            if new_amount_due != 0: # the first_invoice amount_due BEFORE we append it to the array
                first_invoice.amount_due -= new_amount_due
                invoices.append(first_invoice)
        elif billing_schedule == 'Two-Pay':
            billing_cycle = int(round(invoices_paid / 2.0)) # Get period between due dates
            print "Billing Cycle in months:", billing_cycle
            amount_due = new_amount_due / 2 # Divide based on billing_schedule
            print "Billing Cycle amount due:", amount_due

            # Set the invoice amount equal to itself divided by the billing schedule
            first_invoice.amount_due = amount_due

            for i in range(1, 2): # For each bill in the billing schedule...
                # Based on the billing schedule, get the next time the customer has to pay and set that as the billing date. 
                months_after_eff_date = i*billing_cycle
                # print "Months after effective date:", months_after_eff_date # Debugging purposes

                bill_date = old_billing_date + relativedelta(months=months_after_eff_date)
                # print "Bill Date:", bill_date # 

                invoice = Invoice(self.policy.id,
                                  bill_date,
                                  bill_date + relativedelta(months=1),
                                  bill_date + relativedelta(months=1, days=14),
                                  amount_due)

                invoices.append(invoice)
        elif billing_schedule == 'Quarterly':
            billing_cycle = int(round(months_in_between / 4.0))
            print "Billing Cycle in months:", billing_cycle
            amount_due = new_amount_due / 4
            print "Billing Cycle amount due:", amount_due, "\n"

            first_invoice.amount_due = amount_due

            for i in range(1, 4): 
                months_after_eff_date = i*billing_cycle
                # print "Months after effective date:", months_after_eff_date

                bill_date = old_billing_date + relativedelta(months=months_after_eff_date)
                # print "Bill Date:", bill_date

                invoice = Invoice(self.policy.id,
                                  bill_date,
                                  bill_date + relativedelta(months=1),
                                  bill_date + relativedelta(months=1, days=14),
                                  amount_due)

                invoices.append(invoice)
        elif billing_schedule == 'Monthly':
            amount_due = new_amount_due / months_in_between
            print "Billing Cycle amount due:", amount_due
        
            first_invoice.amount_due = amount_due

            for i in range(1, months_in_between): 
                months_after_eff_date = i
                # print "Months after effective date:", months_after_eff_date

                bill_date = old_billing_date + relativedelta(months=months_after_eff_date)
                # print "Bill Date:", bill_date

                invoice = Invoice(self.policy.id,
                                  bill_date,
                                  bill_date + relativedelta(months=1),
                                  bill_date + relativedelta(months=1, days=14),
                                  amount_due)

                invoices.append(invoice)
        else:
            print "You have chosen a bad billing schedule."

        print "\nInvoice Details below:"

        for invoice in invoices: # For every invoice created, add it to the database.
            db.session.add(invoice)
            print invoice.bill_date # Print information about each invoice to make sure dates and payments are correct
            print invoice.due_date
            print invoice.cancel_date
            print invoice.amount_due
            print "\n\n"


################################
# The functions below are for the db and 
# shouldn't need to be edited.
################################
def build_or_refresh_db():
    db.drop_all()
    db.create_all()
    insert_data()
    print "DB Ready!"

def insert_data():
    #Contacts
    contacts = []
    john_doe_agent = Contact('John Doe', 'Agent')
    contacts.append(john_doe_agent)
    john_doe_insured = Contact('John Doe', 'Named Insured')
    contacts.append(john_doe_insured)
    bob_smith = Contact('Bob Smith', 'Agent')
    contacts.append(bob_smith)
    anna_white = Contact('Anna White', 'Named Insured')
    contacts.append(anna_white)
    joe_lee = Contact('Joe Lee', 'Agent')
    contacts.append(joe_lee)
    ryan_bucket = Contact('Ryan Bucket', 'Named Insured')
    contacts.append(ryan_bucket)

    for contact in contacts:
        db.session.add(contact)
    db.session.commit()

    policies = []
    p1 = Policy('Policy One', date(2015, 1, 1), 365)
    p1.billing_schedule = 'Annual'
    p1.agent = bob_smith.id
    policies.append(p1)

    p2 = Policy('Policy Two', date(2015, 2, 1), 1600)
    p2.billing_schedule = 'Quarterly'
    p2.named_insured = anna_white.id
    p2.agent = joe_lee.id
    policies.append(p2)

    p3 = Policy('Policy Three', date(2015, 1, 1), 1200)
    p3.billing_schedule = 'Monthly'
    p3.named_insured = ryan_bucket.id
    p3.agent = john_doe_agent.id
    policies.append(p3)

    for policy in policies:
        db.session.add(policy)
    db.session.commit()

    for policy in policies:
        PolicyAccounting(policy.id)

    payment_for_p2 = Payment(p2.id, anna_white.id, 400, date(2015, 2, 1))
    db.session.add(payment_for_p2)
    db.session.commit()