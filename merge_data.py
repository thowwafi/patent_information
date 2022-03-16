import csv
import glob
import os
import pdb
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
    # appended_data['country_code'] = appended_data.applicant_address.str.split(' ').str[-1].str.strip()
    # column_to_move = appended_data.pop("country_code")  
    # appended_data.insert(2, "country_code", column_to_move)
    print(appended_data.columns)
    appended_data.to_excel('patents_1980_1999_new.xlsx', index=False)
    # appended_data.to_csv('patents_2000_2021_new.csv', index=False, sep=";", encoding="utf-8-sig")
    print('Done!')
