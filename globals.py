import os
import grp
import sys
from color_printer import COLOR_PRINTER

def checkEnv():
    if not 'VER_MODULE_DIR' in os.environ:
        raise EnvironmentError('$VER_MODULE_DIR is not defined')

checkEnv()

def defaultCliCfgFile():
    cliFile = os.path.join(os.environ['VER_MODULE_DIR'], 'etc', 'userCli.cfg')
    if os.path.exists(cliFile):
        return cliFile
    else:
        COLOR_PRINTER.write("%s doesn't exist!\n" % cliFile, fg='ri')
        sys.exit(1)

def defaultBuildFile():
    buildFile = os.path.os.path.join(os.environ['VER_MODULE_DIR'], 'etc', 'build_' + os.environ['YASA_SIMULATOR'] + '.cfg')
    if os.path.exists(buildFile):
        return buildFile
    buildFile = os.path.join(os.environ['VER_MODULE_DIR'], 'etc', 'build.cfg')
    if os.path.exists(buildFile):
        return buildFile
    else:
        COLOR_PRINTER.write("%s doesn't exist!\n" % buildFile, fg='ri')
        sys.exit(1)

def defaultGroupFile():
    groupFile = os.path.join(os.environ['VER_MODULE_DIR'], 'etc', 'group.cfg')
    if os.path.exists(groupFile):
        return groupFile 
    else:
        COLOR_PRINTER.write("%s doesn't exist!\n" % groupFile, fg='ri')
        sys.exit(1)

def defaultTestListFile():
    return 'test.f'

def defaultCovDir():
    return 'coverage'

def defaultYasaDir():
    if 'YASA_HOME' in os.environ:
        return os.environ['YASA_HOME']
    else :
        return os.path.join(os.environ['VER_MODULE_DIR'], 'bin', 'Yasa')

def defautlVplanDir():
    return os.path.join(os.environ['VER_MODULE_DIR'], 'etc', 'vplan')


def defaultTestDir():
    if 'TEST_DIR' in os.environ:
        return os.environ['TEST_DIR']
    else:
        return os.path.join(os.environ['VER_MODULE_DIR'], 'testcases')


def defaultWorkDir():
    if 'WORK_DIR' in os.environ:
        return os.environ['WORK_DIR']
    else:
        return os.path.join(defaultWorkPrjDir(), 'work')


def defaultReportDir():
    if 'REPORT_DIR' in os.environ:
        return os.environ['REPORT_DIR']
    else:
        return os.path.join(defaultWorkPrjDir(), 'report')

def userSimCheck():
    userSimCheckFile = os.path.join(os.environ['VER_MODULE_DIR'], 'etc', 'userSimCheck.py')
    if os.path.isfile(userSimCheckFile):
        return ('userSimCheck', userSimCheckFile)
    return (None, None)


def defaultWorkDir():
    work_dir = os.environ['VER_MODULE_DIR']
    return work_dir.replace('/vulcan/proj/', '/vulcan/local/temp/', 1)
    #prj_home = os.environ['VER_MODULE_DIR']
    #return os.path.join(prj_home, os.path.basename(prj_home) + '_out')

def defaultSHMDumpScriptFile():
    return os.path.join(os.environ['VER_MODULE_DIR'], 'etc', 'shm_dump.tcl')

def defaultFSDBDumpScriptFile():
    return os.path.join(os.environ['VER_MODULE_DIR'], 'etc', 'fsdb_dump.tcl')

def defaultCOVFile():
    return os.path.join(os.environ['VER_MODULE_DIR'], 'etc', 'covfile.ccf')

