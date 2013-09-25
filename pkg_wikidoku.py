#!/usr/local/bin/python3

import os
import re
import sys
import traceback
import subprocess

# TODO is the functionaly of basic_ports test existenz
basic_ports = [] #['help2man', 'libiconv', 'm4', 'pcre', 'perl-threaded', 'portupgrade', 'ruby', 'zsh']
ports_db_path = '/var/db/ports'
portdir = '/usr/ports'
ex_name = r'(^\w.+-)'
ex_name_version = r'(^\w.+-)(\d).\d*'
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

# 'wiki_config_port' beschreibt die 'wikifp' aus der Liste
# 'avail_configed_ports' erhaltenden Portnamen die Konfigurationen.
def wiki_config_port( wikifp, avail_configed_ports ):
    # Abschinttsüberschrift
    wikifp.write('\n=== konfigurierte Ports ===\n')
    for port in avail_configed_ports.keys():
        optionsfp = open( os.path.join( ports_db_path, port, 'options'), 'r')
        optionsfp_list = optionsfp.readlines()[ 4: ]
        wikifp.writelines( [ '\n==== %s ====\n\n'
                        %avail_configed_ports[port], ' <code>\n'])
        for option in optionsfp_list:
            wikifp.write( ' '+option )
        wikifp.write( ' </code>\n\n' )

def wiki_pkg_list(configured_ports, installed_ports):
    install_config_ports = {}
    avail_configed_ports = {}

    # {{{
    # Informationen Paaren zwischen Portbezeichnung und Packetname
    # Durch den Index der Liste 'configured_ports gehen'
    for config_index in range( len(configured_ports) ):
        value = re.match( ex_tilt_dir_prefix, \
                        configured_ports[config_index]).group(1)
        # speichern des Pfades zu den Optionen
        option_path = os.path.join(ports_db_path,
                configured_ports[ config_index ],
                'options')
        # Prüfen ob der Pfad vorhanden ist
        if os.path.exists( option_path ):
            port_optionfp = open( option_path )
            # Zeile für Zeile aus der Datei lesen
            for port_option in port_optionfp.readlines():
                # Prüfen ob "_OPTIONS_READ=" in der Zeile steht
                if '_OPTIONS_READ=' in port_option:
                    # Match auf die Portbezeichnung
                    port = re.match(r'_OPTIONS_READ=(.*)', port_option).group(1)

                    # Match Portname und Version
                    port_name_version = re.match( ex_name_version, port)
                    # Wenn erfolgreich (nicht 'None') wird Portname und Version
                    # gespeichert ansonsten nur der Portname
                    if port_name_version != None:
                        # Wir haben ein Paar mit Version
                        key = port_name_version.group(0)
                    else:
                        # Wir haben ein Paar ohne Version
                        key = re.match( ex_name, port).group(1)[:-1]
            install_config_ports.update({key: value})
            avail_configed_ports.update(
                    { configured_ports[ config_index ]: [ key, value ] })
    # }}}

    # Wenn die Datei 'pkg_list.wiki' bereits existiert, dann löschen.
    if os.path.exists( 'pkg_list.wiki' ):
        os.remove( 'pkg_list.wiki' )
    # Datei neu erstellen
    wikifp = open( 'pkg_list.wiki', 'a' )
    # Abschnittsüberschrift einfügen
    wikifp.write( '=== installierte Ports ===\n\n' )

    # Einzeln die installierten Ports testen ob es auch
    # Konfigurationen vorhanden sind, ansonsten liste
    # das Port nur auf.
    for available_port in installed_ports:
        if available_port in install_config_ports.keys():
            wikifp.write( '* [[' )
            # Wenn das Port mit zur Basisinstalation gehört, schreibe
            # davor den Artikel 'Server/Jails' ansonsten übergebe 'availablePort'
            # an die Liste der noch zu ergänzenden Portkonfigurationen
            if available_port in basic_ports:
                wikifp.write( 'Server/Jails' )

            wikifp.write( '#{0} | {1}]]\n'.format(
                install_config_ports[available_port],
                available_port ))
            # FIXME 1 {{{
            for dir_key in avail_configed_ports.keys():
                if available_port in avail_configed_ports[dir_key]:
                    avail_configed_ports.update({ dir_key:
                                    install_config_ports[available_port] } )
            # FIXME }}}
        elif available_port in install_config_ports.values():
            wikifp.write( '* [[' )
            # Wenn das Port mit zur Basisinstalation gehört, schreibe
            # davor den Artikel 'Server/Jails' ansonsten übergebe 'availablePort'
            # an die Liste der noch zu ergänzenden Portkonfigurationen
            if available_port in basic_ports:
                wikifp.write( 'Server/Jails' )
            wikifp.write( '#{0} | {0}]]\n'.format( available_port ))
            # FIXME 1 {{{
            for dir_key in avail_configed_ports.keys():
                if available_port in avail_configed_ports[dir_key]:
                    print("%s %s" %(available_port, avail_configed_ports[dir_key] ))
                    avail_configed_ports.update({ dir_key: available_port } )
            # FIXME }}}
        else:
            wikifp.write( '* %s\n' %available_port )
    wiki_config_port( wikifp, avail_configed_ports )
    # Datei schließen
    wikifp.close()

# get_configured_ports gibt eine sortierte Liste aller bisher
# konfigurierten Ports zurück.
#
# Es wird nicht überprüft ob das Port noch installiert ist
def get_configured_ports():
    # 'no_options' contains Ports without 'options'-File
    no_options = []
    configed_ports_dirs = os.listdir( ports_db_path )
    for configed_ports_idx in range( len(configed_ports_dirs) ):
        option_path = os.path.join(ports_db_path,
                            configed_ports_dirs[ configed_ports_idx ],
                            'options')
        # Überprüfe, dass das Port eine 'options' Datei besitzt
        # bei nicht vorhanden sein den index in der Liste merken
        if not os.path.exists( option_path ):
            no_options.append(configed_ports_idx)

    # Lösche Ports in der Liste ohne Konfigurationsdatei
    for no_options_idx in no_options:
        configed_ports_dirs.pop(no_options_idx)

    return sorted(configed_ports_dirs)

def get_installed_ports():
    installed_ports = str( subprocess.check_output( [ 'pkg_info', '-a', '-E' ] ), 'UTF-8')
    installed_ports_list = sorted(installed_ports.splitlines())
    # TODO search for error with obsolate version-tag in port parsing (e.g.
    # perl-threaded)
    cnext = False
    saved_port = None
    for installed_ports_idx in range( 0, len( installed_ports_list ) ):
        if (cnext):
            cnext = False
            continue
        # Suche per regex den Portnamen, Verdion und Subversion
        installed_port = re.match( ex_name_version,
                                installed_ports_list[installed_ports_idx] )
        # Prüfen auf letzten _idx um die regex zu ignorieren
        # und die Variable auf 'None' zusetzen
        if installed_ports_idx != ( len(installed_ports_list) -1 ) :
            next_installed_port = re.match( ex_name_version,
                                installed_ports_list[installed_ports_idx + 1] )
        else:
            next_installed_port = None
            installed_ports_list[ installed_ports_idx ] = \
                                                    installed_port.group(1)[:-1]
        # Prüfe ob die Variablen ´gefüllt´ sind.
        if next_installed_port is not None and installed_port is not None:
            # Teste ob der Portname identisch ist und speichere Portname und Versionen
            # speichere letzten identischen Portnamen und resete die Variablen
            if  installed_port.group(1) == next_installed_port.group(1):
                saved_port = installed_port
                installed_ports_list[ installed_ports_idx ] = \
                                                    installed_port.group(0)
                installed_ports_list[ installed_ports_idx + 1 ] = \
                                                    next_installed_port.group(0)
                cnext = True
                installed_port = None
                next_installed_port = None
        # Falls 'installed_port' nicht 'None' ist (kein Match im letzten 
        # 'If' / kein 'next_installed_port')
        # Überprüfe ob es mit dem gespeicherten Portnamen matched
        # falls nicht, resete 'saved_port' und speichern ohne Versionsnummer
        if installed_port:
                if saved_port:
                    if installed_port.group(1) == saved_port.group(1):
                        installed_ports_list[ installed_ports_idx ] = \
                                                        installed_port.group(0)
                    else:
                        saved_port = None
                        installed_ports_list[ installed_ports_idx ] = \
                                                        installed_port.group(1)
                # Falls es kein 'saved_port' gibt speichern ohne versionsnummer
                else:
                    installed_ports_list[ installed_ports_idx ] = \
                                                    installed_port.group(1)[:-1]
                installed_port = None

    return sorted(installed_ports_list)

def main(ports_db_path):
    systemCheck()
    configed_ports = get_configured_ports()
    installed_ports = get_installed_ports()
    wiki_pkg_list(configed_ports, installed_ports)

if __name__ == "__main__":
    try:
        main(ports_db_path)
    except SystemExit:
        sys.stderr.write( '\tSystemExit: %s' %sys.exc_info()[1] )
    except:
        errPrint()

    sys.exit( os.EX_OK )
