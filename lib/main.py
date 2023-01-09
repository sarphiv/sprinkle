doc_short = \
"""
Usage:
  sprinkle start [--] [<args>...]
  sprinkle stop [<job_id>... | -a | --all]
  sprinkle view [((output | log | error) <job_id>)]
  sprinkle status
  sprinkle settings
  sprinkle export [path]
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

  sprinkle export [path]
    Export submission script to path. 
    Defaults to working directory.

  sprinkle [help | -h | -? | --help]
    Show this screen.


Options:
  -h -? --help       Show full help text.
  -a --all           Kill all jobs
"""


import sys
import inspect
from typing import Optional

from docpie import docpie

from lsf import JobSettings, generate_bsub_script, kill_jobs, load_settings, save_settings, submit_job
from lsf_prompt import prompt_settings





class Command:
    def start(arguments: Optional[str]) -> bool:
        # Load settings
        settings = load_settings()
        # If no settings loaded, create and save settings
        if not settings:
            settings = prompt_settings(JobSettings())
            save_settings(settings)
        
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


    def settings() -> bool:
        # Load settings
        settings = load_settings() or JobSettings()
        
        # Prompt about settings
        settings = prompt_settings(settings)
        
        # Save settings
        save_settings(settings)


        # Return successful
        return True


    def export(args) -> bool:
        # Load settings
        settings = load_settings()
        # If no settings loaded, create and save settings
        if not settings:
            settings = prompt_settings(JobSettings())
            save_settings(settings)


        if len(args) == 0:
            path = sprinkle_project_settings_export_file
        elif len(args) == 1:
            # TODO: Verify path is a file path
            # TODO: Create necessary folders
            
            path = args[0]
        else:
            # TODO: inform of incorrect usage
            pass
            
            
        # Save export to chosen path
        script = generate_bsub_script(settings)
        # TODO: Write contents to chosen path


        # Return successful
        return True
    
    
    def help() -> int:
        print(doc_full)
        return 0



try:
    # Parse args with docpie
    args = docpie(doc_short, help=False, attachvalue=False, appearedonly=True)
    # Filter empty args
    args = { 
        key: value 
        for key, value 
        in args.items() 
        if value != False 
           and not (    isinstance(value, list) 
                    and len(value) == 0)
    }


    
    thing = prompt_settings(JobSettings())
    print(thing)

    if "start" in args:
        pass
    elif "stop" in args:
        pass
    elif "view" in args:
        pass
    elif "status" in args:
        pass
    elif "settings" in args:
        pass
    elif "export" in args:
        pass
    elif len(args) == 0 or len({"help", "--help", "-h", "-?"}.intersection(args)) > 0:
        exit_code = Command.help()
    else:
        exit_code = 1


    # Exit with exit code from above
    exit(exit_code)

except (KeyboardInterrupt, EOFError):
    exit(-1)


# print(f'Suggested values: {["@student.dtu.dk", "@dtu.dk" "@gmail.com", "gmail.dk", "@yahoo.com", "yahoo.dk" "hotmail.com" "@hotmail.dk", "@outlook.com", "@outlook.dk", "@msn.dk", "@msn.com"]:<8}')

# completer = FuzzyWordCompleter(["@student.dtu.dk", "@dtu.dk" "@gmail.com", "gmail.dk", "@yahoo.com", "yahoo.dk" "hotmail.com" "@hotmail.dk", "@outlook.com", "@outlook.dk", "@msn.dk", "@msn.com"])
# validator = ThreadedValidator(Validator.from_callable(lambda text: text.isdigit()))


# print("test me")

# exit(0)




#TODO: Ok, maybe MVP first instead...
#TODO: file for default bsub options, and base recommendations off of these
#TODO: Save bsub options in file and output status whether this file exists for the project yet (in current working directory)
#TODO: When trying to edit options again, display current settings instead of default recommendations
#TODO: running start, just submits based off of the options
#TODO: Options selection screen with overview, select option to open prompt
    #TODO: Allow users to also input arguments for their script target
    #TODO: Ability to use sprinkle by e.g. 
    #  sprinkle start [args...] (if no options for project, prompt user for first time project setup)
    #  sprinkle stop [(job id [job_id ...]) | --all] (if none provided, prompt user, add option to kill all)
    #  sprinkle status
    #  sprinkle settings
    #  sprinkle export [path]
    #  sprinkle [help]

    #  sprinkle view [job id --(log | error | output)] (if none, prompt user)

    #TODO: Use environment.yaml instead for both sprinkle and jobs
#TODO: Way to see core and memory efficiency when examining jobs, bstat -C and bstat -M
#TODO: Disclaimer on first run

#TODO: Handle case where JobOptions changed between versions, and existing loads may not work
#TODO: Check if sprinkle project output directories exist before monitoring
#TODO: Error if job submission failed

# TODO: Investigate whether to use conda update --phrune instead of fully recreating

#TODO: Update readme.md when done, remember to remove WIP at top

#TODO: Should also support running from the server
#TODO: Start, monitor, generate start script

#TODO: Add dev flag to pull from dev instead
#TODO: Feature to scp back everything



