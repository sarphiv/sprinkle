import sys
import inspect

from lib.lsf import JobSettings, generate_bsub_script, kill_jobs, load_settings, save_settings, submit_job
from lib.lsf_prompt import prompt_settings




sprinkle_project_dir = ".sprinkle"
sprinkle_project_settings_file = "settings.pkl"
sprinkle_project_settings_export_file = "sprinkle-job-export.sh"
sprinkle_project_script_dir = sprinkle_project_dir + "/script"
sprinkle_project_output_dir = sprinkle_project_dir + "/output"
sprinkle_project_error_dir = sprinkle_project_dir + "/error"



class Command:
    def start() -> bool:
        # Load settings
        settings = load_settings()
        # If no settings loaded, create and save settings
        if not settings:
            settings = prompt_settings(JobSettings())
            save_settings(settings)
        
        # Submit job script
        job_id = submit_job(settings)

        # Print job ID
        print(f'Started job (Name: "{settings.name}", ID: "{job_id}")')


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

    
    def help() -> bool:
        # TODO: Write help text

        # Return successful
        return True
    
    
    def view(args) -> bool:
        print("Not yet implemented.")
        
        return False


def main(args: list[str]):
    methods = inspect.getmembers(Command, predicate=inspect.isroutine)
    methods = {name: method for name, method in methods if not name.startswith('_')}
    
    exit_code = 0

    if not args or len(args) == 0:
        exit_code = Command.help()
    elif args[0].lower() not in methods:
        print(f'Unknown command: "{args[0]}"\nRun "sprinkle help" for guidance.')
        exit_code = 1
    else:
        exit_code = int(not methods[args[0].lower()](args[1:]))


    exit(exit_code)




if __name__ == "__main__":
    main(sys.argv[1:])


# print(f'Suggested values: {["@student.dtu.dk", "@dtu.dk" "@gmail.com", "gmail.dk", "@yahoo.com", "yahoo.dk" "hotmail.com" "@hotmail.dk", "@outlook.com", "@outlook.dk", "@msn.dk", "@msn.com"]:<8}')

# completer = FuzzyWordCompleter(["@student.dtu.dk", "@dtu.dk" "@gmail.com", "gmail.dk", "@yahoo.com", "yahoo.dk" "hotmail.com" "@hotmail.dk", "@outlook.com", "@outlook.dk", "@msn.dk", "@msn.com"])
# validator = ThreadedValidator(Validator.from_callable(lambda text: text.isdigit()))


# print("test me")

# exit(0)




#TODO: Ok, maybe MVP first instead...
#TODO: Disclaimer on first run
#TODO: file for default bsub options, and base recommendations off of these
#TODO: Save bsub options in file and output status whether this file exists for the project yet (in current working directory)
#TODO: When trying to edit options again, display current settings instead of default recommendations
#TODO: running submit, just submits based off of the options
#TODO: Ability to use sprinkle by e.g. 
#  sprinkle start (if no options for project, prompt user for first time project setup)
#  sprinkle stop [(job id [job_id ...]) | --all] (if none provided, prompt user, add option to kill all)
#  sprinkle status
#  sprinkle settings
#  sprinkle export [path]
#  sprinkle [help]

#  sprinkle view [job id --(output | error | script)] (if none, prompt user)

#TODO: Handle case where JobOptions changed between versions, and existing loads may not work
#TODO: Check if sprinkle project output directories exist before monitoring
#TODO: Error if job submission failed

#TODO: Update readme.md when done, remember to remove WIP at top

#TODO: Should also support running from the server
#TODO: Start, monitor, generate start script

#TODO: Add dev flag to pull from dev instead
#TODO: Feature to scp back everything



