from parser import Problem
from action import Action
from formula import Primitive, Forall, When, And
from predicate import Predicate
import itertools


class GroundProblem(Problem):
    """
    Inherits from Problem.
    Houses the basic data structures for a contingent planning problem that has 
    been grounded. It will contain all of the attributes and functionality of the 
    parent class, Problem.

    Inputs:
        domain_file     location of domain PDDL on disk

        problem_file    location of problem PDDL on disk

        no_ground       if the problem is already ground, don't ground again

    Attributes:
       (in addition to those inherited from Problem)

        fluents:        set of ground Predicate objects for the problem

        operators:      set of Operator objects

    Methods:
        none
    """

    def __init__(self, domain_file, problem_file, no_ground=False):
        """Create a new instance of GroundProblem.
        Inputs:
            domain_file:    The location of the PDDL domain on disk

            problem_file:   The location of the PDDL problem on disk

            no_ground:      Whether to ground the PDDL or not
                            Set to True if PDDL already grounded

        """


        super(GroundProblem, self).__init__(domain_file, problem_file)

        if no_ground:
            # create fluents
            self.fluents = set([])
            fluent_dict = {}
            for p in self.predicates:
                f = Predicate (p.name, None, p.args)
                fluent_dict [hash (f)] = f
                self.fluents.add (f)

            # create operators by changing all the formulas
            self.operators = set([])
            for a in self.actions:
                # parameters stay the same
                param = a.parameters
                if a.precondition is None:
                    precond = None
                else:
                    a.precondition.to_ground (fluent_dict)
                    precond = a.precondition

                if a.effect is None:
                    effect = None
                else:
                    a.effect.to_ground (fluent_dict)
                    effect = a.effect

                if a.observe is None:
                    observe = None
                else:
                    p = Predicate (a.observe.name, None, a.observe.args)
                    observe = fluent_dict[hash (p)]
                op = Operator (a.name, param, precond, observe, effect)
                self.operators.add (op)

            self.init.to_ground (fluent_dict)
        else:
            self._ground()

    @property
    def initial_states(self):
        """Generate the possible initial states, as truth assignments to fluents.
        Return a dictionary mapping fluent names to truth assignments.
        """

        return self.init.get_assignments ()

    def is_equal (self, p):
        """Return True iff this ground problem is equivalent to given ground problem.
        Here, we don't care about underlying lifted representation."""

        assert isinstance (p, GroundProblem), "Must compare two ground problems"

        if self.objects != p.objects:
            print "objects"
            return False

        if self.init != p.init:
            return False

        if self.goal != p.goal:
            print "goal"
            return False

        if not all ([sa == pa for sa, pa in \
                zip (sorted (list (self.operators)), \
                sorted (list (p.operators)))]):
            print "operators"
            return False

        if not all ([sp == pp for sp, pp in \
                zip (sorted (list (self.fluents)), \
                sorted (list (p.fluents)))]):
            print "fluents"
            print "*self*"
            print sorted( list( self.fluents))
            print "*p*"
            print sorted (list( p.fluents))
            return False

        if self.types != p.types or self.parent_types != p.parent_types:
            print "types"
            return False
        
        return True


    def _export_domain (self, fp, sp="  "):
        """Write domain PDDL to given file."""

        fp.write("(define" + "\n")

        # domain name
        fp.write (sp)
        fp.write ("(domain %s)%s" % (self.domain_name, "\n"))

        # requirements
        if len (self.types) > 1 or list(self.types)[0] != Predicate.OBJECT:
            fp.write (sp + "(:requirements :strips :typing)\n")
        else:
            fp.write (sp + "(:requirements :strips)\n")

        # types
        #TODO likely wrong, doesn't capture the type hierarchy
        s = " ".join (filter(lambda t: t!= Predicate.OBJECT, self.types))
        fp.write (sp + "(:types %s)%s" %(s, "\n"))

        # fluents (ground predicates)
        fp.write (sp + "(:predicates " + "\n")
        for fluent in self.fluents:
            fp.write (fluent.export (2, sp) + "\n")
        fp.write (sp + ")" + "\n")

        # operators
        for op in self.operators:
            fp.write (op.export (1, sp) + "\n")

        fp.write (")") # close define

    def export(self, f_domain, f_problem):
        """Write out the problem in PDDL.
        Export operators instead of actions.
        Export fluents instead of predicates."""

        sp = "    "
        fp = open(f_domain, "w")
        self._export_domain (fp, sp)
        fp.close()

        if self.init is not None:
            fp = open (f_problem, "w")
            # _export_problem is same as parent's since init is overwritten
            self._export_problem (fp, sp)
            fp.close ()

    def _create_param_dict(self, params):
        """
        Input:
            params:     list of tuples, where the first item is the parameter name,
                        and the second is the parameter type

        Returns:
            A dictionary mapping parameter names to a set of possible objects.
        """

        d = {}

        for param_name, param_type in params:
            if param_type in self.type_to_obj:
                d[param_name] = self.type_to_obj[param_type]
            elif Predicate.OBJECT == param_type:
                d[param_name] = self.objects.copy()
            else:
                # for debugging
                s = "Found a type in the list of parameters that is not in the type_to_obj dict \n"
                s += "param_type = %s\n" % str(param_type)
                s += "type_to_obj = %s" % str(self.type_to_obj)
                raise KeyError(s)

        return d

    def _get_unassigned_vars(self, formula, assigned):
        """Augment the dictionary in assigned with unassigned vars"""

        #if isinstance(formula, Forall):
        #    try:
        #        for v, t in formula.params:
        #            assigned[(v, hash(formula))] = self.type_to_obj[t]
        #    except KeyError as e:
        #        raise KeyError("Cannot get unassigned vars list due to bad parsing of forall object: %s" % str(formula))
        #elif isinstance(formula, Primitive):
        if isinstance(formula, Primitive):
            for v, t in formula.predicate.args:
                if v.startswith("?") and v not in assigned:
                    raise KeyError("Found unbound variable %s in predicate %s" % v, str(formula.predicate))
        else:
            [self._get_unassigned_vars(arg, assigned) for arg in formula.args]

    def _create_valuations(self, params, action=None):
        """
        Input:
            params            list of tuples, where the first item is the parameter name, and the second is the parameter type

        Returns:
            param_names        list of variable names, corresponding to order that will be returned by generator
            val_gen            generator of possible valuations
        """

        d = self._create_param_dict(params)
        
        #if action is not None and action.effect is not None:
            # query the effect for any forall conditionals
            #self._get_unassigned_vars(action.effect, d)

        param_names = list(d.keys())
        possible_values = [d[name] for name in param_names]
        return param_names, itertools.product(*possible_values)

    def _predicate_to_fluent(self, predicate, assignment, fluent_dict={}):
        """
        Inputs:
            predicate            The predicate to be converted
            assignment            a dictionary mapping each possible variable name to an object

        Returns:
            A fluent that has the particular valuation for the variables as given in input. The old predicate is *untouched*
        """

        if predicate is None:
            return None

        fluent_args = []
        for var_name, var_type in predicate.args:
            if var_name in assignment:
                fluent_args.append((assignment[var_name], var_type))
            elif not var_name.startswith("?"):
                # will assume these are already ground
                fluent_args.append((var_name, var_type))
            else:
                raise KeyError("Unknown variable %s in predicate %s" % (var_name, str(predicate)))

        fluent = Predicate(predicate.name, args=None, ground_args=fluent_args)

        if hash (fluent) in fluent_dict:
            return fluent_dict[hash (fluent)]
        else:
            return fluent

    def _partial_ground_formula(self, formula, assignment, fluent_dict):
        """
        Inputs:
            formula            The formula to be converted
            assignment        a dictionary mapping each possible variable name to an object

        Returns:
            A formula that has the particular valuation for the variables as given in input. The old formula is *untouched*
        """

        if formula is None:
            return None

        if isinstance(formula, Primitive):
            return Primitive(self._predicate_to_fluent(formula.predicate, assignment, fluent_dict))
        elif isinstance(formula, Forall):
            
            new_conjuncts = []
            var_names, val_generator = self._create_valuations(formula.params)
            for valuation in val_generator:
                new_assignment = {var_name: val for var_name, val in zip(var_names, valuation)}
                for k in assignment:
                    new_assignment[k] = assignment[k]
                new_conjuncts.append(self._partial_ground_formula(formula.args[0], new_assignment, fluent_dict))
            return And(new_conjuncts)
            
        elif isinstance(formula, When):
            return When(self._partial_ground_formula(formula.condition, assignment, fluent_dict),
                        self._partial_ground_formula(formula.result, assignment, fluent_dict))
        else:
            return type(formula)([self._partial_ground_formula(arg, assignment, fluent_dict) for arg in formula.args])

    def _action_to_operator(self, action, assignment, fluent_dict):
        """
        Inputs:
            action            The action to be converted
            assignment        a dictionary mapping each possible variable name to an object
            fluent_dict        a dictionary mapping fluent names to fluent objects

        Returns:
            An operator that has the particular valuation for the variables as given in input.
        """

        #TODO this naming convention fails when there are no parameters but a forall in the effect
        op_name = action.name + "_" + "_".join([assignment[var_name] for var_name, _ in action.parameters])
        op_params = [(assignment[var_name], t) for var_name, t in action.parameters]
        op_precond = self._partial_ground_formula(action.precondition, assignment, fluent_dict)
        op_observe = self._predicate_to_fluent(action.observe, assignment, fluent_dict)
        op_effect = self._partial_ground_formula(action.effect, assignment, fluent_dict)
        return Operator(op_name, op_params, op_precond, op_observe, op_effect)

    def _create_operators(self, fluent_dict):
        """Create the set of operators by grounding the actions."""

        self.operators = set([])

        for a in self.actions:
            
            var_names, val_generator = self._create_valuations(a.parameters, a)

            for valuation in val_generator:
                assignment = {var_name: val for var_name, val in zip(var_names, valuation)}
                self.operators.add(self._action_to_operator(a, assignment, fluent_dict))

    def _create_fluents(self):
        """Create the set of fluents by grounding the predicates."""

        self.fluents = set([])
        for p in self.predicates:
            var_names, val_generator = self._create_valuations(p.args)
            for valuation in val_generator:
                assignment = {var_name: val for var_name, val in zip(var_names, valuation)}
                self.fluents.add(self._predicate_to_fluent(p, assignment))

    def _get_unground_vars(self, formula, d):
        """
        Inputs:
            formula        The formula
            d            The dictionary mapping a tuple(variable name, formula hash) --> type
        Returns:
            nothing
        Mutates:
            d            The dictionary mapping a tuple(variable name, formula hash) --> type
        """

        if isinstance(formula, Forall):
            d[(formula.v, hash(formula))] = d.t
            [self._get_unground_vars(arg, d) for arg in formula.args]
        elif isinstance(formula, When):
            [self._get_unground_vars(c, d) for c in[formula.condition, formula.result]]
        elif isinstance(formula, Primitive):
            for v, t in formula.predicate.args:
                d[(v, hash(formula))] = t
        else:
            [self._get_unground_vars(arg, d) for arg in formula.args]

    def _ground_init(self, fluent_dict):
        """Ground the initial state."""

        d = {}
        #self._get_unground_vars(self.init, d)
        self.init = self._partial_ground_formula(self.init, d, fluent_dict)

    def _ground(self):
        """Convert this problem into a ground problem."""

        self._create_fluents()

        # to avoid creating a bunch new fluent objects, create a dictionary mapping fluent names to their objects
        fluent_dict = {hash(f): f for f in self.fluents}
        self._create_operators(fluent_dict)
        self._ground_init(fluent_dict)

    def __repr__(self):
        """Similar to dump and __str__."""

        return str(self)

    def __str__(self):
        return "Ground problem %s" % self.problem_name

    def dump(self):
        """For verbose printing
        Key results here are the operators and fluents. The rest are as before, I think"""

        d = {
            "Initial State": self.init,
            "Operators": self.operators,
            "Fluents": self.fluents
        }

        for k, v in d.iteritems():
            print "*** %s ***" % k
            if k == "Operators":
                for op in self.operators:
                    op.dump(lvl=1)  # inherited from superclass Action
            elif hasattr(v, "__iter__"):
                for item in v:
                    print "\t" + str(item)
            else:
                print "\t" + str(v)


class Operator(Action):
    """
    Inherits from Action.

    Data structure to contain ground action from the problem.

    Attributes:
        The attributes should be exactly the same as for an Action object, with 
        the exception that every instance of a Predicate object is actually a 
        Fluent object (i.e., everything is assumed to be ground).

    Methods:
        none
    """

    def __init__(self, name, parameters, precondition, observe, effect):
        """Create a new Operator.

        Inputs:
            name:           The name of the operator

            parameters:     A list of tuples
                            First item is the parameter name
                            Second item is the parameter type

            precondition:   A ground formula for the precondition

            observe:        A ground predicate for the observed fluent

            effect:         A ground formula for the effect
        """

        super(Operator, self).__init__\
            (name, parameters, precondition, observe, effect)

    def __str__(self):
        return super(Operator, self).__str__().replace("action", "operator")\
            .replace("Action", "Operator")

    def __repr__(self):
        return super(Operator, self).__repr__().replace("action", "operator")\
            .replace("Action", "Operator")

    def dump(self, lvl=0):
        """ Verbose string representation for debugging
        Inputs:
            lvl:    Tab level
        """

        # for operators, sufficient just to print the name, because pretty self-explanatory
        print "\t" * lvl + "Operator %s" % self.name
        if len(self.parameters) > 0:
            print "\t" * (lvl + 1) + "Parameters: " + \
                ", ".join([v_type + " " + v_name for v_name, v_type in self.parameters])
        else:
            print "\t" * (lvl + 1) + "Parameters: <none>"
            #print(lvl + 1) * "\t" + "Precondition: " + str(self.precondition)
        #print(lvl + 1) * "\t" + "Effect: " + str(self.effect)
        #print(lvl + 1) * "\t" + "Observe: " + str(self.observe)
