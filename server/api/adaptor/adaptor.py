import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from planning_editor_adaptor.adaptor import PlanningEditorAdaptor

class Adaptor:
    def __init__(self):
        self._adaptors={}
        self.register_adaptor("planning_editor_adaptor",PlanningEditorAdaptor)

    def register_adaptor(self,adaptor_name,adaptor):
        self._adaptors[adaptor_name]=adaptor

    def get_result(self, adaptor_name, **data):
        adaptor=self._adaptors.get(adaptor_name)
        if not adaptor:
            raise ValueError(adaptor_name)
        return adaptor().transform(**data)



