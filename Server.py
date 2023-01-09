# Jonathan Birnbaum

from typing import List


class Server:
    """
    serve class - containing the storage. can add/return data buckets to/from the storage
    the server should not be able to determine the clients access pattern to the storage
    """

    def __init__(self, tree_size: int):
        self.tree_storage = [None] * tree_size  # storage is a list of buckets (list of lists)

    def get_bucket_by_index(self, index: int):
        """
        return the node bucket in the given tree index
        """
        try:
            return self.tree_storage[index]
        except IndexError as e:
            print("Error:", e)

    def get_buckets_by_indices(self, indices_list: List[int]):
        """
        return a list of buckets in the given tree indices
        """
        return [self.get_bucket_by_index(index) for index in indices_list]

    def write_bucket_by_index(self, index: int, bucket: List):
        """
        replace the given bucket with the one in the given index in the tree
        """
        self.tree_storage[index] = bucket
