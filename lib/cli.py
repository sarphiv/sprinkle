import os
import traceback
from typing import Optional

from constants import sprinkle_project_settings_export_file
from lsf import JobSettings, generate_bsub_script, kill_jobs, load_settings, save_settings, submit_job
from lsf_prompt import prompt_settings


doc_short = \
"""
Usage:
  sprinkle start [--] [<args>...]
  sprinkle stop [<job_id>... | -a | --all]
  sprinkle view [((output | log | error) <job_id>)]
  sprinkle status
  sprinkle settings
  sprinkle export [<path>]
  sprinkle [help | --help | -h | -?]

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

  sprinkle export [<path>]
    Export submission script to path. 
    Defaults to working directory.

  sprinkle [help | -h | -? | --help]
    Show this screen.


Options:
  -h -? --help       Show full help text.
  -a --all           Kill all jobs
"""


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



    def start(arguments: Optional[list[str]]) -> int:
        # Load settings
        settings = Command._load_or_create_settings()
        # If no settings, return failure
        if not settings:
            return 1


        # Submit job script
        job_id = submit_job(settings)

        # Print job ID
        print(f'Started job (Name: "{settings.name}", ID: "{job_id}", Command: "{settings.script} {arguments}")')


        # Return successful
        return True



    def stop(args) -> bool:
        if len(args) == 0:
            # TODO: list prompt to select jobs to kill
            # TODO: Remember option to kill all jobs
            pass
        elif len(args) == 1 and args[0] == "--all":
            # TODO: Kill all
            pass
        else:
            # TODO: Kill selected
            killed_job_ids, not_killed_job_ids = kill_jobs(*args)



    def view(args) -> bool:
        # TODO: Not implemented
        pass



    def status() -> bool:
        # TODO: Output status overview of job details
        pass


 
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



    def export(path: Optional[str]) -> int:
        # If no save path provided, use default path
        if not path:
            path = sprinkle_project_settings_export_file


        # Load settings
        settings = Command._load_or_create_settings()
        # If no settings, return failure
        if not settings:
            return 1


        # Get submission script
        script = generate_bsub_script(settings)

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