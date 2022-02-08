import os
import shlex
import subprocess
import sys
from typing import Optional, List

from colorama import Fore, Style

from toncli.modules.utils.system.log import logger
from toncli.modules.utils.system.project import check_for_needed_files_to_deploy
from toncli.modules.utils.func.commands import build as fift_build, build_files
from toncli.modules.utils.system.conf import executable
from toncli.modules.utils.fift.commands import fift_execute_command

bl = Fore.CYAN
rd = Fore.RED
gr = Fore.GREEN
rs = Style.RESET_ALL


class Func:
    def __init__(self, command: Optional[str] = None, args: Optional[List[str]] = None, kwargs: Optional[dict] = None):
        self.command = command

        if kwargs:
            self.kwargs = kwargs
            self.kwargs['func_args'] = shlex.split(self.kwargs['func_args'])
            self.kwargs['fift_args'] = shlex.split(self.kwargs['fift_args'])
        else:
            self.kwargs = {'func_args': [], 'fift_args': [], 'run': False}

        self.args = args if args else []

        # Currently, running command in project root
        self.project_dir = check_for_needed_files_to_deploy(os.getcwd(), False)

    def run(self):
        if not self.command or self.command == 'build':
            self.build()
        elif self.command:
            command = [executable['func'], *self.kwargs['func_args'], self.command, *self.args, *self.kwargs]
            subprocess.run(command)
        else:
            logger.error("🔎 Can't find such command")
            sys.exit()

    def build(self):
        run_code = False

        if self.kwargs['run']:
            run_code = True

        # If file to build is passed
        if len(self.args):
            file_path = self.args[-1]

            if '/' in file_path:
                file_path = file_path.split('/')[-1]

            # Parse file base
            to_save_location = f"{file_path.split('.')[0]}.fif"

            if self.project_dir:
                to_save_location = f"{os.getcwd()}/build/{to_save_location}"

            self.args = list(map(lambda file: f"{os.getcwd()}/{file}", self.args))

            build_files(self.args, to_save_location, self.kwargs['func_args'], cwd=os.getcwd())

        else:
            if not self.project_dir:
                logger.error(
                    f"🤟 It is not project root [{bl}{os.getcwd()}{rs}] - I can't build project without project")
                sys.exit()

            to_save_location = f"{os.getcwd()}/build"

            # Build code
            fift_build(os.getcwd(), cwd=os.getcwd())

        build = [i.replace(os.getcwd(), '') for i in self.args]
        location = to_save_location.replace(os.getcwd(), '')
        logger.info(f"🥌 Build {bl}{build}{rs} {gr}successfully{rs}, check out {gr}.{location}{rs}")

        if run_code:
            logger.info(f"🛫 Will run your code!")
            command = fift_execute_command(to_save_location, self.kwargs['fift_args'])
            subprocess.run(command)
