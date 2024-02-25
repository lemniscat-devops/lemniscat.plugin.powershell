# -*- coding: utf-8 -*-
# above is for compatibility of python2.7.11

import logging
import os
import subprocess, sys   
from lemniscat.core.util.helpers import LogUtil
from lemniscat.core.model.models import VariableValue
import re

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.setLoggerClass(LogUtil)
log = logging.getLogger(__name__.replace('lemniscat.', ''))

class Powershell:
    def __init__(self):
        pass
    
    def cmd(self, cmds, isMultiline, **kwargs):
        outputVar = {}
        capture_output = kwargs.pop('capture_output', True)
        is_env_vars_included = kwargs.pop('is_env_vars_included', False)
        if capture_output is True:
            stderr = subprocess.PIPE
            stdout = subprocess.PIPE
        else:
            stderr = sys.stderr
            stdout = sys.stdout
            
        environ_vars = {}
        if is_env_vars_included:
            environ_vars = os.environ.copy()

        p = subprocess.Popen(cmds, stdout=stdout, stderr=stderr,
                             cwd=None)
        
        while p.poll() is None:
            if(isMultiline is True):
                lines = p.stdout.readlines()
                errors = p.stderr.readlines()
                for line in lines:
                    ltrace = line.decode('utf-8').rstrip('\r\n')
                    m = re.match(r"^\[lemniscat\.pushvar(?P<secret>\.secret)?\] (?P<key>\w+)=(?P<value>.*)", str(ltrace))
                    if(not m is None):
                        if(m.group('secret') == '.secret'):
                            outputVar[m.group('key').strip()] = VariableValue(m.group('value').strip(), True)
                        else:
                            outputVar[m.group('key').strip()] = VariableValue(m.group('value').strip())
                    else:
                        log.info(f'  {ltrace}')
                for error in errors:
                    ltrace = error.decode("utf-8").rstrip("\r\n")
                    if(ltrace.startswith("ERROR:")):
                        log.error(f'  {ltrace}')
                    else:
                        log.warning(f'  {ltrace}')
            else:
                line = p.stdout.readline()
                error = p.stderr.readline()
                if(line != b''):
                    ltrace = line.decode('utf-8').rstrip('\r\n')
                    m = re.match(r"^\[lemniscat\.pushvar(?P<secret>\.secret)\] (?P<key>\w+)=(?P<value>.*)", str(ltrace))
                    if(not m is None):
                        if(m.group('secret') == '.secret'):
                            outputVar[m.group('key').strip()] = VariableValue(m.group('value').strip(), True)
                        else:
                            outputVar[m.group('key').strip()] = VariableValue(m.group('value').strip())
                    else:
                        log.info(f'  {ltrace}')
                if(error != b''):
                    etrace = error.decode("utf-8").rstrip("\r\n")
                    log.error(f'  {etrace}')  
        
        out, err = p.communicate()
        ret_code = p.returncode

        if capture_output is True:
            out = out.decode('utf-8')
            err = err.decode('utf-8')
        else:
            out = None
            err = None

        return ret_code, out, err, outputVar

    def run(self, command):
        return self.cmd(['pwsh', '-Command', command], True)

    def run_script(self, script):
        return self.cmd(["pwsh", "-File", script], True)

    def run_script_with_args(self, script, args):
        return self.cmd(["pwsh", "-File", script, args], True)