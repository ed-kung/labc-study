import pandas as pd

def as_pd(tbl):
    return pd.DataFrame(tbl).fillna('')

def as_latex(tbl):
    for row in tbl:
        print(' & '.join(row) + '\\\\ [1ex]')