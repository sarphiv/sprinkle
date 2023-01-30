import os
import traceback
from typing import Union, Optional, Literal
from dataclasses import replace
from varname import nameof

from tabulate import tabulate

from constants import sprinkle_project_settings_export_file
from lsf import JobSettings, generate_bsub_script, kill_jobs, load_settings, save_settings, submit_job, get_jobs_active, view_job
from lsf_prompt import prompt_settings, prompt_job_active, prompt_jobs_active
from conda import ensure_environment_specification_exists, delete_environment, recreate_environment, exists_environment
from prompt import prompt_choice


# NOTE: Remember to update both doc_short and doc_full
doc_short = \
"""
Usage:
  sprinkle start [--] [<args>...]
  sprinkle stop [<job_id>... | -a | --all]
  sprinkle view [((output | log | error) [<job_id>])] [-a | --all]
  sprinkle status
  sprinkle settings
  sprinkle setup [-d | --delete]
  sprinkle export [<path>] [--] [<args>...]
  sprinkle update
  sprinkle [help | -h | -? | --help]

Options:
  -h -? --help       Show full help text.
  -a --all           For start, kill all jobs; For view, view full file.
  -d --delete        Delete environment without recreating it.
"""

# NOTE: Remember to update README.md
doc_full = \
"""
Sprinkle streamlines management of LSF jobs.

Project repository: https://github.com/sarphiv/sprinkle

In the below, "spr" may be used as a shorthand for "sprinkle".


Usage:
  sprinkle start [--] [<args>...]
    Submit the job script and pass <args> to job script.
    If settings have not been setup, prompt to set them up.
    If environment has not been setup, sets it up.
    If <args> contains dashes, add the two dashes "--" before <args>.

  sprinkle stop [<job_id>... | -a | --all]
    Stop specific jobs or all jobs.
    If nothing specified, prompt to select job to kill.

  sprinkle view [((output | log | error) [<job_id>])] [-a | --all]
    View output, log, or errors of a specific job.

  sprinkle status
    See overview of job details.

  sprinkle settings
    Set up or change existing job settings.
    
  sprinkle setup [-d | --delete]
    Set up job environment (or recreates it in case of changes).
    If settings have not been setup, prompt to set them up.

  sprinkle export [<path>] [<args>...]
    Export submission script to <path> that passes <args> to the job script.
    If <args> contains dashes, add the two dashes "--" before <args>.
    Defaults to working directory.
    
  sprinkle update
    Update sprinkle to latest version.

  sprinkle [help | -h | -? | --help]
    Show this screen.


Options:
  -h -? --help       Show full help text.
  -a --all           For start, kill all jobs; For view, view full file.
  -d --delete        Delete environment without recreating it.
"""



class Command:
    def _check_environment_specification_exists(settings: JobSettings, inform: bool = False) -> bool:
        """Check whether environment specification exists.
        
        Args:
            settings {JobSettings}: Settings to base the check on
            inform {bool}: Whether to inform of missing files (default: {False})
        
        Returns:
            bool: True if both files exist
        """
        # Check for file existence
        environment_exists = os.path.isfile(settings.env_file)
        requirements_exists = os.path.isfile(settings.req_file)


        # Inform of missing files
        if inform:
            if not environment_exists:
                print(f'ERROR: Environment file "{settings.env_file}" does not exist')
            if not requirements_exists:
                print(f'ERROR: Requirements file "{settings.req_file}" does not exist')


        # Return whether both files exist
        return environment_exists and requirements_exists


    def _ensure_project_initialized() -> Optional[JobSettings]:
        """Load settings, or create new settings via prompt if none exist.
        Also auto-generates the environment.yml and requirements.txt files if they don't exist.
        
        Returns:
            Optional[JobSettings]: Loaded or created settings.
        """
        # Load settings
        settings = load_settings()
        settings_loaded = bool(settings)

        # Ensure environment.yml and requirements.txt equivalents exist
        settings_new, modified = ensure_environment_specification_exists(settings)


        # If settings valid and were modified, save
        if settings_new and modified:
            save_settings(settings_new)

        # If settings successfully loaded and environment initialized, return settings
        if settings_new:
            return settings_new

        # If settings loaded but environment not initialized, inform and return failure
        if settings_loaded:
            Command._check_environment_specification_exists(settings, inform=True)
            return None


        # Settings do not exist, create new default settings
        settings = JobSettings()

        
        # Initialize settings to environment and requirements files if present
        if os.path.isfile(JobSettings.defaults.env_file()):
            settings = replace(settings, **{nameof(JobSettings.env_file): JobSettings.defaults.env_file()})
        if os.path.isfile(JobSettings.defaults.req_file()):
            settings = replace(settings, **{nameof(JobSettings.req_file): JobSettings.defaults.req_file()})


        # Prompt for initial setup of settings
        settings = prompt_settings(settings)


        # If settings prompt cancelled, return failure
        if not settings:
            return None


        # Save intermediate settings
        save_settings(settings)


        # Ensure environment initialized
        settings_new, modified = ensure_environment_specification_exists(settings)

        # If not, inform and return failure
        if not settings_new:
            Command._check_environment_specification_exists(settings, inform=True)
            return None


        # If settings modified, save
        if modified:
            save_settings(settings_new)


        # Return populated settings
        return settings_new



    def start(args: list[str] = []) -> int:
        """Start a new job, passing args to job script.
        
        Args:
            args (list[str], optional): Arguments to pass to job script. Defaults to [].
        
        Returns:
            int: 0 if successful, 1 if failure.
        """
        # Load settings
        settings = Command._ensure_project_initialized()
        # If no settings, return failure
        if not settings:
            return 1


        # If environment not yet set up, set it up
        if not exists_environment(settings.env_name):
            recreate_environment(settings.env_name, settings.env_file, output=True)


        # Check if environment and requirements files exists, inform and fail if not
        if not Command._check_environment_specification_exists(settings, inform=True):
            return 1


        # Submit job script
        job_id = submit_job(settings, args)

        # Print job ID
        print(f'Started job (Name: "{settings.name}", ID: "{job_id}", Script: "{settings.script} {" ".join(args)}")')


        # Return successful
        return True



    def stop(job_ids: Union[Literal["all"], list[str]] = []) -> int:
        """Stop jobs, either by ID or all jobs.
        
        Args:
            job_ids (Union[Literal["all"], list[str]], optional): Job IDs to stop or the string all. Defaults to [].
        
        Returns:
            int: 0 if successful, 1 if failure.
        """
        
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



    def view(type: Optional[Literal["output", "log", "error"]], job_id: Optional[str], all: bool) -> int:
        """View output, log, or errors of a specific job.
        
        Args:
            type (Optional[Literal["output", "log", "error"]], optional): Type of view. Defaults to None which prompts for a view.
            job_id (Optional[str], optional): Job ID to view. Defaults to None which prompts for an active job.
            all (bool): Whether to view the full file.
        
        Returns:
            int: 0 if successful, 1 if failure.
        """

        # If no job ID provided, prompt for job ID
        if not job_id:
            # Get active jobs
            job_active = get_jobs_active()
            
            # If no active jobs, inform and exit failure
            if len(job_active) == 0:
                print("No active jobs to view")
                return 1

            # Prompt for active job
            job_details = prompt_job_active(job_active)

            if job_details is None:
                print("No job selected to view")
                return 1
            else:
                job_id = job_details.job_id


        # If no view type provided, prompt for type
        if not type:
            types = ["Output", "Log", "Error"]
            type = prompt_choice(
                "Choose view type", 
                choices=[types, ["Cancel"]],
                index=[[str(i+1) for i in range(len(types))], ['c']]
            )
            
            if type == 'c':
                print("No view type selected")
                return 1
            else:
                type = types[int(type)-1].lower()



        # View job
        success = view_job(type, job_id, all)


        # If not successful, inform
        if not success:
            print(
                "Failed viewing job. This could be because of multiple reasons.\n" + 
                "1. The job does not exist for this project directory.\n" +
                "Please ensure you are in the correct project directory for the selected job.\n" + 
                "2. The job may not yet have started as it is still setting up its environment.\n" +
                "Please wait a minute and try again." +
                (("\n" +
                  "3. The job crashed, so it does not have any output.\n" + 
                  "Try investigating by running: sprinkle view error <job_id>")
                    if type == "output" 
                    else "")
            )

        # Return exit code
        return 0 if success else 1



    def status() -> int:
        """Display status of active jobs.
        
        Returns:
            int: 0 if successful, 1 if failure.
        """
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
        """Prompt user for job settings, and save settings.
        
        Returns:
            int: 0 if settings changed, 1 if settings not changed.
        """
        # Load settings
        settings = load_settings() or JobSettings()
        
        # Prompt about settings
        settings = prompt_settings(settings)

        # If cancelled, return failure
        if not settings:
            return 1

        # Save intermediate settings
        save_settings(settings)
        
        
        # Ensure environment initialized
        settings_new, modified = ensure_environment_specification_exists(settings)
        # If not, inform and return failure
        if not settings_new:
            Command._check_environment_specification_exists(settings, inform=True)
            return 1

        # If settings modified, save
        if modified:
            save_settings(settings_new)


        # Return success
        return 0



    def setup(delete: bool = False) -> int:
        """Recreate environment.
        
        Args:
            delete (bool, optional): Whether to only delete environment. Defaults to False.
        
        Returns:
            int: 0 if successful, 1 if failure.
        """
        # Load settings
        settings = Command._ensure_project_initialized()
        # If no settings, return failure
        if not settings:
            return 1

        # If delete only, delete environment
        if delete:
            return 1 if delete_environment(settings.env_name, output=True) else 0
        # Else, recreate environment
        else:
            return 1 if recreate_environment(settings.env_name, settings.env_file, output=True) else 0



    def export(path: Optional[str], args: list[str] = []) -> int:
        """Export a submission script to a file.
        
        Args:
            path (Optional[str], optional): Path to save submission script to. Defaults to None which uses default path.
            args (list[str], optional): Additional arguments to pass to submission script. Defaults to [].
        
        Returns:
            int: 0 if successful, 1 if failure.
        """

        # If no save path provided, use default path
        if not path:
            path = sprinkle_project_settings_export_file


        # Load settings
        settings = Command._ensure_project_initialized()
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
        """Display help documentation.
        
        Returns:
            int: 0 meaning success. Always.
        """
        print(doc_full)

        return 0