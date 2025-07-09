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
            time_limit(str): time limit (e.g., "1s").
            memory_limit(str): memory limit (e.g., "128MB").
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
    time_limit: str = '1s'
    memory_limit: str = '128MB'
    author: str = ''
    difficulty: str = ''
    
    def save_to_local(self):
        """Saves problem's profile data to a JSON file."""

        # Construct singer-specific folder path
        os.makedirs(save_dir + str(self.id), exist_ok = True)

        json_file_path = save_dir + str(self.id) + '/data.json'
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, indent=4, ensure_ascii=False)