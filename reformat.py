import os
import pandas as pd


home = os.getcwd()


if __name__ == '__main__':
    df = pd.read_excel(f"{home}/patents_2000_2021.xlsx")
    df_ori = df.copy()
    print(df.shape)
    df[['application_type', 'application_number', 'application_date']] = df.application_number.str.split(' ', expand=True)
    column_to_move = df.pop("application_type")
    df.insert(24, "application_type", column_to_move)
    df.to_excel('patents_2000_2021_final.xlsx', index=False)
