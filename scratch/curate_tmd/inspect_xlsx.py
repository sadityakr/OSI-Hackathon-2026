"""Print sheet names, shapes and head of each sheet of an xlsx (read-only inspection)."""
import sys, pandas as pd
x = pd.ExcelFile(sys.argv[1])
for s in x.sheet_names:
    df = x.parse(s, header=None)
    print("==", s, df.shape)
    print(df.iloc[:4, :6].to_string())
