import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../' + "acttion_plan_parser"))
# helper classes
from action import Action
from predicate import Predicate
from formula import *

"""
    General purpose utilities
"""

import re

def get_contents (fname):
    """
        Return the contents of the given file.
        Strip comments (lines starting with ;)
    """
    
    # fp = open (fname, "r")
    contents = fname.lower()

    return re.sub(r"\s*;(.*?)\n", "\n", contents).strip()

class PDDL_Utils (object):
    """
    Collection of general-purpose utilities used for parsing PDDL files.
    """

    @staticmethod
    def apply_type (item_list, t):
        """ Apply the given type to the item list. Only alter untyped items. """

        for i in range (len (item_list) - 1, -1, -1):
            if isinstance (item_list[i], tuple):
                break
            else:
                item_list[i] = (item_list[i], t)

    @staticmethod
    def read_type (node):
        """Read the types for the given node."""

        item_list = []
        n = 0

        while n < len (node.children):
            c = node.children [n].name

            if c == "-":
                PDDL_Utils.apply_type (item_list, node.children[n + 1].name)
                n += 2
            else:
                item_list.append (c)
                n += 1

        # type all untyped objects with default type
        PDDL_Utils.apply_type (item_list, Predicate.OBJECT)
        return item_list

