import os.path
import platform
import sys
from typing import List

import yaml
from colorama import Fore, Style

from toncli.modules.utils.system.log import logger

gr = Fore.GREEN
bl = Fore.CYAN
rs = Style.RESET_ALL


class TonProjectConfig:
    def __init__(self, func_files_locations: List[str], name: str, to_save_location: str, data: str, boc: str,
                 address: str):
        self.name = name
        self.boc = boc
        self.address = address
        self.data = data
        self.to_save_location = to_save_location
        self.func_files_locations = func_files_locations

        if platform.system() == 'Windows':
            from toncli.modules.utils.system.conf import name_replace

            self.boc = boc.replace(name_replace[0], name_replace[1])
            self.address = address.replace(name_replace[0], name_replace[1])
            self.data = data.replace(name_replace[0], name_replace[1])
            self.to_save_location = to_save_location.replace(name_replace[0], name_replace[1])
            self.func_files_locations = [i.replace(name_replace[0], name_replace[1]) for i in func_files_locations]


class ProjectConf:
    def __init__(self, project_root: str):
        """Parse project.yaml to correctly build project"""
        self.contracts: List[TonProjectConfig] = []

        with open(os.path.abspath(f"{project_root}/project.yaml"), "r", encoding='utf-8') as stream:
            try:
                func_configuration = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                logger.error(f"😒 Can't load {bl}project.yaml{rs} in {gr}{project_root}{rs}, error:")
                logger.error(exc)
                sys.exit()

        for contract in func_configuration:
            contract_config = func_configuration[contract]
            func_files_locations = [f"{project_root}/{file_path}" for file_path in contract_config['func']]

            self.contracts.append(TonProjectConfig(**{
                'func_files_locations': func_files_locations,
                'name': contract,
                'boc': f"{project_root}/build/boc/{contract}.boc",
                'address': f"{project_root}/build/{contract}_address",
                'to_save_location': f"{project_root}/build/{contract}.fif",
                'data': f"{project_root}/{contract_config['data']}" if 'data' in contract_config else ""
            }))
