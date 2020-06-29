from bs4 import BeautifulSoup
import common

def ExtractDataFromRow(row):
	cols = row.find_all('td')
	td_cols = [ele.text.strip() for ele in cols]
	td_cols = [td_cols[2], td_cols[3]] if len(td_cols) > 3 else []
	cols  = td_cols
	return cols

def main():
	# https://smart-lab.ru/q/GAZP/f/y/MSFO/
	url = "https://smart-lab.ru/q/shares/"

	html_content = common.get_raw_html(url)
	soup = BeautifulSoup(html_content, "html.parser")
	fin_table = soup.findAll("table", {"class": "simple-little-table trades-table"} )

	rows = fin_table[0].find_all('tr')
	cols = [ExtractDataFromRow(row) for row in rows]
	cols = [col for col in cols if len(col) != 0]

	for col in cols:
		print(col)

	common.save_to_csv(cols, "all_asserts.csv")

if __name__ == "__main__":
	main()