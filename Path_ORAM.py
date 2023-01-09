# Jonathan Birnbaum

import math
import random
import string
from Server import Server
from Client import Client
from Utils import Colors, color_text
from timeit import default_timer as timer

STORE = '1'
RETRIEVE = '2'
DELETE = '3'
EXIT = '9'


def test():
    # for N in [3, 5, 10, 50, 100, 200, 500, 1000, 2000]:
    for N in [3, 5, 10, 50, 100]:
        # N = 500 # number of data blocks supported
        print('--------------------')
        print(f'N = {N}\n')
        tree_height = max(0, math.ceil(math.log(N, 2)) - 1)  # it was proven that this is sufficient in 3.2
        num_of_leaves = 2 ** tree_height
        tree_size = (2 * num_of_leaves) - 1
        print(f'tree_height: {tree_height}')
        print(f'num_of_leaves: {num_of_leaves}')
        print(f'tree_size: {tree_size}\n ')

        random_strings = [''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in
                          range(N)]

        server = Server(tree_size)
        client = Client(N, server)

        print('__STORE__')
        total_request_time = 0
        all_request_start = timer()
        for index in range(N):
            start = timer()
            client.store_date(server, index, random_strings[index])
            end = timer()
            total_request_time += end - start
        all_request_end = timer()

        avg_request_time = total_request_time / N
        total_time = all_request_end - all_request_start
        print(f'total time: {total_time}')
        print(f'Throughput: {N / total_time}')
        print(f'Latency: {avg_request_time}')

        print('\n__RETRIEVE__')
        all_request_start = timer()
        for index in range(N):
            start = timer()
            client.retrieve_data(server, index)
            end = timer()
            total_request_time += end - start
        all_request_end = timer()
        avg_request_time = total_request_time / N
        total_time = all_request_end - all_request_start
        print(f'total time: {total_time}')
        print(f'Throughput: {N / total_time}')
        print(f'Latency: {avg_request_time}')

        print('\n__DELETE__')
        all_request_start = timer()
        for index in range(N):
            start = timer()
            client.delete_data(server, index)
            end = timer()
            total_request_time += end - start
        all_request_end = timer()
        avg_request_time = total_request_time / N
        total_time = all_request_end - all_request_start
        print(f'total time: {total_time}')
        print(f'Throughput: {N / total_time}')
        print(f'Latency: {avg_request_time}')


def get_data_id_from_user() -> int:
    data_id = input('Insert data id (must be integer): ')
    while not data_id.isdigit():
        data_id = input(color_text('data id must be integer. choose again: ', Colors.RED))

    return int(data_id)


def main():
    print(color_text('===== Path ORAM =====', Colors.YELLOW))
    N = input('Please enter number of data blocks support needed (positive integer): ')
    while not N.isdigit() or int(N) < 1:
        N = input(color_text('number of data blocks must be positive integer. choose again: ', Colors.RED))
    N = int(N)
    print('Data blocks supported:', N)

    tree_height = max(0, math.ceil(math.log(N, 2)) - 1)  # it was proven that this is sufficient in 3.2
    num_of_leaves = 2 ** tree_height
    tree_size = (2 * num_of_leaves) - 1

    server = Server(tree_size)
    client = Client(N, server)

    user_request = None
    while user_request != EXIT:
        request = input('\nChoose operation number: (1)store | (2)retrieve | (3)delete | (9)exit\n')

        if request == STORE:
            print(color_text('\n--- STORE ---', Colors.CYAN))
            data_id = get_data_id_from_user()
            data = input('Insert data (string of 4 characters): ')
            client.store_date(server, data_id, data)
            print('Done store')

        elif request == RETRIEVE:
            print(color_text('\n--- RETRIEVE ---', Colors.CYAN))
            requested_data_id = get_data_id_from_user()
            data = client.retrieve_data(server, requested_data_id)
            if data is not None:
                print('requested data:', color_text(data, Colors.GREEN))
            else:
                print(color_text('requested id not in server storage', Colors.RED))
            print('Done retrieve')

        elif request == DELETE:
            print(color_text('\n--- DELETE ---', Colors.CYAN))
            data_id_to_delete = get_data_id_from_user()
            client.delete_data(server, data_id_to_delete)
            print('Done delete')

        elif request == EXIT:
            print('\nExiting')
            exit()

        else:
            print(color_text('invalid operator. choose from: 1/2/3/9', Colors.RED))


# test()
main()
