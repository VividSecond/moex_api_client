import common
import parse_response as pr
import json
import os
import argparse
import numpy

def get_data(sec_file_name, dir_full_path):
    full_path_to_json = os.path.join(dir_full_path, sec_file_name)
    with open(full_path_to_json) as json_file:
        return json.load(json_file)

def request_json_data(request_str):
    return json.loads(common.get_raw_html(request_str))

class DataDispatcher:
    absolute_folder_path = ""
    request_str = ""
    is_need_download = False

    def __init__(self, dir_name, request_str, is_need_download):
        working_dir = os.path.dirname(__file__)
        self.absolute_folder_path = os.path.join(working_dir, dir_name)
        self.request_str = request_str
        self.is_need_download = is_need_download

    def download_data(self, ids):
        if not self.is_need_download:
            return
        downloaded_data = {x : request_json_data(request_str.format(x)) for x in ids}
        for k in downloaded_data:
            sec_data_relative_path = os.path.join(self.absolute_folder_path, k + ".json")
            common.save_json(downloaded_data[k], sec_data_relative_path)

    def load_data(self, ids):
        return { x : get_data(x + ".json", self.absolute_folder_path) for x in ids }

def get_bonds_ids(data_parser, request_str):
    # list of all bonds
    bonds = request_json_data(request_str)
    bonds = {k : data_parser.merge_column_names_and_values(v) \
                for k, v in bonds.items()}

    secids = data_parser.get_data(bonds, [pr.SECID])
    return secids

def parse_input_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', action='store_true')
    return parser.parse_args()

def main():
    args = parse_input_args()
    data_parser = pr.ResponseParser()
    request_all_bonds_str = 'http://iss.moex.com/iss/engines/stock/markets/bonds/boards/TQCB/securities.json?iss.only=securities'
    secids = get_bonds_ids(data_parser, request_all_bonds_str)
    request_sec_str = 'http://iss.moex.com/iss/engines/stock/markets/bonds/boards/TQCB/securities/{0}.json'
    sec_dispetcher =  DataDispatcher('bonds', request_sec_str, args.d)
    sec_dispetcher.download_data(secids)
    request_coupon_str = 'https://iss.moex.com/iss/statistics/engines/stock/markets/bonds/bondization/{0}/securities.json?iss.only=coupons,amortizations'
    coupon_dispetcher =  DataDispatcher('coupons', request_coupon_str, args.d)
    coupon_dispetcher.download_data(secids)

    secs = sec_dispetcher.load_data(secids)
    a_and_c = coupon_dispetcher.load_data(secids)
    general_data = {x : {**secs[x], **a_and_c[x]} for x in secs}
    
    used_blocks = []
    for sec_id, val in general_data.items():
        general_data[sec_id] = {k : v for k, v in val.items() if k in used_blocks}

    for sec_id in general_data:
        general_data[sec_id] = {k : data_parser.merge_column_names_and_values(v) \
            for k, v in general_data[sec_id].items()}

    for sec_id in general_data:
        general_data[sec_id] = {k : (v[0] if len(v) == 1 and k != coupons_blk_name else v) \
            for k, v in general_data[sec_id].items()}


    parsed_data = {x : data_parser.get_data(general_data[x]) for x in general_data}
    parsed_data = {x : p.preprocess_data(parsed_data[x]) for x in parsed_data}
    parsed_data = {x : parsed_data[x] for x in parsed_data if not bond_stat.is_rejected(parsed_data[x])}
    
    effective_returns = {}
    for x in parsed_data:
        effective_returns[x] = bond_stat.calculate_effective_return(parsed_data[x])
    csv_format_data = [[x, *parsed_data[x], effective_returns[x]] for x in parsed_data]
    csv_release_data = [bond_stat.print_data(x, parsed_data[x], effective_returns[x]) for x in parsed_data]

    common.save_to_csv(csv_release_data, 'readble_data.csv')
    common.save_to_csv(csv_format_data, 'effective_returns.csv')

if __name__ == '__main__':
	main()