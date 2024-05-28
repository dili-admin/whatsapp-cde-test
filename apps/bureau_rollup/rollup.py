import xmltodict
import json
from datetime import datetime
from dateutil import relativedelta
import statistics as stat
import itertools
import re

# Added on 4th May'23
def diff_month(d1, d2):
    return(d1.year -d2.year)*12+d1.month-d2.month

def getenquiry_list(data):
    try:
        enqdata_list = data['CAPS']['CAPS_Application_Details'] if 'CAPS' in data else None
    except:
        enqdata_list = []
    if type(enqdata_list) == list:
        enqdata = enqdata_list if enqdata_list else []
    elif type(enqdata_list) == dict:
        enqdata = []
        enqdata.append(enqdata_list)
    else:
        enqdata = []
    return enqdata


def getaccount_list(data, reqDatatype):
    if reqDatatype == 'accountList':
        accdata_list = None if data == [] else data['CAIS_Account']['CAIS_Account_DETAILS'] if 'CAIS_Account' in data else None
        if type(accdata_list) == list:
            accdata = accdata_list if accdata_list else []
        elif type(accdata_list) == dict:
            accdata = []
            accdata.append(accdata_list)
        else:
            accdata = []
    elif reqDatatype == 'accountSumm':
        accdata = None if data == [] else data['CAIS_Account']['CAIS_Summary']['Credit_Account'] if 'CAIS_Summary' in data['CAIS_Account'] else None
    elif reqDatatype == 'outsatndBal':
        accdata = None if data == [] else data['CAIS_Account']['CAIS_Summary']['Total_Outstanding_Balance'] if 'CAIS_Summary' in data['CAIS_Account'] else None
    else:
        raise Exception("Invalide option in getaccount_list")
    return accdata

def date_format(d):
    if d == '00000000' or d == '' or d is None:
        d = '19000101'
    return datetime.strptime(d[:4]+'-'+d[4:6]+'-'+d[-2:], '%Y-%m-%d')

def excl_none_operation(li, func):
    lis = [i for i in li if i is not None]
    if func == 'sum':
        return sum(lis) if len(lis) > 0 else -99999
    elif func == 'max':
        return max(lis) if len(lis) > 0 else -99999
    elif func == 'min':
        return min(lis) if len(lis) > 0 else -99999
    else:
        return stat.mean(lis) if len(lis) > 0 else -99999

def get_split_paygrid_res(li, cond, strind, endind, func, eq):
    resp = None
    lis=[x for x in li[strind:endind] if x == cond] if eq else [x for x in li[strind:endind] if x >= cond]
    deflt = 0 if (func == 'sum') else None
    resp = sum(lis) if (len(lis) > 0 and func == 'sum') else max(lis) if (len(lis) > 0 and func == 'max') else len(lis) if func == 'count' else deflt        
    return resp

def get_var_pd(data, pdDays, mnts):
    resp = 1 if max(data[:mnts]) > pdDays else 0
    return resp

def get_paymenthistory(data):
    payment_history = [item for sublist in data for item in sublist]
    resp = [item.split("/", 1)[0] for item in payment_history] 
    resp = [-1 if item in ['N', 'S', '?'] else 3 if item in ['M', 'B', 'D', 'L'] else int(item) for item in resp]
    return resp

def replace_nones(d):
    resp = {}
    for k, v in d.items():
        resp[k] = -99999 if v is None else v
    return resp

def experian_rollup(input_data):
    try:
        exp_data = input_data['experian'].replace('&lt;', '<').replace('&quot;', "'").replace('&gt;', '>')
        data_dict=xmltodict.parse(exp_data)
    except:
        print("Error in XML Parsing")
        print(input_data)
        data_dict={}
        return {"error": "error in XML parsing"}
    data=data_dict['INProfileResponse'] if 'INProfileResponse' in data_dict else {}
    accounts = getaccount_list(data, 'accountList')
    req_date=date_format(data['CreditProfileHeader']['ReportDate']) if 'CreditProfileHeader' in data else datetime.now()
    invalid = [None,'']
    invalid_div = [None,'', 0, -99999]
    rollupvars={}
   ####################CustomerDetails######################
    try:
        rollupvars['customer_name'] = data['Current_Application']['Current_Application_Details']['Current_Applicant_Details']['First_Name'] + ' ' + data['Current_Application']['Current_Application_Details']['Current_Applicant_Details']['Last_Name']
        rollupvars['mobile_number'] = data['Current_Application']['Current_Application_Details']['Current_Applicant_Details']['MobilePhoneNumber']
    except:
        rollupvars['customer_name'] = ''
        rollupvars['mobile_number'] = ''

    rollupvars['resp_time'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    ####################Enquires#############################
    enquiry_data = getenquiry_list(data)
    if enquiry_data:
        enquiry = [{'DateOfInquiry': date_format(item['Date_of_Request']) if 'Date_of_Request' in item and item['Date_of_Request'] not in invalid else None,
           'DISBURSEDDATE':req_date} for item in enquiry_data]
        enquiry = [{**item, 'enquiries_L1m': item['DISBURSEDDATE'] - relativedelta.relativedelta(months=1),
                'enquiries_L3m': item['DISBURSEDDATE'] - relativedelta.relativedelta(months=3),
                'enquiries_L6m': item['DISBURSEDDATE'] - relativedelta.relativedelta(months=6),
                'enquiries_L12m': item['DISBURSEDDATE'] - relativedelta.relativedelta(months=12)} for item in enquiry]
        enq_L1m = ['1' for item in enquiry if (item['DateOfInquiry'] > item['enquiries_L1m'])]
        enq_L3m = ['1' for item in enquiry if (item['DateOfInquiry'] > item['enquiries_L3m'])]
        enq_L6m = ['1' for item in enquiry if (item['DateOfInquiry'] > item['enquiries_L6m'])]
        enq_L12m = ['1' for item in enquiry if (item['DateOfInquiry'] > item['enquiries_L12m'])]
        rollupvars['total_enqs'] = len(enquiry)
        rollupvars['enq_L1m'] = len(enq_L1m)
        rollupvars['enq_L3m'] = len(enq_L3m)
        rollupvars['enq_L6m'] = len(enq_L6m)
        rollupvars['enq_L12m'] = len(enq_L12m)
    else:
        rollupvars['enq_L1m']=0
        rollupvars['enq_L3m']=0
        rollupvars['enq_L6m']=0
        rollupvars['enq_L12m']=0
        rollupvars['total_enqs']=0    
    if accounts:
        ###################Account#############################
        trades = [{'StartDate': date_format(item['Open_Date']) if 'Open_Date' in item and item['Open_Date'] not in invalid else None,
                  'ClosedDate': date_format(item['Date_Closed']) if 'Date_Closed' in item and item['Date_Closed'] not in invalid else None,
                  'AccountType': item['Account_Type'] if 'Account_Type' in item else None,
                  'CurrentBalance': 0 if 'Current_Balance' not in item else 0 if item['Current_Balance'] in ['', None] else 0 if float(item['Current_Balance'].replace(',','')) < 0 else float(item['Current_Balance'].replace(',','')),
                  'active_tl_flag': 1 if 'Date_Closed' not in item else 0 if item['Date_Closed'] not in ['', None] else 1,
                  'creditlimit': None if 'Credit_Limit_Amount' not in item else None if item['Credit_Limit_Amount'] in invalid else int(item['Credit_Limit_Amount'].replace(',','')),
                  'ScheduledPaymentAmount': 0 if 'Scheduled_Monthly_Payment_Amount' not in item else 0 if item['Scheduled_Monthly_Payment_Amount'] in invalid else int(item['Scheduled_Monthly_Payment_Amount'].replace(',','')),
                  'HighestCreditLoanAmount': 0 if 'Highest_Credit_or_Original_Loan_Amount' not in item else 0 if item['Highest_Credit_or_Original_Loan_Amount'] in invalid else int(item['Highest_Credit_or_Original_Loan_Amount'].replace(',','')),
                  'CreditLimitAmount': 0 if 'Credit_Limit_Amount' not in item else 0 if item['Credit_Limit_Amount'] in invalid else int(item['Credit_Limit_Amount'].replace(',','')),
                  'account_status': int(item['Account_Status']) if 'Account_Status' in item else None} for item in accounts]

        trades = [{**item, 'open_date_missindicator': 0 if item['ClosedDate'] not in invalid_div else 1,
                  'close_date_missindicator': 1 if item['ClosedDate'] not in invalid_div else 0,
                  'HighestCreditLoanAmount': item['HighestCreditLoanAmount'] if item['CreditLimitAmount'] == 0 else item['CreditLimitAmount']} for item in trades]
    
        cc_high_credit_loan_amount=[item['HighestCreditLoanAmount'] for item in trades if item['AccountType'] in ['10'] and item['open_date_missindicator'] == 1]
        if cc_high_credit_loan_amount and len(cc_high_credit_loan_amount) > 1:
            max_cc_high_credit_loan_amount_check = excl_none_operation(cc_high_credit_loan_amount, 'max')
            if max_cc_high_credit_loan_amount_check < 50000:
                max_cc_high_credit_loan_amount = 50000
            else:
                max_cc_high_credit_loan_amount = max_cc_high_credit_loan_amount_check
            if max_cc_high_credit_loan_amount > 50000 and max_cc_high_credit_loan_amount <= 100000:
                rollupvars['bureau_income_CC'] =  round(max_cc_high_credit_loan_amount / 2)
            elif max_cc_high_credit_loan_amount > 100000 and max_cc_high_credit_loan_amount <= 299999:
                rollupvars['bureau_income_CC'] =  round(max_cc_high_credit_loan_amount / 3)
            elif max_cc_high_credit_loan_amount > 299999:
                rollupvars['bureau_income_CC'] =  round(max_cc_high_credit_loan_amount / 4)
            else:
                rollupvars['bureau_income_CC'] =  0
        elif cc_high_credit_loan_amount and len(cc_high_credit_loan_amount) == 1:
            max_cc_high_credit_loan_amount_check = cc_high_credit_loan_amount[0]
            if max_cc_high_credit_loan_amount_check < 50000:
                max_cc_high_credit_loan_amount = 50000
            else:
                max_cc_high_credit_loan_amount = max_cc_high_credit_loan_amount_check
            if max_cc_high_credit_loan_amount > 50000 and max_cc_high_credit_loan_amount <= 100000:
                rollupvars['bureau_income_CC'] =  round(max_cc_high_credit_loan_amount / 2)
            elif max_cc_high_credit_loan_amount > 100000 and max_cc_high_credit_loan_amount <= 299999:
                rollupvars['bureau_income_CC'] =  round(max_cc_high_credit_loan_amount / 3)
            elif max_cc_high_credit_loan_amount > 299999:
                rollupvars['bureau_income_CC'] =  round(max_cc_high_credit_loan_amount / 4)
            else:
                rollupvars['bureau_income_CC'] =  0
        else:
            max_cc_high_credit_loan_amount_check = 0
            rollupvars['bureau_income_CC'] = 0
        rollupvars['max_cc_high_credit_loan_amount'] = max_cc_high_credit_loan_amount_check
        
        ###EMI CAL = P = sum of loan_amount for all personal accounts
        # EMI = (P*r)* ((1+r)^n/(1+r)^n-1)
        # r = 0.16(fixed)
        # n = 36(fixed)
        rate_of_intrest = 0.013333333
        loan_tenure = 36
        loan_amounts = [item['HighestCreditLoanAmount'] for item in trades if item['AccountType'] in ['05'] and item['open_date_missindicator'] == 1]
        sum_loan_amounts = round(sum(loan_amounts)) if len(loan_amounts) > 0 else 0
        #EMI = (sum_loan_amounts * rate_of_intrest) * (((1 + rate_of_intrest) ** loan_tenure) / ((1 + rate_of_intrest) ** loan_tenure - 1))
        EMI = (sum_loan_amounts*rate_of_intrest) * ((1+rate_of_intrest) ** loan_tenure) / ((1+rate_of_intrest) ** loan_tenure-1)
        rollupvars['bureau_income_PL'] = round(EMI * 3)
        rollupvars['bureau_income'] = max([rollupvars['bureau_income_PL'], rollupvars['bureau_income_CC']])

        #########
        rate_of_intrest_PL = 0.013333333
        loan_tenure_PL = 36
        loan_amounts_PL = [item['HighestCreditLoanAmount'] for item in trades if item['ScheduledPaymentAmount'] in invalid_div and item['AccountType'] in ['05'] and item['open_date_missindicator'] == 1]
        sum_loan_amounts_PL = round(sum(loan_amounts_PL)) if len(loan_amounts_PL) > 0 else 0
        EMI_PL = round((sum_loan_amounts_PL*rate_of_intrest_PL) * ((1+rate_of_intrest_PL) ** loan_tenure_PL) / ((1+rate_of_intrest_PL) ** loan_tenure_PL-1))
        rollupvars['pl_sanction_amount'] = sum_loan_amounts_PL

        rate_of_intrest_CL = 0.00916666
        loan_tenure_CL = 24
        loan_amounts_CL = [item['HighestCreditLoanAmount'] for item in trades if item['ScheduledPaymentAmount'] in invalid_div and item['AccountType'] in ['06'] and item['open_date_missindicator'] == 1]
        sum_loan_amounts_CL = round(sum(loan_amounts_CL)) if len(loan_amounts_CL) > 0 else 0
        EMI_CL = round((sum_loan_amounts_CL*rate_of_intrest_CL) * ((1+rate_of_intrest_CL) ** loan_tenure_CL) / ((1+rate_of_intrest_CL) ** loan_tenure_CL-1))
        
        rate_of_intrest_HL = 0.0075
        loan_tenure_HL = 240
        loan_amounts_HL = [item['HighestCreditLoanAmount'] for item in trades if item['ScheduledPaymentAmount'] in invalid_div and item['AccountType'] in ['02'] and item['open_date_missindicator'] == 1]
        sum_loan_amounts_HL = round(sum(loan_amounts_HL)) if len(loan_amounts_HL) > 0 else 0
        EMI_HL = round((sum_loan_amounts_HL*rate_of_intrest_HL) * ((1+rate_of_intrest_HL) ** loan_tenure_HL) / ((1+rate_of_intrest_HL) ** loan_tenure_HL-1))
        
        loan_amounts_GL = [max([(0.01 * item['HighestCreditLoanAmount']), item['CurrentBalance']]) for item in trades if item['ScheduledPaymentAmount'] not in invalid_div and item['AccountType'] in ['07'] and item['open_date_missindicator'] == 1]
        EMI_GL = round(sum(loan_amounts_GL)) if len(loan_amounts_GL) > 0 else 0
        
        #########
        EMI_PL_Bureau = sum([item['ScheduledPaymentAmount'] if item['ScheduledPaymentAmount'] not in invalid_div and item['AccountType'] in ['05'] else 0 for item in trades if item['open_date_missindicator'] == 1])
        rollupvars['EMI_PL_CAL'] = EMI_PL_Bureau + EMI_PL
        EMI_CL_Bureau = sum([item['ScheduledPaymentAmount'] if item['ScheduledPaymentAmount'] not in invalid_div and item['AccountType'] in ['06'] else 0 for item in trades if item['open_date_missindicator'] == 1])
        rollupvars['EMI_CL_CAL'] = EMI_CL_Bureau + EMI_CL
        EMI_HL_Bureau = sum([item['ScheduledPaymentAmount'] if item['ScheduledPaymentAmount'] not in invalid_div and item['AccountType'] in ['02'] else 0 for item in trades if item['open_date_missindicator'] == 1])
        rollupvars['EMI_HL_CAL'] = EMI_HL_Bureau + EMI_HL
        EMI_GL_Bureau = sum([item['ScheduledPaymentAmount'] if item['ScheduledPaymentAmount'] not in invalid_div and item['AccountType'] in ['07'] else 0 for item in trades if item['open_date_missindicator'] == 1])
        rollupvars['EMI_GL_CAL'] = EMI_GL_Bureau + EMI_GL
        sum_emi_actAccount = sum([item['ScheduledPaymentAmount'] for item in trades if item['open_date_missindicator'] == 1 and item['AccountType'] not in ['05', '06', '02', '07']])
        rollupvars['sum_emi_actAccount'] = sum([sum_emi_actAccount, rollupvars['EMI_PL_CAL'], rollupvars['EMI_CL_CAL'], rollupvars['EMI_HL_CAL'], rollupvars['EMI_GL_CAL']])
        #rollupvars['age_oldest_tl_mnths'] = round((req_date - min(d['StartDate'] for d in trades if d['open_date_missindicator'] == 1)).days / 30)
        rollupvars['age_oldest_tl_mnths'] = round((req_date - min(d['StartDate'] for d in trades)).days / 30)
        rollupvars['age_newest_tl_mnths'] = round((req_date - max(d['StartDate'] for d in trades)).days / 30)
        closed_opened_diff_mts = [round(((item['ClosedDate'] - item['StartDate']).days / 30),5) for item in trades if item['open_date_missindicator'] == 0 and item['close_date_missindicator'] == 1]
        #rollupvars['avg_age_tl_mnths'] = round(stat.mean(closed_opened_diff_mts) if closed_opened_diff_mts else None, 3)
        rollupvars['avg_age_tl_mnths'] = round(stat.mean(closed_opened_diff_mts) if closed_opened_diff_mts else 0, 3)

        
        secured_list = ['01','02','03','04','07','11','13','15','17','23','31','32','33','34','42','44','46','60','59','50','70']
        unsecured_list = ['05','06','08','09','10','12','14','16','18','19','20','24','35','36','37','38','39','40','41','43','45','47','51','52','53','54','55','56','57','58','00','61','69','71']
        unsecured_list_exclude = ['05','08','09','12','14','16','18','19','20','24','35','36','37','38','39','40','41','43','45','47','52','53','54','55','56','57','58','61','71']
        rollupvars['num_personal_loans'] = 0 if excl_none_operation([item['active_tl_flag'] for item in trades if item['AccountType'] in ['05', '69']], 'sum') in [None, -99999] else excl_none_operation([item['active_tl_flag'] for item in trades if item['AccountType'] in ['05', '69']], 'sum')
        rollupvars['num_unsecured_tls_exec_cc'] = sum([1 if item['AccountType'] in unsecured_list_exclude and item['close_date_missindicator'] == 0 else 0 for item in trades])
        
        rollupvars['num_secured_tls'] = sum([1 if item['AccountType'] in secured_list else 0 for item in trades])        
        
        rollupvars['num_unsecured_tls'] = sum([1 if item['AccountType'] in unsecured_list else 0 for item in trades])
        rollupvars['mue'] = excl_none_operation([item['CurrentBalance'] if item['AccountType'] in unsecured_list else 0 for item in trades], 'sum')
        l24m = req_date - relativedelta.relativedelta(months=24)
        rollupvars['active_tl_l24m'] = sum([1 if item['active_tl_flag'] == 1 and item['StartDate'] >= l24m else 0 for item in trades])
        rollupvars['num_tradelines'] = len(trades)
        rollupvars['total_unsec_tlbalance'] = excl_none_operation([item['CurrentBalance'] for item in trades if item['AccountType'] in unsecured_list], 'sum') if excl_none_operation([item['CurrentBalance'] for item in trades if item['AccountType'] in unsecured_list], 'sum') not in [ -99999, None] else 0
        rollupvars['num_open_cc'] = excl_none_operation([item['active_tl_flag'] for item in trades if item['AccountType'] in ['10']], 'sum')
        
        tot_cc_CurntBal = excl_none_operation([item['CurrentBalance'] for item in trades if item['AccountType'] in ['10'] and item['active_tl_flag'] == 1], 'sum')
        tot_cc_CurntBal = abs(tot_cc_CurntBal) if tot_cc_CurntBal not in invalid_div and tot_cc_CurntBal != -99999 else tot_cc_CurntBal
        tot_cc_creditlimit = excl_none_operation([item['HighestCreditLoanAmount'] for item in trades if item['AccountType'] in ['10'] and item['active_tl_flag'] == 1], 'sum')
        rollupvars['cc_high_credit_balance'] = round(tot_cc_creditlimit / tot_cc_CurntBal, 5) if tot_cc_CurntBal not in invalid_div and tot_cc_creditlimit not in invalid_div else 0
        
        
        try:
            trades = sorted(trades, key=lambda i: i['StartDate'])
            rollupvars['first_product_cc'] = 'Yes' if trades[0]['AccountType'] in ['10','31', '35', '36'] else 'No'
        except:
            rollupvars['first_product_cc'] = 'No'
        
        #################Payment###############################
        l12m = req_date - relativedelta.relativedelta(months=12)
        l24m = req_date - relativedelta.relativedelta(months=24)
        account = [{'reportedDate': None if 'Date_Reported' not in item else None if 'Date_Reported' in invalid else date_format(item['Date_Reported']),
                   'overdue': None if 'Amount_Past_Due' not in item else None if item['Amount_Past_Due'] in invalid else int(item['Amount_Past_Due'].replace(',','')),
                   'settlementAmount': None if 'Settlement_Amount' not in item else None if item['Settlement_Amount'] in invalid else int(item['Settlement_Amount'].replace(',','')),
                   'writtenOffAmtTotal': None if 'Written_Off_Amt_Total' not in item else None if item['Written_Off_Amt_Total'] in invalid else int(item['Written_Off_Amt_Total'].replace(',','')),
                   'PaymentHistory': None if 'Payment_History_Profile' not in item else None if item['Payment_History_Profile'] in invalid else str(item['Payment_History_Profile']),
                   'StartDate': date_format(item['Open_Date']) if 'Open_Date' in item and item['Open_Date'] not in invalid else None,
                   'ClosedDate': date_format(item['Date_Closed']) if 'Date_Closed' in item and item['Date_Closed'] not in invalid else None,
                   'AccountStatus': 0 if 'Date_Closed' not in item else 1 if item['Date_Closed'] not in ['', None] else 0,'DISBURSEDDATE': req_date,
                   'AccountType': item['Account_Type'] if 'Account_Type' in item else None} for item in accounts]
        
        rollupvars['amntoverdue_l24mths'] = excl_none_operation([d['overdue'] for d in account if d['reportedDate'] >= l24m], 'sum')
        
        l36m = req_date - relativedelta.relativedelta(months=36)
        settlement_l12m=excl_none_operation([d['settlementAmount'] if d['reportedDate'] >= l12m and d['settlementAmount'] not in ['', None] else 0 for d in account], 'sum')
        settlement_l36m=excl_none_operation([d['settlementAmount'] if d['reportedDate'] >= l36m and d['settlementAmount'] not in ['', None] else 0 for d in account], 'sum')
        writeoff_l12m=excl_none_operation([d['writtenOffAmtTotal'] if d['reportedDate'] >= l12m and d['writtenOffAmtTotal'] not in ['', None] else 0 for d in account], 'sum')
        writeoff_l36m=excl_none_operation([d['writtenOffAmtTotal'] if d['reportedDate'] >= l36m and d['writtenOffAmtTotal'] not in ['', None] else 0 for d in account], 'sum')

        rollupvars['settlement_writeoff_l12m'] = excl_none_operation([settlement_l12m, writeoff_l12m], 'sum')
        rollupvars['settlement_writeoff_l36m'] = excl_none_operation([settlement_l36m, writeoff_l36m], 'sum')

        settlement_l12m_exec_cc=excl_none_operation([d['settlementAmount'] if d['reportedDate'] >= l12m and d['settlementAmount'] not in ['', None] and d['AccountType'] not in ['10'] else 0 for d in account], 'sum')
        settlement_l36m_exec_cc=excl_none_operation([d['settlementAmount'] if d['reportedDate'] >= l36m and d['settlementAmount'] not in ['', None] and d['AccountType'] not in ['10'] else 0 for d in account], 'sum')
        writeoff_l12m_exec_cc=excl_none_operation([d['writtenOffAmtTotal'] if d['reportedDate'] >= l12m and d['writtenOffAmtTotal'] not in ['', None] and d['AccountType'] not in ['10'] else 0 for d in account], 'sum')
        writeoff_l36m_exec_cc=excl_none_operation([d['writtenOffAmtTotal'] if d['reportedDate'] >= l36m and d['writtenOffAmtTotal'] not in ['', None] and d['AccountType'] not in ['10'] else 0 for d in account], 'sum')

        rollupvars['settlement_writeoff_l12m_exec_cc'] = excl_none_operation([settlement_l12m_exec_cc, writeoff_l12m_exec_cc], 'sum')
        rollupvars['settlement_writeoff_l36m_exec_cc'] = excl_none_operation([settlement_l36m_exec_cc, writeoff_l36m_exec_cc], 'sum')
#         Added on 4th May'23
        account =[{**item, 'offset_cnt_for_latest_pymnt_months' : diff_month(req_date,item['reportedDate'])} for item in account]
        
        #account = [item for item in account if item['AccountStatus'] == 0]
        payment_grid = [get_paymenthistory(item['PaymentHistory']) for item in account]
        total_tls = len(account)
        payment_grid = payment_grid + [[-1]] * (total_tls - len(payment_grid))
        
#       Added on 4th May'23
        payment_grid =[{'payment_grid': [-1]*item['offset_cnt_for_latest_pymnt_months']+get_paymenthistory(item['PaymentHistory'])} for item in account]
        payment_grid =[{'payment_grid': item['payment_grid']+[-1]*(36-len(item['payment_grid']))} for item in payment_grid]
        payment_grid =[{'payment_grid': item['payment_grid'][:36]} for item in payment_grid]

# Commented the below line on 4th May'23        
#       payment_grid = [{'payment_grid' : item + [-1] * (36 - len(item))} for item in payment_grid]
        payment_grid_ind = max([1 if d['payment_grid'] is not None else 0 for d in payment_grid])
    
        account = [{**d, 'recent_level_of_deliq': next((j for i, j in enumerate(d['payment_grid']) if j > 0 and j is not None), None)} for d in payment_grid]
        account = [{**d, 'rvrs_split_paygrid': list(reversed(d['payment_grid']))} for d in account]
        account = [{**d, 'old_dpd_ind': (36 - next((i for i, j in enumerate(d['rvrs_split_paygrid']) if j > 0 and j is not None), None)) if next((i for i, j in enumerate(d['rvrs_split_paygrid']) if j > 0 and j is not None), None) != None else None,
                        'recnt_dpd_ind': next((i for i, j in enumerate(d['payment_grid']) if j > 0 and j is not None), None),
                        'filt_gt_0': list(filter(lambda x: (int(x) > 0), d['payment_grid']))} for d in account]
        
        account = [{**d, 'maxdpdval': max(d['filt_gt_0']) if len(d['filt_gt_0']) >= 1 else None,
                    'mindpdval': min(d['filt_gt_0']) if len(d['filt_gt_0']) >= 1 else None,
                    'time_since_recnt_deliq': (d['recnt_dpd_ind'] + 1)  if d['recnt_dpd_ind'] is not None else None,
                    'time_since_oldest_deliq': (d['old_dpd_ind']) if d['old_dpd_ind'] is not None else None,
                    'num_times_deliq': get_split_paygrid_res(d['payment_grid'], 1, None, None, 'count', False),
                    'num_times_30p': get_split_paygrid_res(d['payment_grid'], 1, None, None, 'count', True),
                    'num_times_60p': get_split_paygrid_res(d['payment_grid'], 2, None, None, 'count', True),
                    'num_times_90p': get_split_paygrid_res(d['payment_grid'], 3, None, None, 'count', True),
                    'num_times_120p': get_split_paygrid_res(d['payment_grid'], 4, None, None, 'count', True),
                    'num_deliq_3mts': get_split_paygrid_res(d['payment_grid'], 1, None, 3, 'count', False),
                    'num_deliq_6mts': get_split_paygrid_res(d['payment_grid'], 1, None, 6, 'count', False),
                    'num_deliq_12mts': get_split_paygrid_res(d['payment_grid'], 1, None, 12, 'count', False),
                    'num_deliq_24mts': get_split_paygrid_res(d['payment_grid'], 1, None, 24, 'count', False),
                    'num_deliq_36mts': get_split_paygrid_res(d['payment_grid'], 1, None, 36, 'count', False),
                    'num_deliq_48mts': get_split_paygrid_res(d['payment_grid'], 1, None, 48, 'count', False),
                    'num_deliq_6_12mts': get_split_paygrid_res(d['payment_grid'], 1, 6, 12, 'count', False),
                    'max_deliq_6mts': get_split_paygrid_res(d['payment_grid'], 1, None, 6, 'max', False),
                    'max_deliq_12mts': get_split_paygrid_res(d['payment_grid'], 1, None, 12, 'max', False),
                    'max_deliq_24mts': get_split_paygrid_res(d['payment_grid'], 1, None, 24, 'max', False),
                    'max_deliq_36mts': get_split_paygrid_res(d['payment_grid'], 1, None, 36, 'max', False),
                    'max_deliq_48mts': get_split_paygrid_res(d['payment_grid'], 1, None, 48, 'max', False),
                    'max_deliq_6_12mts': get_split_paygrid_res(d['payment_grid'], 1, 6, 12, 'max', False),
                    'num_tls_30dpd_l6mts': get_split_paygrid_res(d['payment_grid'], 1, None, 6, 'count', True),
                    'num_tls_60dpd_l12mts': get_split_paygrid_res(d['payment_grid'], 2, None, 12, 'count', True),
                    'num_tls_90dpd_l18mts': get_split_paygrid_res(d['payment_grid'], 3, None, 18, 'count', True),
                    'num_tls_90dpd_l36mnths': get_split_paygrid_res(d['payment_grid'], 3, None, 36, 'count', True),
                    'num_times_1p_dpd_l12m': get_split_paygrid_res(d['payment_grid'], 1, None, 12, 'count', True)} for d in account]
        
        new_acc = [{'time_since_first_deliquency': d['time_since_oldest_deliq'], 'time_since_recent_deliquency': d['time_since_recnt_deliq'],
                    'num_times_delinquent': d['num_times_deliq'], 'max_delinquency_level': d['maxdpdval'],
                    'num_deliq_6mts': d['num_deliq_6mts'],'num_deliq_3mts': d['num_deliq_3mts'], 'num_deliq_12mts': d['num_deliq_12mts'],
                    'num_deliq_24mts': d['num_deliq_24mts'], 'num_deliq_36mts': d['num_deliq_36mts'], 'num_deliq_48mts': d['num_deliq_48mts'],
                    'num_deliq_6_12mts': d['num_deliq_6_12mts'], 'max_deliq_6mts': d['max_deliq_6mts'],
                    'max_deliq_12mts': d['max_deliq_12mts'], 'max_deliq_24mts': d['max_deliq_24mts'], 'max_deliq_36mts': d['max_deliq_36mts'],
                    'max_deliq_48mts': d['max_deliq_48mts'], 'max_deliq_6_12mts': d['max_deliq_6_12mts'],
                    'num_times_30p_dpd': d['num_times_30p'], 'num_times_60p_dpd': d['num_times_60p'], 'num_times_90p_dpd': d['num_times_90p'],
                    'num_times_120p_dpd': d['num_times_120p'], 'recent_level_of_deliq': d['recent_level_of_deliq'],
                    'max_recent_level_of_deliq': d['recent_level_of_deliq'], 'num_tradelines': 1, 'num_tls_30dpd_l6mts':d['num_tls_30dpd_l6mts'],
                    'num_tls_60dpd_l12mts': d['num_tls_60dpd_l12mts'],'num_tls_90dpd_l18mts': d['num_tls_90dpd_l18mts'],
                    'num_tls_90dpd_l36mnths': d['num_tls_90dpd_l36mnths'],'num_times_1p_dpd_l12m': d['num_times_1p_dpd_l12m']} for d in account]
        
        #####################################################

        rollupvars['time_since_first_deliquency'] = excl_none_operation([d['time_since_first_deliquency'] for d in new_acc], 'max') if excl_none_operation([d['time_since_first_deliquency'] for d in new_acc], 'max') not in [-99999, None] else 0
        rollupvars['time_since_recent_deliquency'] = excl_none_operation([d['time_since_recent_deliquency'] for d in new_acc], 'min') if excl_none_operation([d['time_since_recent_deliquency'] for d in new_acc], 'min') not in [-99999, None] else 99999
        rollupvars['num_times_delinquent'] = excl_none_operation([d['num_times_delinquent'] for d in new_acc], 'sum')
        rollupvars['max_delinquency_level'] = None if payment_grid_ind == 0 else excl_none_operation([d['max_delinquency_level'] for d in new_acc], 'max') if excl_none_operation([d['max_delinquency_level'] for d in new_acc], 'max') not in [-99999, None] else 0
        rollupvars['max_recent_level_of_deliq'] = None if payment_grid_ind == 0 else 0 if payment_grid_ind > 0 and excl_none_operation([d['max_recent_level_of_deliq'] for d in new_acc], 'max') == -99999 else excl_none_operation([d['max_recent_level_of_deliq'] for d in new_acc], 'max')
        rollupvars['num_deliq_3mts'] = None if payment_grid_ind == 0 else excl_none_operation([d['num_deliq_3mts'] for d in new_acc], 'sum') if excl_none_operation([d['num_deliq_6mts'] for d in new_acc], 'sum') not in [-99999, None] else 0
        rollupvars['num_deliq_6mts'] = None if payment_grid_ind == 0 else excl_none_operation([d['num_deliq_6mts'] for d in new_acc], 'sum') if excl_none_operation([d['num_deliq_6mts'] for d in new_acc], 'sum') not in [-99999, None] else 0
        rollupvars['num_deliq_12mts'] = None if payment_grid_ind == 0 else excl_none_operation([d['num_deliq_12mts'] for d in new_acc], 'sum') if excl_none_operation([d['num_deliq_12mts'] for d in new_acc], 'sum') not in [-99999, None] else 0
        rollupvars['num_deliq_24mts'] = None if payment_grid_ind == 0 else excl_none_operation([d['num_deliq_24mts'] for d in new_acc], 'sum') if excl_none_operation([d['num_deliq_24mts'] for d in new_acc], 'sum') not in [-99999, None] else 0
        rollupvars['num_deliq_36mts'] = None if payment_grid_ind == 0 else excl_none_operation([d['num_deliq_36mts'] for d in new_acc], 'sum') if excl_none_operation([d['num_deliq_36mts'] for d in new_acc], 'sum') not in [-99999, None] else 0
        rollupvars['num_deliq_48mts'] = None if payment_grid_ind == 0 else excl_none_operation([d['num_deliq_48mts'] for d in new_acc], 'sum') if excl_none_operation([d['num_deliq_48mts'] for d in new_acc], 'sum') not in [-99999, None] else 0
        rollupvars['num_deliq_6_12mts'] = None if payment_grid_ind == 0 else excl_none_operation([d['num_deliq_6_12mts'] for d in new_acc], 'sum') if excl_none_operation([d['num_deliq_6_12mts'] for d in new_acc], 'sum') not in [-99999, None] else 0
        rollupvars['max_deliq_6mts'] = None if payment_grid_ind == 0 else excl_none_operation([d['max_deliq_6mts'] for d in new_acc], 'max') if excl_none_operation([d['max_deliq_6mts'] for d in new_acc], 'max') not in [-99999, None] else 0
        rollupvars['max_deliq_12mts'] = None if payment_grid_ind == 0 else excl_none_operation([d['max_deliq_12mts'] for d in new_acc], 'max') if excl_none_operation([d['max_deliq_12mts'] for d in new_acc], 'max') not in [-99999, None] else 0
        rollupvars['max_deliq_24mts'] = None if payment_grid_ind == 0 else excl_none_operation([d['max_deliq_24mts'] for d in new_acc], 'max') if excl_none_operation([d['max_deliq_24mts'] for d in new_acc], 'max') not in [-99999, None] else 0
        rollupvars['max_deliq_36mts'] = None if payment_grid_ind == 0 else excl_none_operation([d['max_deliq_36mts'] for d in new_acc], 'max') if excl_none_operation([d['max_deliq_36mts'] for d in new_acc], 'max') not in [-99999, None] else 0
        rollupvars['max_deliq_48mts'] = None if payment_grid_ind == 0 else excl_none_operation([d['max_deliq_48mts'] for d in new_acc], 'max') if excl_none_operation([d['max_deliq_48mts'] for d in new_acc], 'max') not in [-99999, None] else 0
        rollupvars['max_deliq_6_12mts'] = None if payment_grid_ind == 0 else excl_none_operation([d['max_deliq_6_12mts'] for d in new_acc], 'max') if excl_none_operation([d['max_deliq_6_12mts'] for d in new_acc], 'max') not in [-99999, None] else 0
        rollupvars['num_times_30p_dpd'] = None if payment_grid_ind == 0 else excl_none_operation([d['num_times_30p_dpd'] for d in new_acc], 'sum') if excl_none_operation([d['num_times_30p_dpd'] for d in new_acc], 'sum') not in [-99999, None] else 0
        rollupvars['num_times_60p_dpd'] = None if payment_grid_ind == 0 else  excl_none_operation([d['num_times_60p_dpd'] for d in new_acc], 'sum') if excl_none_operation([d['num_times_60p_dpd'] for d in new_acc], 'sum') not in [-99999, None] else 0
        rollupvars['num_times_90p_dpd'] = None if payment_grid_ind == 0 else excl_none_operation([d['num_times_90p_dpd'] for d in new_acc], 'sum') if excl_none_operation([d['num_times_90p_dpd'] for d in new_acc], 'sum') not in [-99999, None] else 0
        rollupvars['num_times_120p_dpd'] = None if payment_grid_ind == 0 else excl_none_operation([d['num_times_120p_dpd'] for d in new_acc], 'sum') if excl_none_operation([d['num_times_120p_dpd'] for d in new_acc], 'sum') not in [-99999, None] else 0
        rollupvars['num_tls_30dpd_l6mts'] = None if payment_grid_ind == 0 else excl_none_operation([d['num_tls_30dpd_l6mts'] for d in new_acc], 'sum') if excl_none_operation([d['num_tls_30dpd_l6mts'] for d in new_acc], 'sum') not in [-99999, None] else 0
        rollupvars['num_tls_60dpd_l12mts'] = None if payment_grid_ind == 0 else excl_none_operation([d['num_tls_60dpd_l12mts'] for d in new_acc], 'sum') if excl_none_operation([d['num_tls_60dpd_l12mts'] for d in new_acc], 'sum') not in [-99999, None] else 0
        rollupvars['num_tls_90dpd_l18mts'] = None if payment_grid_ind == 0 else excl_none_operation([d['num_tls_90dpd_l18mts'] for d in new_acc], 'sum') if excl_none_operation([d['num_tls_90dpd_l18mts'] for d in new_acc], 'sum') not in [-99999, None] else 0
        rollupvars['num_tls_90dpd_l36mts'] = None if payment_grid_ind == 0 else excl_none_operation([d['num_tls_90dpd_l36mnths'] for d in new_acc], 'sum') if excl_none_operation([d['num_tls_90dpd_l36mnths'] for d in new_acc], 'sum') not in [-99999, None] else 0
        rollupvars['num_times_1p_dpd_l12m'] = None if payment_grid_ind == 0 else excl_none_operation([d['num_times_1p_dpd_l12m'] for d in new_acc], 'sum') if excl_none_operation([d['num_times_1p_dpd_l12m'] for d in new_acc], 'sum') not in [-99999, None] else 0
        rollupvars['num_delinquent_tl'] = None if payment_grid_ind == 0 else excl_none_operation([1 if d['num_times_delinquent'] != None and d['num_times_delinquent'] > 0 else 0 for d in new_acc], 'sum')
        rollupvars['time_since_first_deliquency_days'] = (rollupvars['time_since_first_deliquency'] * 30) if rollupvars['time_since_first_deliquency'] not in [-99999, None, ''] else 0
        rollupvars['time_since_recent_deliquency_days'] = (rollupvars['time_since_recent_deliquency'] * 30) if rollupvars['time_since_recent_deliquency'] not in [-99999, None, '', 99999] else 99999
        rollupvars['pct_Satis_tl_to_total_tl'] = round(float(rollupvars['num_tradelines'] - rollupvars['num_delinquent_tl']) / float(rollupvars['num_tradelines'])*100, 3) if rollupvars['num_tradelines'] not in invalid_div else None
        
        
        nones = [i for i in new_acc if i['time_since_recent_deliquency'] is None]
        nonnoes = sorted([i for i in new_acc if i['time_since_recent_deliquency'] is not None],
                         key=lambda i: i['time_since_recent_deliquency'])
        grouped_data_nonnoes = []
        for key, group in itertools.groupby(nonnoes, key=lambda x:x['time_since_recent_deliquency']):
            grouped_data_nonnoes.append(list(group))
        new_acc_new = grouped_data_nonnoes + nones
        try:
            rollupvars['recent_level_of_deliq'] = excl_none_operation([d['recent_level_of_deliq'] for d in new_acc_new[0]], 'max') if excl_none_operation([d['recent_level_of_deliq'] for d in new_acc_new[0]], 'max') not in [-99999, None] else 0
        except TypeError:
            rollupvars['recent_level_of_deliq'] = new_acc_new[0]['recent_level_of_deliq'] if len(new_acc_new) > 0 and new_acc_new[0]['recent_level_of_deliq'] else 0
    
    else:
        rollupvars = {"EMI_CL_CAL":-99999,"EMI_GL_CAL":-99999,"EMI_HL_CAL":-99999,"EMI_PL_CAL":-99999,"active_tl_l24m":-99999,"age_newest_tl_mnths":-99999,"age_oldest_tl_mnths":-99999,"amntoverdue_l24mths":-99999,"avg_age_tl_mnths":-99999,"bureau_income":-99999,"bureau_income_CC":-99999,"bureau_income_PL":-99999,"cc_high_credit_balance":-99999,"customer_name":"-99999","enq_L12m":-99999,"enq_L1m":-99999,"enq_L3m":-99999,"enq_L6m":-99999,
                      "experian_score":-99999,"first_product_cc":"-99999","max_cc_high_credit_loan_amount":-99999,"max_delinquency_level":-99999,"max_deliq_12mts":-99999,"max_deliq_24mts":-99999,"max_deliq_36mts":-99999,"max_deliq_48mts":-99999,"max_deliq_6_12mts":-99999,"max_deliq_6mts":-99999,"max_recent_level_of_deliq":-99999,"mobile_number":"-99999","mue":-99999,"num_delinquent_tl":-99999,"num_deliq_12mts":-99999,"num_deliq_24mts":-99999,"num_deliq_36mts":-99999,"num_deliq_3mts":-99999,"num_deliq_48mts":-99999,"num_deliq_6_12mts":-99999,
                      "num_deliq_6mts":-99999,"num_open_cc":-99999,"num_personal_loans":-99999,"num_secured_tls":-99999,"num_times_120p_dpd":-99999,"num_times_1p_dpd_l12m":-99999,"num_times_30p_dpd":-99999,"num_times_60p_dpd":-99999,"num_times_90p_dpd":-99999,"num_times_delinquent":-99999,"num_tls_30dpd_l6mts":-99999,"num_tls_60dpd_l12mts":-99999,"num_tls_90dpd_l18mts":-99999,"num_tls_90dpd_l36mts":-99999,"num_tradelines":-99999,"num_unsecured_tls":-99999,"num_unsecured_tls_exec_cc":-99999,"pct_Satis_tl_to_total_tl":-99999,
                      "pl_sanction_amount":-99999,"recent_level_of_deliq":-99999,"resp_time":"-99999","settlement_writeoff_l12m":-99999,"settlement_writeoff_l12m_exec_cc":-99999,"settlement_writeoff_l36m":-99999,"settlement_writeoff_l36m_exec_cc":-99999,"sum_emi_actAccount":-99999,"time_since_first_deliquency":-99999,"time_since_first_deliquency_days":-99999,"time_since_recent_deliquency": 99999,"time_since_recent_deliquency_days": 99999,"total_enqs":-99999,"total_unsec_tlbalance":-99999}
    
    try:
        rollupvars['experian_score'] = int(data['SCORE']['BureauScore'])
    except:
        rollupvars['experian_score'] = None
    
    rollupvars = replace_nones(rollupvars)
    
    return rollupvars