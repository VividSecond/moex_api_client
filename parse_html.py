from bs4 import BeautifulSoup
import requests
import common

def ExtractDataFromRow(row):
	cols = row.find_all('th')
	th_cols = [ele.text.strip() for ele in cols]
	indicator_name = th_cols[0] if th_cols else ""
	cols = row.find_all('td')
	td_cols = [ele.text.strip() for ele in cols]
	td_cols = td_cols[1:-2]
	cols  = [indicator_name] + td_cols
	return cols

def create_url(assert_name):
	return "https://smart-lab.ru/q/" + assert_name + "/f/y/MSFO/"

def process_row(rows, row_name):
	dividend_row = [row for row in rows if row[0] == row_name]
	if not dividend_row:
		return []

	dividend_row = dividend_row[0]
	dividend_row = [v if v else '0' for v in dividend_row]
	dividend_quotes = dividend_row[1:]
	return dividend_quotes

def calc_average_from_raw_data(row_data):
	row_data = row_data 
	if not row_data:
		return 0

	row_data = [r.replace('%', '') for r in row_data]
	row_data = [float(q) for q in row_data]
	average = sum(row_data) / len(row_data)
	return average

def main():
	asserts_names = common.read_csv("all_asserts.csv")
	asserts_names = [row[1] for row in asserts_names]
	urls = [create_url(r) for r in asserts_names]

	raw_pages = []
	for url, asserts_name in zip(urls, asserts_names):
		html_content = None
		try:
			html_content = common.get_raw_html(url)
		except:
			pass
		raw_pages.append((asserts_name, html_content))

	dividends = []
	for p in raw_pages:
		fin_table = process_table(p[1])
		values = [p[0], 0, 0]
		if fin_table:
			rows = fin_table[0].find_all('tr')
			rows = [ExtractDataFromRow(row) for row in rows]

			row_values = process_row(rows, "Дивиденд, руб/акцию")
			if row_values:
				div_average = calc_average_from_raw_data(row_values)
				values[1] = div_average

			row_values = process_row(rows, "Див доход, ао, %")
			if row_values:
				div_average = calc_average_from_raw_data(row_values)
				values[2] = div_average

		dividends.append(values)

	common.save_to_csv(dividends, "dividents.csv")

if __name__ == "__main__":
	main()