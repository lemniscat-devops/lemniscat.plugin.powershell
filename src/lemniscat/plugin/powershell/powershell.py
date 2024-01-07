# -*- coding: utf-8 -*-
# above is for compatibility of python2.7.11

import logging
import os
import subprocess, sys   
from lemniscat.core.util.helpers import LogUtil
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
    
    def cmd(self, cmds, **kwargs):
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
            line = p.stdout.readline()
            if(line != b''):
                ltrace = line.decode('utf-8').replace('\n', '')
                m = re.match(r"^\[lemniscat\.pushvar\] (?P<key>\w+)=(?P<value>.*)", str(ltrace))
                if(not m is None):
                    outputVar[m.group('key')] = m.group('value')
                else:
                    log.debug(f'  {ltrace}')
        
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
        return self.cmd(['powershell', '-Command', command])

    def run_script(self, script):
        return self.cmd(["powershell", "-File", script])

    def run_script_with_args(self, script, args):
        return self.cmd(["powershell", "-File", script, args])