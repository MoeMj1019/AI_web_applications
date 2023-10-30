import pandas as pd

# Sample dictionary
data = {
    'Name': ['Alice', 'Bob', 'Charlie'],
    'Age': [25, 30, 35],
    'City': ['New York', 'San Francisco', 'Los Angeles']
}

# Convert the dictionary to a DataFrame
df = pd.DataFrame.from_dict(data)

# Print the DataFrame
print(df)
