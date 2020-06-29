import common


def main():
    d = {'c' : 1}
    b = {'a' : d}
    f = {'m' : b}
    n = common.get_node(f, 'm', 'a')
    res = n == d
    print (res)


if __name__ == '__main__':
	main()

