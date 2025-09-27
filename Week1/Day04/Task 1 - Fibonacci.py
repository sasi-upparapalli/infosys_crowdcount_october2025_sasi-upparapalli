def f(n):
    if n<=1:
        return n
    return f(n-1)+f(n-2)

def g(n):
    if n==0:
        return 1
    return n*g(n-1)

a=int(input())
print([f(i) for i in range(a)])
print(g(a))
