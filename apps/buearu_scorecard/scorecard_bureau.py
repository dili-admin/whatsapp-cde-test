import json


bureau_keys={"age_oldest_tl_mnths":int,"enq_L6m":int,"enq_L12m":int,"num_tls_60dpd_l12mts":int,"num_times_1p_dpd_l12m":int,"pct_Satis_tl_to_total_tl":int,"time_since_recent_deliquency":int,
"cc_high_credit_balance":int,"amntoverdue_l24mths":int,"num_open_cc":int,"enq_L1m_by_L3m":int,"num_secured_tls":int,"num_unsecured_tls":int,"total_unsec_tlbalance":int,"num_open_pl":int,
"num_delinquent_tl":int,"num_tradelines":int,"first_product_cc":str,"avg_age_tl_mnths":int}

def replace_nones(d,dataTypeData):
    resp = {}
    for n in dataTypeData:
        for k, v in d.items():
            resp[k] = -99999 if ((v is None) and (dataTypeData[n] == int)) else "-99999" if ((v is None) and (dataTypeData[n] == str)) else v
        resp[n] = -99999 if ((n not in d) and (dataTypeData[n] == int)) else "-99999" if ((n not in d) and (dataTypeData[n] == str)) else v
    return resp

def min_max(data, key:str, value):
    try:
        for min_max in data[key]:
            if type(value) == int: 
                if value == min_max['min'] and value == min_max['max']:
                    #condition for missing
                    resp = min_max['value']
                    break
                elif value >= min_max['min'] and value < min_max['max']:
                    resp = min_max['value']
                    break
            else:
                if value == min_max['input_val']:
                    resp = min_max['value']
                    break
        return resp
    except:
        resp = 0
        return resp

def bureau_score(data):
    key_min_max={"age_oldest_tl_mnths": [{"min":-99999,"max":-99999,"value":27},{"min":0,"max":12,"value":31},
                        {"min":12,"max":24,"value":43},{"min":24,"max":48,"value":48},
                        {"min":48,"max":54,"value":53},{"min":54,"max":68,"value":58},
                        {"min":68,"max":84,"value":63},{"min":84,"max":102,"value":68},
                        {"min":102,"max":130,"value":73},{"min":130,"max":float('inf'),"value":78}],
                "enq_L6m": [{"min":-99999,"max":-99999,"value":21},{"min":0,"max":1,"value":67},
                        {"min":1,"max":2,"value":62},{"min":2,"max":3,"value":57},
                        {"min":3,"max":5,"value":52},{"min":5,"max":7,"value":42},
                        {"min":7,"max":9,"value":32},{"min":9,"max":float('inf'),"value":27}],
                "enq_L12m": [{"min":-99999,"max":-99999,"value":9},{"min":0,"max":2,"value":60},
                        {"min":2,"max":4,"value":55},{"min":4,"max":6,"value":50},
                        {"min":6,"max":9,"value":40},{"min":9,"max":12,"value":30},
                        {"min":12,"max":15,"value":25},{"min":15,"max":18,"value":20},{"min":18,"max":float('inf'),"value":15}],
                "num_tls_60dpd_l12mts": [{"min":-99999,"max":-99999,"value":25},{"min":0,"max":0,"value":66},
                        {"min":0,"max":2,"value":61},{"min":2,"max":4,"value":62},
                        {"min":4,"max":6,"value":52},{"min":6,"max":8,"value":35},
                        {"min":8,"max":11,"value":28},{"min":11,"max":float('inf'),"value":22}],
                "num_times_1p_dpd_l12m": [{"min":-99999,"max":-99999,"value":13},{"min":0,"max":0,"value":54},
                        {"min":0,"max":2,"value":49},{"min":2,"max":4,"value":50},
                        {"min":4,"max":6,"value":40},{"min":6,"max":8,"value":23},
                        {"min":8,"max":11,"value":16},{"min":11,"max":float('inf'),"value":10}],
                "pct_Satis_tl_to_total_tl": [{"min":-99999,"max":-99999,"value":14},{"min":0,"max":10,"value":9},
                        {"min":10,"max":15,"value":14},{"min":15,"max":30,"value":19},
                        {"min":30,"max":50,"value":24},{"min":50,"max":75,"value":29},
                        {"min":75,"max":90,"value":39},{"min":90,"max":98,"value":44},{"min":98,"max":float('inf'),"value":55}],
                "time_since_recent_deliquency": [{"min":-99999,"max":-99999,"value":20},{"min":0,"max":6,"value":25},
                        {"min":6,"max":12,"value":30},{"min":12,"max":18,"value":35},
                        {"min":18,"max":24,"value":40},{"min":24,"max":36,"value":50},{"min":36,"max":float('inf'),"value":55}],
                "cc_high_credit_balance": [{"min":-99999,"max":-99999,"value":13},{"min":0,"max":20,"value":54},
                        {"min":20,"max":35,"value":49},{"min":35,"max":45,"value":44},
                        {"min":45,"max":60,"value":39},{"min":60,"max":85,"value":34},
                        {"min":85,"max":95,"value":29},{"min":95,"max":float('inf'),"value":24}],
                "amntoverdue_l24mths": [{"min":-99999,"max":-99999,"value":25},{"min":0,"max":0,"value":56},
                        {"min":0,"max":500,"value":51},{"min":500,"max":1000,"value":41},
                        {"min":1000,"max":2000,"value":36},{"min":2000,"max":5000,"value":31},
                        {"min":5000,"max":10000,"value":26},{"min":10000,"max":float('inf'),"value":21}],        
                "num_open_cc": [{"min":-99999,"max":-99999,"value":19},{"min":0,"max":1,"value":25},
                        {"min":1,"max":2,"value":40},{"min":2,"max":3,"value":45},
                        {"min":3,"max":4,"value":50},{"min":4,"max":5,"value":55},
                        {"min":5,"max":8,"value":60},{"min":8,"max":float('inf'),"value":65}],
                "enq_L1m_by_L3m": [{"min":-99999,"max":-99999,"value":14},{"min":0,"max":0,"value":44},
                        {"min":0,"max":50,"value":34},{"min":50,"max":75,"value":29},
                        {"min":75,"max":90,"value":24},{"min":90,"max":95,"value":19},
                        {"min":95,"max":100,"value":14},{"min":100,"max":float('inf'),"value":9}],
                "num_secured_tls":[{"min":-99999,"max":-99999,"value":19},{"min":0,"max":1,"value":24},
                        {"min":1,"max":2,"value":29},{"min":2,"max":3,"value":34},
                        {"min":3,"max":4,"value":39},{"min":4,"max":5,"value":44},
                        {"min":5,"max":6,"value":49},{"min":6,"max":float('inf'),"value":55}], 
                "num_unsecured_tls": [{"min":-99999,"max":-99999,"value":19},{"min":0,"max":1,"value":49},
                        {"min":1,"max":2,"value":44},{"min":2,"max":3,"value":39},
                        {"min":3,"max":4,"value":34},{"min":4,"max":6,"value":29},{"min":6,"max":float('inf'),"value":19}],
                "total_unsec_tlbalance": [{"min":-99999,"max":-99999,"value":19},{"min":0,"max":50000,"value":55},
                        {"min":50000,"max":100000,"value":50},{"min":100000,"max":300000,"value":45},
                        {"min":300000,"max":500000,"value":35},{"min":500000,"max":float('inf'),"value":30}],
                "num_open_pl": [{"min":-99999,"max":-99999,"value":19},{"min":0,"max":1,"value":49},
                        {"min":1,"max":2,"value":44},{"min":2,"max":3,"value":39},{"min":3,"max":float('inf'),"value":34}],
                "num_delinquent_tl": [{"min":-99999,"max":-99999,"value":25},{"min":0,"max":1,"value":65},
                        {"min":1,"max":2,"value":55},{"min":2,"max":3,"value":50},
                        {"min":3,"max":4,"value":45},{"min":4,"max":5,"value":35},
                        {"min":5,"max":6,"value":30},{"min":6,"max":7,"value":25},{"min":7,"max":float('inf'),"value":20}],
                "num_tradelines": [{"min":-99999,"max":-99999,"value":13},{"min":1,"max":3,"value":34},
                        {"min":3,"max":6,"value":31},{"min":6,"max":9,"value":26},
                        {"min":9,"max":12,"value":20},{"min":12,"max":15,"value":18},
                        {"min":15,"max":18,"value":15},{"min":18,"max":float('inf'),"value":12}],
                "first_product_cc": [{"input_val":"-99999","value":19},{"input_val":"Yes","value":39},
                        {"input_val":"No","value":29}],
                "avg_age_tl_mnths": [{"min":-99999,"max":-99999,"value":14},{"min":0,"max":6,"value":19},
                        {"min":6,"max":12,"value":24},{"min":12,"max":24,"value":29},
                        {"min":24,"max":48,"value":34},{"min":48,"max":96,"value":39},
                        {"min":96,"max":120,"value":44},{"min":120,"max":float('inf'),"value":54}]                                                                                                                                                                                                       
                        }


    bureau_data=replace_nones(data, bureau_keys)
    score_resp=[]
    for key in bureau_data:
        if key in bureau_keys:
            score_resp.append(min_max(key_min_max, key, bureau_data[key]))
    resp=sum(score_resp)
    return resp