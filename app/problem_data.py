from dataclasses import dataclass, asdict, field
import os
import json

save_dir = "./problems/"

@dataclass
class ProblemProfile:
    """
    Represents detailed information of a problem.
    
    Attributes:
        Required:
            id(str): ID of the problem.
            title(str): title of the problem.
            description(str): description of the problem.
            input_description(str): description of the input format.
            output_description(str): description of the output format.
            samples(list): sample input and output, where each element is {input, output}.
            constraints(str): data range and constraints.
            testcases(list): test cases, where each element is {input, output}.
        Optional:
            hint(str): additional hints.
            source(str): source of the problem.
            tags(list): tags of the problem.
            time_limit(float): time limit (e.g., "1s").
            memory_limit(int): memory limit (e.g., "128MB").
            author(str): author of the problem.
            difficulty(str): difficulty level.
    """
    id: str
    title: str
    description: str
    input_description: str
    output_description: str
    samples: list
    constraints: str
    testcases: list
    
    hint: str = ''
    source: str = ''
    tags: list[str] = field(default_factory=list)
    time_limit: float = 3.0
    memory_limit: int = 128
    author: str = ''
    difficulty: str = ''
    
    def to_dict(self):
        """Change ProblemProfile to dict"""
        data = asdict(self)
        data['samples'] = json.dumps(data['samples'], ensure_ascii=False)
        data['testcases'] = json.dumps(data['testcases'], ensure_ascii=False)
        data['tags'] = json.dumps(data['tags'], ensure_ascii=False)
        return data