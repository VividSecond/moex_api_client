import numpy as np
from datetime import datetime
from scipy.optimize import fsolve
from scipy.optimize import fmin_cg
import common

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
    return field_val

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

class FieldFactory():
    block_names = [] 
    def __init__(self, blocks):
        self.block_names = blocks

    def create(self, block_id, field_name, converter = CommonConverter):
        return Field(self.block_names[block_id], field_name, converter)

class ResponseParser():
    fields = [None] * ALL
    groups = [None] * 2
    blocks = [None] * 4
    def __init__(self):
        self.groups[COLUMNS] = "columns"
        self.groups[DATA] = "data"

        self.blocks[SECURITIE] = 'securities'
        self.blocks[MARKETDATA] = 'marketdata'
        self.blocks[COUPONS] = 'coupons'
        self.blocks[AMORTIZATIONS] = 'amortizations'

        factory = FieldFactory(self.blocks)
        self.fields[SECID] = factory.create(SECURITIE,'SECID')
        self.fields[ACCRUEDINT] = factory.create(SECURITIE,'ACCRUEDINT')
        self.fields[COUPON_PERIOD] = factory.create(SECURITIE,'COUPONPERIOD')
        self.fields[CLOSE_PRICE] = factory.create(MARKETDATA,'CLOSEPRICE')
        self.fields[LOT_VALUE] = factory.create(SECURITIE,'LOTVALUE')
        self.fields[MAT_DATE] = factory.create(SECURITIE,'MATDATE', DataConverter)
        self.fields[BUYBACK_DATE] = factory.create(SECURITIE,'BUYBACKDATE', DataConverter)
        self.fields[VALUE_RUB] = factory.create(COUPONS,'value_rub')
        self.fields[AMORT_VALUE_RUB] = factory.create(AMORTIZATIONS,'value_rub')
        self.fields[COUPON_DATE] = factory.create(COUPONS,'coupondate', DataConverter)
        self.fields[PREV_ADMITTED_QUOTE] = factory.create(SECURITIE,'PREVADMITTEDQUOTE')
        self.fields[LISTLEVEL] = factory.create(SECURITIE,'LISTLEVEL')
        self.fields[FACEUNIT] = factory.create(SECURITIE,'FACEUNIT')
        self.fields[AMORT_DATE] = factory.create(AMORTIZATIONS,'amortdate', DataConverter)
        self.fields[STATUS] = factory.create(SECURITIE,'STATUS')
    
    def merge_column_names_and_values(self, block):
        data = [dict(zip(block[self.groups[COLUMNS]], x)) for x in block[self.groups[DATA]]]
        return data

    def get_data(self, data, ids):
        count = ALL if not ids else len(ids)
        parsed_data = [None] * ALL
        for i in range(count):
            parsed_data[ids[i]] = self.fields[ids[i]].fill(data)        
        return parsed_data

    def block_name(self, block_id):
        return self.blocks[block_id]

    def field_name(self, field_id):
        return self.fields[field_id].name

def get_prepared_response(respone_parser, request_str, extracted_columns = None):
    raw_response = respone_parser.request_json_data(request_str)
    dict_response = {k : respone_parser.merge_column_names_and_values(v) \
                                for k, v in raw_response.items()}
    
    # erase unused response blocks
    dict_response = {k: v for k, v in dict_response.items() if k in respone_parser.blocks}
    prepared_response = respone_parser.get_data(dict_response, extracted_columns)

def print_data(bond_name, data, effective_return):
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