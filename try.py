import pandas as pd
import re
df=pd.read_csv('./vul4j_dataset.csv')
print(df['human_patch'][:10])