class Node(dataclass):
    ID: str
    data: dict
    
    def to_json(self):
        pass
    
class Transform:
    """
    Base class for transforms
    Performs defined actions on input and output nodes.
    """
    def _update(self,input_nodes,output_nodes,trafo_node):
        """
        Operation takes all nodes, makes maybe necessary updates
        and returns output nodes
        """
        pass
        return input_nodes, output_nodes, trafo_node
    
    def _pre_actions(self,input_nodes,output_nodes,trafo_node):
        """
        Takes necessary pre actions 
        """
        return input_nodes, output_nodes, trafo_node
    
    def _post_actions(self,input_nodes,output_nodes,trafo_node):
        """
        Takes necessary post actions 
        """
        pass
        return input_nodes, output_nodes, trafo_node
    
    def _perform_actions(self,input_nodes,output_nodes,trafo_node):
        """
        Performs necessary actions 
        """
        pass
        return input_nodes, output_nodes, trafo_node
    

    def __call__(self,self,input_nodes,output_nodes,trafo_node)
        input_nodes, output_nodes, trafo_node = self._pre_actions(input_nodes,output_nodes,trafo_node)
        output = self._perform_actions(input_nodes,output_nodes,trafo_node)
        input_nodes, output_nodes, trafo_node = self._update(input_nodes,output_nodes,trafo_node)
        input_nodes, output_nodes, trafo_node = self._post_actions(input_nodes,output_nodes,trafo_node)
        return output,input_nodes, output_nodes, trafo_node
        


class Transformer(Node):
    
    transform: Transform
    
    def update_node(self,node):
        pass
    
    def __call__(self,input_nodes,output_nodes):
        input_nodes, output_nodes, trafo_node = self.transform(input_nodes, output_nodes, trafo_node)
        return input_nodes, output_nodes, trafo_node


class AgentAction(Transform):
    """
    Special transform that performs an agent action
    """
    def __init__(self,model,pre_prompt={},skill=None,context_graph=None):
        """
        Agent actions depend on a model, a promtp that can be provided, a skill and a context graph.
        """
        pass

class Debate(Transform):
    """
    Special Case of a transform where the transform are agents working together to perform a task.
    """
    def __init__(self,network,judge):
        """
        Is a graph that is build up on transformations, but not necessarily a DAG.
        Judge is an object that tracks the states and outputs of the network and
        decides to stop or continue.
        """
        pass
    
    def check_order(self):
        """
        checks if no transform is neighboured by another transform
        and no node is neighboured by antoerh node
        """

class WorkflowGraph(dataclass):
    """
    Graph that performs the workflow
    """

    ID: str
    network: networkx.DiGraph
    ID_context_graph: str 
    
    def check_dag(self):
        """
        checks if the network is a dag
        """
    
    def check_order(self):
        """
        checks if no transform is neighboured by another transform
        and no node is neighboured by antoerh node. It is allowed
        for the first node (in the topological order) to be transform (empty input) or the
        last one (empty output)
        """
        
    def process_outputs(self,outputs):
        """
        Method to postprocess outputs for workflow
        """
        
    def perform_workflow(self):
        """
        Performs the workflow
        """
        # pseudo code
        order = networkx.topological_order(network)
        transforms = []
        ios = {}
        for src,tar in order:
            if isinstance(src,Transformer):
                if src in transforms:
                    if src in ios.keys():
                        # tar is output node
                        ios[src][1] += [tar]
                elif src not in transforms:
                    # we didn't visit transform so far
                    transforms += [src]
                    ios[src] = [[],[tar]] # set i/o lists 
            else: # tar has to be transform
                if tar in transforms:
                    if tar in ios.keys():
                        # src is intput node
                        ios[tar][0] += [src]
                else:
                    transforms += [tar]
                    ios[tar] = [[src],[]] # set i/o lists 
            
            outputs = []
            for trafo in transforms:
                inp, out = ios[trafo]
                output = trafo(inp,out)
                outputs += [output]
                
            final = self.process_outputs(outputs)
            return final
    
