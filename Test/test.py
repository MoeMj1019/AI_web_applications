# Initial list of tuples
data = [(1, 10), (2, 20), (3, 30), (1, 5), (4, 40)]

# Create a dictionary to store the results
result_dict = {}

# Iterate through the original list
for key, value in data:
    if key in result_dict:
        # If the key already exists, add the value to the existing tuple
        result_dict[key] = (key, result_dict[key][1] + value)
    else:
        # If the key doesn't exist, create a new tuple
        result_dict[key] = (key, value)

# Convert the dictionary values back to a list of tuples
result_list = list(result_dict.values())

# Print the result
print(result_list)
#In this code, we iterate through the original list of tuples, and for each tuple, we check if the first element (the key) already exists in the result_dict. If it does, we add the second element to the existing tuple. If not, we create a new tuple in the dictionary. Finally, we convert the dictionary values back to a list of tuples to get the desired result.

#After running this code, result_list will contain the list of tuples with the second elements added to existing tuples where the first element matches.





