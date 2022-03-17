from itertools import accumulate
from os import path
from sys import stdout
import getopt





sprinkle_project_dir = ".sprinkle"
sprinkle_project_options = sprinkle_project_dir + "/options.pkl"
sprinkle_project_script_dir = sprinkle_project_dir + "/script"
sprinkle_project_output_dir = sprinkle_project_dir + "/output"
sprinkle_project_error_dir = sprinkle_project_dir + "/error"

print(f'Suggested values: {["@student.dtu.dk", "@dtu.dk" "@gmail.com", "gmail.dk", "@yahoo.com", "yahoo.dk" "hotmail.com" "@hotmail.dk", "@outlook.com", "@outlook.dk", "@msn.dk", "@msn.com"]:<8}')

completer = FuzzyWordCompleter(["@student.dtu.dk", "@dtu.dk" "@gmail.com", "gmail.dk", "@yahoo.com", "yahoo.dk" "hotmail.com" "@hotmail.dk", "@outlook.com", "@outlook.dk", "@msn.dk", "@msn.com"])
validator = ThreadedValidator(Validator.from_callable(lambda text: text.isdigit()))


print("test me")

exit(0)





start_script_name = "bsub-start.sh"


def get_input(prompt, valid_responses):
    while True:
        answer = input(prompt)

        if answer in valid_responses:
            break
        else:
            stdout.write("\033[F")
            stdout.write('\033[K\033[1G')

    return answer


#TODO: Ok, maybe MVP first instead...
#TODO: Put script in user's bin directory
#TODO: Disclaimer on first run
#TODO: file for default bsub options, and base recommendations off of these
#TODO: Save bsub options in file and output status whether this file exists for the project yet (in current working directory)
#TODO: When trying to edit options again, display current settings instead of default recommendations
#TODO: running submit, just submits based off of the options
#TODO: Functionality to generate bsub script
#TODO: Move functions into different module for readability
#TODO: Ability to use sprinkle by e.g. 
#  sprinkle start (if no options for project, prompt user), 
#  sprinkle stop [job id [job_id ...] | --all] (if none provided, prompt user, add option to kill all), 
#  sprinkle status, 
#  sprinkle monitor error/cluster-output/script-output [job id] (if none, prompt user), 
#  sprinkle [help], 
#  sprinkle export [path], 
#  sprinkle options

#TODO: Option to view newest error or output file, or output.txt file

#TODO: Should also support running from the server
#TODO: Start, monitor, generate start script

#TODO: Add dev flag to pull from dev instead
#TODO: Feature to scp back everything


print(f"Start script already exists: {start_script_name}.\n" +
        "1. Start script (default)\n" +
        "2. Monitor output"
        "3. Generate new start script and start it\n" +
        "4. Generate new start script")


answer = get_input("Choose an option: ", ["", "1", "2", "3"])

if answer in ["", "1"]:
    #check if start script exists
    # if path.exists(f"./{start_script_name}"):
    print("running")
elif answer in ["2"]:
    print("generating")
elif answer in ["3"]:
    pass



def prompt_wizard_options():
    pass

def options_save(options, path):
    pass

def options_load(path):
    pass


def options_submit(options):
    pass

    
def export_string(string, path):
    pass


# Program setup