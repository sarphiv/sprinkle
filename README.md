# sprinkle
Sprinkle is used to simplify deployment of scripts to DTU's High Performance Computing Cluster. 

Automatically sets up Miniconda, environments, submits jobs, manages jobs, and monitors jobs. 


# Installation
On DTU's HPC cluster, simply run the following commands.

```bash
wget -O 'sprinkle-installer' 'https://raw.githubusercontent.com/sarphiv/sprinkle/main/bin/sprinkle' && chmod u+x sprinkle-installer && ./sprinkle-installer update && rm -f sprinkle-installer && source ~/.profile && sprinkle update && sprinkle help
```

<details>
  <summary>Description of the above commands</summary>

  ```bash
  # Downloads newest version of sprinkle
  $ wget -O 'sprinkle-installer' 'https://raw.githubusercontent.com/sarphiv/sprinkle/main/bin/sprinkle'
  # Makes the script executable
  $ chmod u+x sprinkle-installer
  # Runs the installation script
  $ ./sprinkle-installer update
  # Delete downloaded sprinkle file
  $ rm -f sprinkle-installer
  # Update environment variables of current shell
  $ source ~/.profile
  # Run installed sprinkle for final setup
  $ sprinkle update
  # Display help view
  $ sprinkle help
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
- Automatic update (asks for consent)
- Automatic Miniconda installation
- Automatic setup of environment
- Job submission with arguments passed to job
- Interactive stopping of jobs
- View job output, log, and errors
- View job status including CPU and memory usage
- Change job settings
- Export submission script to file


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

  sprinkle view [((output | log | error) [<job_id>])]
    View output, log, or errors of a specific job.

  sprinkle status
    See overview of job details.

  sprinkle settings
    Set up or change existing job settings.

  sprinkle export [<path>] [<args>...]
    Export submission script to path. 
    If <args> contains dashes, add the two dashes "--" before <args>.
    Defaults to working directory.

  sprinkle [help | -h | -? | --help]
    Show this screen.


Options:
  -h -? --help       Show full help text.
  -a --all           Kill all jobs
```


## Frequently asked questions
### My conda environment is a mess, I do not want to export it.
Then you need to make a new conda environment with `conda create -n new_environment_name`,
install the necessary packages to make it work with your project, and then follow the original instructions.

An alternative is to manually write the `environment.yml` file (cleanest option).
You can use [sprinkle's environment file](https://github.com/sarphiv/sprinkle/blob/main/environment.yml) for inspiration.

Whatever you do, test your code with your new environment on your computer first.
It is much easier to find and fix issues there than on DTU's HPC cluster.

### How do I transfer my project to DTU's HPC cluster?
1. On your own computer, navigate a throough a terminal to the directory **CONTAINING** your project directory.
0. Run `scp -r project_directory_on_your_computer s123456@student.dtu.dk@transfer.gbar.dtu.dk:where_you_want_it_on_DTU_HPC`
0. Wait for the upload to finish

### Where are my script's output, log, and errors?
In a hidden folder called `.sprinkle` in your project directory.

### How do I enable developer mode for sprinkle?
Add a file called `DEVELOPER-MODE` to `~/sprinkle/tmp/`