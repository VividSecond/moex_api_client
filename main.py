import common
import parse_response as pr
import json
import os
import argparse
import numpy

def parse_input_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', action='store_true')
    return parser.parse_args()

class Cacher():
    folder_name = ""
    response_name = ""
    def __init__(self, folder_name, response_name):
        self.folder_name = folder_name
        self.response_name = response_name

    def __call__(self, response):
        working_dir = os.path.dirname(__file__)
        absolute_folder_path = os.path.join(working_dir, self.folder_name)
        absolute_file_path = os.path.join(absolute_folder_path, self.response_name)
        common.save_json(response, absolute_file_path)

def main():
    args = parse_input_args()

    fields = [(pr.SECID, pr.SECURITIE,'SECID')]
    secids_data_parser = pr.ResponseParser(fields)
    request_all_bonds_str = 'http://iss.moex.com/iss/engines/stock/markets/bonds/boards/TQCB/securities.json?iss.only=securities'
    dummy_chacher = lambda a: None
    response_secids = pr.get_response(secids_data_parser, request_all_bonds_str, dummy_chacher, [pr.SECID])
    secids = response_secids[pr.SECID]

    bonds_fields = [(pr.ACCRUEDINT, pr.SECURITIE,'ACCRUEDINT'),
                    (pr.COUPON_PERIOD, pr.SECURITIE,'COUPONPERIOD'),
                    (pr.CLOSE_PRICE, pr.MARKETDATA,'CLOSEPRICE'),
                    (pr.LOT_VALUE, pr.SECURITIE,'LOTVALUE'),
                    (pr.MAT_DATE, pr.SECURITIE,'MATDATE', pr.DataConverter),
                    (pr.BUYBACK_DATE, pr.SECURITIE,'BUYBACKDATE', pr.DataConverter),
                    (pr.PREV_ADMITTED_QUOTE, pr.SECURITIE,'PREVADMITTEDQUOTE'),
                    (pr.LISTLEVEL, pr.SECURITIE,'LISTLEVEL'),
                    (pr.FACEUNIT, pr.SECURITIE,'FACEUNIT'),
                    (pr.STATUS, pr.SECURITIE,'STATUS')]
    bonds_data_parser = pr.ResponseParser(bonds_fields)
    request_sec_str = 'http://iss.moex.com/iss/engines/stock/markets/bonds/boards/TQCB/securities/{0}.json'
    fixed_bond_data = {x : pr.get_response(bonds_data_parser, \
                request_sec_str.format(x), Cacher("bonds", x + ".json")) for x in secids}

    amort_a_coupons_fields = [(pr.VALUE_RUB, pr.COUPONS,'value_rub'),
                                (pr.AMORT_VALUE_RUB, pr.AMORTIZATIONS,'value_rub'),
                                (pr.COUPON_DATE, pr.COUPONS,'coupondate', pr.DataConverter),
                                (pr.AMORT_DATE, pr.AMORTIZATIONS,'amortdate', pr.DataConverter)]
    amort_a_coupons_parser = pr.ResponseParser(amort_a_coupons_fields)
    request_coupon_str = 'https://iss.moex.com/iss/statistics/engines/stock/markets/bonds/bondization/{0}/securities.json?iss.only=coupons,amortizations'
    a_and_c = {x : pr.get_response(amort_a_coupons_parser, \
            request_coupon_str.format(x), Cacher("coupons", x + ".json")) for x in secids}

    bonds = {x : {**fixed_bond_data[x], **a_and_c[x]} for x in fixed_bond_data}
    bonds = {x : pr.preprocess_data(bonds[x]) for x in bonds}
    
    effective_returns = {}
    for x in bonds:
        effective_returns[x] = pr.calculate_effective_return(bonds[x])
    csv_format_data = [[x, *bonds[x], effective_returns[x]] for x in bonds]
    csv_release_data = [pr.create_output(x, bonds[x], effective_returns[x]) for x in bonds]

    common.save_to_csv(csv_release_data, 'readble_data.csv')
    common.save_to_csv(csv_format_data, 'effective_returns.csv')

if __name__ == '__main__':
	main()