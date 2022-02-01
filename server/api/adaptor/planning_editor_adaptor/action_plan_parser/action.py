from formula import Formula
from predicate import Predicate

class Action (object):
    """
        Data structure to contain a lifted action provided in the domain file.

        Attributes:
            name: the action name (string)

            parameters: list of tuples that contain a pair of strings:
                1) the variable name
                2) the variable type

            precondition: formula object

            observe: predicate object (or None if the action is not a sensing action)

            effect: formula object

        Methods:
            none
    """

    def __init__ (self, name, parameters, precondition, observe, effect):
        """
            Create a new action.

            Inputs:
                name: the action name (string)

                parameters: list of tuples that contain a pair of strings:
                    1) the variable name
                    2) the variable type

                precondition: formula object
                    #TODO some actions have no precondition, set this to None

                observe: predicate object (or None if the action is not a sensing action)

                effect: formula object
                    #TODO some actions have no effects, set this to None
        """

        assert isinstance (name, str), "name must be a string"
        assert isinstance (parameters, list) and all([isinstance (param, tuple) for param in parameters]), "parameters must be a list of tuples"
        assert isinstance (precondition, Formula) or precondition is None, "precondition must be a Formula object"
        assert isinstance (observe, Predicate) or observe is None, "observe must be a Predicate object or None"
        assert isinstance (effect, Formula) or effect is None, "effect must be a Formula object or None"

        self.name = name
        self.parameters = parameters
        self.precondition = precondition
        self.observe = observe
        self.effect = effect

    def _hash_string (self):
        return self.name + "_" + \
                "_".join([p[0] + "_" + p[1] for p in self.parameters])

    def __hash__ (self):
        return hash (self._hash_string ())

    def __cmp__ (self, a):
        return cmp (self._hash_string (), a._hash_string())

    def __eq__ (self, a):
        return self.is_equal (a)

    def __ne__ (self, a):
        return not (self == a)

    def is_equal (self, a):
        """True iff actions are equal.
        They are equal if the name, precondition, parameters, observe and effects are all equal."""

        return self.name == a.name and \
                all ([sp == ap for sp, ap in zip (self.parameters, a.parameters)]) and \
                self.precondition == a.precondition and \
                self.observe == a.observe and \
                self.effect == a.effect

    def __str__ (self):
        """ String representation for easier debugging """

        #for now, only show name and parameters
        return "action %s (%s)" % (self.name, ", ".join([v_type + " " + v_name for v_name, v_type in self.parameters]))

    def __repr__ (self):
        """Print informative representation."""

        return "Action %s taking parameters %s" % (self.name, ", ".join ([ p for p, t in self.parameters ]))

    def export (self, lvl=1, sp="  ", grounding = False):
        """Print back the action in PDDL form."""

        o = [] # output, which is a list of lines
        param_mapping = {}
        prefix = sp * lvl
        o.append (prefix +  "(:action %s" % self.name)

        if grounding:
            for i in range(len(grounding)):
                param_mapping[self.parameters[i][0]] = grounding[i]
            param_s = " ".join(grounding)
        else:
            if len (self.parameters) > 0 and self.parameters [0][1] != Predicate.OBJECT:
                param_s = " ".join (["%s - %s" % (v, t) for v, t in self.parameters])
            else:
                param_s = " ".join ([v for v, t in self.parameters])

        o.append (prefix + sp + ":parameters (%s)" % param_s)

        if self.precondition is not None:
            o.append (prefix + sp + ":precondition")
            o.append (self.precondition.export (lvl + 2, sp, True, param_mapping))
        if self.effect is not None:
            o.append (prefix + sp + ":effect")
            o.append (self.effect.export (lvl + 2, sp, True, param_mapping))
        if self.observe is not None:
            o.append (prefix + sp + ":observe")
            o.append (self.observe.export (lvl + 2, sp, True))

        o.append (prefix + ")")
        return "\n".join(o)

    def dump (self, lvl=0):
        """ Verbose string representation for debugging
        Inputs:
            lvl:    Tab level
        """

        print ("\t" * lvl + "Action %s" % self.name)
        print ("\t" * (lvl + 1) + "Parameters: " + ", ".join([v_type + " " + v_name for v_name, v_type in self.parameters]))

        print ((lvl + 1) * "\t" + "Precondition: " + str (self.precondition))

        print ((lvl + 1) * "\t" + "Effect: " + str (self.effect))

        print ((lvl + 1) * "\t" + "Observe: " + str(self.observe))
