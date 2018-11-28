#!/user/bin/env python2.7

import unittest
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from accounting import db
from models import Contact, Invoice, Payment, Policy
from utils import PolicyAccounting

"""
#######################################################
Test Suite for Accounting
#######################################################
"""
class TestChangeBillingSchedule(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print "Setting up TestChangeBillingSchedule class..."
        cls.test_agent = Contact('Test Joe Lee', 'Agent')
        cls.test_insured = Contact('Test Anna White', 'Named Insured')
        db.session.add(cls.test_agent)
        db.session.add(cls.test_insured)
        db.session.commit()

        cls.policy = Policy('Test Policy Two', date(2015, 2, 1), 1600)
        db.session.add(cls.policy)
        db.session.commit()

        cls.policy.named_insured = cls.test_insured.id
        cls.policy.agent = cls.test_agent.id
        cls.policy.billing_schedule = 'Quarterly'
        db.session.commit()
        print "Class set up!\n"
    
    @classmethod
    def tearDownClass(cls):
        print "Tearing down class..."
        for invoice in cls.policy.invoices:
            db.session.delete(invoice)
        db.session.delete(cls.test_insured)
        db.session.delete(cls.test_agent)
        db.session.delete(cls.policy)
        db.session.commit()
        print "Class torn down!\n"
    
    def setUp(self):
        pass

    def tearDown(self):
        pass
    
    def test_change_billing_schedule(self):
        print "Testing change of billing schedule..."
        pa = PolicyAccounting(self.policy.id)

        self.assertTrue(self.policy.invoices)

        first_invoice_paid = Invoice.query.filter_by(policy_id=self.policy.id).first()
        first_invoice_paid.amount_due = 0

        self.assertEquals(pa.change_billing_schedule(), 9) 
        # This test relies on the temporary return value
        print "Done!"

class TestBillingSchedules(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print "Setting up TestBillingSchedules class..."
        cls.test_agent = Contact('Test Agent', 'Agent')
        cls.test_insured = Contact('Test Insured', 'Named Insured')
        db.session.add(cls.test_agent)
        db.session.add(cls.test_insured)
        db.session.commit()

        cls.policy = Policy('Test Policy', date(2015, 1, 1), 1200)
        db.session.add(cls.policy)
        cls.policy.named_insured = cls.test_insured.id
        cls.policy.agent = cls.test_agent.id
        db.session.commit()
        print "Class set up!\n"

    @classmethod
    def tearDownClass(cls):
        print "Tearing down class..."
        db.session.delete(cls.test_insured)
        db.session.delete(cls.test_agent)
        db.session.delete(cls.policy)
        db.session.commit()
        print "Class torn down!\n"

    def setUp(self):
        pass

    def tearDown(self):
        print "Tearing down..."
        for invoice in self.policy.invoices:
            db.session.delete(invoice)
        db.session.commit()
        print "Torn down!\n"

    def test_annual_billing_schedule(self):
        print "Testing annual billing schedule...\n"
        self.policy.billing_schedule = "Annual"
        #No invoices currently exist
        self.assertFalse(self.policy.invoices)
        #Invoices should be made when the class is initiated
        pa = PolicyAccounting(self.policy.id)
        self.assertEquals(len(self.policy.invoices), 1)
        self.assertEquals(self.policy.invoices[0].amount_due, self.policy.annual_premium)
        print "Done!\n"

    def test_monthly_billing_schedule(self):
        print "Test monthly billing schedule...\n"
        self.policy.billing_schedule = "Monthly"
        self.assertFalse(self.policy.invoices)
        pa = PolicyAccounting(self.policy.id)
        self.assertEquals(len(self.policy.invoices), 12)
        self.assertEquals(self.policy.invoices[0].amount_due, self.policy.annual_premium/12)
        print "Done!\n"


class TestReturnAccountBalance(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print "Setting up TestReturnAccountBalance class..."
        cls.test_agent = Contact('Test Agent', 'Agent')
        cls.test_insured = Contact('Test Insured', 'Named Insured')
        db.session.add(cls.test_agent)
        db.session.add(cls.test_insured)
        db.session.commit()

        cls.policy = Policy('Test Policy', date(2015, 1, 1), 1200)
        cls.policy.named_insured = cls.test_insured.id
        cls.policy.agent = cls.test_agent.id
        db.session.add(cls.policy)
        db.session.commit()
        print "Class set up!\n"

    @classmethod
    def tearDownClass(cls):
        print "Tearing down class..."
        db.session.delete(cls.test_insured)
        db.session.delete(cls.test_agent)
        db.session.delete(cls.policy)
        db.session.commit()
        print "Class torn down!\n"

    def setUp(self):
        print "Setting up..."
        self.payments = []
        print "Set up!\n"

    def tearDown(self):
        print "Tearing down..."
        for invoice in self.policy.invoices:
            db.session.delete(invoice)
        for payment in self.payments:
            db.session.delete(payment)
        db.session.commit()
        print "Torn down!\n"

    def test_annual_on_eff_date(self):
        print "Testing account balance on annual effective date...\n"
        self.policy.billing_schedule = "Annual"
        pa = PolicyAccounting(self.policy.id)
        self.assertEquals(pa.return_account_balance(date_cursor=self.policy.effective_date), 1200)
        print "Done!\n"

    def test_quarterly_on_eff_date(self):
        print "Testing account balance on quarterly effective date...\n"
        self.policy.billing_schedule = "Quarterly"
        pa = PolicyAccounting(self.policy.id)
        self.assertEquals(pa.return_account_balance(date_cursor=self.policy.effective_date), 300)
        print "Done!\n"

    def test_quarterly_on_last_installment_bill_date(self):
        print "Testing account balance on last installment of quarterly bill date...\n"
        self.policy.billing_schedule = "Quarterly"
        pa = PolicyAccounting(self.policy.id)
        invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
                                .order_by(Invoice.bill_date).all()
        self.assertEquals(pa.return_account_balance(date_cursor=invoices[3].bill_date), 1200)
        print "Done!\n"

    def test_quarterly_on_second_installment_bill_date_with_full_payment(self):
        print "Testing account balance on second-to-last installment of quarterly bill date with full payment...\n"
        self.policy.billing_schedule = "Quarterly"
        pa = PolicyAccounting(self.policy.id)
        invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
                                .order_by(Invoice.bill_date).all()
        self.payments.append(pa.make_payment(contact_id=self.policy.named_insured,
                                             date_cursor=invoices[1].bill_date, amount=600))
        self.assertEquals(pa.return_account_balance(date_cursor=invoices[1].bill_date), 0)
        print "Done!\n"
