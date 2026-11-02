# Skill rework

First rework of MIA. 

new dependencies: networkx (on backend) and PostgreSQL for daabase

## Goals

- Usability:
    - Skills should go into their own Window in the web interface
    - An viewer/editor shall be provided

- Skills
    - Provide the data structure properly (proper definition)
    - Context graphs for each skill
    - DB storage (extension to PostgreSQL)
    - Benchmarks
    
## Graphs

### Workflow Datastructure

- Graph is a DAG
- There are 3 types of nodes:
    - Data Nodes (hold data object, dicts or dataclasses)
    - Transform nodes (holds a callable object to Transform the data objects, and data)
    - Master Nodes are transform nodes where the transformation is an agent task with agent(s) that perform the task and an acceptance criterion. Basically it is a harnish with inputs and outputs that has an acceptance criterion, so it could interpreted as a tranform node as well.
- Rules: Between all nodes there has to be a transform (if really necessary use a nil transform that does nothing)
- Metadata of the graph holds
    - ID
    - Associated Context Graph ID
    - Testbench ID
    - Description
    
- Algorithm:
    - topological sorting of DAG.
    - Loop through the edges
    - collect input and outputs belonging to a transform node (we can collect hose as we have demanded that between all normal nodes there has to be a transform)
    - Execute the transform with existing information of all nodes (Input output, transform).
    - Write outputs into the output nodes. Note: Output nodes can hold parameters like a folder where to store things. So there should be a dedicated field.

        
### Context Graph

- It is a more general directed graph
- Each Workflow has a linked context graphs (several workflows can have the same context graph)
- Is updated over time through performed work and reviews.
- It has categories of nodes (data points) and edges (type of relations)
- every elment (nodes, edges) just hold an ID and a JSON entry to allow unstructured data
- The graph has an ID
- Each graph is defined by these categories of nodes and edges and flows what should happen to the data.
- The types are provided as JSON schema (of the jsons we store in the DB)

## DB

To store the data all graph objects are converted to dictionaries and stored as JSON. The Dataobjects must be a able to turned into JSONS. To reconstruct 
which type of data class is used an ID has to be stored as a complex object can't be stored inside a JSON. We could use pickle for example but this depends too
heavily on Python and wouldn't be robut in the long run.
Transforms are collected within a toolbox and have an ID that helps to reconstruct it like the data classes

In DB:
    - Nodes:
        - ID + a JSON field for unstructured data
        - The JSON field holds further information but some are fixed:
            - Type: Node Type
    - edges:
        - ID, start_node_id, end_node_ID, + JSON field for more info
    - Transform nodes nodes, but they have a special role so we define them here, the JSON holds the following extended info:
        - type: "transformation"
        - transfomration: transformation ID or code to execute.
    - Master nodes nodes, but they have a special role so we define them here, the JSON holds the following extended info:
        - type: "master"
        - debate: 
            - agents (LLMs, routines ...)
            - Info to each class of agents: 
                - LLMS:
                    - Skill files
                    - model
                    - input prompts
                    - parameters
                    - input format
                    - output format
                - routines:
                    - executable
                    - parameters to run
                    - input format
                    - output format
                - Note: To implement Debates maybe building on an existing framework like langgraph.
            - A small graph describing the relations between the participants (one node graph is allowd)
            - parameter: Should be available to re-use existing debates.
            - Finalization Criteria: How the master decides the outcome

## Skill (definition)

- ID
- command
- workflow graph
- associated context graph
-benchmarks
