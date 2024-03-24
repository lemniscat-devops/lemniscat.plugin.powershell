# -*- coding: utf-8 -*-
# above is for compatibility of python2.7.11

import logging
import os
import subprocess, sys
from queue import Queue
import threading   
from lemniscat.core.util.helpers import LogUtil
from lemniscat.core.model.models import VariableValue
import re

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

def enqueue_stream(stream, queue, type):
    for line in iter(stream.readline, b''):
        queue.put(str(type) + line.decode('utf-8').rstrip('\r\n'))

def enqueue_process(process, queue):
    process.wait()
    queue.put('x')

logging.setLoggerClass(LogUtil)
log = logging.getLogger(__name__.replace('lemniscat.', ''))

class Powershell:
    def __init__(self):
        pass
    
    def cmd(self, cmds, **kwargs):
        outputVar = {}
        capture_output = kwargs.pop('capture_output', True)
        stderr = subprocess.PIPE
        stdout = subprocess.PIPE
            

        p = subprocess.Popen(cmds, stdout=stdout, stderr=stderr,
                             cwd=None)
        
        q = Queue()
        to = threading.Thread(target=enqueue_stream, args=(p.stdout, q, 1))
        te = threading.Thread(target=enqueue_stream, args=(p.stderr, q, 2))
        tp = threading.Thread(target=enqueue_process, args=(p, q))
        te.start()
        to.start()
        tp.start()        
        
        if(capture_output is True):
            while True:        
                line = q.get()
                if line[0] == 'x':
                    break
                if line[0] == '2':  # stderr
                    if(line[1:].startswith("ERROR:")):
                        log.error(f'  {line[1:]}')
                    else:
                        log.warning(f'  {line[1:]}')
                if line[0] == '1':
                    ltrace = line[1:]
                    m = re.match(r"^\[lemniscat\.pushvar(?P<secret>\.secret)?\] (?P<key>[^=]+)=(?P<value>.*)", str(ltrace))
                    if(not m is None):
                        if(m.group('secret') == '.secret'):
                            outputVar[m.group('key').strip()] = VariableValue(m.group('value').strip(), True)
                        else:
                            outputVar[m.group('key').strip()] = VariableValue(m.group('value').strip())
                    else:
                        log.info(f'  {ltrace}')

        tp.join()
        to.join()
        te.join()         
        
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
        return self.cmd(['pwsh', '-Command', command])

    def run_script(self, script):
        return self.cmd(["pwsh", "-File", script])

    def run_script_with_args(self, script, args):
        return self.cmd(["pwsh", "-File", script, args])