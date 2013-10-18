#!/usr/local/bin/python3

import os
import re
import sys
import traceback
import subprocess

# TODO is the functionaly of basic_ports test existenz
basic_ports = [] #['help2man', 'libiconv', 'm4', 'pcre', 'perl-threaded', 'portupgrade', 'ruby', 'zsh']
# 'lang_pattern' is a work around for matches with obsolate version-tag in port
# parsing (e.g. perl-threaded)
lang_pattern = [ 'apr', 'cyrus-sasl', 'c-ares', 'gd', 'hdf', 'jack',
'openldap', 'perl-threaded', 'py27', 'ruby', 'sdl', 'swig', 'tk-8.5', 'wxgtk2']
ports_db_prefix = '/var/db/ports'
portdir = '/usr/ports'
ex_name = r'(^\w.+)\-'
ex_name_version = r'(^\w.+)-(\d).\d*'
ex_tilt_dir_prefix = r'^\w.+_(\w.*)$'

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

# XXX headline more fancy idea
# def headder(inum):
#     return "="*inum

# Die Funktion 'percent_match' gibt das Verhältnis von 0.0..1.0
# der gefundenden Strings.
def percent_match ( pattern_list, string ):

    relation = 0.0
    for pattern in pattern_list:
        match = re.search( pattern, string )
        if match is not None:
            current_relation = len( pattern ) / len( string )
            if current_relation > relation:
                relation = current_relation

    return relation

# Informationen Paaren zwischen Portbezeichnung und Packetname
# Durch den Index der Liste 'config_ports_dir gehen'
#
# Suche "_OPTIONS_READ=" und parse die Portbezeichnung
#
# Wenn erfolgreich (nicht 'None') wird Portname und Version
# gespeichert ansonsten nur der Portname
def ports_named_pairing( config_ports_dir ):

    install_config_ports = {}
    avail_configed_ports = {}

    for config_index in range( len( config_ports_dir ) ):
        value = re.match( ex_tilt_dir_prefix, \
                          config_ports_dir[ config_index ] ).group(1)

        option_path = os.path.join( ports_db_prefix, \
                                    config_ports_dir[ config_index ], \
                                    'options')

        if os.path.exists( option_path ):
            port_optionfp = open( option_path )
            for port_option in port_optionfp.readlines():
                if '_OPTIONS_READ=' in port_option:
                    port = re.match(r'_OPTIONS_READ=(.*)', \
                                    port_option ).group(1)

                    port_name_version = re.match( ex_name_version, port )

                    if port_name_version is not None and \
                        not percent_match(  lang_pattern, \
                                            port_name_version.group(0) ):

                        key = port_name_version.group(0)
                    else:
                        key = re.match( ex_name, port ).group(1)

            install_config_ports.update( { key: value } )
            avail_configed_ports.update( \
                { config_ports_dir[ config_index ]: [ key, value ] } )

    return install_config_ports, avail_configed_ports

#
# TODO genauere Erklärung zur Funktion
#
def wiki_pkg_list(  install_config_ports, \
                    avail_configed_ports, \
                    installed_ports ):

    if os.path.exists('pkg_list.wiki'):
        os.remove('pkg_list.wiki')

    wikifp = open('pkg_list.wiki', 'a')
    wikifp.write('=== installierte Ports ===\n\n')

    # Einzeln die installierten Ports testen ob es auch
    # Konfigurationen vorhanden sind, ansonsten liste
    # das Port nur auf.
    #
    # Wenn das Port mit zur Basisinstalation gehört, schreibe
    # davor den wiki-Artikel 'Server/Jails' ansonsten übergebe 'available_port'
    # an die Liste der noch zu ergänzenden Portkonfigurationen
    #
    # Wenn das Port mit zur Basisinstalation gehört, schreibe
    # davor den Artikel 'Server/Jails' ansonsten übergebe 'available_port'
    # an die Liste der noch zu ergänzenden Portkonfigurationen
    #
    # 'wiki_config_port' beschreibt die 'wikifp' aus der Liste
    # 'avail_configed_ports' erhaltenden Portnamen die Konfigurationen.
    for available_port in installed_ports:
        if available_port in install_config_ports.keys():
            wikifp.write('* [[')
            if available_port in basic_ports:
                wikifp.write('Server/Jails')

            wikifp.write( '#{0} | {1}]]\n'.format( \
                install_config_ports[ available_port ], available_port ) )

            for dir_key in avail_configed_ports.keys():
                if available_port in avail_configed_ports[ dir_key ]:
                    avail_configed_ports.update( \
                        { dir_key: install_config_ports[ available_port ] } )
        elif available_port in install_config_ports.values():
            wikifp.write('* [[')
            if available_port in basic_ports:
                wikifp.write('Server/Jails')
            wikifp.write( '#{0} | {0}]]\n'.format( available_port ) )

            for dir_key in avail_configed_ports.keys():
                if available_port in avail_configed_ports[ dir_key ]:
                    avail_configed_ports.update( { dir_key: available_port } )
        else:
            wikifp.write('* %s\n' %available_port )

    wikifp.write('\n=== konfigurierte Ports ===\n')

    for port in avail_configed_ports.keys():
        optionsfp = open( os.path.join( ports_db_prefix, port, 'options'), 'r')
        optionsfp_list = optionsfp.readlines()[ 4: ]
        wikifp.writelines( [ '\n==== %s ====\n\n' \
            %avail_configed_ports[ port ], ' <code>\n'] )
        for option in optionsfp_list:
            wikifp.write( ' ' + option )
        wikifp.write(' </code>\n\n')
    wikifp.close()

# get_configured_ports gibt eine sortierte Liste aller bisher
# konfigurierten Ports zurück.
#
# 'no_options' contains Ports without 'options'-File
#
# Überprüfe, dass das Port eine 'options' Datei besitzt bei nicht
# vorhanden sein lösche Ports in der Liste
#
# FIXME Es wird nicht überprüft ob das Port noch installiert ist
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
# 'If' / kein 'next_installed_port')
# Überprüfe ob es mit dem gespeicherten Portnamen matched
# falls nicht, resete 'saved_port' und speichern ohne Versionsnummer
#
# Falls es kein 'saved_port' gibt speichern ohne versionsnummer
def get_installed_ports():
    installed_ports = str( subprocess.check_output( \
        ['pkg_info', '-a', '-E'] ), 'UTF-8')
    installed_ports_list = sorted( installed_ports.splitlines() )
    cnext = False
    saved_port = None

    for installed_ports_idx in range( 0, len( installed_ports_list ) ):
        if cnext:
            cnext = False
            continue

        installed_port_name_version = re.match( ex_name_version, \
            installed_ports_list[ installed_ports_idx ] )

        if installed_ports_idx != ( len( installed_ports_list ) - 1 ):
            next_installed_port_name_version = re.match( ex_name_version, \
                installed_ports_list[ installed_ports_idx + 1 ] )
        else:
            next_installed_port_name_version = None
            installed_ports_list[ installed_ports_idx ] = \
                installed_port.group(1)

        if installed_port_name_version is not None:
            if next_installed_port_name_version is not None:
                if  installed_port.group(1) == next_installed_port.group(1):
                    saved_port = installed_port
                installed_ports_list[ installed_ports_idx ] = \
                    installed_port.group(0)
                installed_ports_list[ installed_ports_idx + 1 ] = \
                    next_installed_port.group(0)
                cnext = True
                installed_port_name_version = None
                next_installed_port_name_version = None

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
    configed_ports_dir = get_configed_ports_dir()
    install_config_ports, avail_configed_ports = \
        ports_named_pairing( configed_ports_dir )
    installed_ports = get_installed_ports()
    wiki_pkg_list( install_config_ports, avail_configed_ports, installed_ports )

if __name__ == '__main__':
    try:
        main( ports_db_prefix )
    except SystemExit:
        sys.stderr.write('\tSystemExit: %s' %sys.exc_info()[1] )
    except:
        errPrint()

    sys.exit( os.EX_OK )

# vim: set tw=79 ts=4 sw=4 et: #
