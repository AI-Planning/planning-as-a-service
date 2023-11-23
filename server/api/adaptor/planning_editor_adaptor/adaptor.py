import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from action_plan_parser.parser import Problem
import copy
import json
import re
import traceback

TEMPLATE={
    "status":"ok",
    "result":{
        "output":"None",
        "parse_status": "ok",
        "type": "full",
         "length": 0,
         "plan":[],
         "planPath":"None",
         "logPath":"None"
    }
}

class PlanningEditorAdaptor:
    def __init__(self):
        pass

    def generate_error_result(self):
        pass

    def generate_result(self,plan,stdout):
        result = copy.deepcopy(TEMPLATE)
        result["result"]["length"]=len(plan)
        result["result"]["plan"]=plan
        result["result"]["output"]=stdout
        return result

    def handle_plan(self,domain_file,actions,stdout,output_type):

            try:
                # Generate one action with the plan text when the output type is 'log'. 
                if output_type=="log":
                    plan=[]
                    plan.append({"name":"Raw Result","action":actions})
                    result=self.generate_result(plan,stdout)
                    return result

                # Parse plan text and generate a plan with list of actions
                else:
                    domain=Problem(domain_file)
                    plan = []
                    act_map = {}
                    for a in domain.actions:
                        act_map[a.name] = a
                    action_list=re.findall(r"(\([a-z\d _-]*\))", actions)

                    for action_str in action_list:
                        elements=[element for element in action_str[1:-1].split(" ") if len(element)>0]
                        a_name=elements[0]
                        if len(elements)>0:
                            a_params=elements[1:]
                        else:
                            a_params=False

                        if a_name in act_map:
                            a = act_map[a_name]
                            plan.append({"name": action_str, "action": a.export(grounding=a_params)})      

                    result=self.generate_result(plan,stdout)
                    
                    return result

            # Then the adaptor could not parse the plan, generate one action with the plan text
            except Exception:
                plan=[]
                plan.append({"name":"Raw Result","action":actions})
                result=self.generate_result(plan,stdout)
                return result

    def transform(self,**kwargs):
        raw_data=kwargs["result"]

        # When the solver could not solve the problem
        if raw_data["stderr"] != '':
            result = copy.deepcopy(TEMPLATE)
            result["status"]="error"
            result["result"]["output"]=""
            result["result"]["error"]= "stderr: \n"+raw_data["stderr"]+"\nstdout: \n"+raw_data["stdout"]    
            result["result"]["parse_status"]="err"
            return result

        else:
            # Orginal arguments data(input data defined in manifest) send to the worker
            arguments=kwargs["arguments"]
            
            # request data send to the check API. 
            # request_data=kwargs["request_data"]

            domain_file=arguments["domain"]["value"]
            
            result={"plans":[],"status":"ok"}
            for plan_name in raw_data["output"]:
                actions=raw_data["output"][plan_name]
                actions=actions.lower()
                parsed_plan=self.handle_plan(domain_file,actions,raw_data["stdout"],raw_data["output_type"])
                result["plans"].append(parsed_plan)
            return result

            




