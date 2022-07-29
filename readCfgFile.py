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
# Copyright (c) 2019-2020, Jude Zhang zhajio.1988@gmail.com

from buildCfg import *
from groupCfg import *
from globals import *
from pathlib import Path

class readCfgFileBase(baseCfg):
    def __init__(self, name, file):
        self._section = ConfigObj(infile=file, stringify=True)
        super(readCfgFileBase, self).__init__(name, self._section, None)
        self._subSectionType = {}
        self._validSection = ['build', 'testgroup']

    def _readSubSection(self):
        for k, v in getSections(self._section).items():
            if self._checkSubSection(k) and k in self._subSectionType:
                self._subSection[k] = self._subSectionType[k](k, v, self)
                self._subSection[k].parse()

    def _checkSubSection(self, key):
        if key not in self._validSection:
            raise ParseError('[%s] is unknown section' % key)
        return True
    
    
class readBuildCfgFile(readCfgFileBase):
    def __init__(self, file):
        super(readBuildCfgFile, self).__init__('readBuildCfgFile', file)
        self._subSectionType = {'build': buildCfg}
        self.parse()

    @property
    def build(self):
        if 'build' in self.subSection:
            return self.subSection['build']

    def getBuild(self, build=''):
        return self.build.getBuild(build)


    def compileOption(self, buildName):
        return self._toList(self.build.compileOption) + self._toList(self.getBuild(buildName).compileOption)

    def simOption(self, buildName):
        return self._toList(self.build.simOption) + self._toList(self.getBuild(buildName).simOption)

    def preCompileOption(self, buildName):
        return self._toList(self.build.preCompileOption) + self._toList(self.getBuild(buildName).preCompileOption)

    def preSimOption(self, buildName):
        return self._toList(self.build.preSimOption) + self._toList(self.getBuild(buildName).preSimOption)

    def postCompileOption(self, buildName):
        return self._toList(self.build.postCompileOption) + self._toList(self.getBuild(buildName).postCompileOption)

    def postSimOption(self, buildName):
        return self._toList(self.build.postSimOption) + self._toList(self.getBuild(buildName).postSimOption)

    def _toList(self, preOptions):
        if isinstance(preOptions, str):
            return [preOptions]
        elif isinstance(preOptions, list):
            return preOptions

class readGroupCfgFile(readCfgFileBase):
    def __init__(self, file):
        super(readGroupCfgFile, self).__init__('readGroupCfgFile', file)
        self._subSectionType = {'testgroup': groupCfg}
        self.parse()
        self._validBuild = []
        self._allBuild = []
        self._tests = {}

    @property
    def testGroup(self):
        if 'testgroup' in self.subSection:
            return self.subSection['testgroup']

    @property
    def validBuild(self):
        return self._validBuild[0]

    @property
    def allBuild(self):
        return list(set(self._allBuild))

    def get_testcases_by_folder(self, folder):        
        p = Path(defaultTestDir())
        folder = folder.strip()

        pattern = '*.sv'

        if folder.endswith('.sv'):
           pattern = folder
        elif folder:    
            pattern = folder + '/**/*.sv'
        
        testcases = []
        for testcase in p.rglob(pattern):
            if testcase.parent.stem == testcase.stem:
                testcases.append(testcase.stem)

        if testcases:
            if 'folder_' in self._tests:
                self._tests['folder_'].extend(testcases)
            else:
                self._tests['folder_'] = testcases

    def getTests(self, groupName):
        groupSection = self.testGroup.getGroup(groupName)
        globalBuild = groupSection.buildOption
        globalTests = groupSection.testsOption
        globalFolders = groupSection.foldersOption
        if globalBuild:
            self._validBuild.append(globalBuild)
            self._allBuild.append(globalBuild)
        if globalTests:
            self._tests[groupName] = globalTests
        if groupSection.include:
            for incGroup in groupSection.incGroups:
                if incGroup.testsOption:
                    self._tests[incGroup.name] = incGroup.testsOption
                if incGroup.buildOption:
                    self.setValidBuild(globalBuild, incGroup.buildOption)
                    self._allBuild.append(incGroup.buildOption)
        for folder in globalFolders:
            testcases = self.get_testcases_by_folder(folder)

        self.checkBuild(self._validBuild, groupName)
        return self._tests

    def setValidBuild(self, globalBuild, subBuild):
        if globalBuild and subBuild and globalBuild != subBuild:
            self._validBuild.append(globalBuild)
        elif subBuild and not globalBuild:
            self._validBuild.append(subBuild)
        elif globalBuild and not subBuild:
            self._validBuild.append(globalBuild)

    def checkBuild(self, buildList, groupName):
        buildSet = set(buildList)
        if len(buildSet) != 1:
            raise ValueError(('group %s has included subgroup is must be in same build' % groupName))

if __name__ == '__main__':
#    config = readBuildCfgFile(defaultBuildFile())
#    print(config.build.simOption)
#    print(config.build.compileOption)
#    print(config.build.getBuild('dla').name)
#    print(config.build.getBuild('dla').compileOption)
#    print(config.simOption('dla'))
#    print(config.preCompileOption('dla'))
#    print(config.postCompileOption('dla'))
#    print(config.preSimOption('dla'))
#    print(config.postSimOption('dla'))


    config = readGroupCfgFile(defaultGroupFile())
    config.getTests('v1_regr')
    config.getTests('top_regr')

    #for v in config.testgroup.subSection.values():
    #    print(v.include)
    #    print(v.name)
        #print(v.buildOption)
        #print(v.argsOption)
        #print(v.testsOption)
        #print('haha', v.include)
        #for include in v.include:
        #   print(config.getGroup(include).testsOption)
