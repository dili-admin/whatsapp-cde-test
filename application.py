import json
#https://docs.python.org/2/library/operator.html
from flask import Flask, jsonify, request
import logging
from datetime import datetime
import string 
import random
from encrypt_files import encrypt_file, enc_key

from apps.bureau_rollup.rollup import experian_rollup
from apps.buearu_scorecard.scorecard_bureau import bureau_score
from apps.credit_policy.credit_policy_salaried import creditpolicy as salaried_creditpolicy
from apps.credit_policy.credit_policy_selfemployed import creditpolicy as selfemployed_creditpolicy
from apps.decision_tree.decision_tree_salaried import decision_tree as salaried_decision_tree
from apps.decision_tree.decision_tree_selfemployed import decision_tree as self_employed_decision_tree
from apps.limit_assignment.limit_assign_salaried import limit_asign as salaried_limit_asign
from apps.limit_assignment.limit_assign_self_employed import limit_asign as self_employed_limit_asign

app = Flask(__name__)

logging.basicConfig(filename='logs/error_application.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route("/quick_approval", methods=['POST'])
def quick_approval():
    data = request.get_json()
    expreian_data_check_old=False if 'experian' not in data else False if data['experian'] in ['', None, {}] else True
    expreian_data_check_new=False if 'experian' not in data else False if data['experian'] in ['', None, {}] else False if 'xmlReport' not in data['experian'] else False if 'xmlReport' in data['experian'] and data['experian']['xmlReport'] in ['', None] else True
    
    if expreian_data_check_old and expreian_data_check_new:
        expreian_data_check = True
    elif expreian_data_check_old and not(expreian_data_check_new):
        expreian_data_check = True
    elif not(expreian_data_check_old) and expreian_data_check_new:
        expreian_data_check = True
    elif not(expreian_data_check_old) and not(expreian_data_check_new):
        expreian_data_check = False
    else:
        expreian_data_check = False
    try:
        data['experian'] = data['experian']['xmlReport']
    except:
        data['experian'] = data['experian']

    application_id=data['application_id'] if 'application_id' in data else ''
    customer_name= data['customer_name'] if 'customer_name' in data else ''
    if expreian_data_check:
        experian_rollup_resp=experian_rollup(data)
        bureau_scorecard_resp=bureau_score(experian_rollup_resp)
        employment_type=data['employment_type'] if 'employment_type' in data else None
        if employment_type:
            combined_rollup_data = {**experian_rollup_resp, "loan_amount": data['loan_amount'], "employment_type": data['employment_type'], "bureau_score": bureau_scorecard_resp }
            if employment_type == 'salaried':
                credit_policy_resp=salaried_creditpolicy(combined_rollup_data)
                if credit_policy_resp['policy_decision'] == 'Approve':
                    limit_assign_resp=salaried_limit_asign(combined_rollup_data)
                    decision_tree_resp=salaried_decision_tree(combined_rollup_data)
                    if decision_tree_resp['decision']=='Decline':
                        resp = {"application_id": application_id,"customer_name" :customer_name, "bureau_score": bureau_scorecard_resp ,"experian_rollup":experian_rollup_resp,"decision":decision_tree_resp['decision'], "reason": decision_tree_resp['reason'], "limit_assignment": 0}
                    else:
                        resp = {"application_id": application_id,"customer_name" :customer_name, "bureau_score": bureau_scorecard_resp ,"experian_rollup":experian_rollup_resp,"decision":decision_tree_resp['decision'], "reason": decision_tree_resp['reason'], "limit_assignment": limit_assign_resp}
                else:
                    resp = {"application_id": application_id,"customer_name" :customer_name, "bureau_score": bureau_scorecard_resp ,"experian_rollup":experian_rollup_resp,"decision":credit_policy_resp['policy_decision'], "reason":credit_policy_resp['policy_reasons']}
            elif employment_type == 'self_employed':
                credit_policy_resp=selfemployed_creditpolicy(combined_rollup_data)
                if credit_policy_resp['policy_decision'] == 'Approve':
                    limit_assign_resp=self_employed_limit_asign(combined_rollup_data)
                    decision_tree_resp=self_employed_decision_tree(combined_rollup_data)
                    if decision_tree_resp['decision']=='Decline':
                        resp = {"application_id": application_id,"customer_name" :customer_name, "bureau_score": bureau_scorecard_resp ,"experian_rollup":experian_rollup_resp,"decision":decision_tree_resp['decision'], "reason": decision_tree_resp['reason'], "limit_assignment":0}
                    else:
                        resp = {"application_id": application_id,"customer_name" :customer_name, "bureau_score": bureau_scorecard_resp ,"experian_rollup":experian_rollup_resp,"decision":decision_tree_resp['decision'], "reason": decision_tree_resp['reason'], "limit_assignment": limit_assign_resp}
                else:
                    resp = {"application_id": application_id,"customer_name" :customer_name, "bureau_score": bureau_scorecard_resp ,"experian_rollup":experian_rollup_resp,"decision":credit_policy_resp['policy_decision'], "reason":credit_policy_resp['policy_reasons']}        
            else:
                resp = {"application_id": application_id,"customer_name" :customer_name, "status": "Failed", "Error": "employment_type must be self_employed/salaried"}, 400   
        else:
            resp = {"application_id": application_id,"customer_name" :customer_name, "status": "Failed", "Error": "employment_type is Missing"}, 400   
    else:
        resp = {"application_id": application_id, "customer_name" :customer_name, "status": "Failed", "Error": "Experian Data is Missing"}, 400
    
    filename=datetime.now().strftime("%d_%m_%Y_%H_%M_%S_") + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    jsonFile = open("BureauReports/"+filename+".txt", "w")
    request_data = json.dumps(data)
    jsonFile.write("-----------------------------\n REQUEST \n----------------------- \n")
    jsonFile.write(request_data)
    jsonFile.write("\n -----------------------------\n RESPONSE \n----------------------- \n")
    resp_data= json.dumps(resp)
    jsonFile.write(resp_data)
    jsonFile.close()
    encrypt_file(enc_key, "BureauReports/"+filename+".txt")
    return resp
