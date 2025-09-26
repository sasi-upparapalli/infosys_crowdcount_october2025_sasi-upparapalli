def calc(a, o, b):
    if o == '+': return a + b
    elif o == '-': return a - b
    elif o == '*': return a * b
    elif o == '/': return a / b if b != 0 else "Error"
    elif o == '%': return a % b if b != 0 else "Error"
    elif o == '//': return a // b if b != 0 else "Error"
    elif o == '': return a ** b
    else: return "Invalid operator"

print(calc(10, '+', 5))
print(calc(10, '-', 5))
print(calc(10, '*', 5))
print(calc(10, '/', 2))
print(calc(10, '%', 3))
print(calc(10, '//', 2))
print(calc(2, '', 3))
