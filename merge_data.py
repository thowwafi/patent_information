import csv
import glob
import os
import pdb
import pandas as pd


home = os.getcwd()
OUTPUT_PATH = os.path.join(home, 'new_output')
MERGED_PATH = 'patents_2010_2021'

if __name__ == '__main__':
    appended_data = []
    files = glob.glob(f"{OUTPUT_PATH}/*.xlsx")
    files = sorted(files)
    for infile in files[30:]:
        print(infile)
        data = pd.read_excel(infile, dtype=str)
        infile_csv = infile.replace('.xlsx', '.csv').replace('new_output', 'output_csv')
        data.to_csv(infile_csv, index=False, sep=";", encoding="utf-8-sig")
        appended_data.append(data)

    all_data = pd.concat(appended_data)
    print(all_data.columns)
    all_data.to_excel(f'{MERGED_PATH}.xlsx', index=False)
    print("Excel Done!")
    all_data.to_csv(f'{MERGED_PATH}.csv', index=False, sep=";", encoding="utf-8-sig")
    print('Done!')
