
import argparse
import ast
import logging
import os
import re
from logging import Logger
from lemniscat.core.contract.engine_contract import PluginCore
from lemniscat.core.model.models import Meta, TaskResult, VariableValue
from lemniscat.core.util.helpers import FileSystem, LogUtil
from lemniscat.plugin.powershell.filestore import FileStore

from lemniscat.plugin.powershell.powershell import Powershell

_REGEX_CAPTURE_VARIABLE = r"(?:\${{(?P<var>[^}]+)}})"

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

    def __prepareVariables(self, withSecrets: bool = False) -> dict:
        result = {}
        
        for key in self.variables:
            if(withSecrets is True):
                result[key] = self.variables[key].value
            else:
                if(not self.variables[key].sensitive):
                    result[key] = self.variables[key].value
        return result
    
    def _replace_unresolved_variables(self, script: str) -> str:
        # replace unresolved variables with empty string
        self._logger.info("Unresolved variables will be replaced with empty string")
        return re.sub(_REGEX_CAPTURE_VARIABLE, '', script)

    def __run_powershell(self) -> TaskResult:
        # launch powershell command
        pwsh = Powershell()
        result = {}
        if(self.parameters.get('storeVariablesInFile') is not None):
            config = self.parameters['storeVariablesInFile']
            format = 'json'
            if(config.get('format') is not None):
                format = config['format']
            withSecrets = False
            if(config.get('withSecrets') is not None):
                withSecrets = config['withSecrets']
            file = FileStore()
            vars = self.__prepareVariables(withSecrets)
            if(format == 'json'):
                file.saveJsonFile(f'{os.getcwd()}/vars.json', vars)
                self._logger.info(f'Variables saved to {os.getcwd()}/vars.json')
            elif(format == 'yaml'):
                file.saveYamlFile(f'{os.getcwd()}/vars.yaml', vars)
                self._logger.info(f'Variables saved to {os.getcwd()}/vars.json')
            else:
                raise ValueError(f'Format {format} is not supported.')
        
        if(self.parameters['type'] == 'inline'):
            script = self.parameters['script']
            self._logger.debug("---------------------------")
            self._logger.debug("Interpreted script: ")
            script = self._replace_unresolved_variables(script)
            script = script.replace("'", "\"")
            self._logger.debug(f"{script}")
            self._logger.debug("---------------------------")
            result = pwsh.run(script)
        elif(self.parameters['type'] == 'file'):
            if(self.parameters.keys.__contains__('args')):
                result = pwsh.run_script_with_args(self.parameters['filePath'], self.parameters['args'])
            else:    
                result= pwsh.run_script(self.parameters['filePath'])
        
        if(result[3] is not None):   
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
        super().invoke(parameters, variables)
        self._logger.debug(f'Run {self.parameters["type"]} -> {self.meta}')
        task = self.__run_powershell()
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
    variables = {}   
    vars = ast.literal_eval(__cli_args.variables)
    for key in vars:
        variables[key] = VariableValue(vars[key])
    action.invoke(ast.literal_eval(__cli_args.parameters), variables)