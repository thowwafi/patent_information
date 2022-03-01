import csv
import glob
import os
import pandas as pd


home = os.getcwd()
OUTPUT_PATH = os.path.join(home, 'new_output')

if __name__ == '__main__':
    appended_data = []
    files = glob.glob(f"{OUTPUT_PATH}/*.xlsx")
    files = sorted(files)
    for infile in files[20:]:
        print(infile)
        data = pd.read_excel(infile, dtype=str)
        appended_data.append(data)

    appended_data = pd.concat(appended_data)
    print(appended_data.columns)
    # appended_data.to_excel('patents_2000_2021_new.xlsx', index=False)
    appended_data.to_csv('patents_2000_2021_new.csv', index=False, sep=";", encoding="utf-8-sig", float_format="", quoting=csv.QUOTE_NONNUMERIC)
