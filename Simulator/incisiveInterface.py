"""
Interface for the Cadence Incisive simulator
"""
import os
import re
from os.path import join, dirname, abspath, relpath
import sys
import argparse
from pathlib import Path
from utils import *
import logging
from .simulatorInterface import (simulatorInterface, run_command)
from .simCheck import *

LOGGER = logging.getLogger(__name__)

class waveArgsAction(argparse.Action):
    def __call__(self, parser, args, values, option = None):
        args.wave = values
        if args.wave == 'shm':
            appendAttr(args, 'compileOption', '-access +r')
        elif args.wave == 'fsdb':
            appendAttr(args, 'compileOption', '-access +r')
            appendAttr(args, 'simOption', '+fsdb+autoflush')
        elif args.wave == 'gui':
            appendAttr(args, 'compileOption', '-access +rwc -linedebug -uvmlinedebug')
            appendAttr(args, 'simOption', '-access +rwc -linedebug -gui')
        elif args.wave == 'debug':
            appendAttr(args, 'compileOption', '-access +rwc -linedebug -uvmlinedebug')
            appendAttr(args, 'simOption', '-access +rwc -linedebug -uvmlinedebug')

class covArgsAction(argparse.Action):
    def __call__(self, parser, args, values, option = None):
        args.cov = values
        if args.cov == 'all':
            appendAttr(args, 'compileOption', '-coverage all')
            appendAttr(args, 'simOption', '-coverage all')
            appendAttr(args, 'simOption', '-covoverwrite')
            appendAttr(args, 'simOption', '-write_metrics')
        elif args.cov =='covfile':
            appendAttr(args, 'simOption', '-covoverwrite')
            appendAttr(args, 'simOption', '-write_metrics')

class seedArgsAction(argparse.Action):
    def __call__(self, parser, args, values, option = None):
        args.seed = values
        if args.seed == 0:
            appendAttr(args, 'simOption', '-svseed 0')
        else:
            appendAttr(args, 'simOption', '-svseed %d' % args.seed)

class testArgsAction(argparse.Action):
    def __call__(self, parser, args, values, option = None):
        args.test = values
        if args.test:
            appendAttr(args, 'simOption', '+UVM_TESTNAME=%s' % args.test)

class dpArgsAction(argparse.Action):
    def __call__(self, parser, args, values, option = None):
        args.dp = values
        if args.dp:
            for i in args.dp.split(','):
                appendAttr(args, 'simOption', '+uvm_set_verbosity=uvm_test_top*,' + i + ',UVM_DEBUG,time,0')

class incisiveInterface(simulatorInterface):
    """
    Interface for the Cadence Incisive simulator
    """

    name = "irun"
    supports_gui_flag = True

    @staticmethod
    def add_arguments(parser, group):
        """
        Add command line arguments
        """
        group.add_argument('-t', '-test', dest='test', action=testArgsAction, help='assign test name')

        parser.add_argument('-w', '-wave', nargs='?', const='shm', dest='wave', action=waveArgsAction,
                            choices=['shm', 'fsdb', 'gui', 'debug'],
                            help='dump waveform(shm), default shm')
        parser.add_argument('-cov', nargs='?', const='all', dest='cov', action=covArgsAction,
                            help='collect code coverage, default all kinds collect(line+cond+fsm+tgl+branch+assert')

        parser.add_argument('-seed', type=positive_int, dest='seed', default=0, action=seedArgsAction,
                            help='set testcase ntb random seed')
        parser.add_argument('-dp', nargs='?', dest='dp', default='', action=dpArgsAction,
                            help='set IDs with UVM_DEBUG')

    @classmethod
    def find_prefix_from_path(cls):
        """
        Find irun simulator from PATH environment variable
        """
        return cls.find_toolchain(['irun'])

    def __init__(self):
        simulatorInterface.__init__(self)
        self._simCheck = irunSimCheck()

    @property
    def simCheck(self):
        return self._simCheck;

    def compileExe(self):
        """
        Returns Incisive compile executable cmd
        """
        return 'irun'

    def simExe(self):
        """
        Returns Incisive simv executable cmd
        """
        return 'irun'

#    def executeCompile(self, buildDir, cmd, printer, timeout):
#        """
#        Incisive doesn't need compile step, so override this function
#        in base class, then do nothing 
#        """
#        pass

    def executeSimulataion(self, testWordDir, simCmd, timeout):
        if not run_command(simCmd, testWordDir, timeout):
            return False
        else:
            return True

    def merge_coverage(self, group_root_dir, build_dir, args=None):
        p_group = Path(group_root_dir)
        p_build = Path(build_dir)

        with open(p_build.joinpath('cov_sv.list'), 'w') as f:
            for i in p_group.glob('**/cov_work/scope/test_sv*'):
                f.write(str(p_group.joinpath(i)) + "\n")

        with open(p_build.joinpath('imc_command'), 'w') as f:
            f.write("merge -out merged_covs -overwrite -metrics all -initial_model union_all -runfile cov_sv.list" + "\n")
            f.write("load -run cov_work/scope/merged_covs" + "\n")
            f.write("report -summary -metrics all -text -out coverage.report" + "\n")

        imc_cmd = "imc -64bit union_all -exec imc_command -quiet"

        if not run_command(imc_cmd, build_dir):
            return False
        else:
            return True

class irunSimCheck(simCheck):
    """
    Irun specified simulation results checker
    """  
    irunErrorPattern = r'^((ncsim)|(irun)): \*E,.*'  
    coreDumpPattern = r'Completed context dump phase'
    simEndPattern = r'ncsim> exit'    
    timingViolationPattern = r'.*Timing violation.*'

    def __init__(self):
        super(irunSimCheck, self).__init__()
        self._simEndPattern = re.compile(irunSimCheck.simEndPattern)        
        self.setErrPatterns(irunSimCheck.irunErrorPattern)    
        self.setErrPatterns(irunSimCheck.coreDumpPattern)
        self.setWarnPatterns(irunSimCheck.timingViolationPattern)        
