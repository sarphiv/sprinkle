# WORK IN PROGRESS

# sprinkle
Shell script used to simplify deployment of python scripts to DTU's High Performance Computing Cluster. 

Automatically sets up miniconda, generates submission scripts with conda integration, submits jobs, and monitors jobs. 


# Installation
On DTU's HPC cluster, simply run the following commands then follow the on-screen instructions.

Copy-pasta friendly:
```bash
wget -O 'sprinkle' 'https://raw.githubusercontent.com/sarphiv/sprinkle/main/bin/sprinkle' && chmod u+x sprinkle && ./sprinkle && rm -f sprinkle && source ~/.profile && sprinkle
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
# Update environment variables of current shell
source ~/.profile
# Run installed sprinkle for final setup
$ sprinkle
```


# Usage
1. **On your local machine**
    1. Ensure your code actually works on your own machine first.
    0. Navigate to your project directory via the shell.
    0. Activate your project's conda environment with `conda activate <environment name>`.
    0. Run `conda list -e requirements.txt`.
    0. Transfer project directory to DTU's HPC cluster with e.g. `scp` or `ThinLinc`. 
2. **On DTU's HPC cluster**
    1. Navigate to your project directory via the shell.
    0. Run `sprinkle start` and follow instructions.
    0. Run `sprinkle help` to learn about more commands.


# Feature list
- Semi-automatic update
- Miniconda installation
- Submission script generation
- Job submission
- Automatic job conda environment setup
- Monitoring of recent output, errors, and program output
- Killing of newest job
