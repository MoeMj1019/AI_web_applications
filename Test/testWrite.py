import pandas as pd

# Sample dictionary
data = {
    'Name': ['Alice', 'Bob', 'Charlie'],
    'Age': [25, 30, 35],
    'City': ['New York', 'San Francisco', 'Los Angeles']
}

data = pd.DataFrame(data)

data.to_csv('data.csv', encoding='utf-8', index=False)
