import pandas as pd

file_path = "F:\\1.Boulot\\03_Github\\datalyzer\\data\\spotify_2023.csv"

df = pd.read_csv(file_path, sep=",", encoding="latin-1")
print(df.dtypes)
print(df.head())
