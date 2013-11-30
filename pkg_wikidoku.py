#!/usr/local/bin/python3

import os
import re
import sys
import traceback
import subprocess

# TODO is the functionaly of basic_ports test existenz
basic_ports = [] #['help2man', 'libiconv', 'm4', 'pcre', 'perl-threaded', 'portupgrade', 'ruby', 'zsh']
ports_db_prefix = '/var/db/ports'
portdir = '/usr/ports'

# regularexpression
re_name_version = r'(^\w.+)-(\d).\d*'
re_tilt_dir_prefix = r'^\w.+_(\w.+)$'

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


#
# TODO genauere Erklärung zur Funktion
#
def wiki_pkg_list(  ports_relation, installed_ports ):

    if os.path.exists('pkg_list.wiki'):
        os.remove('pkg_list.wiki')

    wikifp = open('pkg_list.wiki', 'a')
    wikifp.write('=== installierte Ports ===\n\n')

    # Einzeln die installierten Ports testen ob es auch
    # Konfigurationen vorhanden sind, ansonsten liste
    # das Port nur auf.
    #
    # Wenn das Port mit zur Basisinstalation gehört, schreibe
    # davor den Artikel 'Server/Jails' ansonsten übergebe an
    # 'port_option_filepart' die Portoptionen
    relation_values = []
    port_option_filepart = ['\n=== konfigurierte Ports ===\n']
    for available_port in installed_ports:
        if available_port in ports_relation.keys():
            relation_values = ports_relation[ available_port ]
            port_option_dir = relation_values[0]
            pkg_name = relation_values[1]

            wikifp.write('* [[')
            if pkg_name in basic_ports:
                wikifp.write('Server/Jails')

            wikifp.write( '#{0} | {1}]]\n'.format( pkg_name, available_port ) )

            optionsfp = open( os.path.join( ports_db_prefix, port_option_dir, \
                                            'options'), 'r')
            optionsfp_list = optionsfp.readlines()[ 4: ]
            port_option_filepart.append('\n==== %s ====\n\n' %pkg_name)
            port_option_filepart.append(' <code>\n' )

            for option in optionsfp_list:
                port_option_filepart.append( ' ' + option )
            port_option_filepart.append(' </code>\n\n')

        else:
            wikifp.write('* %s\n' %available_port )

    wikifp.writelines(port_option_filepart)
    wikifp.close()

# Die Funktion 'get_best_relation' gibt das Verhältnis von 0.0..1.0
# des besten Vergleiches zurueck.
def get_best_relation ( pattern_list, string ):

    relation = 0.0
    for pattern in pattern_list:
        try:
            match = re.search( pattern, string )
        except:
            continue
        if match is not None:
            current_relation = len( pattern ) / len( string )
            if current_relation > relation:
                relation = current_relation

    return relation

# Die Funktion 'get_best_match' gibt den besten String
# des besten Vergleiches zurueck.
def get_best_match ( pattern, string_list ):
    string = None
    relation = 0.0
    for current_string in string_list:
        match = re.search( pattern, current_string )
        if match is not None:
            current_relation = len( pattern ) / len( current_string )
            if current_relation > relation:
                relation = current_relation
                string = current_string
    return string

# Informationen Paaren zwischen Portbezeichnung und Packetname
# Durch den Index der Liste 'config_ports_dir gehen'
#
# Suche "_OPTIONS_READ=" und parse die Portbezeichnung
#
# Suche nach Portsbezeichnung die dem portnamen am ehesten zutreffend sind.
def ports_named_pairing( config_ports_dir, installed_ports ):

    install_config_ports = {}

    for config_index in range( len( config_ports_dir ) ):
        value1 = config_ports_dir[ config_index ]
        option_path = os.path.join( ports_db_prefix, \
                config_ports_dir[ config_index ], 'options')

        if os.path.exists( option_path ):
            port_optionfp = open( option_path )
            for port_option in port_optionfp.readlines():
                if '_OPTIONS_READ=' in port_option:
                    port_name_version = re.match(r'_OPTIONS_READ=(.*)', port_option ).group(1)
                    break

            port_name_version = re.match( re_name_version, port_name_version )
            print(option_path)
            if port_name_version is not None:
                relation_group_0 = get_best_relation( installed_ports, port_name_version.group(0) )
                relation_group_1 = get_best_relation( installed_ports, port_name_version.group(1) )
                if relation_group_0 > relation_group_1:
                    key = get_best_match( port_name_version.group(0), installed_ports )

                if relation_group_0 < relation_group_1:
                    key = get_best_match( port_name_version.group(1), installed_ports )
                value2 = re.match( re_tilt_dir_prefix, value1 ).group(1)
            else:
                value2 = re.match( re_tilt_dir_prefix, value1 ).group(1)
                if value2 is NULL:
                    value2 = value1

                key = get_best_match( value2, installed_ports )
        else:
            continue

        print("key: "+key)
        print("value1: "+value1)
        print("value2: "+value2)
        install_config_ports.update( { key: [ value1, value2 ] } )

    return install_config_ports

# get_configed_ports_dir gibt eine sortierte Liste aller bisher
# konfigurierten Ports zurück.
#
# 'no_options' contains Ports without 'options'-File
#
# Überprüfe, dass das Port eine 'options' Datei besitzt bei nicht
# vorhanden sein lösche Portsverzeichnis in der Liste
def get_configed_ports_dir():
    no_options = []
    configed_ports_dirs = os.listdir( ports_db_prefix )
    for configed_ports_idx in range( len( configed_ports_dirs ) ):
        option_path = os.path.join( ports_db_prefix, \
            configed_ports_dirs[ configed_ports_idx ], 'options')
        if not os.path.exists( option_path ):
            no_options.append( configed_ports_idx )

    for no_options_idx in no_options:
        configed_ports_dirs.pop( no_options_idx )

    return sorted( configed_ports_dirs )

#
# TODO genauere erklärung zur funktion
#
# Suche per regex den Portnamen, Version und Subversion
#
# Prüfen auf letzten '_idx' um die regex zu ignorieren
# und die Variable auf 'None' zu setzen
#
# Prüfe ob die Variablen ´gefüllt´ sind.
#
# Teste ob der Portname identisch ist und speichere Portname
# und Versionen speichere letzten identischen Portnamen und
# resete die Variablen
#
# Falls 'installed_port' nicht 'None' ist (kein Match im letzten
# 'If' / kein 'next_installed_port_name_version')
# Überprüfe ob es mit dem gespeicherten Portnamen matched
# falls nicht, resete 'saved_port' und speichern ohne Versionsnummer
#
# Falls es kein 'saved_port' gibt speichern ohne versionsnummer
def get_installed_ports():
    installed_ports = str( subprocess.check_output( \
        ['pkg_info', '-a', '-E'] ), 'ascii')
    installed_ports_list = sorted( installed_ports.splitlines() )
    cnext = False
    saved_port = None

    for installed_ports_idx in range( len( installed_ports_list ) ):
        if cnext:
            cnext = False
            continue

        installed_port_name_version = re.match( re_name_version, \
            installed_ports_list[ installed_ports_idx ] )

        if installed_ports_idx != ( len( installed_ports_list ) - 1 ):
            next_installed_port_name_version = re.match( re_name_version, \
                installed_ports_list[ installed_ports_idx + 1 ] )
        else:
            next_installed_port_name_version = None
            installed_ports_list[ installed_ports_idx ] = \
                installed_port_name_version.group(1)

        if installed_port_name_version is not None:
            if next_installed_port_name_version is not None:
                if installed_port_name_version.group(1) == next_installed_port_name_version.group(1):
                    saved_port = installed_port_name_version

                    installed_ports_list[ installed_ports_idx ] = \
                        installed_port_name_version.group(0)
                    installed_ports_list[ installed_ports_idx + 1 ] = \
                        next_installed_port_name_version.group(0)
                    cnext = True
                    installed_port_name_version = None
                    next_installed_port_name_version = None
                    continue

            if saved_port is not None:
                if installed_port_name_version.group(1) == saved_port.group(1):
                    installed_ports_list[ installed_ports_idx ] = \
                            installed_port_name_version.group(0)
                else:
                    saved_port = None
                    installed_ports_list[ installed_ports_idx ] = \
                            installed_port_name_version.group(1)
            else:
                installed_ports_list[ installed_ports_idx ] = \
                        installed_port_name_version.group(1)
            installed_port_name_version = None

    return sorted( installed_ports_list )

def main( ports_db_prefix ):
    systemCheck()
    installed_ports = get_installed_ports()
    configed_ports_dir = get_configed_ports_dir()
    ports_relation = ports_named_pairing( configed_ports_dir, \
                                                installed_ports )
    wiki_pkg_list( ports_relation, installed_ports )

if __name__ == '__main__':
    try:
        main( ports_db_prefix )
    except SystemExit:
        sys.stderr.write('\tSystemExit: %s' %sys.exc_info()[1] )
    except:
        errPrint()

    sys.exit( os.EX_OK )

# vim: set tw=79 ts=4 sw=4 et: #
