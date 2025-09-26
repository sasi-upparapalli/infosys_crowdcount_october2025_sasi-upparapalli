def calc(a, o, b):
    match o:
        case '+': return a + b
        case '-': return a - b
        case '*': return a * b
        case '/': return a / b if b != 0 else "Error"
        case '%': return a % b if b != 0 else "Error"
        case '//': return a // b if b != 0 else "Error"
        case '': return a ** b
        case _: return "Invalid operator"

print(calc(10, '+', 5))
print(calc(10, '-', 5))
print(calc(10, '*', 5))
print(calc(10, '/', 2))
print(calc(10, '%', 3))
print(calc(10, '//', 2))
print(calc(2, '', 3))
