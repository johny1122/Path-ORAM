# Jonathan Birnbaum

import math
from typing import List


def get_left_child_index(index: int):
    """
    get left child index of the given node index in tree
    """
    return (2 * index) + 1


def get_right_child_index(index: int):
    """
    get right child index of the given node index in tree
    """
    return (2 * index) + 2


def get_parent_index(index: int):
    """
    get parent index of the given node index in tree
    """
    return math.floor((index - 1) / 2)


def get_path_to_leaf(leaf_index: int, tree_height: int) -> List[int]:
    """
    get list of indices of nodes from root to given leaf
    """
    path = []
    curr_node = leaf_index
    for i in range(tree_height + 1):
        path.append(curr_node)
        curr_node = get_parent_index(curr_node)

    return path[::-1]


def get_node_indices_of_level(level_index: int):
    """
    get list of indices of all nodes in the given tree level
    """
    first_index_in_level = (2 ** level_index) - 1
    return list(range(first_index_in_level, (2 * first_index_in_level) + 1))


def color_text(text, rgb):
    r, g, b = rgb
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"


class Colors:
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    CYAN = (0,255,255)
