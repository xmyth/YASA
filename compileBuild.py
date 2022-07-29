#******************************************************************************
# * Copyright (c) 2019, XtremeDV. All rights reserved.
# *
# * Licensed under the Apache License, Version 2.0 (the "License");
# * you may not use this file except in compliance with the License.
# * You may obtain a copy of the License at
# *
# * http://www.apache.org/licenses/LICENSE-2.0
# *
# * Unless required by applicable law or agreed to in writing, software
# * distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# * See the License for the specific language governing permissions and
# * limitations under the License.
# *
# * Author: Jude Zhang, Email: zhajio.1988@gmail.com
# *******************************************************************************
import os
import sys
from globals import *
from readCfgFile import *
from utils import *
import tbInfo
from yasaCli import yasaCli
from random import randint
from exceptions import TestcaseUnknown
from color_printer import COLOR_PRINTER

class compileBuildBase(object):
    def __init__(self, cli=None, ini_file=None, simulator_if=None):
        """
        Argument object and input build file control

        :param args: The parsed argument object
        :param ini_file: user input build file instead of defaultBuildFile
        :returns: None
        """
        self._cli = cli
        self._simulator_if = simulator_if
        self._args = self._cli.getParsedArgs()
        if  ini_file is not None and os.path.exists(ini_file):
            self.buildCfg = readBuildCfgFile(ini_file)
        else:
            self.buildCfg = readBuildCfgFile(defaultBuildFile())
        self._testList = tbInfo.testList()
        self._testcasesDir = []
        self._seeds = []

    def prepareEnv(self):
        """
        Prepare build dir and testcase dirs
        """
        self.createRootWorkDir()
        if not self._args.simOnly:
            self.createBuildDir()
            self.createCompileCsh()
        if not self._args.compOnly:
            self.createCaseDir()
            self.genTestscaseSimCsh()

    def createRootWorkDir(self):
        createDir(defaultWorkDir())

    def createBuildDir(self):
        createDir(self._buildDir, self._args.clean)

    def createCaseDir(self):
        if self._args.unique_sim:
            createDir(self._testcaseRootDir, self._args.clean)

    @property
    def _buildDir(self):
        pass

    @property
    def _testcaseRootDir(self):
        pass

    @property
    def testList(self):
        return self._testList

    def get_test_sv(self, test):
        if test in self._testList:
            return os.path.join(self._testList[test], test + '.sv')
        else:
            return None

    def get_shm_tcl(self, test):
        tcl = self.testList.get_shm_tcl(test)
        if not tcl:
            tcl = defaultSHMDumpScriptFile()
        if os.path.isfile(tcl):
            return tcl
        else:
            return None

    def get_fsdb_tcl(self, test):
        tcl = self.testList.get_fsdb_tcl(test)
        if not tcl:
            tcl = defaultFSDBDumpScriptFile()
        if os.path.isfile(tcl):
            return tcl
        else:
            return None

    def get_covfile_ccf(self):
        ccf = defaultCOVFile()
        if os.path.isfile(ccf):
            return ccf
        else:
            return None


    @property
    def _testCaseWorkDir(self):
        """
        testcases work dir list, uesd in yasaTop,
        for creating testcasesuite
        """
        return self._testcasesDir

    def _check(self):
        """
        testcases work dir list, uesd in yasaTop,
        for creating testcasesuite
        """
        try:
            if not self.testList.check(self._args.test) and self._args.test:
                raise TestcaseUnknown(self._args.test)
            elif self._args.show:
                tbInfo.show(self._args.show)
                sys.exit(0)
        except TestcaseUnknown as err:
                tbInfo.show('test')
                COLOR_PRINTER.write('test: '  + str(err) + '\n', fg='ri')
                sys.exit(1)

    def generateSeed(self):
        """
        generate testcase used seeds.
        repeat default is 1
        if seed is default 0, used random data.
        if seed is not default, used setted seed data.
        """
        self._seeds = []
        for i in range(self._args.repeat):
            if self._args.seed == 0:
                seed = '%d' % (randint(1, 0xffffffff))
            else:
                seed = self._args.seed
            self._seeds.append(seed)

    def createCompileCsh(self):
        """
        generate compile used cshell files in buildDir.
        buildDir can change based on single test or group test flow
        in single test flow, buildDir change based on unique_sim cli
        """
        self._testList.genTestFileList(self._buildDir)
        with open(os.path.join(self._buildDir, 'pre_compile.csh'), 'w') as f:
            for item in self.buildCfg.preCompileOption(self._args.build):
                f.write(item + '\n')
        with open(os.path.join(self._buildDir, 'compile.csh'), 'w') as f:
            f.write('#!/bin/sh -fe\n')
            f.write(self._simulator_if.compileExe() + ' \\' + '\n')
            for index, item in enumerate(self.compileCshContent()):
                if index == len(self.compileCshContent())-1:
                    f.write('\t' + item + '\n')
                else:
                    f.write('\t' + item + ' \\' + '\n')
        with open(os.path.join(self._buildDir, 'post_compile.csh'), 'w') as f:
            for item in self.buildCfg.postCompileOption(self._args.build):
                f.write(item + '\n')

    def compileCshContent(self):
        """
        compile cshell file content, can be from build.cfg file, userCli
        and argparse namespace
        """
        cshContent = self.buildCfg.compileOption(self._args.build)
        if self._cli.userCliCompileOption():
            cshContent = cshContent + self._cli.userCliCompileOption()
        if hasattr(self._args, 'compileOption') and self._args.compileOption:
            cshContent  = cshContent + self._args.compileOption
        #return cshContent + ['-f %s' % defaultTestListFile()] + ['-l compile.log']
        if self._simulator_if.name == 'irun':
            if self._args.cov == 'covfile' and self.get_covfile_ccf():
                cshContent.append('-covfile ' + self.get_covfile_ccf())
            cshContent.append('-elaborate')
            cshContent.append('-nclibdirname ' + os.path.join(self._buildDir, 'INCA_libs'))
            cshContent.append('-f ' + os.path.join(self._buildDir, 'top.f'))
            cshContent.append('-f ' + os.path.join(self._buildDir, 'test.f'))
            cshContent.append('-snapshot top')
            cshContent.append('-top top')
        elif self._simulator_if.name == 'vcs':
            cshContent.append('-f ' + os.path.join(self._buildDir, 'top.f'))
            cshContent.append('-f ' + os.path.join(self._buildDir, 'test.f'))
            cshContent.append('-top top')
        return cshContent + ['-l compile.log']

    def compileCmd(self):
        """
        compilation command is a string of shell command, run in a python subprocess.
        when enable lsf subparser, insert lsf cmds at the top of shell command.
        """
        compileCmd = 'set -e; chmod a+x pre_compile.csh compile.csh post_compile.csh; ./pre_compile.csh %s; ./compile.csh; ./post_compile.csh;' % self._args.test
        if self._args.subparsers == 'lsf':
            lsfOptions = self._args.lsfOptions
            return "bsub -Is "  + " ".join(lsfOptions) + '"%s"' % compileCmd
        else:
            return compileCmd

    def createSimCsh(self, testcaseDir, seed, isGroup):
        """
        simulation cshell file content, can be from build.cfg file, userCli
        and argparse namespace
        """
        with open(os.path.join(testcaseDir, 'pre_sim.csh'), 'w') as f:
            for item in self.buildCfg.preSimOption(self._args.build):
                f.write(item + '\n')
            if len(self.buildCfg.preSimOption(self._args.build)) >=1 :
                f.write(self._args.test + '\n')
        with open(os.path.join(testcaseDir, 'sim.csh'), 'w') as f:
            #FIXME: if add shebang line, will cause */simv: No match. shell error
            #f.write('#!/bin/csh -fe\n')
            f.write('#!/bin/sh -fe\n')
            if not isGroup and self._args.wave == 'shm':
                f.write('if (($# > 0)) && [[ "$1" == "-v" ]]; then' + '\n')
                command_line = ['simvision', '-waves', '-snapshot top', '-cdslib',
                    os.path.join(self._buildDir, 'INCA_libs/top.nc/cds.lib'), os.path.join(testcaseDir, 'waves.shm') ]
                f.write(' '.join(command_line) + '\n')
                f.write('else' + '\n')
            elif not isGroup and self._args.wave == 'fsdb':
                f.write('if (($# > 0)) && [[ "$1" == "-v" ]]; then' + '\n')
                if self._simulator_if.name == 'irun':
                   command_line = ['verdi', '-sv', '-nologo', '-f', os.path.join(self._buildDir, 'verdi.f'), '-top top',
                       '-ssf', os.path.join(testcaseDir, 'waves.vf') ]
                else:      
                   command_line = ['verdi', '-sv', '-nologo', '-elab', os.path.join(self._buildDir, 'simv.daidir/kdb.elab++'), '-top top',
                       '-ssf', os.path.join(testcaseDir, 'waves.vf') ]

                f.write(' '.join(command_line) + '\n')
                f.write('else' + '\n')
            if self._simulator_if.name == 'irun':
                f.write(self._simulator_if.simExe() + ' \\' + '\n')
                if not isGroup and self._args.wave == 'shm':
                    tcl= self.get_shm_tcl(self._args.test)
                    if tcl:
                        f.write('\t' + '-input ' + tcl + ' \\' + '\n')
                elif not isGroup and self._args.wave == 'fsdb':
                    tcl= self.get_fsdb_tcl(self._args.test)
                    if tcl:
                        f.write('\t' + '-input ' + tcl + ' \\' + '\n')
            else:
                f.write(os.path.join(self._buildDir, self._simulator_if.simExe()) + ' \\' + '\n')
                if not isGroup and self._args.wave == 'shm':
                    tcl= self.get_shm_tcl(self._args.test)
                    if tcl:
                        f.write('\t' + '-ucli -i ' + tcl + ' \\' + '\n')
                elif not isGroup and self._args.wave == 'fsdb':
                    tcl= self.get_fsdb_tcl(self._args.test)
                    if tcl:
                        f.write('\t' + '-ucli -i ' + tcl + ' \\' + '\n')
            for index, item in enumerate(self.simCshContent()):
                if index == len(self.simCshContent())-1:
                    #TODO: move this line to vcsInterface, because ntb_random_seed is vcs keyword
                    if self._simulator_if.name == 'irun':
                        f.write('\t' + '-nclibdirname ' + os.path.join(self._buildDir, 'INCA_libs') + ' \\' +
                                '\n')
                        f.write('\t' + '-snapshot top' + ' \\' + '\n')
                        f.write('\t' + '-r top' + ' \\' + '\n')
                    if self._args.seed == 0:
                        if self._simulator_if.name == 'vcs':
                            f.write('\t' + '+ntb_random_seed=%s' % seed + ' \\' + '\n')
                        elif self._simulator_if.name == 'irun':
                            f.write('\t' + '-svseed %s' % seed + ' \\' + '\n')
                    if self._args.cov and self._simulator_if.name == 'vcs':
                        f.write('\t' + '-cm_name %s' % self._args.test + '__' + str(seed) + ' \\' + '\n')
                    if self._args.cov == 'covfile' and self.get_covfile_ccf():
                        f.write('\t' + '-covfile ' + self.get_covfile_ccf() + ' \\' + '\n')
                    if isGroup:
                        f.write('\t' + item + ' >& /dev/null\n')
                    else:
                        f.write('\t' + item + '\n')
                else:
                    f.write('\t' + item + ' \\' + '\n')
            if not isGroup:
                if self._args.wave == 'fsdb' or self._args.wave == 'shm':
                    f.write('fi' + '\n')
        with open(os.path.join(testcaseDir, 'post_sim.csh'), 'w') as f:
            for item in self.buildCfg.postSimOption(self._args.build):
                f.write(item + '\n')

    def simCshContent(self):
        simContent = []
        simContent = self.buildCfg.simOption(self._args.build)
        if self._cli.userCliSimOption():
            simContent = simContent + self._cli.userCliSimOption()
        if hasattr(self._args, 'simOption') and self._args.simOption:
            simContent = simContent+ self._args.simOption
        return simContent + ['-l sim.log']

    def simCmd(self):
        simCmd = 'set -e; chmod a+x pre_sim.csh sim.csh post_sim.csh; ./pre_sim.csh %s; ./sim.csh; ./post_sim.csh;' % self._args.test
        if self._args.subparsers == 'lsf':
            lsfOptions = self._args.lsfOptions
            return "bsub -Is "  + " ".join(lsfOptions) + '"%s"' % simCmd
        else:
            return simCmd

class singleTestCompile(compileBuildBase):
    def __init__(self, cli=None, ini_file='', simulator_if=None):
        super(singleTestCompile, self).__init__(cli, ini_file, simulator_if)
        try:
            self._build =  self.buildCfg.getBuild(self._args.build)
        except buildUnknown as err:
            tbInfo.show('build')
            COLOR_PRINTER.write('build: '  + str(err) + '\n', fg='ri')
            sys.exit(1)
        self.setTestlist()
        self._check()
        self.generateSeed()

    def generateSeed(self):
        """
        generate testcase used seeds.
        repeat default is 1
        if seed is default 0, used random data.
        if seed is not default, used setted seed data.
        """
        self._seeds = []

        if self._args.repeat == 1:
            seed = self._args.seed
            if seed == 0:
                seed = 10
            self._seeds.append(seed)

        else:
            for i in range(self._args.repeat):
                if self._args.seed == 0:
                    seed = '%d' % (randint(1, 0xffffffff))
                else:
                    seed = self._args.seed
                self._seeds.append(seed)

    @property
    def _buildDir(self):
        """
        when enable unique_sim. buildDir and testcase dir are both under defaultWorkDir.
        >>> YASAsim  -t sanity1 -u
        ${VER_MODULE_NAME}_out/candy_lover
        ${VER_MODULE_NAME}_out/sanity1/sanity1__2814985384/
        when use unique_sim, you can run sanity2 and other cases
        simulation directly, such as:
        >>> YASAsim  -t sanity2 -u -so
        ${VER_MODULE_NAME}_out/candy_lover
        ${VER_MODULE_NAME}_out/sanity2/sanity2__113547301/

        if not, buildDir is under testcase root dir
        >>> YASAsim  -t sanity1
        ${VER_MODULE_NAME}_out/sanity1/candy_lover
        ${VER_MODULE_NAME}_out/sanity1/sanity1__2814985384/

        Note: group testcases don't have unique_sim support.
        """
        if self._args.fo:
            return '_'.join([defaultWorkDir(),  self._args.fo])
        elif self._args.unique_sim:
            return os.path.join(defaultWorkDir(), self._build.name)
        elif self._args.test:
            return os.path.join(defaultWorkDir(), self._testcaseRootDir, self._build.name)

    @property
    def _testcaseRootDir(self):
        """
        create testcase dir, if have prefix, add join prefix and test, use '__'
        >>> YASAsim -t sanity1 -test_prefix jude
        ${VER_MODULE_NAME}_out/jude__sanity1/candy_lover
        ${VER_MODULE_NAME}_out/jude__sanity1/sanity1__3758707525/
        """

        if self._args.fo:
            return '_'.join([defaultWorkDir(),  self._args.fo])
        else:
            return os.path.join(defaultWorkDir(), self._args.testPrefix + '__' + self._args.test if self._args.testPrefix else self._args.test)

    def setTestlist(self):
        """
        set testcase list based on testcase loacation
        """
        if self._build.testDir:
            self._testList.testDir = self._build.testDir
        else:
            self._testList.testDir = defaultTestDir()
        tbInfo.testlist.setTestLists(self._build.name, self._testList)

    def genTestscaseSimCsh(self):
        """
        generate testcase sim cshell files and corresponding files loacation
        """

        dir = ''
        if self._args.fo:
            dir = self._testcaseRootDir
            self._testcasesDir.append(dir)
            self.createSimCsh(dir, self._seeds[0], 0)
        else:
            for i in self._seeds:
                dir = os.path.join(self._testcaseRootDir, self._args.test + '__' + str(i))
                self._testcasesDir.append(dir)
                createDir(dir)
                if len(self._seeds) >= 2:
                    self.createSimCsh(dir, i, 1)
                else:
                    self.createSimCsh(dir, i, 0)

    def createRootWorkDir(self):
        if self._args.fo:
            createDir('_'.join([defaultWorkDir(),  self._args.fo]))
        else:
            createDir(defaultWorkDir())

    def createCompileCsh(self):
        """
        generate compile used cshell files in buildDir.
        buildDir can change based on single test or group test flow
        in single test flow, buildDir change based on unique_sim cli
        """
        self._testList.genTestFileList(self._buildDir, [self._args.test])
        with open(os.path.join(self._buildDir, 'pre_compile.csh'), 'w') as f:
            for item in self.buildCfg.preCompileOption(self._args.build):
                f.write(item + '\n')
        with open(os.path.join(self._buildDir, 'compile.csh'), 'w') as f:
            f.write('#!/bin/sh -fe\n')
            f.write(self._simulator_if.compileExe() + ' \\' + '\n')
            for index, item in enumerate(self.compileCshContent()):
                if index == len(self.compileCshContent())-1:
                    f.write('\t' + item + '\n')
                else:
                    f.write('\t' + item + ' \\' + '\n')
        with open(os.path.join(self._buildDir, 'verdi.f'), 'w') as f:
            for index, item in enumerate(self.compileCshContent()):
                if item.startswith('-define') or item.startswith('+define+'):
                    f.write(item + '\n')
            f.write('-f ' + os.path.join(self._buildDir, 'top.f') + '\n')
            f.write('-f ' + os.path.join(self._buildDir, 'test.f') + '\n')
        with open(os.path.join(self._buildDir, 'post_compile.csh'), 'w') as f:
            for item in self.buildCfg.postCompileOption(self._args.build):
                f.write(item + '\n')

    def compileCshContent(self):
        """
        compile cshell file content, can be from build.cfg file, userCli
        and argparse namespace
        """
        cshContent = self.buildCfg.compileOption(self._args.build)
        if self._cli.userCliCompileOption():
            cshContent = cshContent + self._cli.userCliCompileOption()
        if hasattr(self._args, 'compileOption') and self._args.compileOption:
            cshContent  = cshContent + self._args.compileOption
        #return cshContent + ['-f %s' % defaultTestListFile()] + ['-l compile.log']
        if self._simulator_if.name == 'irun':
            cshContent.append('-elaborate')
            cshContent.append('-nclibdirname ' + os.path.join(self._buildDir, 'INCA_libs'))
            cshContent.append('-f ' + os.path.join(self._buildDir, 'top.f'))
            cshContent.append('-f ' + os.path.join(self._buildDir, 'test.f'))
            cshContent.append('-snapshot top')
            cshContent.append('-top top')
        elif self._simulator_if.name == 'vcs':
            cshContent.append('-f ' + os.path.join(self._buildDir, 'top.f'))
            cshContent.append('-f ' + os.path.join(self._buildDir, 'test.f'))
            cshContent.append('-top top')
        return cshContent + ['-l compile.log']

class groupTestCompile(compileBuildBase):
    def __init__(self, cli=None, group_file='', build_file='', simulator_if=None):
        super(groupTestCompile, self).__init__(cli, build_file, simulator_if)
        if  group_file is not None and os.path.exists(group_file):
            self.groupCfg = readGroupCfgFile(group_file)
        else:
            self.groupCfg = readGroupCfgFile(defaultGroupFile())
        try:
            self._group = self.groupCfg.testGroup.getGroup(self._args.group)
            self._build = self.buildCfg.getBuild(self._group.buildOption)
        except groupUnknown as err:
            tbInfo.show('group')
            COLOR_PRINTER.write('group: '  + str(err) + '\n', fg='ri')
            sys.exit(1)
        except buildUnknown as err:
            tbInfo.show('build')
            COLOR_PRINTER.write('build: '  + str(err) + '\n', fg='ri')
            sys.exit(1)
        self._args.build = self._group.buildOption
        self._testcases = self.groupCfg.getTests(self._args.group)
        self.setTestlist()

    @property
    def _buildDir(self):
        if self._group.name:
            return os.path.join(defaultWorkDir(), self._groupRootDir, self._group.buildOption)

    @property
    def _groupRootDir(self):
        return os.path.join(defaultWorkDir(), self._args.testPrefix + '__' + self._group.name if self._args.testPrefix else self._group.name)

    def setTestlist(self):
        for buildName in self.groupCfg.allBuild:
            build = self.buildCfg.getBuild(buildName)
            if build.testDir:
                self._testList.testDir = build.testDir
            else:
                self._testList.testDir = defaultTestDir()
            tbInfo.testlist.setTestLists(build.name, self._testList)

    def _getSysArgv(self):
        """
        Get cli argv from sys.argv, then add it to testcase options.
        but '-g' and '-t' are exclusive, because have konwn '-g' option
        in __init__ function, so return a sys.argv without '-g' option.
        """
        if '-g' in sys.argv[1:]:
            sysArgvList = sys.argv[1:]
            index = sysArgvList.index('-g')
            sysArgvList.pop(index)
            sysArgvList.pop(index)
            return sysArgvList

    def createCompileCsh(self):
        """
        generate compile used cshell files in buildDir.
        buildDir can change based on single test or group test flow
        in single test flow, buildDir change based on unique_sim cli
        """
        testcases = []
        for v in self._testcases.values():
            for test in v:
                testcases.append( test.split()[0] )
        testcases = set(testcases)
        self._testList.genTestFileList(self._buildDir, testcases)
        with open(os.path.join(self._buildDir, 'pre_compile.csh'), 'w') as f:
            for item in self.buildCfg.preCompileOption(self._args.build):
                f.write(item + '\n')
        with open(os.path.join(self._buildDir, 'compile.csh'), 'w') as f:
            f.write('#!/bin/sh -fe\n')
            f.write(self._simulator_if.compileExe() + ' \\' + '\n')
            for index, item in enumerate(self.compileCshContent()):
                if index == len(self.compileCshContent())-1:
                    f.write('\t' + item + '\n')
                else:
                    f.write('\t' + item + ' \\' + '\n')
        with open(os.path.join(self._buildDir, 'post_compile.csh'), 'w') as f:
            for item in self.buildCfg.postCompileOption(self._args.build):
                f.write(item + '\n')

    def genTestscaseSimCsh(self):
        """
        In this function, k stands for group name, v stands for a list of testcases and
        each testcase's arguments. split the testAndOptions, then get testcase's argument
        plus '-b' build name and '-t' testname, _cli.parseArgs() use this list as argv for
        parsing. By this method, you can get new parsed argument namespace for each testcase.
        testcase dir name is: group name + '__' + testcase name + '__' + random seed
        """
        dir = ''
        for k, v in self._testcases.items():
            for testAndOptions in v:
                testAndOptions = '-b %s '%(self.groupCfg.validBuild) + '-t ' + testAndOptions
                self._cli.parseArgs(argv=[x for x in testAndOptions.split(' ') if x !=''] + self._getSysArgv())
                self._args = self._cli.getParsedArgs()
                self._check()
                self.generateSeed()
                for i in self._seeds:
                    dir = os.path.join(self._groupRootDir, k + '__' + self._args.test + '__' + str(i))
                    self._testcasesDir.append(dir)
                    createDir(dir)
                    self.createSimCsh(dir, i, 1)

#if __name__ == '__main__':
#    import sys
#    from Simulator.vcsInterface import vcsInterface
#    simulator_if = vcsInterface()
#
#    cli = yasaCli("Yet another simulation architecture")
#    cli.parseArgs(sys.argv[1:])
#    #userCliCfg.compileOption(args)
#    #compile = singleTestCompile(cli,  simulator_if=simulator_if)
#    #compile.prepareEnv()
#    #compile.generateSeed()
#    compile = groupTestCompile(cli,  simulator_if=simulator_if)
#    compile.prepareEnv()
#    compile.generateSeed()
