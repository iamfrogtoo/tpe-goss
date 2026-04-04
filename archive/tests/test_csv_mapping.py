import requests

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSU9r4JTOOhZ3qQKEXNZpHqR9B-EQ35U3XwR74LKkJk1v1Rdan8VMgZjKWb1khjCU_VVp4hJ2sJPnx3/pub?gid=2059190189&single=true&output=csv"
res = requests.get(URL)
text = res.text
rows = [r.strip() for r in text.split('\n') if r.strip()]

if len(rows) > 1:
    header = rows[0].split(',')
    print(f"Header: {header}")
    for i, h in enumerate(header):
        print(f"Index {i}: {h}")
    
    first_row = rows[1].split(',')
    print(f"\nFirst Data Row: {first_row}")
    for i, v in enumerate(first_row):
        print(f"Index {i}: {v}")
