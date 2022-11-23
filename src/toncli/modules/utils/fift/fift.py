# Copyright (c) 2022 Disintar LLP Licensed under the Apache License Version 2.0

import os
import platform
import shlex
import subprocess
import sys
import tempfile
import re
from typing import List, Optional

from colorama import Fore, Style

from toncli.modules.utils.func.func import Func
from toncli.modules.utils.system.conf import config_folder, executable, lite_client_tries, getcwd
from toncli.modules.utils.fift.commands import fift_execute_command
from toncli.modules.utils.lite_client.commands import lite_client_execute_command
from toncli.modules.utils.system.log import logger
from toncli.modules.utils.system.project import check_for_needed_files_to_deploy

bl = Fore.CYAN
rd = Fore.RED
gr = Fore.GREEN
rs = Style.RESET_ALL


class Fift:
    def __init__(self, command: str, args: Optional[List[str]] = None, kwargs: Optional[dict] = None,
                 quiet: Optional[bool] = False, cwd: Optional[str] = None):
        """
        Easy interact with fift command

        :param command: command to run
        :param args: argumets passed to command
        :param kwargs: kwargs
        :param quiet: Is output of lite-client needed
        :param cwd: Project root
        """
        self.cwd = cwd if cwd else getcwd()
        self.command = command
        self.quiet = quiet

        if kwargs:
            self.kwargs = kwargs
            self.kwargs['fift_args'] = shlex.split(self.kwargs['fift_args'])
            self.kwargs['lite_client_args'] = shlex.split(self.kwargs['lite_client_args'])
        else:
            self.kwargs = {'fift_args': [],
                           'lite_client_args': [],
                           'build': False,
                           'net': 'testnet',
                           'update': False}

        self.args = args

        # Currently, running command in project root
        self.project_dir = check_for_needed_files_to_deploy(getcwd(), True)
        self.cli_fif_lib = None

    def run(self, get_output=False):
        """Run specific command"""

        if not self.command or self.command == 'interactive':
            self.run_interactive()
        elif self.command == 'run':
            return self.run_script(get_output=get_output)
        elif self.command == 'sendboc':
            return self.sendboc()
        else:
            logger.error("🔎 Can't find such command")
            sys.exit()

    def sendboc(self):
        """Send BOC to blockchain"""
        from toncli.modules.utils.fift.cli_lib import build_cli_lib

        if not len(self.args):
            logger.error("👉 You need to specify FIFT file path to sendboc")
            sys.exit()

        filename = self.args[0]

        # Check that
        with open(filename, 'r', encoding='utf-8') as f:
            code = f.read()

            if 'saveboc' not in code:
                logger.error(f"🦷 You need to add {bl}saveboc{rs} to your fif file {gr}{filename}{rs}")
                sys.exit()

        if platform.system() == 'Windows':
            if '\\' in filename:
                filename = os.path.split(filename)[-1]
        else:
            if '/' in filename:
                filename = filename.split('/')[-1]

        # get file-base
        if '.' in filename:
            filename = filename.split('.')[0]

        if os.path.exists(os.path.abspath(f'{self.cwd}/build/boc')):
            path = os.path.abspath(f'{self.cwd}/build/boc/{filename}.boc')
        else:
            # if not project root - create temp directory
            path = tempfile.mkdtemp()
            path = os.path.abspath(f"{path}/{filename}.boc")

        logger.info(f"💾 Will save BOC to {gr}{path}{rs}")

        # If we never created cli.fif in project root
        if self.project_dir:
            self.cli_fif_lib = build_cli_lib(os.path.abspath(f'{self.cwd}/build/cli.fif'), {  # Generate cli.fif
                "is_project": '1',
                "project_root": self.cwd,
                "build_path": path,
            })

        # If it's not project root
        elif not self.project_dir:
            self.cli_fif_lib = build_cli_lib(render_kwargs={
                "is_project": '0',
                "project_root": tempfile.gettempdir(),
                "build_path": path
            })

        # generate BOC file
        # Our own cli.fif file need to be added before run
        command = fift_execute_command(file=self.args[0], args=[*self.args[1:], *self.kwargs['fift_args']],
                                       pre_args=["-L", self.cli_fif_lib])

        subprocess.run(command, cwd=os.path.abspath(self.cwd))

        # send boc file
        command = lite_client_execute_command(self.kwargs['net'], ['-v', '2', '-c', f'sendfile {path}'],
                                              update_config=self.kwargs['update'])
        output = None
        if self.quiet:
            output = open(os.devnull, 'w', encoding='utf-8')

        for _try in range(lite_client_tries):
            try:
                output = subprocess.check_output(command, cwd=os.path.abspath(self.cwd))
                if 'Connection refused' in output.decode():
                    continue
                break
            except Exception as e:
                if _try != 1:
                    continue
                else:
                    logger.error(f"😢 Error in lite-client execution: {' '.join(command)}")

    def run_script(self, get_output=False):
        """Runs fift in script mode on file"""
        if not len(self.args):
            logger.error("👉 You need to specify file path to run")
            sys.exit()

        if not len(self.kwargs['fift_args']):
            self.kwargs['fift_args'] = ["-I", os.path.abspath(f"{config_folder}/fift-libs"), "-s"]
        else:
            self.kwargs['fift_args'].append("-s")

        if self.project_dir and self.kwargs['build']:
            func = Func()
            func.run()

        command = [executable['fift'], *self.kwargs['fift_args'], *self.args]

        if get_output:
            proc = subprocess.Popen(command,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    text=True)
            return proc
        else:
            return subprocess.run(command)

    def run_interactive(self):
        """Run interactive fift"""
        logger.info(f"🖥  Run interactive fift for you ({bl}Ctrl+c{rs} to exit)")
        logger.info(f"🖥  A simple Fift interpreter. Type `bye` to quit, or `words` to get a list of all commands")
        if not len(self.kwargs['fift_args']):
            self.kwargs['fift_args'] = ["-I", os.path.abspath(f"{config_folder}/fift-libs"), "-i"]
        else:
            self.kwargs['fift_args'].append("-i")

        command = [executable['fift'], *self.kwargs['fift_args']]
        logger.debug(f"🖥  Command ({' '.join(command)})")

        try:
            subprocess.run(command)
        except KeyboardInterrupt:
            logger.info("🖥  Bye! Have a good code!)")
            sys.exit()

class FiftParser:
    # Wannabe fift parser. Currently only proc specs and tests
    def __init__(self, path: str):
        self.path      = path
        self.code      = None
        self.proc_find = re.compile('(\d*)\s?(?:DECLMETHOD|DECLPROC)\s(\S+)$', re.MULTILINE)
        self.load(path)

    def load(self, path: Optional[str] = None) -> int:
        if path is not None:
            self.path = path
        with open(self.path, 'r', encoding='utf-8') as code_file:
            self.code = code_file.read()
        return len(self.code)

    def list_proc(self) -> List[tuple]:
        return self.proc_find.findall(self.code)

    def lookup_tests(self, names: List[str]) -> List[tuple]:
        found = []
        for test_name in names:
            #Escaping any regex chars and replacing astrisks win non-space char class
            mask_parts = list(map(lambda x: re.escape(x), test_name.split('*')))
            proc_clean = "\S+".join(mask_parts)
            no_mask    = len(mask_parts) == 1
            if not test_name.startswith("__test"):
                #- or _ are allowed delimiters. Being an exotic type comes at a price
                proc_clean = "__test[-_]*" + proc_clean

            name_re    = re.compile("(?:DECLMETHOD|DECLPROC)\s(" + proc_clean + ")$", re.MULTILINE)
            found_proc = False

            if no_mask:
                #Return on first find
                proc_match = name_re.search(self.code)
                if proc_match is not None:
                    found.append(proc_match.group(1))
                    found_proc = True
            else:
                #Find all matching mask
                proc_match = name_re.findall(self.code)
                if len(proc_match) > 0:
                    found.extend(proc_match)
                    found_proc = True

            if not found_proc:
                logger.error(f"No tests matching {rd}{test_name}{rs} found!")
        return found
