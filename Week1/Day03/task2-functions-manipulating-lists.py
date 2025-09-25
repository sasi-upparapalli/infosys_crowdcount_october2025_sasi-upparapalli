
data = [1, 2, 'abc', 3, 4]

print("Original list:", data)

data.append('new')               # Add an item
print("After append:", data)

data.remove(2)                   # Remove an item
print("After removing 2:", data)

data[0] = 'first'                # Modify an item
print("After modifying index 0:", data)

print("Reversed list:", data[::-1])  # Reverse the list

item = 'abc'
if item in data:
    print("Index of", item, ":", data.index(item))
else:
    print(item, "not found in list.")
