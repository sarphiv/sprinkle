# 🪄✨Sprinkle✨
Sprinkle is used to simplify deployment of scripts to DTU's High Performance Computing Cluster. 


# ✅ Feature list
- Automatic **Miniconda** installation
- Automatic setup of environment
- Job submission with arguments passed to job
- Interactive stopping of jobs
- View job output, log, and errors
- View job status including **CPU and memory usage**
- Change job settings
- Export submission script to file


# 🚀 Installation
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


# 👉 Usage
All commands below should be ❗ **run in your project directory** ❗.

1. **On your local machine**
    1. `conda activate <environment name>` _(activate your project's environment)_
    0. `conda env export > environment.yml` _(or create the environment file manually - see FAQ below)_
    0. Transfer project directory to DTU's HPC cluster _(see FAQ below)_
2. **On DTU's HPC cluster**
    1. `sprinkle start` and then enter job parameters _(such as CPU cores, memory, time, and main script)_
    0. `sprinkle help` _(view other commands)_


# 📖 Frequently asked questions
<details>
  <summary><b>How do I create the environment file?</b></summary>

  There are multiple ways. However, remember the `environment.yml` file 
  should be created **before transfering your project to DTU's HPC cluster**.

  - Either __**create a new environment**__
    ```bash
    conda create -n new_environment_name
    conda activate new_environment_name
    conda install <package_name1> <package_name2> ...
    pip install <package_name1> <package_name2> ...
    conda env export > environment.yml
    ```
  - Or __**manually write the `environment.yml` file**__
    1. Create a new file called `environment.yml` (can be done with `touch environment.yml`)
    0. Write your environment file (example below, version numbers can be specified).
        ```yaml
        name: new_environment_name
        channels:
          - defaults
          - conda-forge
          - pytorch
        dependencies:
          - python
          - pip
          - pytorch
          - pytorch-cuda
          - torchvision
          - torchaudio
          - pip:
            - scikit-learn
            - opencv-python
            - tqdm
        ```

  Test your code with your new environment on your own computer first.
  It is much easier to find and fix issues there than on DTU's HPC cluster.
</details>

<details>
  <summary><b>How do I transfer my project to DTU's HPC cluster?</b></summary>

  1. **On your own computer**, navigate through a terminal to the directory **CONTAINING** your project directory.
      - Example: If your project is in `~/DTU/12345/project_directory`, navigate to `~/DTU/012345`.
  0. Run `scp -r project_directory s123456@transfer.gbar.dtu.dk:project_directory`
  0. Wait for the upload to finish

  If the above fails, contact [HPC support](https://www.hpc.dtu.dk/) for more information and guidance.
</details>

<details>
  <summary><b>Where are my script's output, log, and errors?</b></summary>

  In a bunch of files in a hidden directory called `.sprinkle` in your project directory.
</details>

<details>
  <summary><b>My script doesn't work on DTU's HPC cluster.</b></summary>

  Check the error, log, and output files with `sprinkle view error job_id`, 
  where `job_id` is for your failed job.

  The error, log, and output files can also be found 
  in a hidden directory called `.sprinkle` in your project directory.
</details>

<details>
  <summary><b>How do I connect to DTU's HPC cluster?</b></summary>

  Use `ssh s123456@login.hpc.dtu.dk` or `ThinLinc` to connect to DTU's HPC cluster.
  If you use `ssh` remember to run `linuxsh` to not overload the login node.
  Contact [HPC support](https://www.hpc.dtu.dk/) for more information and guidance.
</details>

<details>
  <summary><b>How do I enable developer mode for sprinkle?</b></summary>

  Add a file called `DEVELOPER-MODE` to `~/sprinkle/tmp/`.
  The next call to sprinkle will switch branches and recreate the environment.
  Remove the file to leave developer mode upon the next call to sprinkle.
</details>

# 🗔 CLI
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
    Export submission script to <path> that passes <args> to the job script.
    If <args> contains dashes, add the two dashes "--" before <args>.
    Defaults to working directory.
    
  sprinkle update
    Update sprinkle to latest version.

  sprinkle [help | -h | -? | --help]
    Show this screen.


Options:
  -h -? --help       Show full help text.
  -a --all           Kill all jobs
```

# 🧑‍⚖️ Disclaimer
This project is a personal project and therefore not affiliated with DTU. 

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
