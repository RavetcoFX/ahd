"""This file houses the primary entrypoint, and main business logic of ahd.

Module Variables
----------------

usage (str);
    Used by docopt to setup argument parsing;
    Defines the actual command line interface.

CONFIG_FILE_PATH(str):
    The path to the configuration file.

CURRENT_PATH(str):
    Used to keep track of users current directory
    to cd back into it after script execution.


Documentation
-------------
Docs website: https://ahd.readthedocs.io
"""

# Standard lib dependencies
import os                             # Used primarily to validate paths
import sys
import webbrowser                     # Used to auto-launch the documentation link
import subprocess                     # Used to run the dispatched commands
from configparser import ConfigParser # Used to serialize and de-serialize config files

# Internal dependencies
from .autocomplete import command, generate_bash_autocomplete

# Third-party dependencies
from docopt import docopt             # Used to parse arguments and setup POSIX compliant usage info


usage = """Add-hoc dispatcher
    Create ad-hoc commands to be dispatched within their own namespace.

    Usage: 
        ahd [-h] [-v] [-d]
        ahd docs [-a] [-o]
        ahd config [-e] [-i CONFIG_FILE_PATH]
        ahd register <name> [<command>] [<paths>]
        ahd <name> [<command>] [<paths>]

    Options:
    -h, --help            show this help message and exit
    -v, --version         show program's version number and exit
    -a, --api             shows the local API docs
    -o, --offline         shows the local User docs instead of live ones
    -e, --export          exports the configuration file
    -i CONFIG_FILE_PATH, --import CONFIG_FILE_PATH 
                          imports the configuration file
    """

commands =  [ # Used for autocompletion generation
    command("docs", ["-a", "--api", "-o", "--offline"]),
    command("register", [])
]


config = ConfigParser() # Global configuration parser

# The default (and currently only) path to the configuration file
CONFIG_FILE_PATH = f"{os.path.dirname(__file__)}{os.sep}.ahdconfig"


CURRENT_PATH = os.curdir # Keeps track of current directory to return to after executing commands

def main():
    """The primary entrypoint for the ahd script.
    
    All primary business logic is within this function."""

    # Setup arguments for parsing
    arguments = docopt(usage, version="ahd V 0.1.0")
    # print(arguments)

    if len(sys.argv) == 1:
        print("\n", usage)
        exit()


    if os.path.exists(CONFIG_FILE_PATH): # If the file already exists
        config.read(CONFIG_FILE_PATH) # Read it

    else: # If a file does not exist create one
        with open(CONFIG_FILE_PATH, "w") as config_file:
                config.write(config_file)
    
    # Begin argument parsing

    if arguments["docs"]:
        webbrowser.open_new("https://ahd.readthedocs.io")
        exit()

    if not arguments["<paths>"]:
        arguments["<paths>"] = ""
    else:
        arguments["<paths>"] = _preprocess_paths(arguments["<paths>"])
    
    if not arguments["<command>"]:
        arguments["<command>"] = ""
    
    if "." == arguments["<command>"]: # If <command> is . set to specified value
        arguments["<command>"] = config[arguments["<name>"]]["command"]

    if arguments["register"]:
        config[arguments["<name>"]] = {
            "command": arguments["<command>"],
            "paths": arguments["<paths>"],
        }

        if not os.name == "nt": # Generate bash autocomplete
            for index, custom_command in enumerate(config):
                if not index == 0: # for some reason the first thing in config object is garbage
                    commands.append(command(custom_command, []))

            autocomplete_file_text = generate_bash_autocomplete(commands)
            with open("/etc/bash_completion.d/ahd.sh", "w") as autocomplete_file:
                autocomplete_file.write(autocomplete_file_text)
            print(autocomplete_file_text)


        with open(CONFIG_FILE_PATH, "w") as config_file:
            config.write(config_file)

    else: # If not registering a command
        if arguments['<name>']:
            if config[arguments['<name>']]['paths'].startswith("["):
                paths = config[arguments['<name>']]['paths']
                if os.name == "nt":
                    paths = paths.replace("/", f"{os.sep}")
                paths = paths[1:-1:].split(",") # Removes the leading and trailing brackets and splits based on commas
                for current_path in paths:
                    print(f"Running: cd {current_path.strip()} && {config[arguments['<name>']]['command']} ".replace("\'",""))
                    subprocess.Popen(f"cd {current_path.strip()} && {config[arguments['<name>']]['command']} ".replace("\'",""), shell=True)

            else: # if only a single path is specified instead of a 'list' of them
                subprocess.Popen(f"cd {config[arguments['<name>']]['paths']} && {config[arguments['<name>']]['command']} ".replace("\'",""), shell=True)
    
    if arguments["config"]:
        if arguments["--export"]:
            print(f"{os.curdir}{os.sep}.ahdconfig")
            with open(f"{os.curdir}{os.sep}.ahdconfig", "w") as config_file:
                config.write(config_file)
        if arguments["--import"]:
            with open(arguments["--import"], "r") as config_file:
                config.read(config_file)
    os.chdir(CURRENT_PATH)

def _preprocess_paths(paths:str):
    """Preprocesses paths from input and splits + formats them
    into a useable list for later parsing.
    
    Example
    -------
    ```
    paths = 'C:\\Users\\Kieran\\Desktop\\Development\\Canadian Coding\\SSB, C:\\Users\\Kieran\\Desktop\\Development\\Canadian Coding\\website, C:\\Users\\Kieran\\Desktop\\Development\\Personal\\noter'
    
    paths = _preprocess_paths(paths)

    print(paths) # Prints: ['C:/Users/Kieran/Desktop/Development/Canadian Coding/SSB', 'C:/Users/Kieran/Desktop/Development/Canadian Coding/website', 'C:/Users/Kieran/Desktop/Development/Personal/noter']
    ```
    """
    result = paths.split(",")
    for index, path in enumerate(result):
        result[index] = path.replace("\\", "/").strip()

    return result

if __name__ == "__main__":
    main()
