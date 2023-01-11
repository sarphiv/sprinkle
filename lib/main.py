import sys
import inspect

from docpie import docpie
from cli import doc_short, Command



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
           and not (value is None)
    }


    if "start" in args:
        exit_code = Command.start(
            args["<args>"] if "<args>" in args else 
                []
        )
    elif "stop" in args:
        exit_code = Command.stop(
            args["<job_id>"] if "<job_id>" in args else 
                "all" if "-a" in args else 
                []
        )
    elif "view" in args:
        exit_code = Command.view(
            "output" if "output" in args else
                "log" if "log" in args else
                "error" if "error" in args else 
                None,
            args["<job_id>"][0] if "<job_id>" in args else 
                None
        )
    elif "status" in args:
        exit_code = Command.status()
    elif "settings" in args:
        exit_code = Command.settings()
    elif "export" in args:
        exit_code = Command.export(
            args["<path>"] if "<path>" in args else 
                [],
            args["<args>"] if "<args>" in args else 
                []
        )
    elif len(args) == 0 or len({"help", "--help", "-h", "-?"}.intersection(args)) > 0:
        exit_code = Command.help()
    else:
        exit_code = 1


    # Exit with exit code from above
    exit(exit_code)

except (KeyboardInterrupt, EOFError):
    exit(-1)



#TODO: Ok, maybe MVP first instead...
    #TODO: file for default bsub options, and base recommendations off of these
    #TODO: Save bsub options in file and output status whether this file exists for the project yet (in current working directory)
    #TODO: When trying to edit options again, display current settings instead of default recommendations
    #TODO: running start, just submits based off of the options
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
    #TODO: check for missing environment.yml or other location, before starting
    #TODO: Fix regex for reading active job time start and elapsed
    #TODO: Way to see core and memory efficiency when examining jobs, bstat -C and bstat -M
#TODO: Disclaimer on first run
#TODO: Change indexing of prompt choice to display start at 1, but still use 0 indexing internally

    #TODO: Handle case where JobOptions changed between versions, and existing loads may not work
#TODO: Check if sprinkle project output directories exist before monitoring
#TODO: Error if job submission failed

#TODO: Investigate whether to use conda update --phrune instead of fully recreating

#TODO: Update readme.md when done, remember to remove WIP at top

#TODO: Add dev flag to pull from dev instead
#TODO: Feature to scp back everything



