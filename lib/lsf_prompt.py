from varname import nameof
from typing import Callable, Optional, Any, Union
from os import getcwd
from dataclasses import replace
import re

from prompt import prompt_range_integer, prompt_path, prompt_string, prompt_regex, prompt_boolean, prompt_choice
from lsf import JobSettings, JobDetails, get_jobs_active


# Track whether module initialized
# NOTE: Doing this to avoid paying cost of reflection upon import
module_initialized = False


# Formatting of job settings
def as_is(object: Any) -> str:
    return str(object)

def as_is_boolean(object: bool) -> str:
    return as_is(object).lower()

def surround(prefix: str = "", suffix: str = "") -> Callable[[str], str]:
    return lambda x: prefix + str(x) + suffix

def empty_coalesce(default_value: str) -> str:
    return lambda x: str(x) if x is not None and x != "" else default_value


job_settings_formatter: dict[str, tuple[str, Callable[[str], str]]] = lambda: {
    f"{nameof(JobSettings.name)}": 
        ("Job name", as_is),
    f"{nameof(JobSettings.env_name)}": 
        ("Environment name", as_is),
    f"{nameof(JobSettings.env_on_done_delete)}": 
        ("Auto-delete environment", as_is_boolean),

    f"{nameof(JobSettings.working_dir)}": 
        ("Working directory", empty_coalesce(getcwd())),
    f"{nameof(JobSettings.env_file)}": 
        ("Environment file", empty_coalesce("[Auto-generated ONCE]")),
    f"{nameof(JobSettings.req_file)}": 
        ("Requirements file", empty_coalesce("[Auto-generated ONCE]")),
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



# Prompting for job settings
def prompt_new_string(allow_empty: bool = False, allow_spaces: bool = False) -> Callable[[str, str, str], str]:
    def prompt(attr: str, value_current: str, value_default: str) -> str:    
        name, formatter = job_settings_formatter[attr]

        return {attr: prompt_string(
            f"{name}\nCurrent: {formatter(value_current)} (Default: {formatter(value_default)})\n\nChoose new value: ",
            value_disallowed=None if allow_empty else [""],
            str_disallowed=None if allow_spaces else [" "],
            value_suggestion=formatter(value_default) if allow_empty else None
        )}


    return prompt


def prompt_new_boolean(attr: str, value_current: bool, value_default: bool) -> bool:
    name, formatter = job_settings_formatter[attr]

    return {attr: prompt_boolean(
        f"{name}\nCurrent: {formatter(value_current)} (Default: {formatter(value_default)})\n\nChoose new value: "
    )}


def prompt_new_natural(attr: str, value_current: int, value_default: int) -> int:
    name, formatter = job_settings_formatter[attr]

    return {attr: prompt_range_integer(
        f"{name}\nCurrent: {formatter(value_current)} (Default: {formatter(value_default)})\n\nChoose new value: ",
        value_min=1, 
        value_max=float("inf"),
    )}


def prompt_new_directory(allow_empty: bool = False) -> Callable[[str, str, str], str]:
    def prompt(attr: str, value_current: str, value_default: str) -> str:
        name, formatter = job_settings_formatter[attr]

        return {attr: prompt_path(
            f"{name}\nCurrent: {formatter(value_current)} (Default: {formatter(value_default)})\n\nChoose new value: ",
            path_type="directory",
            value_allow_empty=allow_empty,
            value_suggestion=formatter(value_default) if allow_empty else None
        )}


    return prompt


def prompt_new_file(allow_empty: bool = False) -> Callable[[str, str, str], str]:
    def prompt(attr: str, value_current: str, value_default: str) -> str:
        name, formatter = job_settings_formatter[attr]
        
        path = prompt_path(
            f"{name}\nCurrent: {formatter(value_current)} (Default: {formatter(value_default)})\n\nChoose new value: ",
            path_type="file",
            value_allow_empty=allow_empty,
            value_suggestion=formatter(value_default) if allow_empty else None
        )

        if allow_empty and path == formatter(value_default):
            path = ""


        return {attr: path}


    return prompt


def prompt_new_script(attr: str, value_current: str, value_default: str) -> str:
    # Get display name and value formatter
    name, formatter = job_settings_formatter[attr]
    
    # Prompt for value
    value_new = prompt_string(
        f"{name}\nCurrent: {formatter(value_current)} (Default: {formatter(value_default)})\n\nChoose new value: ",
    )
    
    # If python script and missing python, prompt whether should add
    if value_new.endswith(".py") and not value_new.startswith("python "):
        if prompt_boolean("Python script detected without call to python.\n\nPrepend 'python ' to command (Recommended: yes)?"):
            value_new = "python " + value_new


    # Return new attribute value pair
    return {attr: value_new}


def prompt_new_time(attr: str, value_current: str, value_default: str) -> str:
    name, formatter = job_settings_formatter[attr]

    return {attr: prompt_regex(
        f"{name}\nCurrent: {formatter(value_current)} (Default: {formatter(value_default)})\n\nChoose new value: ",
        re.compile(r"^\d{1,2}:\d{1,2}$")
    )}


def prompt_new_queue(attr: str, value_current: str, value_default: str) -> str:
    name, formatter = job_settings_formatter[attr]
    
    queue_cpu = ["hpc", "epyc", "milan", "rome", ]
    queue_gpu = ["gpuv100", "gpua100", "gpua10", "gpua40", "gpuk40", "gpuamd"]
    queue = queue_cpu + queue_gpu
    
    response = prompt_choice(
        f"{name}\nCurrent: {formatter(value_current)} (Default: {formatter(value_default)})\n\nChoose new value: ",
        [queue_cpu, queue_gpu],
    )
    
    queue_chosen = queue[int(response)-1]


    return {attr: queue_chosen, 
            nameof(JobSettings.is_gpu_queue): queue_chosen in queue_gpu}



job_settings_prompter: dict[str, Callable[[str, str, str], Union[str, int]]] = lambda: {
    f"{nameof(JobSettings.name)}": prompt_new_string(allow_empty=False),
    f"{nameof(JobSettings.env_name)}": prompt_new_string(allow_empty=False),
    f"{nameof(JobSettings.env_on_done_delete)}": prompt_new_boolean,

    f"{nameof(JobSettings.working_dir)}": prompt_new_directory(allow_empty=True),
    f"{nameof(JobSettings.env_file)}": prompt_new_file(allow_empty=True),
    f"{nameof(JobSettings.req_file)}": prompt_new_file(allow_empty=True),
    f"{nameof(JobSettings.script)}": prompt_new_script,

    f"{nameof(JobSettings.time_max)}": prompt_new_time,
    f"{nameof(JobSettings.queue)}": prompt_new_queue,
    # Skipping: is_gpu_queue

    f"{nameof(JobSettings.cpu_cores)}": prompt_new_natural,
    f"{nameof(JobSettings.cpu_mem_per_core_mb)}": prompt_new_natural,
    f"{nameof(JobSettings.cpu_mem_max_gb)}": prompt_new_natural,

    f"{nameof(JobSettings.email)}": prompt_new_string(allow_empty=True),

    # Skipping: version
}


# Mapping dictionary string keys
job_settings_name_to_attr: dict[str, str] = lambda: {
    name: attr_name
    for attr_name, (name, _) in job_settings_formatter.items()
}



# Prompts
def prompt_settings(settings_current: JobSettings) -> Optional[JobSettings]:
    """Prompts user to change job settings

    Args:
        settings_current (JobSettings): Current job settings

    Returns:
        Optional[JobSettings]: New job settings or None if canceled
    """
    global module_initialized, job_settings_formatter, job_settings_prompter, job_settings_name_to_attr

    # If module not initialized, initialize
    if not module_initialized:
        job_settings_formatter = job_settings_formatter()
        job_settings_prompter = job_settings_prompter()
        job_settings_name_to_attr = job_settings_name_to_attr()
        
        module_initialized = True


    # Store settings
    settings_default = JobSettings()
    settings = settings_current

    # Loop untill save or cancel
    while True:
        # Map job settings attribute name to value
        settings_attr_to_value = {
            key: getattr(settings, key) 
            for key in job_settings_formatter
        }

        # List of (formatted name, formatted value)
        settings_name_formatted_value = [
            (name, format(settings_attr_to_value[attr])) 
            for attr, (name, format) in job_settings_formatter.items()
        ]
        
        # List of formatted names
        settings_names = [name for name, _ in settings_name_formatted_value]


        # Prompt to choose between job settings and save/cancel
        response_name = prompt_choice(
            "Choose setting to change",
            choices=[settings_name_formatted_value, [["Save"], ["Cancel"]]],
            index=[[str(i+1) for i in range(len(settings_name_formatted_value))], ["s", "c"]],
            headers=["Setting", "Value"]
        )


        # If save settings, return new settings
        if response_name == "s":
            return settings
        # Else if cancel, return nothing to mean no saving
        elif response_name == "c":
            return None
        # Else, change setting and reprompt for additional changes
        else:
            # Convert name index to name
            response_name = settings_names[int(response_name)-1]
            # Convert name to attribute name
            attr = job_settings_name_to_attr[response_name]

            # Prompt for new value(s)
            response_values = job_settings_prompter[attr](
                attr,
                settings_attr_to_value[attr], 
                getattr(settings_default, attr)
            )

            # Update job settings with new value(s)
            settings = replace(settings, **response_values)



def prompt_job_active(jobs_active: dict[str, JobDetails] = None) -> Optional[JobDetails]:
    """Prompts user to select active job
    
    Args:
        jobs_active (dict[str, JobDetails], optional): Active jobs. Defaults to None, which retrieves current active jobs.

    Returns:
        JobDetails, optional: Selected job
    """
    if jobs_active is None:
        # Get active job details
        job_details = get_jobs_active()
    else:
        job_details = jobs_active

    # If no active jobs, return nothing
    if len(job_details) == 0:
        return None


    # Prompt to select job
    response = prompt_choice(
        "Choose job",
        choices=[
            [[job.name_short, job.job_id, job.queue, job.status, job.time_start, job.time_elapsed]
                for job in job_details.values()], 
            [["Cancel"]]
        ],
        index=[[str(i+1) for i in range(len(job_details))], ["c"]],
        headers=["Name", "Job ID", "Queue", "Status", "Start", "Elapsed"],
        # WARN: Low job ID's will clash with indexes. Assuming job ID's are above a thousand.
        value_suggestions=[job.job_id for job in job_details.values()] + ["Cancel"]
    )

    # If cancel, return nothing to mean no selection
    if response == "c":
        return None
    # Else, return job details
    else:
        return list(job_details.values())[int(response)-1]



def prompt_jobs_active(jobs_active: dict[str, JobDetails] = None) -> dict[str, JobDetails]:
    """Prompts user to select active jobs
    
    Args:
        jobs_active (dict[str, JobDetails], optional): Active jobs. Defaults to None, which retrieves current active jobs.

    Returns:
        dict[str, JobDetails]: Selected jobs
    """
    if jobs_active is None:
        # Get active job details
        job_details = get_jobs_active()
    else:
        job_details = jobs_active

    # If no active jobs, return nothing
    if len(job_details) == 0:
        return {}

    # List of selected jobs
    selected = [False] * len(job_details)

    # Continue prompting until jobs have been selected
    while True:
        # Prompt to toggle job selection and finish/cancel
        response = prompt_choice(
            "Choose job(s)",
            choices=[
                [['X' if selected[i] else " ", job.name_short, job.job_id, job.queue, job.status, job.time_start, job.time_elapsed]
                    for i, job in enumerate(job_details.values())], 
                [['', "Finish"], ['', "Cancel"]]
             ],
            index=[[str(i+1) for i in range(len(selected))], ["f", "c"]],
            headers=["", "Name", "Job ID", "Queue", "Status", "Start", "Elapsed"],
            # WARN: Low job ID's will clash with indexes. Assuming job ID's are above a thousand.
            value_suggestions=[job.job_id for job in job_details.values()] + ["Finish", "Cancel"]
        )


        # If finish selection, return selection
        if response == "f":
            return {job.job_id: job for selected, job in zip(selected, job_details.values()) if selected}
        # Else if cancel, return nothing to mean no selection
        elif response == "c":
            return {}
        # Else, toggle job selection
        else:
            selected[int(response)-1] = not selected[int(response)-1]

