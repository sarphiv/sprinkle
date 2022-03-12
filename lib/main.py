from os import path
from sys import stdout
import getopt
import menu



main_menu = menu.Menu()
main_menu.set_options([("firstOption", exit),
                      ("secondOption",exit),
                      ("thirdOption", exit)])
main_menu.open()

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
#TODO: Ability to use sprinkle by e.g. sprinkle start, sprinkle stop [job id], sprinkle status, sprinkle monitor error/cluster-output/script-output [job id], sprinkle help, sprinkle export, sprinkle options

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
job_queue_gpu = ["gpuv100", "gpua100"]
job_queue_cpu = ["hpc"] 



job_name = "sprinkle-job"


job_environment_name = "sprinkle-job-env"
job_environment_on_done_delete = True


job_queue_names = ["hpc", "gpuv100", "gpua100"]
job_queue_name = job_queue_names[0]

job_cpu_cores = 16
job_cpu_memory_core = "400MB"
job_cpu_memory_max = "6GB"

job_time_max = "24:00"

job_email = "".strip()

job_script_target = "main.py"




def generate_bsub_script(options): 
    def conditional_string(condition, string, end="\n"):
        return string if condition + end else ""

    return (f"""
#!/bin/bash
### Job name
#BSUB -J {job_name}


### Job queue
#BSUB -q {job_queue_name} 
"""
+
conditional_string(job_queue_name in [job_queue_gpu],
f'''
### GPUs to request and if to reserve it exclusively\n"
#BSUB -gpu "num=1:mode=exclusive_process"''')
+
f"""
### Cores to request
#BSUB -n {job_cpu_cores}

### Force cores to be on same host
#BSUB -R "span[hosts=1]" 

### Number of threads for OpenMP parallel regions
export OMP_NUM_THREADS=$LSB_DJOB_NUMPROC


### Amount of memory per core
#BSUB -R "rusage[mem={job_cpu_memory_core}]" 

### Maximum amount of memory before killing task
#BSUB -M {job_cpu_memory_max} 


### Wall time (HH:MM), how long before killing task
#BSUB -W {job_time_max}


### Output and error file. %J is the job-id -- 
### -o and -e mean append, -oo and -eo mean overwrite -- 
#BSUB -oo Output_%J.out 
#BSUB -eo Error_%J.err
"""
+
conditional_string(job_email, 
f"""
### Email to receive notifications
#BSUB -u {job_email}

### Notify via email at start
#BSUB -B

### Notify via email at completion
#BSUB -N""")
+
f"""

# Get shell environment
source ~/.bashrc

# Check if job environment exists
conda env list | grep "^${job_environment_name}" >> /dev/null
SPRINKLE_JOB_ENV_EXISTS=$?

# If environment does not exist, create environment
if [[ ${{SPRINKLE_JOB_ENV_EXISTS}} -ne 0 ]]; then
    # Create environment
    conda create -n {job_environment_name} --file requirements.txt -y
    
    # Activate environment for script
    conda activate {job_environment_name}
# Else, attempt installing packages in case there were changes
else
    # Activate environment for script
    conda activate {job_environment_name}

    # Attempt installing (new) packages 
    conda install --file requirements.txt -y
fi


# Run job script and save output to file
python {job_script_target} > Script_$J.out

"""
+
conditional_string(job_environment_on_done_delete, 
f"""
### Remove environment when done
conda env remove -n {job_environment_name} -y
""")
)