/*function Policy(policyNumber, effectiveDate, status, billingSchedule, annualPremium, accountBalance, namedInsured, agent){
    this.policyNumber = policyNumber;
    this.effectiveDate = effectiveDate;
    this.status = status;
    this.billingSchedule = billingSchedule;
    this.annualPremium = annualPremium;
    this.accountBalance = accountBalance;
    this.namedInsured = namedInsured;
    this.agent = agent;
}*/

var currentPolicies = [
    {
        policyNumber: "Policy One", 
        effectiveDate: "1/1/2015", 
        status: "Active", 
        billingSchedule: "Annual", 
        annualPremium: 365, 
        accountBalance: 0, 
        namedInsured: "John Doe", 
        agent: "Bob Smith"
    }
];

function PoliciesViewModel() {
    var self = this;
    
    /*this.policies = ko.observableArray([
        new Policy(this.currentPolicies[0], this.currentPolicies[1], this.currentPolicies[2], this.currentPolicies[3], this.currentPolicies[4], this.currentPolicies[5], this.currentPolicies[6], this.currentPolicies[7])
    ]);*/
    self.policies = ko.observableArray([]);


    currentPolicies.forEach(function(policy){
        self.policies().push(policy);
    });
};

ko.applyBindings(new PoliciesViewModel());