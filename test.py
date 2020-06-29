n1 = 25
n2 = 45
if n2 < n1 or n1 < 0:
    print('invalid range')
for i in range(n1, n2 + 1):
    if i % 3 == 0 and i % 2 != 0:
        print (i)
    elif i % 5 == 0 and i % 2 != 0:
        print (i)
        