"""This module contain the common function can be used to parse the PDDL file"""
# -----------------------------Authorship-----------------------------------------
# -- Authors  : YD
# -- Group    : Planning Visualisation
# -- Date     : 13/Oct/2018
# -- Version  : 1.0
# --------------------------------------------------------------------------------
# -----------------------------Reviewer-------------------------------------------
# -- Authors  : Sharukh, Gang chen
# -- Group    : Planning Visualisation
# -- Date     : 16/Oct/2018
# -- Version  : 1.0
# --------------------------------------------------------------------------------
import re


def parse_objects(text):
    """
    This function is used to get a list of objects from bracket. (obj1 obj2 obj3)
    :param text: text contain objects in format (obj1 obj2 obj3)
    :return: an array of objects
    """
    text = remove_bracket(text)
    text = re.sub(r'\s+-\s*\w+|-\s+\w+', ' ', text)
    objects = re.split(r'\s+', text)
    result = []
    for object in objects:
        if ":" not in object and len(object) != 0:
            result.append(object)
    return result


def get_one_block(input):
    """
    This function is used to get one block of text by remove the first "(", and try to find the close
    bracket.
    :param input: whole text file
    :return: one block of text
    """
    output = ""
    forward_bracket = 0;
    for n in range(len(input)):
        if input[n] == "(":
            forward_bracket += 1

        if input[n] == ")":
            forward_bracket -= 1

        if forward_bracket >= 0:
            output += input[n]
        else:
            break;
    return output


def find_parens(text_block, depth=1):
    """
    This function is going to return the index of the start "(" and close ")" at certain depth.
    For example,((a)(b)) will return {0:7} if depth=1 and {1:3,4:6} if depth =2
    :param text_block: text contain bracket
    :param depth: which level of bracket are you intersted in
    :return: dictionary contain the start and end index of bracket.
    """
    toret = {}
    pstack = []

    for i, token in enumerate(text_block):
        if token == '(':
            pstack.append(i)

        elif token == ')':
            if len(pstack) == 0:
                raise IndexError("No matching closing parens at: " + str(i))
            if len(pstack) == depth:
                toret[pstack.pop()] = i
            else:
                pstack.pop()

    if len(pstack) > 0:
        raise IndexError("No matching opening parens at: " + str(pstack.pop()))

    return toret


def get_bracket(text, depth):
    """
    This function return all the text block in a certain depth.
    :param text: text contain bracket
    :param depth:  which level of bracket are you intersted in
    :return: return array of text block
    """
    ruleindex = find_parens(text, depth)
    rules = []
    for start, end in ruleindex.items():
        rules.append(text[start:end + 1])
    return rules


def remove_bracket(text):
    """
    This function remove the first and last bracket of the text
    :param text: text start with "(" and end with "?"
    :return: return text content between the "(" and ")"
    """
    return text[1:len(text) - 1]


def comment_filter(text):
    lines = []
    for l in text.split('\n'):
        loc = l.find(';')
        if loc == -1:
            lines.append(l)
        elif loc > 0:
            lines.append(l[:loc])
    return '\n'.join(lines)
