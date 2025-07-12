import asyncio
import docker
import sqlite3
import json
import os
import io
import tarfile
import time
import threading
import re
import tracemalloc

stdout_output = b""
stderr_output = b""

# 存储正在运行的任务
running_tasks = {}

async def get_requirements(
    problem_id: int,
    language: str
) -> tuple:
    """
    Get requirements of the submission.
    
    Args:
        problem_id(int): id of the problem
        language(str): language of the submission
        
    Returns:
        A tuple containing test cases, time limit, memory limit.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_requirements_sync, problem_id, language)

def get_requirements_sync(problem_id: int, language: str) -> tuple:
    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        
        # Get info of the problem.
        cursor.execute(
                """SELECT testcases, time_limit, memory_limit
                FROM problems WHERE id = ?""",
                (problem_id, )
            )
        problem_row = cursor.fetchone()
        
        # Get info of the language.
        cursor.execute(
                "SELECT * FROM languages WHERE name = ?",
                (language, )
            )
        language_row = cursor.fetchone()
        
    if language_row:
        # Set time and memory limit.
        time_limit = problem_row[1]
        if problem_row[1] == 1.0:
            time_limit = language_row[5]

        memory_limit = problem_row[2]
        if problem_row[2] == 128:
            memory_limit = language_row[6]
        
    return (json.loads(problem_row[0]), time_limit, memory_limit)

def run_code(container):
    """
    Run code in container and get output of outs and errors.
    """
    global stdout_output
    global stderr_output
    
    # Initialize output
    stdout_output = b""
    stderr_output = b""
    
    exec_result = container.exec_run(
        cmd = ["/bin/sh", "-c", "python main.py < input.txt"],
        workdir = "/submission",
        demux = True
    )
    
    if exec_result.output:
        stdout, stderr = exec_result.output
        if stdout:
            stdout_output += stdout
        if stderr:
            stderr_output += stderr
            
def validate_python(code: str) -> bool:
    """
    Check code written in python.
    Written by claude.
    """
    dangerous_patterns = [
        r'\bexec\s*\(',
        r'\beval\s*\(',
        r'\bopen\s*\(',
        r'\b__import__\s*\(',
        r'\bimport\s+os\b',
        r'\bfrom\s+os\b',
        r'\bimport\s+sys\b',
        r'\bimport\s+subprocess\b',
        r'\bsystem\s*\(',
        r'__[a-zA-Z_]+__',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return False
    
    return True

def validate_cpp(code: str) -> bool:
    """
    Check code written in cpp.
    Written by claude.
    """
    dangerous_patterns = [
        r'#include\s*<cstdlib>',
        r'#include\s*<unistd.h>',
        r'#include\s*<sys/',
        r'\bsystem\s*\(',
        r'\bexec[vl]p?\s*\(',
        r'\bfork\s*\(',
        r'\basm\s*\(',
        r'__asm__',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return False
    
    return True

async def update_log(submission_id: int, status: str, counts: int, log: list):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, update_log_sync, submission_id, status, counts, log)

def update_log_sync(submission_id: int, status: str, counts: int, log: list):
    with sqlite3.connect('./app/oj_system.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE submissions SET status = ?, counts = ?, log = ? WHERE id = ?",
            (status, counts, json.dumps(log), submission_id,)
        )
        conn.commit()
          
async def judge_in_docker(
    submission_id: int,
    problem_id: int,
    code: str,
    language: str
):
    
    # Get requirements of the submission
    requirements = await get_requirements(problem_id, language)
    test_cases = requirements[0]
    time_limit = requirements[1]
    memory_limit = requirements[2]
    
    log: list[dict] = []
    for i in range(len(test_cases)):
        log.append({"id": i + 1, "result": "UNK", "time": 0.0, "memory": 0})
        
    if language == "cpp":
        if not validate_cpp(code):
            return
    elif language == "python":
        if not validate_python(code):
            return
    else:
        return
        
    os.makedirs(f"./app/submission/{submission_id}", exist_ok=True)
    
    with open(f"./app/submission/{submission_id}/main.py", "w", encoding="utf-8") as f:
        f.write(code)
    
    client: docker.DockerClient = docker.from_env()
    
    seccomp_profile_path = os.path.abspath('./app/default_seccomp.json')
    with open(seccomp_profile_path, 'r') as f:
        seccomp_profile = json.load(f)
    
    for i, item in enumerate(test_cases):
        # Prepare for the container, written by gemini.
        container_args = {
            'name': f'oj_{submission_id}_{i}',
            'detach': True,
            'remove': False,
            'mem_limit': str(memory_limit) + 'm',
            'pids_limit': 128, 
            'cpu_period': 100000,
            'cpu_quota': int(time_limit * 100000),
            'network_disabled': True,
            'read_only': True,
            'tmpfs': {'/tmp': 'rw,noexec,nosuid,size=64m'},
            'user': '1000:1000',
            'security_opt': [f'seccomp={json.dumps(seccomp_profile)}',
                             'no-new-privileges'],
            'cap_drop': ['ALL'],
            'volumes': { 
                os.path.abspath(f"./app/submission/{submission_id}"): { 
                    'bind': '/submission', 
                    'mode': 'rw' 
                }
            },
            'working_dir': '/submission', 
            'stdin_open': True, 
            'command': ['python', 'main.py'], 
        }
        container = client.containers.run("python-eval-env", **container_args)
        
        # Prepare for input
        input_data = str(item["input"]).encode("utf-8")
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            tarinfo = tarfile.TarInfo(name="input.txt")
            tarinfo.size = len(input_data)
            tar.addfile(tarinfo, io.BytesIO(input_data))
        tar_stream.seek(0)
        container.put_archive("/submission", tar_stream.read())

        # Run code
        start_time = time.monotonic()
        tracemalloc.start()
        before = tracemalloc.take_snapshot()

        exec_thread = threading.Thread(target = run_code, args = (container,))
        exec_thread.start()
        exec_thread.join(timeout = time_limit)
        
        log[i]["time"] = time.monotonic() - start_time
        
        after = tracemalloc.take_snapshot()
        delta_mem = after.compare_to(before, 'lineno')
        
        log[i]["memory"] = (sum(stat.size for stat in delta_mem) // 1024) / 1024
        
        container.reload()
        
        if container.attrs['State'].get('OOMKilled'):
            log[i]["result"] = "MLE"
            log[i]["memory"] = memory_limit
            container.remove(force = True)
            continue
        
        if exec_thread.is_alive():
            log[i]["result"] = "TLE"
            log[i]["time"] = time_limit
            container.stop(timeout = 1)
            container.remove(force = True)
            continue

        if "runtime" in stdout_output.decode():
            # If RE, making following tests is unnecessary
            container.remove(force = True)
            for j in range(i, len(test_cases)):
                log[j]["result"] = "RE"
            break
        
        container.remove(force = True)
        ans_out = str(item["output"]).split('\n')
        test_out = str(stdout_output.decode()).split('\n')
        
        ans_out.pop()
        test_out.pop()
        
        if test_out[-1] == '':
            test_out.pop()
        
        log[i]["result"] = "AC"
        
        # Check output
        if len(test_out) != len(ans_out):
            log[i]["result"] = "WA"
            continue
        
        for ans, test in zip(ans_out, test_out):
            if len(test) == 0:
                if len(ans) != 0:
                    log[i]["result"] = "WA"
                    break
            
            elif test[-1] == ' ':
                if ans != test[0 : -1]:
                    log[i]["result"] = "WA"
                    break
                    
            else:
                if ans != test:
                    log[i]["result"] = "WA"
                    break
    
    # Update log    
    counts = 0
    status = "success"
    for item in log:
        if item["result"] == "AC":
            counts += 10
        elif item["result"] == "WA":
            pass
        else:
            status = "error"
    
    await update_log(submission_id, status, counts, log)
    