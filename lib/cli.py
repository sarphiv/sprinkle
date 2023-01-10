import os
import traceback
from typing import Union, Optional, Literal

from tabulate import tabulate

from constants import sprinkle_project_settings_export_file
from lsf import JobSettings, generate_bsub_script, kill_jobs, load_settings, save_settings, submit_job, get_jobs_active, view_job
from lsf_prompt import prompt_settings, prompt_job_active, prompt_jobs_active
from prompt import prompt_choice



doc_short = \
"""
Usage:
  sprinkle start [--] [<args>...]
  sprinkle stop [<job_id>... | -a | --all]
  sprinkle view [((output | log | error) <job_id>)]
  sprinkle status
  sprinkle settings
  sprinkle export [<path>] [--] [<args>...]
  sprinkle [help | -h | -? | --help]

Options:
  -h -? --help       Show full help text.
  -a --all           Kill all jobs
"""

doc_full = \
"""
Sprinkle streamlines management of LSF jobs.

Project repository: https://github.com/sarphiv/sprinkle


Usage:
  sprinkle start [--] [<args>...]
    Submit the job script and pass <args> to job script.
    If <args> contains dashes, add the two dashes "--" before <args>.

  sprinkle stop [<job_id>... | -a | --all]
    Stop specific jobs or all jobs.
    If nothing specified, prompt to select job to kill.

  sprinkle view [((output | log | error) <job_id>)]
    View output, log, or errors of a specific job.

  sprinkle status
    See overview of job details.

  sprinkle settings
    Set up or change existing job settings.

  sprinkle export [<path>] [<args>...]
    Export submission script to path. 
    If <args> contains dashes, add the two dashes "--" before <args>.
    Defaults to working directory.

  sprinkle [help | -h | -? | --help]
    Show this screen.


Options:
  -h -? --help       Show full help text.
  -a --all           Kill all jobs
"""



# TODO: Add docstrings

class Command:
    def _load_or_create_settings() -> Optional[JobSettings]:
        # Load settings
        settings = load_settings()

        # If no settings available, attempt creating
        if not settings:
            # Prompt for settings
            settings = prompt_settings(JobSettings())
            
            # If settings prompt cancelled, return failure
            if not settings:
                return None

            # Save new settings
            save_settings(settings)


        # Return populated settings
        return settings



    def start(args: list[str] = []) -> int:
        # Load settings
        settings = Command._load_or_create_settings()
        # If no settings, return failure
        if not settings:
            return 1


        # Check if environment file exists, inform and fail if not
        working_directory_old = os.getcwd()
        working_directory_new = settings.working_dir or working_directory_old

        os.chdir(working_directory_new)
        environment_exists = os.path.isfile(settings.env_file)
        os.chdir(working_directory_old)

        if not environment_exists:
            print(f'Environment file "{settings.env_file}" does not exist in working directory "{working_directory_new}"')
            return 1


        # Submit job script
        job_id = submit_job(settings, args)

        # Print job ID
        print(f'Started job (Name: "{settings.name}", ID: "{job_id}", Script: "{settings.script} {" ".join(args)}")')


        # Return successful
        return True



    def stop(job_ids: Union[Literal["all"], list[str]] = []) -> int:
        # WARN: Not handling case where jobs finish while executing this code

        # Get active jobs 
        job_active = get_jobs_active()
        job_start_ids = set(job_active.keys())
        job_not_found_ids = set()
        
        # If no jobs available, inform and exit
        if len(job_start_ids) == 0:
            print("No active jobs to stop")
            return 1


        # If all jobs should be killed, mark all for killing
        if job_ids == "all":
            job_kill_ids = job_start_ids
        # Else if no jobs provided, prompt for active jobs to kill, exit if none
        elif len(job_ids) == 0:
            job_kill_ids = set(prompt_jobs_active(job_active).keys())

            if len(job_kill_ids) == 0:
                print("No jobs selected to stop")
                return 1
        # Else jobs provided, mark selected active jobs for killing
        else:
            job_query_ids = set(job_ids)
            job_kill_ids = job_start_ids & job_query_ids
            job_not_found_ids = job_query_ids - job_kill_ids
        

        # Send kill signal
        job_killed_ids, job_alive_ids = kill_jobs(list(job_kill_ids))


        # Track whether any jobs were killed and that all were killed successfully.
        # Inform of the above status.
        success = False

        if len(job_killed_ids) > 0:
            print(f"Successfully killed job(s): {', '.join(job_killed_ids)}")
            success = True

        if len(job_alive_ids) > 0:
            print(f"Failed killing job(s): {', '.join(job_alive_ids)}")
            success = False

        if len(job_not_found_ids) > 0:
            print(f"Failed finding job(s): {', '.join(job_not_found_ids)}")
            success = False


        # Return exit code
        return 0 if success else 1



    def view(type: Optional[Literal["output", "log", "error"]], job_id: Optional[str]) -> int:
        # NOTE: Because of docpie, either both are none, or both are not none
        if not type and not job_id:
            # Prompt for type
            types = ["Output", "Log", "Error"]
            type = prompt_choice(
                "Choose view type", 
                choices=[types, ["Cancel"]],
                index=[[str(i) for i in range(len(types))], ['c']]
            )
            
            if type == 'c':
                print("No view type selected")
                return 1
            else:
                type = types[int(type)]


            # Prompt for active job
            job_details = prompt_job_active()

            if job_details is None:
                print("No job selected to view")
                return 1
            else:
                job_id = job_details.job_id
            

        # View job
        success = view_job(type, job_id)

        # Return exit code
        return 0 if success else 1



    def status() -> int:
        # Coalesce nothing
        def na(value: str) -> str:
            return value if value else "N/A"
        
        # Get active jobs
        jobs_active = get_jobs_active()


        # If no jobs, inform and exit failure
        if len(jobs_active) == 0:
            print("No active jobs to show")
            
            return 1
        # Else, display jobs and exit success
        else:        
            print(tabulate(
                [[job.name_short, job.job_id, job.queue, 
                job.status, na(job.cpu_usage), na(job.mem_usage), na(job.mem_usage_avg), na(job.mem_usage_max), 
                job.time_start, job.time_elapsed]
                for job in jobs_active.values()],
                headers=["Name", "Job ID", "Queue", "Status", "CPU", "MEM", "Avg", "Max", "Started", "Elapsed"]
            ))

            return 0

 
    def settings() -> int:
        # Load settings
        settings = load_settings() or JobSettings()
        
        # Prompt about settings
        settings = prompt_settings(settings)
        
        # If settings changed, save settings and return success
        if settings:
            save_settings(settings)
            return 0
        # Else settings not changed, return failure
        else:
            return 1



    def export(path: Optional[str], args: list[str] = []) -> int:
        # If no save path provided, use default path
        if not path:
            path = sprinkle_project_settings_export_file


        # Load settings
        settings = Command._load_or_create_settings()
        # If no settings, return failure
        if not settings:
            return 1


        # Get submission script
        script = generate_bsub_script(settings, args)

        # Attempt writing script to file
        try:
            # Create parent directories
            path_dirs = os.path.dirname(path)
            if path_dirs:
                os.makedirs(path_dirs, exist_ok=True)

            # Write script to file
            with open(path, "w") as file:
                file.write(script)
                file.flush()
        # Any failure, inform and return failure
        except:
            traceback.print_exc()
            print(f"Failed writing to file at: {path}")
            return 1


        # Inform success
        print(f"Successfully exported submission script to: {path}")

        # Return successful
        return 0



    def help() -> int:
        print(doc_full)

        return 0