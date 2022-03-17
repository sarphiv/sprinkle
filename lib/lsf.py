from dataclasses import dataclass
from itertools import islice
import pickle
import os
import subprocess
import re

from prompt import prompt_integer, prompt_string, prompt_list
from main import sprinkle_project_options, sprinkle_project_output_dir, sprinkle_project_error_dir, sprinkle_project_script_dir


@dataclass(frozen=True)
class JobOptions:
    name: str
        
    env_name: str
    env_on_done_delete: bool
    script_target: str

    time_max: str
    queue: str
    is_gpu_queue: bool
    
    cpu_cores: int
    cpu_memory_per_core: str
    cpu_memory_max: str
    
    email: str


@dataclass(frozen=True)
class JobDetails:
    short_name: str
        
    job_id: str
    queue: str
    status: str
    time_start: str
    time_elapsed: str



def save_options(options: JobOptions, path: str) -> None:
    pass


def load_options(path: str) -> JobOptions:
    pass


def prompt_options() -> JobOptions:
    pass
    # TODO: No spaces in job name nor env name


def submit_options(options: JobOptions) -> str:
    # If sprinkle directories do not exist for project, create them
    for dir in [sprinkle_project_output_dir, sprinkle_project_error_dir, sprinkle_project_script_dir]:
        if not os.path.isdir(dir):
            os.makedirs(dir)
    
    # Submit job script and save stdout
    submission = subprocess.run(
        ["bsub"], 
        stdout=subprocess.PIPE, 
        input=generate_bsub_script(options),
        encoding="ascii"
    )
    
    # Retrieve job id
    job_id = re.search("Job <(\d+)>", submission.stdout).group(1)


    # Return new submission job id
    return job_id




def get_active_jobs() -> dict[str, JobDetails]:
    # Get job status
    status = subprocess.run(
        ["bstat"], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        encoding="ascii"
    )
    
    # If there were no jobs, return nothing    
    if status.stdout == '':
        return {}
    # Else there were jobs, parse and return job details
    else:
        # Store details
        job_details = {}

        # For each line in status message, skip header, parse jobs
        for line in islice(status.stdout.splitlines(), 1, None):
            # Parse job details
            details = re.findall("([^\s]+)", line)
            
            # Instantiate job details object
            job_details[details[0]] = JobDetails(
                short_name=details[3],
                job_id=details[0],
                queue=details[2],
                status=details[5],
                time_start=details[6],
                time_elapsed=details[7]
            )


        # Return details about all active jobs
        return job_details


def prompt_active_jobs() -> str:
    # Get active job details
    job_details = get_active_jobs()
    # Prompt user for an active job
    job_id = prompt_list(job_details)
    
    # Return chosen job ID
    return job_id




def generate_bsub_script(options: JobOptions): 
    def conditional_string(condition, string, end="\n"):
        return string if condition + end else ""

    return (f"""
#!/bin/bash
### Job name
#BSUB -J {options.name}


### Job queue
#BSUB -q {options.queue} 
"""
+
conditional_string(options.is_gpu_queue,
f'''
### GPUs to request and if to reserve it exclusively\n"
#BSUB -gpu "num=1:mode=exclusive_process"''')
+
f"""
### Cores to request
#BSUB -n {options.cpu_cores}

### Force cores to be on same host
#BSUB -R "span[hosts=1]" 

### Number of threads for OpenMP parallel regions
export OMP_NUM_THREADS=$LSB_DJOB_NUMPROC


### Amount of memory per core
#BSUB -R "rusage[mem={options.cpu_memory_per_core}]" 

### Maximum amount of memory before killing task
#BSUB -M {options.cpu_memory_max} 


### Wall time (HH:MM), how long before killing task
#BSUB -W {options.time_max}


### Output and error file. %J is the job-id -- 
### -o and -e mean append, -oo and -eo mean overwrite -- 
#BSUB -oo {sprinkle_project_output_dir}/%J.txt
#BSUB -eo {sprinkle_project_error_dir}/%J.txt
"""
+
conditional_string(options.email, 
f"""
### Email to receive notifications
#BSUB -u {options.email}

### Notify via email at start
#BSUB -B

### Notify via email at completion
#BSUB -N""")
+
f"""

# Get shell environment
source ~/.bashrc

# Check if job environment exists
conda env list | grep "^${options.env_name}" >> /dev/null
SPRINKLE_JOB_ENV_EXISTS=$?

# If environment does not exist, create environment
if [[ ${{SPRINKLE_JOB_ENV_EXISTS}} -ne 0 ]]; then
    # Create environment
    conda create -n {options.env_name} --file requirements.txt -y
    
    # Activate environment for script
    conda activate {options.env_name}
# Else, attempt installing packages in case there were changes
else
    # Activate environment for script
    conda activate {options.env_name}

    # Attempt installing (new) packages 
    conda install --file requirements.txt -y
fi


# Run job script and save output to file
python {options.script_target} > {sprinkle_project_script_dir}/$J.txt

"""
+
conditional_string(options.env_on_done_delete, 
f"""
### Remove environment when done
conda env remove -n {options.env_name} -y
""")
)