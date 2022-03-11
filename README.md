# WORK IN PROGRESS

# sprinkle
Shell script used to simplify deployment of python scripts to DTU's High Performance Computing Cluster. 

Automatically sets up miniconda, generates submission scripts with conda integration, submits jobs, and monitors jobs. 


# Installation
On DTU's HPC cluster, simply run the following commands then follow the on-screen instructions.

Copy-pasta friendly:
```bash
wget -O 'sprinkle' 'https://raw.githubusercontent.com/sarphiv/sprinkle/main/bin/sprinkle' && chmod u+x sprinkle && ./sprinkle && rm -f sprinkle
```

Description of commands:
```bash
# Downloads newest version of sprinkle
$ wget -O 'sprinkle' 'https://raw.githubusercontent.com/sarphiv/sprinkle/main/bin/sprinkle'
# Makes the script executable
$ chmod u+x sprinkle
# Runs the installation script
$ ./sprinkle
# Delete downloaded sprinkle file
$ rm -f sprinkle
```

The downloaded `sprinkle` **file** (do not delete the `sprinkle` **directory**) can safely be deleted after installation.


# Usage
1. On your local machine
    1. Navigate to your project directory via the shell.
    0. Ensure your code actually works on your own machine first.
    0. Activate your project's conda environment with `conda activate <environment name>`.
    0. Run one or both of the following:
        - `conda list -e conda-requirements.txt`
        - `python -m pipreqs --savepath pip-requirements.txt` (requires the `pipreqs` python package)
    0. Transfer project directory to DTU's HPC cluster with e.g. `scp` or `ThinLinc`. 
2. On DTU's HPC cluster
    1. Navigate to your project directory via the shell.
    0. Run `sprinkle`
    0. Generate submission script and submit it


# Feature list
- Semi-automatic update
- Miniconda installation
- Submission script generation
- Job submission
- Monitoring of recent output, errors, and program output
- Killing of newest job
