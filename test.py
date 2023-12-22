def init_base():
    with open('init.sql', 'r') as file:
        queries = file.read().split(';')
        for query in queries:
            print(query)


if __name__ == '__main__':
    pass
