from varname import nameof
from typing import Callable, Optional, Any, Union
from os import getcwd
from tabulate import tabulate
from dataclasses import replace
import re

from prompt import prompt_base, prompt_range_integer, prompt_path, prompt_string, prompt_regex, prompt_boolean, prompt_choice
from lsf import JobSettings, JobDetails, get_active_jobs


# Formatting
def as_is(object: Any) -> str:
    return str(object)

def as_is_boolean(object: bool) -> str:
    return as_is(object).lower()

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
        ("Auto-delete environment", as_is_boolean),

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


# Prompting
def prompt_new_string(attr: str, value_current: str, value_default: str) -> str:
    name, formatter = job_settings_formatter[attr]

    return {attr: prompt_string(
        f"{name}\nCurrent: {formatter(value_current)} (Default: {formatter(value_default)})\n\nChoose new value: ",
        str_disallowed=[" "],
    )}


def prompt_new_boolean(attr: str, value_current: bool, value_default: bool) -> bool:
    name, formatter = job_settings_formatter[attr]

    return {attr: prompt_boolean(
        f"{name}\nCurrent: {formatter(value_current)} (Default: {formatter(value_default)})\n\nChoose new value: ",
        value_true=["true"],
        value_false=["false"]
    )}


def prompt_new_natural(attr: str, value_current: int, value_default: int) -> int:
    name, formatter = job_settings_formatter[attr]

    return {attr: prompt_range_integer(
        f"{name}\nCurrent: {formatter(value_current)} (Default: {formatter(value_default)})\n\nChoose new value: ",
        value_min=1, 
        value_max=float("inf"),
    )}


def prompt_new_directory(attr: str, value_current: str, value_default: str) -> str:
    name, formatter = job_settings_formatter[attr]

    return {attr: prompt_path(
        f"{name}\nCurrent: {formatter(value_current)} (Default: {formatter(value_default)})\n\nChoose new value: ",
        path_type="directory"
    )}


def prompt_new_file(attr: str, value_current: str, value_default: str) -> str:
    name, formatter = job_settings_formatter[attr]

    return {attr: prompt_path(
        f"{name}\nCurrent: {formatter(value_current)} (Default: {formatter(value_default)})\n\nChoose new value: ",
        path_type="file"
    )}


def prompt_new_time(attr: str, value_current: str, value_default: str) -> str:
    name, formatter = job_settings_formatter[attr]

    return {attr: prompt_regex(
        f"{name}\nCurrent: {formatter(value_current)} (Default: {formatter(value_default)})\n\nChoose new value: ",
        re.compile(r"^\d{1,2}:\d{1,2}$")
    )}


def prompt_new_queue(attr: str, value_current: str, value_default: str) -> str:
    name, formatter = job_settings_formatter[attr]
    
    
    queue =     ["hpc", "gpuv100", "gpua100"]
    queue_gpu = ["gpuv100", "gpua100"]

    
    response = prompt_choice(
        f"{name}\nCurrent: {formatter(value_current)} (Default: {formatter(value_default)})\n\nChoose new value: ",
        queue
    )
    
    queue_chosen = queue[int(response)]


    return {attr: queue_chosen, 
            nameof(JobSettings.is_gpu_queue): queue_chosen in queue_gpu}



job_settings_prompter: dict[str, Callable[[str, str, str], Union[str, int]]] = {
    f"{nameof(JobSettings.name)}": prompt_new_string,
    f"{nameof(JobSettings.env_name)}": prompt_new_string,
    f"{nameof(JobSettings.env_on_done_delete)}": prompt_new_boolean,

    f"{nameof(JobSettings.working_dir)}": prompt_new_directory,
    f"{nameof(JobSettings.env_spec)}": prompt_new_file,
    f"{nameof(JobSettings.script)}": prompt_new_string,

    f"{nameof(JobSettings.time_max)}": prompt_new_time,
    f"{nameof(JobSettings.queue)}": prompt_new_queue,
    # Skipping: is_gpu_queue

    f"{nameof(JobSettings.cpu_cores)}": prompt_new_natural,
    f"{nameof(JobSettings.cpu_mem_per_core_mb)}": prompt_new_natural,
    f"{nameof(JobSettings.cpu_mem_max_gb)}": prompt_new_natural,

    f"{nameof(JobSettings.email)}": prompt_new_string,

    # Skipping: version
}


# Mapping
job_settings_name_to_attr: dict[str, str] = {
    name: attr_name
    for attr_name, (name, _) in job_settings_formatter.items()
}


def prompt_settings(settings_suggested: JobSettings) -> Optional[JobSettings]:
    """_summary_

    Args:
        suggested_settings (JobSettings): _description_

    Returns:
        JobSettings: _description_
    """
    settings_default = JobSettings()
    settings = settings_suggested

    
    while True:
        settings_attr_to_value = {
            key: getattr(settings, key) 
            for key in job_settings_formatter
        }
        
        settings_name_formatted_value = [
            (name, format(settings_attr_to_value[attr])) 
            for attr, (name, format) in job_settings_formatter.items()
        ]
        
        settings_names = [name for name, _ in settings_name_formatted_value]

        
        response_name = prompt_choice(
            "Choose setting to change",
            choices=[settings_name_formatted_value] + [[["Save"], ["Cancel"]]],
            index=[[str(i) for i in range(len(settings_name_formatted_value))]] + [["s", "c"]],
            headers=["Setting", "Value"]
        )


        # If save settings, return new settings
        if response_name == "s":
            return settings
        # Else, return nothing to mean no settings
        elif response_name == "c":
            return None
        

        response_name = settings_names[int(response_name)]

        attr = job_settings_name_to_attr[response_name]
        response_values = job_settings_prompter[attr](
            attr,
            settings_attr_to_value[attr], 
            getattr(settings_default, attr)
        )
        
        
        settings = replace(settings, **response_values)


    # TODO: fill out description and comments for function



def prompt_active_jobs() -> Optional[str]:
    # Get active job details
    job_details = get_active_jobs()
    
    # If no active jobs, return None
    if len(job_details) == 0:
        return None


    # Prompt user for an active job
    # TODO: Finish prompting for job
    job_id = prompt_choice(job_details)
    
    # Return chosen job ID
    return job_id
