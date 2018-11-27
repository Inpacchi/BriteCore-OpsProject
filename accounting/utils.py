#!/user/bin/env python2.7

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from accounting import db
from models import Contact, Invoice, Payment, Policy

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
        billing_schedules = {'Annual': 1, 'Semi-Annual': 3, 'Quarterly': 4, 'Monthly': 12}

        if not date_cursor: # If date_cursor is equal to the default value (None) or null, set it equal to the current date
            print "No date has been set. Setting date to current date."
            date_cursor = datetime.now().date()

        # Access the database to grab invoices according to the current policy. Filter them by looking for all invoices whose billing date is on or before 
        # the date_cursor, then order them by the billing date. The .all() method returns all matched invoices.
        invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
                                .filter(Invoice.bill_date <= date_cursor)\
                                .order_by(Invoice.bill_date)\
                                .all()

        due_now = 0 # Set our due_now variable to 0 as it is to be modified by invoices and payments

        if len(invoices) != 0: # If invoices is empty, don't bother executing code on it as we are wasting time
            if len(invoices) == 1:
                if not invoices.deleted: # Check the deleted status of the invoice to see if it was paid or not
                    print "1 invoice is present. Listing..."
                    print "The current invoice has a balance due of $", invoices[0].amount_due
                    due_now = invoices[0].amount_due
            else:
                print len(invoices), "invoices are present. Listing..."
                for invoice in invoices:
                    if not invoices.deleted: # Check the deleted status of the invoice to see if it was paid or not
                        print "The current invoice has a balance due of $", invoice.amount_due
                        due_now += invoice.amount_due # Increase due_now for each invoice found

            print "The current amount due is $", due_now
        else:
            print "No invoices are present."

        # Same logic as invoices above
        payments = Payment.query.filter_by(policy_id=self.policy.id)\
                                .filter(Payment.transaction_date <= date_cursor)\
                                .all()

        if len(payments) != 0: # Same logic as above length of invoices above
            print len(payments), " payments have been made. Listing..."
            for payment in payments:
                print "A payment has been made in the amount $", payment.amount_paid
                due_now -= payment.amount_paid # Subtract each payment from due_now

            print "The current amount due is now $", due_now, "\n"
        else:
            print "No payments have been made."

        if len(invoices) == 0 and len(payments) == 0: # If there are no payments or invoices, the account balance has not been paid
            # If that's the case, set due_now equal to the annual premium divided by the billing schedule
            due_now = self.policy.annual_premium / billing_schedules.get(self.policy.billing_schedule) #
            print "Since no invoices are present and as such, no payments have been made, the current amount due is $", due_now, "\n"

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
        
        invoice = Invoice.query.filter_by(policy_id=self.policy.id).first() # Get the paid invoice
        invoice.deleted = True # Change it's deleted status to true to reflect payment

        db.session.add(payment) # Add the payment to the database
        db.session.commit() # Commit the changes (save)

        return payment

    def evaluate_cancellation_pending_due_to_non_pay(self, date_cursor=None):
        if not date_cursor: # If date_cursor is equal to the default value (None) or null, set it equal to the current date
            date_cursor = datetime.now().date()

        

        if(date_cursor > invoice.due_date and date_cursor <= invoice.cancel_date)
            policy.status = 'Cancellation Pending due to non-pay'
        
        """
         If this function returns true, an invoice
         on a policy has passed the due date without
         being paid in full. However, it has not necessarily
         made it to the cancel_date yet.
        """
        pass

    def evaluate_cancel(self, date_cursor=None):
        if not date_cursor: # If date_cursor is equal to the default value (None) or null, set it equal to the current date
            date_cursor = datetime.now().date()

        # Access the database to grab invoices according to the current policy. Filter them by looking for all invoices whose billing date is on or before 
        # the date_cursor, then order them by the billing date. The .all() method returns all matched invoices.
        invoices = Invoice.query.filter_by(policy_id=self.policy_id)\
                                .filter(Invoice.cancel_date <= date_cursor)\
                                .order_by(Invoice.bill_date)\
                                .all()

        for invoice in invoices: # For each invoice...
            if not self.return_account_balance(invoice.cancel_date): # If there is no account balance on the cancel date...
                continue # Continue on to the next iteration of the for loop
            else:
                print "THIS POLICY SHOULD HAVE CANCELED" # Otherwise the policy should be cancelled
                break
        else:
            print "THIS POLICY SHOULD NOT CANCEL" # This is where you end up if invoices returns continue

    def make_invoices(self):
        for invoice in self.policy.invoices: # If there are any invoices, delete them as we are making new ones
            invoice.delete()

        billing_schedules = {'Annual': None, 'Semi-Annual': 3, 'Quarterly': 4, 'Monthly': 12}

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

