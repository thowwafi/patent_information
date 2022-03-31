from datetime import timedelta
from log_settings import logger
import os
import pandas as pd
import sys
import time
from timeit import default_timer as timer


def get_citations(file_name):
    """
    Returns a list of citations in the given file.
    """
    path = os.path.join(outputs, year_path)
    df = pd.read_excel(path, dtype=str)
    columns = ['publication_number']
    df_unique = df.drop_duplicates(subset=['applicant_name', 'applicant_address'])[columns]
    df.publication_number.str.split(' ').str[:2].str.join(" ")
    import pdb; pdb.set_trace()


if __name__ == '__main__':
    home = os.getcwd()
    outputs = os.path.join(home, 'output_excel')
    extensionsToCheck = [str(i) for i in list(range(2020, 2021))]
    for year_path in sorted(os.listdir(outputs), reverse=True):
        if any(ext in year_path for ext in extensionsToCheck):
            print(year_path)
            start = timer()
            get_citations(year_path)
            end = timer()
            print(timedelta(seconds=end-start))
            logger.info(f"{year_path} -- done -- {timedelta(seconds=end-start)}")
    print('done')
    logger.info('done')