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


    # Parse arguments and call appropriate command
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

    elif "update" in args:
        print("WARNING: This text should never appear. The update call should have been intercepted.")
        exit_code = 1

    elif len(args) == 0 or len({"help", "--help", "-h", "-?"}.intersection(args)) > 0:
        exit_code = Command.help()

    else:
        exit_code = 1


    # Exit with exit code from above
    exit(exit_code)

# Catch keyboard interrupts and whatever the other thing is (CTRL+D and CTRL+D)
except (KeyboardInterrupt, EOFError):
    exit(-1)
