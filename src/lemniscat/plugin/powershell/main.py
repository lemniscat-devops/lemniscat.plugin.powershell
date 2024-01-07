
import argparse
import ast
import logging
import os
from logging import Logger
from lemniscat.core.contract.engine_contract import PluginCore
from lemniscat.core.model.models import Meta, TaskResult
from lemniscat.core.util.helpers import FileSystem, LogUtil

from lemniscat.plugin.powershell.powershell import Powershell


class Action(PluginCore):

    def __init__(self, logger: Logger) -> None:
        super().__init__(logger)
        plugin_def_path = os.path.abspath(os.path.dirname(__file__)) + '/plugin.yaml'
        manifest_data = FileSystem.load_configuration_path(plugin_def_path)
        self.meta = Meta(
            name=manifest_data['name'],
            description=manifest_data['description'],
            version=manifest_data['version']
        )

    def __run_powershell(self, parameters: dict = {}, variables: dict = {}) -> TaskResult:
        # launch powershell command
        pwsh = Powershell()
        result = {}
        if(parameters['type'] == 'InlineScript'):
            result = pwsh.run(parameters['script'])
        elif(parameters['type'] == 'FileScript'):
            if(parameters.keys.__contains__('args')):
                result = pwsh.run_script_with_args(parameters['filePath'], parameters['args'])
            else:    
                result= pwsh.run_script(parameters['filePath'])
           
        super().appendVariables(result[3])  
                
        if(result[0] != 0):
            return TaskResult(
                name=f'Powershell run',
                status='Failed',
                errors=result[2])
        else:
            return TaskResult(
                name='Powershell run',
                status='Completed',
                errors=[0x0000]
        )
        

    def invoke(self, parameters: dict = {}, variables: dict = {}) -> TaskResult:
        self._logger.debug(f'Run {parameters["type"]} -> {self.meta}')
        task = self.__run_powershell(parameters, variables)
        return task
    
    def test_logger(self) -> None:
        self._logger.debug('Debug message')
        self._logger.info('Info message')
        self._logger.warning('Warning message')
        self._logger.error('Error message')
        self._logger.critical('Critical message')

def __init_cli() -> argparse:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-p', '--parameters', required=True, 
        help="""(Required) Supply a dictionary of parameters which should be used. The default is {}
        """
    )
    parser.add_argument(
        '-v', '--variables', required=True, help="""(Optional) Supply a dictionary of variables which should be used. The default is {}
        """
    )                
    return parser
        
if __name__ == "__main__":
    logger = LogUtil.create()
    action = Action(logger)
    __cli_args = __init_cli().parse_args()   
    action.invoke(ast.literal_eval(__cli_args.parameters), ast.literal_eval(__cli_args.variables))