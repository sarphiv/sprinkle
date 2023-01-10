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
        pass
    elif "stop" in args:
        pass
    elif "view" in args:
        pass
    elif "status" in args:
        pass
    elif "settings" in args:
        exit_code = Command.settings()
    elif "export" in args:
        exit_code = Command.export(args["<path>"] if "<path>" in args else None)
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



