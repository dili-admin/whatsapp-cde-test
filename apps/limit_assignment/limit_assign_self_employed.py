import json

def limit_asign(data):
    bureau_income = 0 if 'bureau_income' not in data else data['bureau_income']
    sum_emi_actAccount = 0 if 'sum_emi_actAccount' not in data else data['sum_emi_actAccount']
    estimated_Foir = round(bureau_income * 0.7) if bureau_income not in [-99999, 0, None] else 0
    final_amount_emi = abs(estimated_Foir - sum_emi_actAccount)
    intrest_rate = 0.01333333
    tenure = 36
    final_amount = ((final_amount_emi/(((1+intrest_rate) ** tenure)/(((1+intrest_rate) ** tenure)-1))))/intrest_rate
    if final_amount <40000:
        resp = 40000
    elif final_amount > 100000:
        resp = 100000
    else:
        resp = round(final_amount)
    return resp
