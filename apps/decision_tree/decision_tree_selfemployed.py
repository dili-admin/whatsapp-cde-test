import json

def decision_tree(data):
    employment_type = '' if 'employment_type' not in data else data['employment_type']
    bureau_score = 0 if 'bureau_score' not in data else data['bureau_score']
    loan_amount = 0 if 'loan_amount' not in data else data['loan_amount']
    #composite_score = 0 if 'composite_score' not in data else data['composite_score']
    #bs_score = 0 if 'bs_score' not in data else data['bs_score']
    #cus_segment = '' if 'customer_seg' not in data else data['customer_seg']
    
    if ((employment_type == 'self_employed')):
        if ((bureau_score >= 759)):
            resp = {'decision': 'Approve', 'reason': 'bureau score is greater than 759'}         
        elif (((bureau_score >= 705) and (bureau_score < 759)) and (loan_amount <= 75000)):
            resp = {'decision': 'Review', 'reason': 'bureau score is greater than 705'}
        elif (((bureau_score >= 705) and (bureau_score < 759)) and (loan_amount > 75000)):
            resp = {'decision': 'Approve', 'reason': 'bureau score is greater than 705 and less than 759'}
        elif (((bureau_score >= 650) and (bureau_score < 704))):
            resp = {'decision': 'Approve', 'reason': 'bureau score is greater than 650 and less than 704'}
        elif ((bureau_score >= 1) and (bureau_score < 649)):
            resp = {'decision': 'Decline', 'reason': 'bureau score is less than 649'}           
        elif ((bureau_score == -1) or (bureau_score == 0)):
            resp = {'decision': 'Decline', 'reason': 'buereau score is not valide'}  
        else:
            resp = {'decision': 'Decline', 'reason': 'buereau score is not valide'}  
    else:
        resp = {'decision': 'Decline', 'reason': 'Invalide Employement Type'}                                                
    return resp
