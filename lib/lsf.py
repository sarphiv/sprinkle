from enum import Enum
from typing import Optional
from dataclasses import dataclass
from itertools import islice
import pickle
import os
import subprocess
import re

from constants import sprinkle_project_dir, sprinkle_project_settings_file, sprinkle_project_log_dir, sprinkle_project_error_dir, sprinkle_project_output_dir


@dataclass(frozen=True)
class JobSettings:
    name: str                           = "default-job-name"
    env_name: str                       = "default-env-name"
    env_on_done_delete: bool            = False

    working_dir: str                    = ""
    env_file: str                       = "environment.yml"
    script: str                         = "python main.py"

    time_max: str                       = "24:00"
    queue: str                          = "hpc"
    is_gpu_queue: bool                  = False
    
    cpu_cores: int                      = 16
    cpu_mem_per_core_mb: int            = 512
    cpu_mem_max_gb: int                 = 6
    
    email: str                          = ""
    
    version: str                        = "1"


@dataclass(frozen=True)
class JobDetails:
    name_short: str
        
    job_id: str
    queue: str
    status: str
    cpu_usage: Optional[str]
    mem_usage: Optional[str]
    time_start: str
    time_elapsed: str




def save_settings(settings: JobSettings) -> None:
    if not os.path.isdir(sprinkle_project_dir):
        os.makedirs(sprinkle_project_dir)

    with open(f"{sprinkle_project_dir}/{sprinkle_project_settings_file}", "wb") as file:
        settings = pickle.dump(settings, file)


def load_settings() -> Optional[JobSettings]:
    settings_file_path = f"{sprinkle_project_dir}/{sprinkle_project_settings_file}"
    
    if not os.path.isfile(settings_file_path):
        return None


    with open(settings_file_path, "rb") as file:
        settings = pickle.load(file)

    return settings if JobSettings.version == settings.version else None




def submit_job(settings: JobSettings, args: list[str] = []) -> str:
    # If sprinkle directories do not exist for project, create them
    for dir in [sprinkle_project_log_dir, sprinkle_project_error_dir, sprinkle_project_output_dir]:
        if not os.path.isdir(dir):
            os.makedirs(dir)
    
    # Submit job script and save stdout
    submission = subprocess.run(
        ["bsub"], 
        stdout=subprocess.PIPE, 
        input=generate_bsub_script(settings, args),
        encoding="ascii"
    )
    
    # Retrieve job id
    job_id = re.search("Job <(\d+)>", submission.stdout).group(1)


    # Return new submission job id
    return job_id


def kill_jobs(job_ids: list[str]) -> tuple[list[str], list[str]]:
    # If no jobs to kill, return nothing
    if len(job_ids) == 0:
        return [], []


    # Send kill command
    killed = subprocess.run(
        ["bkill"], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        input=" ".join(job_ids),
        encoding="ascii"
    )


    # Parse killed and not killed job ids
    success = []
    failure = []
    for line in killed.stdout.splitlines():
        match = re.findall(r"Job <(\d+)> is being terminated", line)
        if match:
            success.append(match[0])
            continue
        
        match = re.findall(r"Job <(\d+)>: No matching job found", line)
        if match:
            failure.append(match[0])
            continue

        match = re.findall(r"Job <(\d+)>: Job has already finished", line)
        if match:
            failure.append(match[0])
            continue


        # No known message was seen. Warn user
        print(f"WARNING: Unknown kill job message: {line}\nPlease share this with a sprinkle developer")



    # Return jobs killed and not killed
    return success, failure



def view_job(details: JobDetails, directory: str) -> bool:
    # TODO: Implement viewing of job outputs
    pass


def get_jobs_active() -> dict[str, JobDetails]:
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
            details = re.findall(r"([^\s]+)", line)
            
            # Instantiate job details object
            job_details[details[0]] = JobDetails(
                name_short=details[3],
                job_id=details[0],
                queue=details[2],
                status=details[5],
                cpu_usage=None,
                mem_usage=None,
                time_start=details[6],
                time_elapsed=details[7]
            )


        # Return details about all active jobs
        return job_details




def generate_bsub_script(settings: JobSettings, args: list[str] = []) -> str: 
    def conditional_string(condition, string, end="\n"):
        return string + end if condition else ""

    return (f"""\
#!/bin/bash
### Job name
#BSUB -J {settings.name}


### Job queue
#BSUB -q {settings.queue} 
"""
+
conditional_string(settings.is_gpu_queue,
f'''
### GPUs to request and if to reserve it exclusively\n"
#BSUB -gpu "num=1:mode=exclusive_process"''')
+
f"""
### Cores to request
#BSUB -n {settings.cpu_cores}

### Force cores to be on same host
#BSUB -R "span[hosts=1]" 

### Number of threads for OpenMP parallel regions
export OMP_NUM_THREADS=$LSB_DJOB_NUMPROC


### Amount of memory per core
#BSUB -R "rusage[mem={settings.cpu_mem_per_core_mb}MB]" 

### Maximum amount of memory before killing task
#BSUB -M {settings.cpu_mem_max_gb}GB


### Wall time (HH:MM), how long before killing task
#BSUB -W {settings.time_max}


### Output and error file. %J is the job-id -- 
### -o and -e mean append, -oo and -eo mean overwrite -- 
#BSUB -oo {sprinkle_project_log_dir}/%J-{settings.name}.txt
#BSUB -eo {sprinkle_project_error_dir}/%J-{settings.name}.txt
"""
+
conditional_string(settings.email, 
f"""
### Email to receive notifications
#BSUB -u {settings.email}

### Notify via email at start
#BSUB -B

### Notify via email at completion
#BSUB -N""")
+
f"""

# Get shell environment
source ~/.bashrc
"""
+
conditional_string(settings.working_dir,
f"""
# Change working directory
cd {settings.working_dir}

""")
+
f"""
# Check if job environment exists
conda env list | grep "^${settings.env_name}" >> /dev/null
SPRINKLE_JOB_ENV_EXISTS=$?

# If environment does not exist, create environment
if [[ ${{SPRINKLE_JOB_ENV_EXISTS}} -ne 0 ]]; then
    # Create environment
    conda env create -n {settings.env_name} -f {settings.env_file}
# Else, environment exists, attempt installing packages in case there were changes
else
    # Attempt installing (new) packages 
    conda env update -n {settings.env_name} -f {settings.env_file} --prune
fi

# Activate environment for script
conda activate {settings.env_name}


# Run job script and save output to file
# NOTE: %J is not available so using environment variable
{settings.script} {" ".join(args)} > {sprinkle_project_output_dir}/$LSB_JOBID-{settings.name}.txt

"""
+
conditional_string(settings.env_on_done_delete, 
f"""
### Remove environment when done
conda env remove -n {settings.env_name} -y
""")
)