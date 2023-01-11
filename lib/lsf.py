from typing import Optional, Literal
from dataclasses import dataclass, replace
from itertools import islice
import pickle
import os
import subprocess
import re

from varname import nameof

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
    time_start: str
    time_elapsed: str
    cpu_usage: Optional[str] = None
    mem_usage: Optional[str] = None
    mem_usage_avg: Optional[str] = None
    mem_usage_max: Optional[str] = None




def save_settings(settings: JobSettings) -> None:
    """Save job settings to pickle file
    
    Args:
        settings (JobSettings): Settings to save
    """
    
    # If sprinkle directories do not exist for project, create them
    if not os.path.isdir(sprinkle_project_dir):
        os.makedirs(sprinkle_project_dir)

    # Save settings to pickle file
    with open(f"{sprinkle_project_dir}/{sprinkle_project_settings_file}", "wb") as file:
        settings = pickle.dump(settings, file)



def load_settings() -> Optional[JobSettings]:
    """Load job settings from pickle file
    
    Returns:
        Optional[JobSettings]: Job settings or None if settings file does not exist
    """

    # Construct path to settings file
    settings_file_path = f"{sprinkle_project_dir}/{sprinkle_project_settings_file}"
    
    # If settings file does not exist, return None
    if not os.path.isfile(settings_file_path):
        return None


    # Load settings from pickle file
    with open(settings_file_path, "rb") as file:
        settings = pickle.load(file)


    # Return settings if version matches current software's settings version
    return settings if JobSettings.version == settings.version else None



def submit_job(settings: JobSettings, args: list[str] = []) -> str:
    """Submit a job to the cluster and return the job id
    
    Args:
        settings (JobSettings): Settings for the job
        args (list[str], optional): Arguments to pass to the job. Defaults to [].
    
    Returns:
        str: Job id
    """
    
    #TODO: Error if job submission failed
    
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
    """Kill jobs by job id
    
    Args:
        job_ids (list[str]): List of job ids to kill
    
    Returns:
        tuple[list[str], list[str]]: Tuple of (killed job ids, not killed job ids)
    """
    
    # If no jobs to kill, return nothing
    if len(job_ids) == 0:
        return [], []


    # Send kill command
    killed = subprocess.run(
        ["bkill"] + job_ids, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
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



def get_jobs_active() -> dict[str, JobDetails]:
    """Get all active jobs
    
    Returns:
        dict[str, JobDetails]: Dictionary of active jobs, where key is job id
    """
    
    # WARN: Race condition possible. Solving via ostrich algorithm.

    # Get job status
    status_meta = subprocess.run(
        ["bstat"], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        encoding="ascii"
    )
    status_cpu = subprocess.run(
        ["bstat", "-C"], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        encoding="ascii"
    )
    status_mem = subprocess.run(
        ["bstat", "-M"], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        encoding="ascii"
    )


    # If there were no jobs, return nothing    
    if status_meta.stdout == '':
        return {}


    # Parse and return job details
    
    # Store details
    job_details = {}

    # For each line in meta status message, skip header, parse jobs
    for line in islice(status_meta.stdout.splitlines(), 1, None):
        # Parse meta details
        meta = re.findall(r"(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+([\S ]+)\s+(\S+)", line)
        if len(meta) == 0:
            continue
        else:
            meta = meta[0]


        # Instantiate job details object
        job_details[meta[0]] = JobDetails(
            name_short=meta[3],
            job_id=meta[0],
            queue=meta[2],
            status=meta[5],
            cpu_usage=None,
            mem_usage=None,
            mem_usage_avg=None,
            mem_usage_max=None,
            time_start=meta[6].strip(),
            time_elapsed=meta[7]
        )

    # For each line in cpu status message, skip header, parse jobs
    cpu_attr = nameof(JobDetails.cpu_usage)
    for line in islice(status_cpu.stdout.splitlines(), 1, None):
        # Parse cpu details
        cpu = re.findall(r"(\S+)\s+(?:\S+\s+){5}(\S+)", line)
        if len(cpu) == 0:
            continue
        else:
            cpu = cpu[0]
        
        # Set cpu usage
        job_details[cpu[0]] = replace(job_details[cpu[0]], **{cpu_attr: cpu[1]})

    # For each line in memory status message, skip header, parse jobs
    mem_attr = nameof(JobDetails.mem_usage)
    mem_avg_attr = nameof(JobDetails.mem_usage_avg)
    mem_max_attr = nameof(JobDetails.mem_usage_max)
    for line in islice(status_mem.stdout.splitlines(), 1, None):
        # Parse memory details
        mem = re.findall(r"(\S+)\s+(?:\S+\s+){4}(\S+)\s+(\S+)\s+(\S+)\s+\S+", line)
        if len(mem) == 0:
            continue
        else:
            mem = mem[0]
        
        # Set memory usage
        job_details[mem[0]] = replace(job_details[mem[0]], **{mem_attr: mem[1], mem_avg_attr: mem[3], mem_max_attr: mem[2]})


    # Return details about all active jobs
    return job_details



def view_job(type: Literal["output", "log", "error"], job_id: str) -> bool:
    """View job output, log, or error

    Args:
        type (Literal["output", "log", "error"]): Type of file to view
        job_id (str): Job ID

    Returns:
        bool: True if file exists and was successfully viewed, False otherwise
    """
    # Get directory for file
    match type:
        case "output":
            directory = sprinkle_project_output_dir
        case "log":
            directory = sprinkle_project_log_dir
        case "error":
            directory = sprinkle_project_error_dir
    
    # If directory does not exist, return failure
    if not os.path.isdir(directory):
        return False


    # Search for associated file
    directory_contents = os.listdir(directory)
    file = ""
    for content in directory_contents:
        if job_id in content:
            file = content
            break
    
    # If file does not exist, return failure
    if not os.path.isfile(f"{directory}/{file}"):
        return False


    # Track bottom of file
    try:
        subprocess.run(["tail", "-f", f"{directory}/{file}"])
    except KeyboardInterrupt:
        pass


    # Return success
    return True



def generate_bsub_script(settings: JobSettings, args: list[str] = []) -> str: 
    """Generates a bsub script for a job

    Args:
        settings (JobSettings): Settings for the job to be run
        args (list[str], optional): Arguments to pass to the job.
    
    Returns:
        str: Generated bsub script
    """
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
# WARN: This does not prune pip packages
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