from prompt import prompt_integer, prompt_string, prompt_list
from lsf import JobSettings, JobDetails, get_active_jobs




def prompt_settings(suggested_settings: JobSettings) -> JobSettings:
    pass
    # TODO: No spaces in job name nor env name
    
    
def prompt_active_jobs() -> str:
    # Get active job details
    job_details = get_active_jobs()
    # Prompt user for an active job
    job_id = prompt_list(job_details)
    
    # Return chosen job ID
    return job_id
