import numpy as np
from datetime import datetime
from scipy.optimize import fsolve
from scipy.optimize import fmin_cg
import common
import json

#blocks names
SECURITIE, MARKETDATA, COUPONS, AMORTIZATIONS = range(4)

#group names
COLUMNS, DATA = range(2)

#fields names
ACCRUEDINT, COUPON_PERIOD, CLOSE_PRICE, \
    LOT_VALUE, MAT_DATE, BUYBACK_DATE, PREV_ADMITTED_QUOTE, \
    VALUE_RUB, COUPON_DATE, LISTLEVEL, FACEUNIT, AMORT_DATE,\
    STATUS, SECID, AMORT_VALUE_RUB, ALL, *_ = range(100)

def CommonConverter(field_val):
    return field_val

def DataConverter(field_val):
    converted_val = None if '0000-00-00' in field_val else datetime.strptime(field_val, '%Y-%m-%d')
    return converted_val

class Field():
    name = ''
    block = ''
    converter = None
    def __init__(self, block, name, converter):
        self.block = block
        self.name = name
        self.converter = converter

    def fill(self, data):
        if type(data[self.block]) == list:
            return [self.converter(x[self.name]) for x in data[self.block]]
        return self.converter(data[self.block][self.name])

class ResponseParser():
    fields = {}
    groups = [None] * 2
    blocks = [None] * 4
    def __init__(self, fields):
        self.groups[COLUMNS] = "columns"
        self.groups[DATA] = "data"

        self.blocks[SECURITIE] = 'securities'
        self.blocks[MARKETDATA] = 'marketdata'
        self.blocks[COUPONS] = 'coupons'
        self.blocks[AMORTIZATIONS] = 'amortizations'

        for field in fields:
            self.fields[field[0]] = Field(field[1], self.blocks[field[2]], field[3] if field[3] else CommonConverter)    
    
    def merge_column_names_and_values(self, block):
        data = [dict(zip(block[self.groups[COLUMNS]], x)) for x in block[self.groups[DATA]]]
        return data

    def extract_data(self, data):
        parsed_data = {i : v.fill(data) for i, v in self.fields.items()}     
        return parsed_data

def get_response(respone_parser, request_str, response_cacher):
    json_response = json.loads(common.get_raw_html(request_str))
    response_cacher(json_response)
    dict_response = {k : respone_parser.merge_column_names_and_values(v) \
                                for k, v in json_response.items()}
    
    # erase unused blocks in response
    dict_response = {k: v for k, v in dict_response.items() if k in respone_parser.blocks}    
    return respone_parser.get_data(dict_response)

def create_output(bond_name, data, effective_return):
    print_list = [bond_name, data[MAT_DATE], data[PREV_ADMITTED_QUOTE], data[LISTLEVEL], len(data[-1]), effective_return, data[FACEUNIT]]
    return print_list

def check_data_correctness(data):
    is_price_empty = data[CLOSE_PRICE] == None and data[PREV_ADMITTED_QUOTE] == None
    is_data_empty = data[MAT_DATE] == None and data[BUYBACK_DATE] == None
    is_coupons_empty = False if data[-1] else True
    return is_price_empty or is_data_empty or is_coupons_empty

def preprocess_data(data):
    data[PREV_ADMITTED_QUOTE] = data[PREV_ADMITTED_QUOTE] if data[PREV_ADMITTED_QUOTE] else data[CLOSE_PRICE]
    data[MAT_DATE] = data[MAT_DATE] if data[MAT_DATE] else data[BUYBACK_DATE]
    data[-1] = [(x[0] if x[0] else 0, x[1])  for x in data[-1] if x[1] > datetime.today()]
    data[-2] = [(x[0] if x[0] else 0, x[1])  for x in data[-2] if x[1] > datetime.today()]
    return data

def calculate_effective_return(data):
    accruedint = data[ACCRUEDINT]
    lot_value = data[LOT_VALUE]
    mat_date = data[MAT_DATE]

    price = data[PREV_ADMITTED_QUOTE] if data[PREV_ADMITTED_QUOTE] else data[CLOSE_PRICE]
    price = price * lot_value / 100

    today = datetime.today()
    date_diff = (mat_date - today).days
    coupons_data = data[-1]
    coupons_data = [(x[0], (x[1] - today).days) for x in coupons_data]

    amort_data = data[-2]
    amort_data = [(x[0], (x[1] - today).days) for x in amort_data]

    def func(r):
        val = - accruedint - price
        for coupon in coupons_data:
            exponent = coupon[1] / 365
            coupon_add = coupon[0] / (1 + r) ** exponent
            val = val + coupon_add
        for amort in amort_data:
            exponent = amort[1] / 365
            amort_add = amort[0] / (1 + r) ** exponent
            val = val + amort_add
        return abs(val)

    sol = fsolve(func, 0)
    return sol[0]