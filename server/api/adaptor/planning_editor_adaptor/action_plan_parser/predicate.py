class Predicate (object):
    """
        Simple data structure for the predicate objects.

        Attributes:
            name: the predicate name (string)

            args: list of tuples that contain a pair of strings
                * the first is the variable name
                * the second is the variable type

            ground_args:    List of tuples that contain a pair of strings.
                            The first is the object name and the second is the variable type.

        Methods:
            is_ground:    Returns True when args is empty, and False otherwise.

            ground:    Takes in an iterable of tuples that contain a pair of strings.
                       The first is a variable name and the second is an object name.
                       It should throw an error if the variable type and the object type do not match.
                       It should also throw an error if the set of variables passed in isn't a subset of the variables in args.
                       The effect should be to remove the appropriate elements from the args list,
                       and add the appropriate elements to the ground_args list.
    """

    OBJECT = "default_object"

    def __init__ (self, name, args, ground_args=None):
        """
            Create a new predicate.

            Inputs:
                name: the predicate name (string)

                args: list of tuples that contain a pair of strings
                    * the first is the variable name
                    * the second is the variable type
        """

        assert isinstance (name, str), "Predicate name must be a string"
        assert ground_args is None or args is None,\
        "Either this Predicate is ground or it is not"

        if ground_args is None:
            assert isinstance (args, list) and all([isinstance(arg, tuple) for arg in args]), \
            "args must be a list of tuples"
        else:
            assert isinstance (ground_args, list), "ground_args must be a list"

        self.name = name
        self.args = args
        self.ground_args = ground_args

    def _hash_string (self):
        """Return the string used for hashing."""

        if self.args is None:
            # then this is a fluent
            return self.name + "_" + \
                    "_".join([arg[0] for arg in self.ground_args])
        else:
            # this is an unground predicate
            return self.name + "_" + \
                    "_".join([arg[0] + "_" + arg[1] for arg in self.args])

    def __hash__(self):
        """Hash function, to compare two fluents.
        Equal when names and arguments are equal."""

        return hash (self._hash_string ())

    def __eq__ (self, p):
        return self.is_equal (p)

    def __ne__ (self, p):
        return not (self == p)

    def __cmp__ (self, p):
        return cmp(self._hash_string(), p._hash_string())

    def is_equal (self, p):
        """Return True iff two predicates are equal."""

        #if self.name != p.name:
        #    print "prim: names don't match"
        #if self.args != p.args:
        #    print "args don't match"
        #    print "*self*"
        #    print self.args
        #    print "*p*"
        #    print p.args
        #if self.ground_args != p.ground_args:
        #    print "ground_args don't match"

        return self.name == p.name and \
                self.args == p.args and \
                self.ground_args == p.ground_args

    def export (self, lvl=1, sp="  ", untyped=False, grounding={}):
        """Return a PDDL representation of this predicate, as a string."""

        o = [] # list of output lines
        sep = ""

        if self.ground_args is None:
            l = self.args
        else:
            l = self.ground_args

        if len (l) > 0:
            sep = " "

        if not untyped and len (l) > 0 and l [0][1] != Predicate.OBJECT:
            arg_s = " ".join (["%s - %s" % (v, t) for v, t in l])
        else:
            arg_s = " ".join ([v for v, t in l])
        
        for k in grounding:
            arg_s = arg_s.replace(k, grounding[k])

        return (sp * lvl) + "(%s%s%s)" % (self.name, sep, arg_s)

    def ground (self, it):
        """Takes in an iterable of tuples that contain a pair of strings.
        The first is a variable name and the second is an object name.
        It should throw an error if the variable type and the object type do not match.
        It should also throw an error if the set of variables passed in isn't a subset of the variables in args.
        The effect should be to remove the appropriate elements from the args list, and add the appropriate elements to the ground_args list.
        """

        assert hasattr (it, '__iter__') and all ([ isinstance(item, tuple) and \
        len(item) == 2 and isinstance (item[0], str) and isinstance (item[1], str) for item in it ]),\
        "first argument must be iterable, and be a sequence of tuples, which are pairs of strings"

        it_var_names = set ([ item[0] for item in it ])
        it_obj_names = set ([ item[1] for item in it ])

        self_var_names = set ([ arg[0] for arg in self.args ])
        self_var_types = set ([ arg[1] for arg in self.args ])
        #TODO not fully implemented

    def is_ground (self):
        """Return True iff args is empty."""

        return len (self.args) == 0

    def dump (self):
        """Informative representation."""

        return str (self)

    def __str__ (self):
        """String representation of this object for easy debugging."""

        if self.ground_args is None:
            return "%s (%s)" % (self.name, \
            ", ".join(["%s %s" % (arg[1], arg[0]) for arg in self.args]))
        else:
            #return "%s (%s)" % (self.name, \
            #", ".join(["%s %s" % (arg[1], arg[0]) for arg in self.ground_args]))
            return "%s(%s)" % (self.name, " ".join([str(arg[0]) for arg in self.ground_args]))

    def __repr__ (self):
        return "Predicate " + str(self)

