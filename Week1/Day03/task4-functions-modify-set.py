s1 = {"python", "C++", "Java"}

s1.add("SQL")
print("After add:", s1)

s1.update(["HTML", "CSS"])
print("After update:", s1)

s1.discard("C++")
print("After discard:", s1)

s1.remove("Java")
print("After remove:", s1)

s2 = s1.copy()
print("Copied set:", s2)

s1.clear()
print("After clear:", s1)
