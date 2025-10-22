smedia = {
    "Twitter": 140,
    "Facebook": "status",
    "Instagram": "photo",
    "Snapchat": "message",
    "Linkedin": "work"
}

print("Original dictionary:", smedia)
print("Length:", len(smedia))
print("Max key:", max(smedia))
print("Min key:", min(smedia))

del smedia["Facebook"]
print("After deleting 'Facebook':", smedia)

popped_value = smedia.pop("Instagram")
print("Popped 'Instagram':", popped_value)
print("After pop:", smedia)

smedia.clear()
print("After clear:", smedia)
