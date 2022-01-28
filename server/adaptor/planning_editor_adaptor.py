import parser_functions
from action_plan_parser.parser import Problem
import copy
import json
TEMPLATE={
    "status":"ok",
    "result":{
        "output":"Todo",
        "parse_status": "ok",
        "type": "full",
         "length": 0,
         "plan":[],
         "planPath":"Todo",
         "logPath":"Todo"
    }


}

def get_plan_from_actions(domain_file, actions):
    domain=Problem(domain_file)
    plan = []
    act_map = {}
    for a in domain.actions:
        act_map[a.name] = a
    text_blocks = parser_functions.get_bracket(actions, 1)
    print(text_blocks)
    for act_line in text_blocks:
        print(act_line)
        while ' )' == act_line[-2:]:
            act_line = act_line[:-2] + '  )'
        act_line = act_line.rstrip('\r\n')
        a_name = act_line[1:-1].split(' ')[0]
        if len(act_line.split(' ')) > 1:
            a_params = act_line[1:-1].split(' ')[1:]
        else:
            a_params = False
        a = act_map[a_name]
        plan.append({'name': act_line, 'action': a.export(grounding=a_params)})

    result = copy.deepcopy(TEMPLATE)
    result["result"]["length"]=len(text_blocks)
    result["result"]["plan"]=plan

    return result


# domain_content=open("domain.pddl", 'r',encoding='utf-8-sig').read().lower()
# actions=open("plan.txt", 'r',encoding='utf-8-sig').read().lower()
# result=get_plan_from_actions(domain_content,actions)

def get_data():
    domain_content=open("domain.pddl", 'r',encoding='utf-8-sig').read().lower()
    actions=open("plan.txt", 'r',encoding='utf-8-sig').read().lower()
    # result=json.dumps(get_plan_from_actions(domain_content,actions))
    result=json.dumps(get_plan_from_actions(domain_content,actions))
    
    return result