# WORK IN PROGRESS

# sprinkle
Shell script used to simplify deployment of python scripts to DTU's High Performance Computing Cluster. 

Automatically sets up miniconda, generates submission scripts with conda integration, submits jobs, and monitors jobs. 


# Installation
On DTU's HPC cluster, simply run the following commands.

```bash
wget -O 'sprinkle' 'https://raw.githubusercontent.com/sarphiv/sprinkle/main/bin/sprinkle' && chmod u+x sprinkle && ./sprinkle && rm -f sprinkle && source ~/.profile && sprinkle
```

<details>
  <summary>Description of the above commands</summary>

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
  $ source ~/.profile
  # Run installed sprinkle for final setup
  $ sprinkle
  ```
</details>


# Usage
1. **On your local machine**
    1. Activate your project's environment with `conda activate <environment name>`.
    0. In your project directory, export your packages with `conda env export > environment.yml`.
    0. Transfer project directory to DTU's HPC cluster with e.g. `scp` or `ThinLinc`. 
2. **On DTU's HPC cluster**
    1. Run `sprinkle start` in your project directory.
    0. Run `sprinkle help` to view other commands.


# Feature list
- Semi-automatic update
- Miniconda installation
- Submission script generation
- Job submission
- Automatic job conda environment setup
- Monitoring of recent output, errors, and program output
- Killing of jobs

# CLI
```
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

  sprinkle export [<path>]
    Export submission script to path. 
    Defaults to working directory.

  sprinkle [help | -h | -? | --help]
    Show this screen.


Options:
  -h -? --help       Show full help text.
  -a --all           Kill all jobs
```
