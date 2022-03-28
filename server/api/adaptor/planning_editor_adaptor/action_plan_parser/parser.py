import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../' + "action_plan_parser"))

from collections import OrderedDict
from formula import Formula, And, Primitive, Forall, When, Xor, Not, Oneof, Or
from action import Action
from predicate import Predicate
from pddl_tree import PDDL_Tree
from utils import PDDL_Utils


class Problem(object):
    """
    A problem instance.

    Attributes:
        domain_name : Name of domain

        problem_name : Name of the problem

        predicates: List of predicate objects

        init: Formula object

        goal: Set of ground Predicate objects

        actions: List of action objects

        types: Set of strings of each object type

        objects: Set of strings that correspond to the objects in the problem

        type_to_obj: Dictionary mapping type strings to the set of objects of that type

        obj_to_type: Dictionary mapping object strings to the set of types for that object

        parent_types: Dictionary mapping types to their parents, or None if no parents exist

    Methods:
        dump:    Detailed printing of object for debugging purposes
        export:  Save this problem into 2 PDDL files
    """

    OBJECT = "default_objec"

    def __init__(self, domain_file, problem_file = None):
        """
        Create a new problem instance.

        Inputs:
            domain_file: The path to the domain file

            problem_file: The path to the problem file
                Allow this to be None during testing
        """

        # this is common to domain and problem file
        self.objects = set([])
        self.obj_to_type = {}
        self.type_to_obj = {}

        # make sure that domain is parsed before the problem
        self._parse_domain(domain_file)

        if problem_file is None:
            self.init = None
            self.goal = None
            self.objects = None
        else:
            self._parse_problem(problem_file)

    def __eq__ (self, p):
        """Overload the == operator."""

        return self.is_equal (p)

    def __ne__ (self, p):
        """Overload the != operator."""

        return not (self == p)

    def is_equal (self, p):
        """Return True iff this problem is the same as the given problem."""
        assert isinstance (p, Problem), "Must be comparing two of same type"
        if self.objects != p.objects:
            print ("objects")
            return False

        if self.init != p.init:
            #print "init"
            #print "*self*"
            #print self.init
            #print "*p*"
            #print p.init
            return False

        if self.goal != p.goal:
            print ("goal")
            return False

        if not all ([sa == pa for sa, pa in zip (self.actions, p.actions)]):
            print ("actions")
            return False

        if not all ([sp == pp for sp, pp in zip (self.predicates, p.predicates)]):
            print ("predicates")
            return False

        if self.types != p.types or self.parent_types != p.parent_types:
            print ("types")
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

        # predicates
        fp.write (sp + "(:predicates " + "\n")
        for p in self.predicates:
            fp.write (p.export (2, sp) + "\n")
        fp.write (sp + ")" + "\n")

        # actions
        for action in self.actions:
            fp.write (action.export (1, sp) + "\n")

        fp.write (")") # close define

    def _export_problem (self, fp, sp="  "):
        """Write the problem PDDL to given file."""

        fp.write ("(define" + "\n")

        fp.write (sp + "(problem %s)%s" % (self.problem_name, "\n"))
        fp.write (sp + "(:domain %s)%s" % (self.domain_name, "\n"))

        # objects
        o = []
        o.append (sp + "(:objects")
        for obj in self.objects:
            if self.obj_to_type[obj] == Predicate.OBJECT:
                o.append (sp + sp + obj)
            else:
                #TODO may not be correct
                t = list (self.obj_to_type [obj]) [0]
                o.append (sp + sp + "%s - %s" % (obj, t))
        o.append (sp + ")")
        fp.write ("\n".join(o) + "\n")

        # init
        o = []
        o.append (sp + "(:init")
        for f in self.init.args:
            o.append (f.export (2, sp, True))
        o.append (sp + ")") # close init
        fp.write ("\n".join(o) + "\n")

        # goal
        o = []
        o.append (sp + "(:goal")
        for p in self.goal.args:
            o.append (p.export (2, sp, True))
        o.append (sp + ")") # close goal
        fp.write ("\n".join (o) + "\n")

        fp.write (")") # close define

    def export(self, f_domain, f_problem):
        """Write out the problem in PDDL."""

        # write domain file
        sp = "    "
        fp = open(f_domain, "w")
        self._export_domain (fp, sp)
        fp.close()

        if self.init is not None:
            fp = open (f_problem, "w")
            self._export_problem (fp, sp)
            fp.close ()

    def __str__(self):
        return "Problem %s from domain %s" % (self.problem_name, self.domain_name)

    def __repr__(self):
        return str(self)

    def dump(self):
        """Print in detail about this problem"""

        d = OrderedDict()
        d["Predicates"] = self.predicates
        d["Initial State"] = self.init
        d["Goal State"] = self.goal
        d["Actions"] = self.actions
        #d["Types"] = self.types
        d["Parent Types"] = self.parent_types
        #d["Objects"] = self.objects
        d["Obj -> Type Mapping"] = self.obj_to_type
        #d["Type -> Obj Mapping"] = self.type_to_obj

        for k, v in d.iteritems():
            print ("*** %s ***" % k)
            if isinstance(v, dict):
                if len(v) == 0:
                    print ("\t<no items>")
                for k, val in v.iteritems():
                    print ("\t%s -> %s" % (k, str(val)))
            elif hasattr(v, '__iter__'):
                if len(v) == 0:
                    print ("\tNone")
                elif k == "Actions":
                    for action in self.actions:
                        action.dump(lvl=1)
                else:
                    print ("\t" + "\n\t".join([str(item) for item in v]))
            else:
                print ("\t" + str(v))
            print ("")

    def _parse_domain(self, f_domain):
        """
        Extract information from the domain file.

        The following will be extracted:
            * types
            * predicates
            * actions
        """

        parse_tree = PDDL_Tree.create(f_domain)

        assert "domain" in parse_tree, "Domain must have a name"
        self.domain_name = parse_tree ["domain"].named_children ()[0]

        # must read types before constants
        if ":types" in parse_tree:
            if "-" in parse_tree[":types"].named_children():
                type_hierarchy = PDDL_Utils.read_type(parse_tree[":types"])
                self.parent_types = {subtype: parent for subtype, parent in type_hierarchy}
                self.types = set(parse_tree[":types"].named_children())
                self.types.discard("-")
            else:
                self.types = set(parse_tree[":types"].named_children())
                self.parent_types = {t: None for t in self.types}
        else:
            self.types = set([Predicate.OBJECT])
            self.parent_types = {Predicate.OBJECT: None}

        # must read in constants before actions or predicates
        if ":constants" in parse_tree:
            object_list = PDDL_Utils.read_type(parse_tree[":constants"])
            self._add_objects(object_list)

        #TODO this may not be correct, depending on the type hierchy
        const_map = {const: list(self.obj_to_type[const])[0] for const in self.objects}

        self.predicates = [self.to_predicate(c, map=const_map) for c in parse_tree[":predicates"].children]

        # some predicates have this property: they are untyped.
        for predicate in self.predicates:
            if Predicate.OBJECT not in self.types and any([arg[1] == Predicate.OBJECT for arg in predicate.args]):
                for t in self.types:
                    if self.parent_types[t] is None:
                        self.parent_types[t] = Predicate.OBJECT

                self.parent_types[Predicate.OBJECT] = None
                self.types.add(Predicate.OBJECT)
                self.type_to_obj[Predicate.OBJECT] = set([])
                for obj, type_list in self.obj_to_type.iteritems():
                    type_list.add(Predicate.OBJECT)
                    self.type_to_obj[Predicate.OBJECT].add(obj)

                # only need to do this once, obviously
                break

        self.actions = [self.to_action(c) for c in parse_tree.find_all(":action")]

    def _get_supertypes(self, t, d):
        """Find all the supertypes of t and add them to d.
           Do the same on all the supertypes as well."""

        # get the supertype of t
        if self.parent_types[t] is None:
            d[t] = set([])
        else:
            parent = self.parent_types[t]
            self._get_supertypes(parent, d)
            d[t] = d[parent].union(set([parent]))

    def _add_objects(self, object_list):
        """Add the objects to the object set.
        Input:
            object_list:
                a list of tuples, where the first element is the object name and the second is the object type.
        Returns:
            nothing
        Mutates:
            self.objects
            self.obj_to_type
            self.type_to_obj
        """

        object_types = set([t for _, t in object_list])
        if not object_types.issubset(self.types):
            # for debugging
            s = "The types found in the problem file must be a subset of the types listed in the domain file\n"
            s += "Domain types: %s" % str(self.types) + "\n"
            s += "Problem types: %s" % str(object_types)
            raise ValueError(s)

        for obj, t in object_list:
            self.objects.add(obj)

            if t not in self.type_to_obj:
                self.type_to_obj[t] = set([])
            self.type_to_obj[t].add(obj)

            self.obj_to_type[obj] = set([])
            k = t
            while k in self.parent_types:
                self.obj_to_type[obj].add(k)
                k = self.parent_types[k]

    def _parse_problem(self, f_problem):
        """
        Extract information from the problem file.

        The following will be extracted:
            * problem name
            * objects
            * initial state
            * goal state
            * type_to_obj
            * obj_to_type
        """

        parse_tree = PDDL_Tree.create(f_problem)

        assert "problem" in parse_tree, "Problem must have a name"
        self.problem_name = parse_tree ["problem"].named_children ()[0]

        # objects must be parsed first
        if ":objects" in parse_tree:
            object_list = PDDL_Utils.read_type(parse_tree[":objects"])
            self._add_objects(object_list)

        #TODO this may not be valid with a non-flat type hierchy
        obj_map = {obj: list(self.obj_to_type[obj])[0] for obj in self.objects}

        # the goal can be expressed in either a formula form, or a direct form
        if len(parse_tree[":goal"].children) == 1 and parse_tree[":goal"].children[0].name == "and":
            self.goal = And([Primitive(self.to_fluents(c)) for c in parse_tree[":goal"].children[0].children])
        else:
            self.goal = And([Primitive(self.to_fluents(c)) for c in parse_tree[":goal"].children])

        # it is critical that the formula here be checked against the objects
        if len(parse_tree[":init"].children) == 1 and \
                parse_tree[":init"].children[0].name == "and":
            self.init = self.to_formula(parse_tree[":init"].children[0], obj_map)
        else:
            # initial condition is one big AND
            self.init = And([self.to_formula(c, obj_map) for c in parse_tree[":init"].children])

    def to_action(self, node):
        """
            Create an action out of this PDDL_Tree node.
            For now, will assume this makes sense.
        """

        name = node.children[0].name
        parameter_map = {}

        if ":parameters" in node:
            params = PDDL_Utils.read_type(node[":parameters"])
            parameter_map = {p[0]: p[1] for p in params}  # map of variable-names to types
        else:
            params = []

        if ":precondition" in node:
            assert len(node[":precondition"].children) == 1,\
                "precondition should have one top-level child"
            precond = self.to_formula(node[":precondition"].children[0], parameter_map)
        else:
            precond = None

        if ":observe" in node:
            assert len(node[":observe"].children) == 1,\
                "observe should have one top-level child"
            observe = self.to_predicate(node[":observe"].children[0], map=parameter_map)
        else:
            observe = None

        if ":effect" in node:
            assert len(node[":effect"].children) == 1,\
                "effect should have one top-level child"
            effect = self.to_formula(node[":effect"].children[0], parameter_map)
        else:
            effect = None

        return Action(name, params, precond, observe, effect)

    def to_predicate(self, node, f='predicate', map=None):
        """
            Create a predicate out of this PDDL_Tree node.
            For now, will assume this makes sense.
        """

        args = PDDL_Utils.read_type(node)

        # change the type if there is only 1 type
        if len (self.types) == 1:
            t_args = args
            t = list (self.types) [0]
            args = []
            for arg in t_args:
                if arg[1] != t:
                    args.append ( (arg[0], t) )
                else:
                    args.append (arg)

        # here is where the map comes in...
        if map is None:
            if 'predicate' == f:
                return Predicate(node.name, args)
            elif 'fluent' == f:
                return Predicate(node.name, args=None, ground_args=args)
        else:
            new_args = []
            for v, t in args:
                if v in map:
                    new_args.append((v, map[v]))
                else:
                    new_args.append((v, t))

            if 'predicate' == f:
                return Predicate(node.name, new_args)
            elif 'fluent' == f:
                return Predicate(node.name, args=None, ground_args=new_args)

    def to_fluents(self, node):
        """
            Return a list of fluents out of this PDDL_Tree node.
            For now, will assume this makes sense.
        """

        # same call as predicate, except cast to fluent
        return self.to_predicate(node, 'fluent')

    def to_formula(self, node, parameter_map=None):
        """
            Return a formula out of this PDDL_Tree node.
            For now, will assume this makes sense.
        """

        # forall is so weird that we can treat it as an entirely seperate entity
        if "forall" == node.name:
            # treat args differently in this case
            assert len(node.children) in[2, 4],\
                "Forall must have a variable(typed or untyped) and formula that it quantifies"
            i = len(node.children) - 1

            if len(node.children) == 2 and len(node.children[0].children) > 0:
                # adjust this node by changing the structure of the first child
                new_child = PDDL_Tree(PDDL_Tree.EMPTY)
                new_child.add_child(PDDL_Tree(node.children[0].name))

                for c in node.children[0].children:
                    new_child.add_child(c)
                node.children[0] = new_child
                l = PDDL_Utils.read_type(new_child)

            for v, t in l:
                parameter_map[v] = t
            args = [self.to_formula(c, parameter_map) for c in node.children[i:]]
            for v, t in l:
                del(parameter_map[v])
            return Forall(l, args)

        i = 0
        args = [self.to_formula(c, parameter_map) for c in node.children[i:]]

        if "and" == node.name:
            return And(args)
        elif "or" == node.name:
            return Or(args)
        elif "oneof" == node.name:
            return Oneof(args)
        elif "not" == node.name:
            return Not(args)
        elif "xor" == node.name:
            return Xor(args)
        elif "nondet" == node.name:
            assert len(node.children) == 1,\
                                       "nondet must only have a single child as a predicate"
            # make p != p2, otherwise might run into issues with mutation in some later step
            return Oneof([args[0], Not(args)])
        elif "unknown" == node.name:
            assert len(node.children) == 1,\
                "unknown must only have a single child as a predicate"
            # make p != p2, otherwise might run into issues with mutation in some later step
            p = Primitive(self.to_predicate(node.children[0], map=parameter_map))
            p2 = Primitive(self.to_predicate(node.children[0], map=parameter_map))
            return Xor([p, Not([p2])])
        elif "when" == node.name:
            assert len(args) == 2,\
                "When clause must have exactly 2 children"
            return When(args[0], args[1])
        else:
            # it's a predicate
            return Primitive(self.to_predicate(node, map=parameter_map))
