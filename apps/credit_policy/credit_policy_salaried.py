import operator

policyrulesdict = {
    'num_unsecured_tls_exec_cc':{
        'operator': operator.gt,
        'value': 6,
        'reason': 'Total Number of UnSecured Active Loans Exclude CC > 6'
    },
   'num_personal_loans':{
        'operator': operator.gt,
        'value': 3,
        'reason': 'Total Number of personal loans including short term PL > 3'
    },
    'settlement_writeoff_l12m_exec_cc':{
        'operator': operator.gt,
        'value': 5000,
        'reason': 'Settlement/write off total amount > 5000 in the last 12 months'
    },
    'settlement_writeoff_l36m_exec_cc':{
        'operator': operator.gt,
        'value': 5000,
        'reason': 'Settlement/write off total amount > 5000 in the last 36 months'
    },
    'num_tls_30dpd_l6mts':{
        'operator': operator.gt,
        'value': 0,
        'reason': 'Number of accounts 30 DPD > 0 in the last 6 months'
    },
    'num_tls_60dpd_l12mts':{
        'operator': operator.gt,
        'value': 0,
        'reason': 'Number of accounts 60 DPD > 0 in the last 12 months'
    },
    'num_tls_90dpd_l36mts':{
        'operator': operator.gt,
        'value': 0,
        'reason': 'Number of accounts 90 DPD > 0 in the last 36 months'
    },
    'debitburdenratio':{
        'operator': operator.gt,
        'value': 0.80,
        'reason': 'Debt Burden Ratio < 80%'
    },
    'experian_score':{
        'operator': operator.lt,
        'value': 650,
        'reason': 'Bureau Score is less than 650'
    }
}

def check_condition(inp, relate, cut):    
    return relate(inp, cut)


def creditpolicy(data):
    policy_reasons = [policyrulesdict[k]['reason'] for k in policyrulesdict if (k in data) and (data[k] not in [-99999, "-99999"]) and check_condition(data[k],policyrulesdict[k]['operator'],policyrulesdict[k]['value'])]
    policy_decision = 'Decline' if policy_reasons else 'Approve'
    resp =  {
    'policy_decision' : policy_decision,
    'policy_reasons': policy_reasons
        }
    return resp
