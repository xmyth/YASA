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
from utils import *
from globals import *
from readCfgFile import readGroupCfgFile, readBuildCfgFile

class flowList(object):
    def __init__ (self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def list(self):
        pass

    @list.setter
    def list(self,value):
        pass

    def check(self, value):
        return value in self.list

    def show(self):
        print ('Available '+self.name+':\n' + '\n'.join(['\t' + x for x in self.list]))


class testList(flowList):
    def __init__ (self):
        super(testList,self).__init__('Tests')
        self._testDir=defaultTestDir()
        self._testlist = {}

    @property
    def list(self):
        return self._testlist.keys()

    @property
    def testDir(self):
        return self._testDir

    @testDir.setter
    def testDir(self, value):
        if not os.path.isdir(expandDirVar(value)):
            raise SystemError('%s is not exists!' % value)
        self._testDir = expandDirVar(value)
        self._testlist = {}
        self._getTestList()

    def genTestFileList(self, dir, valid_tests=[]):
        testcases = []

        for test in self._testlist.values():

            if valid_tests:
                if os.path.basename(test) in valid_tests:
                    testcases.append(test)
            else:
                testcases.append(test)
            
        with open(os.path.join(dir,defaultTestListFile()), 'w') as file:
            file.write('+incdir+' + self._testDir + '\n')
            for test in testcases:
                file.write('+incdir+' + test + '\n')
                file.write('+incdir+' + os.path.join(test, '..') + '\n')
                file.write(os.path.join(test, os.path.basename(test) + '.sv') + '\n')

    def _getTestList(self):
        for dirpath, dirname, filename in os.walk(self._testDir, topdown=True, followlinks=True):
            if '.svn' in dirname:
                dirname.remove('.svn')
            for file in filename:
                basename, extname = os.path.splitext(file)
                if extname == '.sv' and basename == os.path.basename(dirpath):
                    self._testlist[basename] = dirpath
    def get_testfile(self, test):
        if test in self._testlist:
            return os.path.join(self._testlist[test], test + '.sv')

    def get_shm_tcl(self,test):
        if test in self._testlist:
            tcl = os.path.join(self._testlist[test], 'shm_dump.tcl')
            if os.path.isfile(tcl):
                return tcl
        return None

    def get_fsdb_tcl(self,test):
        if test in self._testlist:
            tcl = os.path.join(self._testlist[test], 'fsdb_dump.tcl')
            if os.path.isfile(tcl):
                return tcl
        return None

class allTestList(object):
    def __init__ (self):
        self._testlists={}

    def setTestLists(self, build, testlist):
        self._testlists[build] = testlist

    def show(self):
        if self._testlists:
            print ('Available tests:')
            for key, value in self._testlists.items():
                print('\t'+ key + ':\n' + '\n'.join(['\t\t' + x for x in sorted(value.list)]))
        else:
            testList().show()

class groupList(flowList):
    def __init__(self):
        super(groupList, self).__init__('Groups')
        self._groupFile = defaultGroupFile()
        self._grouplist = readGroupCfgFile(self._groupFile).testGroup.subSection.keys()

    @property
    def list(self):
        return self._grouplist

    @property
    def groupFile(self):
        return self._groupFile

    @groupFile.setter
    def groupFile(self, value):
        if not os.path.isfile(value):
            raise SystemError('%s is not exists!' % value)
        self._groupFile = value
        self._grouplist = readGroupCfgFile(self._groupFile).testGroup.subSection.keys()

class buildList(flowList):
    def __init__ (self):
        super(buildList, self).__init__('Builds')
        self._buildlist= readBuildCfgFile(defaultBuildFile()).build.subSection.keys()

    @property
    def list(self):
        return self._buildlist

testlist = allTestList()
buildlist = buildList()
grouplist = groupList()

def show(name):
    getattr(sys.modules[__name__], name + 'list').show()


#if __name__ == '__main__':
#    tests = testList()
#    tests._getTestList()
#    testlist.setTestLists('default_build', tests)
#    show('test')
#    show('build')
#    show('group')
