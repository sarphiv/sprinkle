from os import path
from sys import stdout
import getopt


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
#TODO: Add dev flag to pull from dev instead

#TODO: Option to view newest error or output file, or output.txt file

#TODO: Should also support running from the server
#TODO: Automatically set up python so this script can run
#TODO: Start, monitor, generate start script
#TODO: Automatically pull down miniconda and set up environment
#TODO: Option to delete conda environment after done

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



# Program setup
job_queue_gpu = ["gpuv100", "gpua100"]
job_queue_cpu = ["hpc"] 



job_name = ""


job_queue_names = ["hpc", "gpuv100", "gpua100"]
job_queue_name = job_queue_names[0]

job_cpu_cores = 32

job_email = "".strip()






def get_bsub_options(): 
    return f"""
#!/bin/bash
### Job name
#BSUB -J {job_name}


### Job queue
#BSUB -q {job_queue_name} 


{'### GPUs to request and if to reserve it exclusively\n\
#BSUB -gpu "num=1:mode=exclusive_process"' 
if job_queue_name in [job_queue_gpu] 
else ""}


### Cores to request
#BSUB -n {job_cpu_cores}

### Force cores to be on same host
#BSUB -R "span[hosts=1]" 


### Amount of memory per core
#BSUB -R "rusage[mem=600MB]" 

### Maximum amount of memory before killing task
#BSUB -M 6GB 


### Wall time (HH:MM), how long before killing task
#BSUB -W 24:00


### Output and error file. %J is the job-id -- 
### -o and -e mean append, -oo and -eo mean overwrite -- 
#BSUB -oo Output_%J.out 
#BSUB -eo Error_%J.err


{f"### Email to receive notifications\n\
#BSUB -u {job_email}\n\
\n\
### Notify via email at start\n\
#BSUB -B\n\
\n\
### Notify via email at completion\n\
#BSUB -N"
if job_email
else ""}

"""