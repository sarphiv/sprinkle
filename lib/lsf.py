from typing import Optional, Literal
from dataclasses import dataclass, replace
from itertools import islice
import pickle
import os
import subprocess
import re

from varname import nameof

from constants import sprinkle_project_dir, sprinkle_project_settings_file, sprinkle_project_log_dir, sprinkle_project_error_dir, sprinkle_project_output_dir, sprinkle_env_file_name, sprinkle_req_file_name



@dataclass(frozen=True)
class JobSettings:
    script: str                         = "python main.py"

    cpu_cores: int                      = 16
    cpu_mem_gb: int                     = 8

    env_file: str                       = ""
    req_file: str                       = ""
    working_dir: str                    = ""

    queue: str                          = "hpc"
    is_gpu_queue: bool                  = False
    time_max: str                       = "24:00"

    name: str                           = "default-job-name"
    env_name: str                       = "default-env-name"
    env_on_done_delete: bool            = False

    email: str                          = ""
    
    version: str                        = "3"


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



def view_job(type: Literal["output", "log", "error"], job_id: str, all: bool) -> bool:
    """View job output, log, or error

    Args:
        type (Literal["output", "log", "error"]): Type of file to view
        job_id (str): Job ID
        all (bool): View all output, log, or error

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
        subprocess.run((["less"] if all else ["tail", "-f"]) + [f"{directory}/{file}"])
    except KeyboardInterrupt:
        pass


    # Return success
    return True



def generate_environment_yml(env_name: str, env_file_name: str, req_file_name: str) -> None:
    """Generates a basic environment.yml for a job
    
    Args:
        env_name (str): Name of environment
        env_file_name (str): File path of environment file
        req_file_name (str): File path of requirements file
    """
    # Open and write to environment.yml equivalent file
    with open(env_file_name, 'w') as f:
        f.write(f"""\
name: {env_name}
channels:
  - defaults

dependencies:
  - python
  - pip

  - pip:
    - -r {req_file_name}
""")


def generate_requirements_txt(req_file_name: str) -> None:
    """Generates a requirements.txt equivalent for a job by inspecting the source code

    Args:
        req_file_name (str): File path of requirements file
    """
    # Get requirements
    requirements = subprocess.run(
        ["pipreqs", "--force", "--print"],
        stdout=subprocess.PIPE, 
        stderr=subprocess.DEVNULL,
        encoding="ascii"
    ).stdout
    
    # Open and write to requirements.txt equivalent file
    with open(req_file_name, 'w') as f:
        f.write(requirements)
    


def ensure_environment_specification_exists(settings: Optional[JobSettings]) -> tuple[Optional[JobSettings], bool]:
    """Ensures that an environment.yml and/or requirements.txt equivalent exists for a job
    by creating the necessary files or by verifying that the specified files exist

    Args:
        settings (Optional[JobSettings]): Settings for the job to be run

    Returns:
        tuple[Optional[JobSettings], bool]: Tuple containing the job settings if valid environment, 
            and a boolean indicating whether files were generated.
    """
    # if no settings given, return None
    if settings is None:
        return (None, False)


    # Get environment and requirements file names
    env_file_name = settings.env_file if settings.env_file else sprinkle_env_file_name
    req_file_name = settings.req_file if settings.req_file else sprinkle_req_file_name

    
    # Mark environment and/or requirements files were generated
    env_file_generated = False
    req_file_generated = False
    # Mark whether settings do not specify missing file(s)
    settings_valid = True


    # Change working directory to project directory
    working_directory_old = os.getcwd()
    working_directory_new = settings.working_dir or working_directory_old
    os.chdir(working_directory_new)

    # If no environment file specified, generate environment file
    if settings.env_file == "":
        env_file_generated = True
        generate_environment_yml(settings.env_name, env_file_name, req_file_name)
        settings = replace(settings, **{nameof(JobSettings.env_file): env_file_name})
    # Else, check if specified file exists
    else:
        settings_valid &= os.path.isfile(settings.env_file)


    # if no requirements file specified, generate requirements file
    if settings.req_file == "":
        req_file_generated = True
        generate_requirements_txt(req_file_name)
        settings = replace(settings, **{nameof(JobSettings.req_file): req_file_name})
    # else, check if specified file exists
    else:
        settings_valid &= os.path.isfile(settings.req_file)


    # Change working directory back to current working directory
    os.chdir(working_directory_old)
    
    
    # Return settings if files exist, also return whether files were generated
    return (settings if settings_valid else None, env_file_generated or req_file_generated)



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
### GPUs to request and if to reserve it exclusively\n
#BSUB -gpu "num=1:mode=exclusive_process"''')
+
f"""
### Cores to request
#BSUB -n {settings.cpu_cores}

### Force cores to be on same host
#BSUB -R "span[hosts=1]" 

### Number of threads for OpenMP parallel regions
export OMP_NUM_THREADS=$LSB_DJOB_NUMPROC


### Amount of memory to request
#BSUB -R "rusage[mem={settings.cpu_mem_gb}GB]"


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
conda env list | grep "^{settings.env_name}" >> /dev/null
SPRINKLE_JOB_ENV_EXISTS=$?

# If environment does not exist, create environment
if [[ ${{SPRINKLE_JOB_ENV_EXISTS}} -ne 0 ]]; then
    # Create environment
    # WARN: Race condition. Two (or more) jobs may attempt to create the same new environment.
    #  This causes jobs to fail, because the others fail the conda commmand,
    #  and then they continue on before the environment has been set up.
    conda env create -n {settings.env_name} -f {settings.env_file}
# Else, environment exists, attempt installing packages in case there were changes
# WARN: This does not prune pip packages
else
    # Attempt installing (new) packages 
    conda env update -n {settings.env_name} -f {settings.env_file} --prune
fi

# If failed environment setup, inform and exit
if [[ $? -ne 0 ]]; then
    echo "Failed to set up environment ({settings.env_name}) for job ($LSB_JOBID)." >&2
    echo 'This may be caused by multiple jobs trying to set up the same environment for the first time.' >&2
    echo 'If the job environment has NEVER been created before, a possible fix is to start one job,' >&2
    echo 'let it finish setting up the environment, and afterwards start all the other jobs,' >&2
    echo 'that use the same environment, can be rapidly started.' >&2
    echo 'BEFORE DOING THE ABOVE, PLEASE RUN: conda env remove -n {settings.env_name} -y' >&2
    exit 1
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