l=[i*i for i in range(5)]
t=(i+i for i in range(5))
d={i:i*i for i in range(5)}
print(l)
print(tuple(t))
print(d)

def h(*a,**b):
    print(a)
    print(b)
h(1,2,3,x=4,y=5)

k=lambda x,y:x+y
print(k(5,6))
