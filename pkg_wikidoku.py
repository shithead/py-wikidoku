#!/usr/local/bin/python3

import os
import sys
import subprocess


basicPorts = ['help2man', 'libiconv', 'm4', 'pcre', 'perl-threaded', 'portupgrade', 'ruby', 'zsh']
portsDatabasePath = '/var/db/ports'

def errPrint( errorcode = os.EX_SOFTWARE, msg = None ):
    sys.stderr.write( '*** ERROR ***\n' )
    if msg is None:
        traceback.print_exc()
    else:
        sys.stderr.write( '\t%s\n' %msg )
        sys.exit( errorcode )

def systemCheck():
    if sys.platform.startswith('freebsd'):
        print('Your OS is EVIL!!!')
    else:
        print('Your OS is LAME!!!')
        sys.exit( os.EX_OSERR )

def wikiConfigPorts(wikiFile, availableConfigedPorts):
    wikiFile.write('\n=== konfigurierte Ports ===\n')
    for port in availableConfigedPorts:
        print(port)
        optionsFile = open( os.path.join( portsDatabasePath, port, 'options'), 'r')
        optionsFile_list = optionsFile.readlines()[ 4: ]
        wikiFile.writelines( [ '\n==== %s ====\n\n' %port, ' <code>\n'])
        for option in optionsFile_list:
            wikiFile.write( ' '+option )
        wikiFile.write( ' </code>\n\n' )

def wikiPackageList(configuredPorts, installedPorts):
    installConfigPorts = []
    if os.path.exists( 'pkg_list.wiki' ):
        os.remove( 'pkg_list.wiki' )
    portsFile = open( 'pkg_list.wiki', 'a' )
    portsFile.write( '=== installierte Ports ===\n\n' )
    for availablePort in installedPorts:
        if availablePort in configuredPorts:
            portsFile.write( '* [[' )
            if availablePort in basicPorts:
                portsFile.write( 'Server/Jails' )
            else:
                installConfigPorts.append( availablePort )
            portsFile.write( '#{0} | {0}]]\n'.format( availablePort ))
        else:
            portsFile.write( '* %s\n' %availablePort )
    wikiConfigPorts(portsFile, installConfigPorts)
    portsFile.close()

def main(portsDatabasePath):
    systemCheck()
    configuredPorts_list = sorted( os.listdir( portsDatabasePath ) )
    installedPortsUnformate_str = str( subprocess.check_output( [ 'pkg_info', '-a', '-E' ] ), 'UTF-8')
    installedPorts_list = installedPortsUnformate_str.splitlines()
    for installedPortsIndex in range(0, len(installedPorts_list)):
        installedPorts_list[installedPortsIndex] = installedPorts_list[installedPortsIndex][ : installedPorts_list[ installedPortsIndex ].rfind('-')]

    wikiPackageList(configuredPorts_list, installedPorts_list)

if __name__ == "__main__":
    try:
        main(portsDatabasePath)
    except SystemExit:
        sys.stderr.write( '\tSystemExit: %s' %sys.exc_info()[1] )
    except:
        errPrint()

    sys.exit( os.EX_OK )
