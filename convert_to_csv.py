import pandas as pd


def convert_to_csv(input_path, output_path):
    """
    Convert all .xlsx files in input_path to .csv files in output_path.
    """
    df = pd.read_excel(input_path, dtype=str)
    print(df.shape)
    df.to_csv(output_path, index=False, sep=";", encoding="utf-8-sig")


if __name__ == '__main__':
    input_path = 'patents_2000_2021_new.xlsx'
    output_path = 'patents_2000_2021.csv'
    convert_to_csv(input_path, output_path)
    print('Done!')
