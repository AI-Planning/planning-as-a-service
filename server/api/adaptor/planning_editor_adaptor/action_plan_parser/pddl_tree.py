import sys
import os
# sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../' + "utils"))

# my utility function
import utils

# related classes
from predicate import Predicate
from formula import *
from action import Action

# from stdlib
import re
from sys import stderr

class PDDL_Tree (object):
    """
        A node in the PDDL Tree.
        Also the root node, thus represents the PDDL Tree itself.
    """

    # set tab at 4 spaces
    TAB = " " * 4
    EMPTY = "<empty>"

    def __init__ (self, name):
        """Create a new tree node with given name."""

        self.name = name
        self.children = []
        
    def __getitem__ (self, k):
        """
            Allow retrieval of children based on name.
            Throw an error if nothing found
            No speedup, just convenient interface.
        """

        for c in self.children:
            if c.name == k:
                return c

        raise KeyError ("No subtree with name %s found in this tree" % k)

    def __contains__ (self, k):
        """Allow membership checking of named subtree k. For convenience, no actual speedup."""

        return k in self.named_children()

    def find_all (self, k):
        """
            Find all children of this node with name k
            Return as a generator
        """

        for c in self.children:
            if c.name == k:
                yield c

    def named_children (self):
        """
            Return a list of the names of this node's children.
            Particularly useful if the children are all leaves.
        """

        return [c.name for c in self.children]

    def add_child (self, child):
        """Add the given child to the end of the list of children."""
        
        self.children.append(child)

    def dump (self):
        """Informative representation."""

        return self.print_tree ()
        
    def print_tree (self, lvl=0):
        """Print the entire tree to the console."""

        print (PDDL_Tree.TAB * lvl + str(self.name))
        
        for child in self.children:
            child.print_tree(lvl + 1)

    def has_children (self):
        """Return True iff this node has children. """
        
        return len(self.children) == 0

    def is_leaf (self):
        """ Return True iff this node is a leaf. """
        
        return not self.has_children()

    def is_empty (self):
        """Return True if this node is a (filler) empty node."""

        return self.name == PDDL_Tree.EMPTY

    @staticmethod
    def create (fname):
        """Create a PDDL Tree out of the given PDDL file."""

        pddl_list = PDDL_Tree._get_pddl_list (utils.get_contents(fname))
        pddl_tree = PDDL_Tree._make_tree(pddl_list)
        PDDL_Tree._alter_tree (pddl_tree)
        return pddl_tree

    @staticmethod
    def _alter_tree (root):
        """Alter tree to get correct semantic structure."""

        alter_set = set([":precondition", ":effect", ":observe"])
        i = 0

        while i < len (root.children):
            if root.children[i].name == ":parameters":
                if not root.children[i + 1].is_empty():
                    root.children[i].add_child (root.children [i + 1])

                # this also clears the original father node
                while len(root.children[i + 1].children) > 0:
                    c = root.children[i + 1].children.pop(0)
                    root.children[i].add_child (c)

                root.children.pop(i + 1) # finally, remove the subtree
            elif root.children[i].name in alter_set:
                subtree = root.children.pop(i + 1)
                root.children[i].add_child (subtree)
            else:
                PDDL_Tree._alter_tree (root.children[i])
            i += 1

    @staticmethod
    def _make_tree (pddl_list):
        """
            Make a tree out of a PDDL list.
            Meant to be called internally
        """
        
        root = PDDL_Tree (pddl_list[0])
        
        for child in pddl_list[1:]:
            if isinstance (child, list):
                if len (child) == 0:
                    root.add_child (PDDL_Tree(PDDL_Tree.EMPTY))
                else:
                    subtree = PDDL_Tree._make_tree(child)
                    root.add_child(subtree)
            else:
                root.add_child (PDDL_Tree (child))
                
        return root

    @staticmethod
    def _get_pddl_list (contents):
        """
            Given the contents of a PDDL file, return a list of correctly nested lists.
            This is also the pre-processing step.
        """

        contents = re.sub(r"\s+", " ", contents.replace("(", "[").replace(")", "]"))

        # do tricky things with brackets by hand
        l = list(contents)
        i = 0

        while i < len(l) - 1:
            if l[i] == "[" and l[i + 1] == " ":
                l.pop(i + 1)
            elif l[i] == " " and l[i + 1] == "]":
                l.pop(i)
                i -= 1
            elif (l[i] == "]" and l[i + 1] == "[") or (l[i] not in ["[", "]", " "] and l[i + 1] == "["):
                # cases for adding spaces:
                # between successive close-open brackets
                # between the ending of non-space non-bracket char and open bracket
                l.insert(i + 1, " ")
            i += 1

        contents = "".join(l)

        contents = contents.replace(" ", ",")

        # the expression in first bracket defines what is allowed to be the name of a predicate, and what is not
        contents = re.sub(r"([^,\[\]]+)", r"'\1'", contents)


        # for easier debugging, put on different lines
        contents = contents.replace(",", ",\n")
        #print contents
        return eval(contents)

