from varname import nameof
from typing import Callable, Optional, Any
from os import getcwd
from tabulate import tabulate

from prompt import prompt_base, prompt_integer, prompt_string, prompt_list
from lsf import JobSettings, JobDetails, get_active_jobs



def as_is(object: Any) -> str:
    return str(object)

def surround(prefix: str = "", suffix: str = "") -> Callable[[str], str]:
    return lambda x: prefix + str(x) + suffix

def empty_coalesce(default_value: str) -> str:
    return lambda x: str(x) if x is not None and x != "" else default_value


job_settings_formatter: dict[str, tuple[str, Callable[[str], str]]] = {
    f"{nameof(JobSettings.name)}": 
        ("Job name", as_is),
    f"{nameof(JobSettings.env_name)}": 
        ("Environment name", as_is),
    f"{nameof(JobSettings.env_on_done_delete)}": 
        ("Auto-delete environment", as_is),

    f"{nameof(JobSettings.working_dir)}": 
        ("Working directory", empty_coalesce(getcwd())),
    f"{nameof(JobSettings.env_spec)}": 
        ("Environment file", as_is),
    f"{nameof(JobSettings.script)}": 
        ("Script (or command)", as_is),

    f"{nameof(JobSettings.time_max)}": 
        ("Job max time (HH:mm)", as_is),
    f"{nameof(JobSettings.queue)}": 
        ("Cluster queue", as_is),
    # Skipping: is_gpu_queue

    f"{nameof(JobSettings.cpu_cores)}": 
        ("CPU cores", as_is),
    f"{nameof(JobSettings.cpu_mem_per_core_mb)}": 
        ("Per CPU core memory", surround(suffix=" MB")),
    f"{nameof(JobSettings.cpu_mem_max_gb)}": 
        ("Max total CPU memory", surround(suffix=" GB")),

    f"{nameof(JobSettings.email)}": 
        ("Notification email", empty_coalesce("No notification")),

    # Skipping: version
}

def prompt_settings(suggested_settings: JobSettings) -> JobSettings:
    """_summary_

    Args:
        suggested_settings (JobSettings): _description_

    Returns:
        JobSettings: _description_
    """
    suggested_values = {
        key: getattr(suggested_settings, key) 
        for key in job_settings_formatter
    }
    
    setting_values = [
        (desc, format(suggested_values[attr_name])) 
        for attr_name, (desc, format) in job_settings_formatter.items()
    ]
    
    setting_desc = [setting for (setting, value) in setting_values]
    
    
    # print(tabulate(setting_values, headers=["Setting", "Value"]))
    prompt_string(
        info_text=f"{tabulate(setting_values, headers=['Setting', 'Value'], showindex=True)}\n\nChoose setting to change", 
        value_allowed=setting_desc + [str(i) for i in range(len(setting_desc))],
        value_suggestions=setting_desc
    )
    
    
    #TODO: handle input of index and setting name
    
    pass
    # TODO: No spaces in job name nor env name
    
    
def prompt_active_jobs() -> Optional[str]:
    # Get active job details
    job_details = get_active_jobs()
    
    # If no active jobs, return None
    if len(job_details) == 0:
        return None


    # Prompt user for an active job
    # TODO: Finish prompting for job
    job_id = prompt_list(job_details)
    
    # Return chosen job ID
    return job_id
