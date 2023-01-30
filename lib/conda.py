from typing import Optional
from dataclasses import replace
import os
import subprocess

from varname import nameof

from lsf import JobSettings



def get_environments() -> tuple[set[str], Optional[str]]:
    """Gets a set of all environments available in the current conda installation and the current environment

    Returns:
        tuple[set[str], Optional[str]]: Tuple containing a set of all environments and the current environment
    """
    # Get list of environments
    output = subprocess.run(
        ["conda", "env", "list"],
        stdout=subprocess.PIPE, 
        stderr=subprocess.DEVNULL,
        encoding="ascii"
    ).stdout.splitlines()

    # Parse list of environments
    environments = []
    environment_active = None

    for line in output:
        if line.startswith("#"):
            continue
        
        components = line.split()
            
        environments.append(components[0])
        if components[1] == '*':
            environment_active = components[0]


    # Return set of enviroments
    return set(environments), environment_active



def exists_environment(env_name: str) -> bool:
    """Checks if an environment exists in the current conda installation
    
    Args:
        env_name (str): Name of environment
    
    Returns:
        bool: True if environment exists, False otherwise
    """
    return env_name in get_environments()[0]



def recreate_environment(env_name: str, env_file_name: str, output: bool = False) -> bool:
    """(Re)creates an environment in the current conda installation
    
    Args:
        env_name (str): Name of environment
        env_file_name (str): File path of environment file
        output (bool, optional): If True, output is printed to stdout. Defaults to False.

    Returns:
        bool: True if environment was successfully (re)created, False otherwise
    """
    # Get list of environments and the activate environment
    environments, active = get_environments()


    # Commands to execute
    commands = []
    
    # If environment is active, deactivate
    if active == env_name:
        commands.append("conda deactivate")

    # If environment exists, remove first
    if env_name in environments:
        commands.append(f"conda env remove -n {env_name}")

    # Create environment from environment file
    commands.append(f"conda env create -n {env_name} -f {env_file_name or JobSettings.defaults.env_file()}")


    # Execute commands
    for command in commands:
        # If output, execute and print output
        if output:
            exit_status = os.system(command)
        # Else, execute and discard output
        else:
            exit_status = subprocess.run(
                command, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            ).returncode

        # If exit status is non-zero, return failure
        if exit_status != 0:
            return False


    # Return success
    return True



def delete_environment(env_name: str, output: bool = False) -> bool:
    """Deletes an environment in the current conda installation
    
    Args:
        env_name (str): Name of environment
        output (bool, optional): If True, output is printed to stdout. Defaults to False.
    
    Returns:
        bool: True if environment was successfully deleted, False otherwise
    """
    # Get list of environments and the activate environment
    environments, active = get_environments()


    # If environment does not exist, return failure
    if env_name not in environments:
        return False

    # If environment is active, deactivate
    if active == env_name:
        subprocess.run(
            ["conda", "deactivate"], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )


    # If output, execute and print output
    if output:
        return os.system(f"conda env remove -n {env_name}") == 0
    # Else, execute and discard output
    else:
        return subprocess.run(
            ["conda", "env", "remove", "-n", env_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        ) == 0



def generate_environment_yml(env_name: str, env_file_name: str, req_file_name: str) -> None:
    """Generates a basic environment.yml for a job
    
    Args:
        env_name (str): Name of environment
        env_file_name (str): File path of environment file
        req_file_name (str): File path of requirements file
    """
    # Open and write to environment.yml equivalent file
    with open(env_file_name, 'w') as f:
        f.write(f"""\
name: {env_name}
channels:
  - defaults

dependencies:
  - python
  - pip

  - pip:
    - -r {req_file_name}
""")


def generate_requirements_txt(req_file_name: str) -> None:
    """Generates a requirements.txt equivalent for a job by inspecting the source code

    Args:
        req_file_name (str): File path of requirements file
    """
    # Get requirements
    requirements = subprocess.run(
        ["pipreqs", "--force", "--print"],
        stdout=subprocess.PIPE, 
        stderr=subprocess.DEVNULL,
        encoding="ascii"
    ).stdout
    
    # Open and write to requirements.txt equivalent file
    with open(req_file_name, 'w') as f:
        f.write(requirements)
    


def ensure_environment_specification_exists(settings: Optional[JobSettings]) -> tuple[Optional[JobSettings], bool]:
    """Ensures that an environment.yml and/or requirements.txt equivalent exists for a job
    by creating the necessary files or by verifying that the specified files exist

    Args:
        settings (Optional[JobSettings]): Settings for the job to be run

    Returns:
        tuple[Optional[JobSettings], bool]: Tuple containing the job settings if valid environment, 
            and a boolean indicating whether files were generated.
    """
    # if no settings given, return None
    if settings is None:
        return (None, False)


    # Get environment and requirements file names
    env_file_name = settings.env_file or JobSettings.defaults.env_file()
    req_file_name = settings.req_file or JobSettings.defaults.req_file()

    
    # Mark environment and/or requirements files were generated
    env_file_generated = False
    req_file_generated = False
    # Mark whether settings do not specify missing file(s)
    settings_valid = True


    # If no environment file specified, generate environment file
    if settings.env_file == "":
        env_file_generated = True
        generate_environment_yml(settings.env_name, env_file_name, req_file_name)
        settings = replace(settings, **{nameof(JobSettings.env_file): env_file_name})
    # Else, check if specified file exists
    else:
        settings_valid &= os.path.isfile(settings.env_file)


    # if no requirements file specified, generate requirements file
    if settings.req_file == "":
        req_file_generated = True
        generate_requirements_txt(req_file_name)
        settings = replace(settings, **{nameof(JobSettings.req_file): req_file_name})
    # else, check if specified file exists
    else:
        settings_valid &= os.path.isfile(settings.req_file)


    # Return settings if files exist, also return whether files were generated
    return (settings if settings_valid else None, env_file_generated or req_file_generated)
