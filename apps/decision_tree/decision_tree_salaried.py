import json

def decision_tree(data):
    employment_type = '' if 'employment_type' not in data else data['employment_type']
    bureau_score = 0 if 'bureau_score' not in data else data['bureau_score']
    loan_amount = 0 if 'loan_amount' not in data else data['loan_amount']
    
    if ((employment_type == 'salaried')):
        if ((bureau_score >= 760)):
            resp = {'decision': 'Approve', 'reason': 'bureau score is greater than 760'}      
        elif (((bureau_score >= 705) and (bureau_score < 759)) and (loan_amount <= 75000)):
            resp = {'decision': 'Approve', 'reason': 'bureau score is greater than 705'}
        elif (((bureau_score >= 705) and (bureau_score < 759)) and (loan_amount > 75000)):
            resp = {'decision': 'Approve', 'reason': 'bureau score is greater than 705 and less than 759'}
        elif (((bureau_score >= 650) and (bureau_score < 704))):
            resp = {'decision': 'Approve', 'reason': 'bureau score is greater than 650 and less than 704'}
        elif ((bureau_score >= 1) and (bureau_score < 649)):
            resp = {'decision': 'Decline', 'reason': 'bureau score is less than 649'}        
        elif (((bureau_score == -1) and (loan_amount <= 75000))):
            resp = {'decision': 'Review', 'reason': 'bureau score is -1'}  
        elif (((bureau_score == 0) and (loan_amount <= 75000))):
            resp = {'desicion': 'Review', 'reason': 'bureau score is 0'} 
        else:
            resp = {'decision': 'Decline', 'reason': 'buereau score is not valide'}        
    else:
        resp = {'decision': 'Decline', 'reason': 'Invalide Employement Type'}                                                 
    return resp
