print("Welcome to the Springboard Form!\n")

name = input("Enter your name: ")
batch = input("Enter your batch: ")
project = input("Enter your project name: ")
mentor_enrolled = input("Is a mentor enrolled? (yes/no): ")
email = input("Enter your email: ")
phone = input("Enter your phone number (1–10 digits): ")
domain = input("Enter your domain (e.g., AI, Web, Data): ")

print("Name:", name, ", Batch:", batch, ", Project:", project)  # Comma method
print("Email: " + email + ", Phone: " + phone)                  # Plus method
print("Mentor Enrolled: %s, Domain: %s" % (mentor_enrolled, domain))  # Percent method
print("Project: {}, Batch: {}, Mentor: {}".format(project, batch, mentor_enrolled))  # .format method
print(f"Thank you {name}, your Infosys Springboard form has been submitted!")  # F-string method
