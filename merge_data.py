import glob
import os
import pandas as pd


home = os.getcwd()
OUTPUT_PATH = os.path.join(home, 'output')

if __name__ == '__main__':
    appended_data = []
    files = glob.glob(f"{OUTPUT_PATH}/*.xlsx")
    files = sorted(files)
    for infile in files:
        print(infile)
        data = pd.read_excel(infile)
        appended_data.append(data)

    appended_data = pd.concat(appended_data)
    appended_data.to_excel('patents_2000_2021.xlsx', index=False)
