
from predicate import Predicate


class Formula(object):
    """
        This is an abstract class.

        Attributes:
            args: list of Formula objects

        Methods:
            normalize: restructure the Formula object to be in canonical form:
                1)  At most one Oneof object should exist,
                    and be on the outside if it does

                2)  The argument of any Not object should be a
                    Primitive object

                3)  An And object should not have any arguments
                    (directly or indirectly) that are And object

                    3b)     There can be more than one And
                            object if there is a Oneof object
    """

    def __init__(self, name, args):
        """
            Inputs:
                name:   Type of formula
                args:   list of formula objects
        """

        assert isinstance(args, list) and \
            all([isinstance(arg, Formula) for arg in args]),\
            "args must be a list of Formula objects"
        self.name = name
        self.args = args

    def to_ground (self, fluent_dict):
        """Assert that this formula is actually ground.
        Doesn't actually ground the formula, just recursively
        change all args to ground_args.

        fluent_dict allows referencing existing fluents to save space"""

        [arg.to_ground (fluent_dict) for arg in self.args]

    def __eq__ (self, f):
        return self.is_equal (f)

    def __ne__ (self, f):
        return not self.is_equal(f)

    def __repr__ (self):
        return str(self)

    def is_equal (self, f):
        assert isinstance(f, Formula), \
            "comparison must be between formulas, found %s" % str (type(f))

        #if self.name != f.name:
        #    print "names different"
        #    print self.name
        #    print f.name
        #if not all ([sa == fa for sa, fa in zip (self.args, f.args)]):
        #    diff_args = filter (lambda i: i[0] != i[1], \
        #            zip (self.args, f.args))
        #    print "args different"
        #    print "*self*"
        #    print self.args
        #    print "*f*"
        #    print f.args
        #    print "**diff **"
        #    print [str(sa) + "\n" + str (fa) for sa, fa in diff_args]
        return (self.name == f.name) and \
               len(self.args) == len(f.args) and \
               all ([sa == fa for sa, fa in zip (self.args, f.args)])

    def export (self, lvl=0, sp="  ", untyped=False, grounding={}):
        """Export this formula as a PDDL.
        Overwrite this method by subclasses as needed."""

        arg_lines = []
        prefix = sp * lvl
        arg_lines.append (prefix + "(" + self.name)
        for arg in self.args:
            if isinstance (arg, Formula):
                arg_lines.append (arg.export (lvl + 1, sp, untyped, grounding))
            else:
                res_str = str(arg)
                for k in grounding:
                    res_str = res_str.replace(k, grounding[k])
                arg_lines.append (prefix + res_str)

        arg_lines.append (prefix + ")")
        return "\n".join (arg_lines)

    def normalize(self, lvl=0):
        """
            Return a normalized formula

            Compile away nested ANDs
            Compile away Oneofs that are on the 'inside' [harder...]
            What else is in cannonical form?

            Output:
                Restructure the Formula object to be in canonical form.

        """

        pass

    def enforce_normalize(self):
        # 1) Verify that Oneof is not nested inside not Oneof
        # 5) Verify that Oneof is not nested under Forall
        if not isinstance(self, Oneof) and \
            any([isinstance(child, Oneof) for child in self.args]):
            assert False, "Oneof must be on outside, if it exists"

        # 2) the argument to a Not object should be a primitive object
        if isinstance(self, Not) and \
            not all([isinstance(child, Primitive) for child in self.args]):
            assert False, "Not object must have all children be primitives"

        # 3) Verify And object not nested under And object
        if isinstance(self, And):
            i = 0
            queue = self.args[:]
            while len(queue) > 0:
                arg = queue.pop()
                if isinstance(arg, And):
                    assert False, "Cannot nest And under another And"
                else:
                    queue.extend(arg.args)

        # 4) Forall objects should be outside of all but Oneof
        if not isinstance(self, Oneof) and \
            any([isintance(child, Forall) for child in self.args]):
            assert False, \
                "Forall object cannot be nested inside anything \
            except a Oneof object"

        # 6) Only thing that can be pulled out of a when is a Oneof
        if any([isinstance(c, When) for c in self.args]) and \
            not isinstance(self, Oneof):
            assert False, \
                "Only thing that can be pulled out of a when is a Oneof"


class Forall(Formula):

    def __init__(self, params, args):
        """
        Inputs:
            params:     list of tuples.
                        The first item is the variable name
                        The second item is the variable type

            args:       list of formula objects(input is of length 1)
        """

        assert len(args) == 1, "Args list of forall class must be 1"
        super(Forall, self).__init__("forall", args)
        self.params = params

    def export (self, lvl, sp, untyped=False, grounding={}):
        """Special export for forall must include
        variable that is quanitified."""

        if all ([p[1] == Predicate.OBJECT for p in self.params]):
            param_line = " ".join ([p[0] for p in self.params])
        else:
            param_line = " ".join (["%s - %s" % (p[0], p[1]) \
                    for p in self.params])

        s = super (Forall, self).export (lvl, sp, untyped, grounding)
        s_replace = "forall (%s)" % param_line
        return s.replace ("forall", s_replace)

    def __eq__ (self, f):
        return self.is_equal (f)

    def __ne__ (self, f):
        return not self.is_equal (f)

    def __str__(self):
        """
            String representation for easier debugging.
        """

        return "forall(%s),(%s)" % \
            (", ".join([v + " " + t for v, t in self.params]), \
             str(self.args[0]))

    def dump(self):
        """Informative string representation."""

        return str(self)


class Or (Formula):

    def __init__ (self, args):
        """Inputs:
            args:   list of formula objects
        """

        super (Or, self).__init__("or", args)

    def __str__(self):
        """
            String representation for easier debugging.
        """

        return "Or (%s)" % ", ".join([str(arg) for arg in self.args])

    def __eq__ (self, f):
        return self.is_equal (f)

    def __ne__ (self, f):
        return not (self.is_equal (f))

    def dump(self):
        """Informative string representation."""

        return str(self)


class And(Formula):

    def __init__(self, args):
        """
            Inputs:
                args:    list of formula objects
        """
        args = list(filter(lambda x: not isinstance(x, And), args)) +  [item for andarg in filter(lambda x: isinstance(x, And), args) for item in andarg.args]

        super(And, self).__init__("and", args)

    def __str__(self):
        """
            String representation for easier debugging.
        """

        return "And (%s)" % ", ".join([str(arg) for arg in self.args])

    def __eq__ (self, f):
        return self.is_equal (f)

    def __ne__ (self, f):
        return not (self.is_equal (f))

    def get_assignments(self, assignments=None):
        """Return a generator over the truth assignments to this formula."""

        # each predicate will have its own assignments
        # so the idea is to get at each predicate
        pass

    def dump(self):
        """Informative string representation."""

        return str(self)


class Xor(Formula):
    """These come from the initial state
    (unknown(foo ?a ?b)) -->
    Xor(Primitive(foo_a_b), Not(Primitive(foo_a_b )))
    """

    def __init__(self, args):
        """
            Inputs:
                args:    list of formula objects
        """

        super(Xor, self).__init__("xor", args)

    def __eq__ (self, f):
        return self.is_equal (f)

    def __ne__ (self, f):
        return not (self == f)

    def __str__(self):
        """
            String representation for easier debugging.
        """

        return "Xor(%s)" % ", ".join([str(arg) for arg in self.args])

    def dump(self):
        """Informative string representation."""

        return str(self)


class Not(Formula):
    """
        Attributes:
            args: one-item list of Formula objects
    """

    def __init__(self, args):
        """
            Inputs:
                args:    list of formula objects
        """

        super(Not, self).__init__("not", args)
        assert len(args) == 1, \
              "Not args must be a list with only one element, \
              got %s" % str (args)

    def __eq__ (self, f):
        return self.is_equal (f)

    def __ne__ (self, f):
        return not (self.is_equal (f))

    def __str__(self):
        """String representation for easier debugging."""

        return "not(" + str(self.args[0]) + ")"

    def dump(self):
        """Informative string representation."""

        return str(self)


class When(Formula):
    """
        Attributes(in addition to those inherited from Formula):
            condition

            result
    """

    def __init__(self, condition, result):
        """
            Inputs:
                condition:        the precondition(Formula obj.)
                result:            the result(Formula obj.)
        """

        assert isinstance(condition, Formula), \
            "Condition must be a Formula object"
        assert isinstance(result, Formula), \
            "Result must be a Formula object"
        super(When, self).__init__("when", [condition, result])
        self.condition = condition
        self.result = result

    def __eq__ (self, f):
        return self.is_equal (f)

    def __ne__ (self, f):
        return not (self.is_equal (f))

    def __str__(self):
        """
            String representation for easier debugging.
        """

        return "when(%s),(%s)" % (self.condition, self.result)

    def dump(self):
        """Informative string representation."""

        return str(self)


class Oneof(Formula):
    """
        Attributes:
            args:    List of formula objects
    """

    def __init__(self, args):
        """
            Inputs:
                args:    list of formula objects
        """

        super(Oneof, self).__init__("oneof", args)

    def __eq__ (self, f):
        return self.is_equal (f)

    def __ne__ (self, f):
        return not (self.is_equal (f))

    def __str__(self):
        """String representation for easier debugging."""

        return "oneof(%s)" % ", ".join([str(arg) for arg in self.args])

    def dump(self):
        """Informative string representation."""

        return str(self)


class Primitive(Formula):
    """
        Attributes:
            args: empty list

            predicate: of the Predicate class
    """

    def __init__(self, predicate):
        """
            Inputs:
                predicate:        Predicate object
        """

        assert isinstance(predicate, Predicate),\
            "First argument must be of Predicate class"
        super(Primitive, self).__init__("Primitive", [])
        self.predicate = predicate

    def to_ground (self, fluent_dict):
        """Doesn't actually ground, just forces the Primitive
        to accept that it is *already* ground.

        fluent_dict allows referencing to existing fluents to save space
        """

        self.predicate.ground_args = self.predicate.args
        self.predicate.args = None
        if hash (self.predicate) not in fluent_dict:
            for p in sorted (fluent_dict.values()):
                print (p)
            print ("Did not find %s" % str(self.predicate))
        self.predicate = fluent_dict[hash(self.predicate)]

    def __eq__ (self, f):
        return isinstance (f, Primitive) and \
                self.predicate == f.predicate

    def __ne__ (self, f):
        return not (self == f)

    def __str__(self):
        """
            String representation for easier debugging
        """

        return str(self.predicate)

    def __repr__ (self):
        return "Primitive " + str(self)

    def export (self, lvl, sp, untyped, grounding={}):
        """Return PDDL representation of this primitive."""

        return self.predicate.export (lvl, sp, untyped, grounding)

    def dump(self):
        """Informative string representation."""

        return str(self)
