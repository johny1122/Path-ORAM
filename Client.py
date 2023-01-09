# Jonathan Birnbaum

import random
import secrets
from typing import Union
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Server import Server
from Utils import *

DATA_SIZE = 4  # in bytes (string of 4 chars)
KEY_SIZE = 32  # in bytes
NONCE_TAG_SIZE = 16  # in bytes
DUMMY_DATA = 'XXXX'
DUMMY_ID = 'x'
ROOT_INDEX = 0


class Client:
    """
    client class - should be able to store, retrieve and delete data from the server storage without
    the server knowledge of the clients data content and access pattern.
    client should be able to encrypt/decrypt and authenticate the data
    """

    def __init__(self, N: int, server: Server):
        self.tree_height = max(0, math.ceil(math.log(N, 2)) - 1)  # it was proven that this is sufficient in 3.2
        self.bucket_size = math.ceil(math.log(N, 2))
        num_of_leaves = 2 ** self.tree_height
        self.tree_size = (2 * num_of_leaves) - 1
        self.leaves_indices = list(range(num_of_leaves - 1, self.tree_size))

        self.num_of_files = N
        self.position_map = dict()
        self.secret_key = get_random_bytes(KEY_SIZE)
        self.initialize_tree_with_dummies(server)

    def initialize_tree_with_dummies(self, server: Server):
        """
        fill the tree storge of the given server with dummy data
        """
        for bucket_id in range(self.tree_size):
            encrypted_bucket = [self.encrypt_data(DUMMY_ID, DUMMY_DATA) for _ in range(self.bucket_size)]
            server.write_bucket_by_index(bucket_id, encrypted_bucket)

    def read_path(self, leaf_index: int, server: Server):
        """
        return the list of indices and buckets of the nodes from root to the given tree leaf
        """
        path_indices = get_path_to_leaf(leaf_index, self.tree_height)
        path_buckets = server.get_buckets_by_indices(path_indices)
        return path_buckets, path_indices

    def generate_new_leaf_index(self):
        """
        return a random leaf index
        """
        return secrets.choice(self.leaves_indices)

    def get_next_node_index_in_path_to_leaf(self, data_id: int, curr_bucket_index: int):
        """
        return the bucket of the next node of path from root to leaf of given data_id which stored in
         the bucket curr_bucket_index
        """
        if data_id == DUMMY_ID:  # if dummy id - return one of the bucket's children
            left_child_index = get_left_child_index(curr_bucket_index)
            right_child_index = get_right_child_index(curr_bucket_index)
            return secrets.choice([left_child_index, right_child_index])

        # if not a dummy id
        leaf_index = self.position_map[data_id]
        if leaf_index == curr_bucket_index:  # if curr bucket is leaf - no children
            return leaf_index
        path_indices = get_path_to_leaf(leaf_index, self.tree_height)
        curr_index_in_path_list = path_indices.index(curr_bucket_index)
        return path_indices[curr_index_in_path_list + 1]

    def insert_data_to_bucket(self, encrypted_data, bucket, bucket_id: int, server: Server):
        """
         insert the given data to the given bucket. (replace first dummy with given data)
         decrypt and re-encrypt all bucket and write back to the server
        """
        new_bucket = []
        replaced_with_dummy = False
        # traverse bucket to find a dummy data to replace with new data
        for encrypted_block in bucket:
            curr_data_id, curr_data = self.decrypt_data(encrypted_block)
            if (not replaced_with_dummy) and (
                    curr_data_id == DUMMY_ID):  # if found first dummy - replace with encrypted_data
                new_bucket.append(encrypted_data)
                replaced_with_dummy = True
            else:  # if not searched data - just re-encrypt again
                re_encrypt_data = self.encrypt_data(curr_data_id, curr_data)
                new_bucket.append(re_encrypt_data)

        # write re_encrypted root bucket with added data back to the server
        server.write_bucket_by_index(bucket_id, new_bucket)

    def remove_data_from_bucket(self, data_id_to_remove: int, bucket, bucket_index: int,
                                server: Server, still_remove: bool):
        """
         remove the given data from the given bucket. (replace with dummy)
         decrypt and re-encrypt all bucket and write back to the server
        """
        searched_data = None
        re_encrypt_bucket = []
        for encrypted_data_block in bucket:
            data_id, data = self.decrypt_data(encrypted_data_block)

            # check if still not found and this is searched data
            if still_remove and (data_id == data_id_to_remove):
                searched_data = data
                # if data found, it should be removed from bucket - so write dummy instead
                re_encrypted_data = self.encrypt_data(DUMMY_ID, DUMMY_DATA)

            else:  # if not searched data - just re-encrypt again
                re_encrypted_data = self.encrypt_data(data_id, data)

            re_encrypt_bucket.append(re_encrypted_data)  # add encrypted data to new bucket

        server.write_bucket_by_index(bucket_index,
                                     re_encrypt_bucket)  # write back full re-encrypted bucket to server

        return searched_data

    def prevent_overflow(self, server: Server):
        """
        prevent from overflows in the tree according to the algorithm shown here https://youtu.be/3RWyVGwG9U8?t=2792
        """
        for level in range(self.tree_height):  # for each level apart from leaves
            if level == ROOT_INDEX:  # if root level - there is only one bucket so choose only root
                curr_chosen_bucktes_indices = [ROOT_INDEX]

            else:  # other levels have at least 2 buckets
                curr_level_indices = get_node_indices_of_level(level)
                curr_chosen_bucktes_indices = random.sample(curr_level_indices, 2)

            curr_chosen_bucktes = server.get_buckets_by_indices(curr_chosen_bucktes_indices)
            for bucket_index, bucket in zip(curr_chosen_bucktes_indices,
                                            curr_chosen_bucktes):  # for each of the chosen buckets
                data_to_push_down = None
                data_id_to_push_down = None
                index_to_push_down = random.randint(0,
                                                    self.bucket_size - 1)  # choose one data in file to push down
                new_bucket = []
                for index, encrypted_block in enumerate(bucket):  # for each data in bucket
                    curr_data_id, curr_data = self.decrypt_data(encrypted_block)

                    if index == index_to_push_down:  # the data to push down - replace with dummy
                        data_to_push_down = curr_data
                        data_id_to_push_down = curr_data_id
                        re_encrypted_data = self.encrypt_data(DUMMY_ID, DUMMY_DATA)
                    else:  # not data to push down
                        re_encrypted_data = self.encrypt_data(curr_data_id, curr_data)

                    new_bucket.append(re_encrypted_data)

                server.write_bucket_by_index(bucket_index, new_bucket)

                # encrypted elements to push down
                encrypted_push_down = self.encrypt_data(data_id_to_push_down, data_to_push_down)
                encrypted_dummy = self.encrypt_data(DUMMY_ID, DUMMY_DATA)

                # indices and buckets of left and right children
                next_node_index_to_leaf = self.get_next_node_index_in_path_to_leaf(data_id_to_push_down,
                                                                                   bucket_index)
                left_child_index = get_left_child_index(bucket_index)
                right_child_index = get_right_child_index(bucket_index)
                left_bucket = server.get_bucket_by_index(left_child_index)
                right_bucket = server.get_bucket_by_index(right_child_index)

                if next_node_index_to_leaf == left_child_index:  # need to push data to left child - write dummy to right
                    self.insert_data_to_bucket(encrypted_push_down, left_bucket, left_child_index, server)
                    self.insert_data_to_bucket(encrypted_dummy, right_bucket, right_child_index, server)

                else:  # need to push data to right child - write dummy to left
                    self.insert_data_to_bucket(encrypted_dummy, left_bucket, left_child_index, server)
                    self.insert_data_to_bucket(encrypted_push_down, right_bucket, right_child_index, server)

    # __________________ Encrypt-Decrypt data __________________

    def encrypt_data(self, data_id, data: str):
        """
        encrypt data
        :param data_id: int of data id
        :param data: data to encrypt
        :return: encrypted data (encryption of nonce + tag + ciphertext)
        """
        cipher = AES.new(self.secret_key, AES.MODE_EAX)

        # convert data (str) to bytes
        data_parts = str(data_id) + data
        data_parts_in_bytes = str.encode(data_parts)

        # encrypt
        ciphertext_in_bytes, tag_in_bytes = cipher.encrypt_and_digest(data_parts_in_bytes)
        nonce_in_bytes = cipher.nonce
        return nonce_in_bytes + tag_in_bytes + ciphertext_in_bytes

    def decrypt_data(self, data):
        """
        return decrypted data of given data.
        can raise ValueError or KeyError if decryption or authentication didn't succeed
        :param data: encrypted data
        """
        nonce_in_bytes, tag_in_bytes, ciphertext_in_bytes = \
            data[:NONCE_TAG_SIZE], data[NONCE_TAG_SIZE:2 * NONCE_TAG_SIZE], data[2 * NONCE_TAG_SIZE:]
        cipher = AES.new(self.secret_key, AES.MODE_EAX, nonce_in_bytes)

        try:
            plaintext_in_bytes = cipher.decrypt_and_verify(ciphertext_in_bytes, tag_in_bytes)
            plaintext = bytes.decode(plaintext_in_bytes)
            if plaintext[:-DATA_SIZE].isnumeric():  # if id is a number - not dummy data
                data_id, data = int(plaintext[:-DATA_SIZE]), plaintext[-DATA_SIZE:]
            else:  # if id is not a number - dummy data
                data_id, data = plaintext[:-DATA_SIZE], plaintext[-DATA_SIZE:]
            return data_id, data
        except (ValueError, KeyError):
            print("Incorrect decryption")

    # __________________ API methods __________________

    def store_date(self, server: Server, data_id: int, data: str) -> None:
        """
        write data to root bucket. decrypt root bucket and find a dummy data to replace with given data.
        assign new random leaf to data and store in position_map.
        call prevent_overflow() to make sure root will not be full of real data
        :param server: server object
        :param data_id: int of data id
        :param data: data to store
        """
        if data_id in self.position_map:
            print(color_text('Error: data_id is already in use. choose a different one', Colors.RED))
            return

        if len(data) != DATA_SIZE:
            print(color_text(f'Error: data must be string of {DATA_SIZE} characters', Colors.RED))
            return

        encrypted_data = self.encrypt_data(data_id, data)

        root_bucket = server.get_bucket_by_index(ROOT_INDEX)
        self.insert_data_to_bucket(encrypted_data, root_bucket, ROOT_INDEX, server)

        # assign new random leaf to data and save in position map
        self.position_map[data_id] = self.generate_new_leaf_index()
        # move data blocks down the tree to prevent overflows
        self.prevent_overflow(server)

    def retrieve_data(self, server: Server, requested_data_id: int) -> Union[str, None]:
        """
        get data by id. search the correct path from root to leaf of given data by its id.
        call store_data() to write the requested data back to the root
        :param server: server object
        :param requested_data_id: int of data id to find
        :return: requested data. can raise ValueError or KeyError if decryption or authentication didn't succeed
        """
        if requested_data_id not in self.position_map:
            return None
        leaf_of_data = self.position_map[requested_data_id]
        path_buckets, path_indices = self.read_path(leaf_of_data, server)

        # from now, it is guarantied that searched data is in the path from root to leaf

        # traverse path from root to leaf and look for the searched data
        searched_data = None
        for bucket_index, bucket in zip(path_indices, path_buckets):
            still_searching = searched_data is None
            removed_data = self.remove_data_from_bucket(requested_data_id, bucket, bucket_index, server,
                                                        still_searching)
            if still_searching:
                searched_data = removed_data

        # now data is not in storage so delete its id from position map
        self.position_map.pop(requested_data_id)
        # write searched data to root, assign new random leaf to data and prevent overflow
        self.store_date(server, requested_data_id, searched_data)

        return searched_data

    def delete_data(self, server: Server, data_id_to_delete: int) -> None:
        """
        delete the data associated with the given data id and remove the id from position_map
        :param server: server object
        :param data_id_to_delete: int of data id to delete from the storage in the server
        :return: None
        """
        if data_id_to_delete not in self.position_map:
            print(color_text('Error: given data_id does not exist in server. choose a different one',
                             Colors.RED))
            return
        leaf_of_data = self.position_map[data_id_to_delete]
        path_buckets, path_indices = self.read_path(leaf_of_data, server)

        # traverse path from root to leaf and look for the searched data
        searched_data = None
        for bucket_index, bucket in zip(path_indices, path_buckets):
            still_searching = searched_data is None
            removed_data = self.remove_data_from_bucket(data_id_to_delete, bucket, bucket_index, server,
                                                        still_searching)
            if still_searching:
                searched_data = removed_data

        # now data is not in storage so delete its id from position map
        self.position_map.pop(data_id_to_delete)
