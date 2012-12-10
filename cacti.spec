%if %_use_internal_dependency_generator
%define __noautoreq 'pear(/usr/share/php/adodb/adodb.inc.php)'
%else
%define _requires_exceptions pear(/usr/share/php/adodb/adodb.inc.php)
%endif

%define pia_version 3.1

Summary:	Php frontend for rrdtool
Name:		cacti
Version:	0.8.7i
Release:	4
License:	GPL
Group:		System/Servers
URL:		http://www.cacti.net
Source0:	http://www.cacti.net/downloads/%{name}-%{version}-PIA-%{pia_version}.tar.gz
Patch0:		cacti-0.8.7i-PIA-3.1-fhs.diff
Patch1:		cacti-0.8.7i-PIA-3.1-use-external-adodb.diff
Requires:	apache-mod_php >= 2.0.54
Requires:	php-adodb >= 1:4.64-1mdk
Requires:	php-cli
Requires:	php-gd
Requires:	php-mysql
Requires:	php-snmp
Requires:	php-xml
Requires:	php-sockets
Requires:	net-snmp-utils
Requires:	net-snmp
Requires:	rrdtool
BuildArch:	noarch

%description
Cacti is a complete frondend to rrdtool, it stores all of the
nessesary information to create graphs and populate them with
data in a MySQL database.

The frontend is completely PHP driven. Along with being able
to maintain Graphs, Data Sources, and Round Robin Archives in
a database, cacti handles the data gathering also. There is
also SNMP support for those used to creating traffic graphs
with MRTG.

The plugin architecture patch has been applied

%prep

%setup -q -n %{name}-%{version}-PIA-%{pia_version}

%patch0 -p1
%patch1 -p0

rm -rf lib/adodb
find . -type f -name "*.orig" | xargs rm -f

# fix perms
find . -type d | xargs chmod 755
find . -type f | xargs chmod 644
chmod +x scripts/*.{pl,sh}
chmod +x poller.php cmd.php

# no .htaccess file
rm -f cli/.htaccess

%build

%install
install -d -m 755 %{buildroot}%{_datadir}/%{name}

install -d -m 755 %{buildroot}%{_datadir}/%{name}
cp *.php %{buildroot}%{_datadir}/%{name}
cp -pr docs %{buildroot}%{_datadir}/%{name}
cp -pr images %{buildroot}%{_datadir}/%{name}
cp -pr install %{buildroot}%{_datadir}/%{name}
cp -pr include %{buildroot}%{_datadir}/%{name}

cp -pr scripts %{buildroot}%{_datadir}/%{name}
cp -pr cli %{buildroot}%{_datadir}/%{name}
cp -pr resource %{buildroot}%{_datadir}/%{name}
cp -pr lib %{buildroot}%{_datadir}/%{name}

install -d -m 755 %{buildroot}%{_datadir}/%{name}/sql
install -m 644 cacti.sql %{buildroot}%{_datadir}/%{name}/sql

install -d -m 755 %{buildroot}%{_datadir}/%{name}/plugins

# fix SQL schemas
perl -pi -e 's/TYPE=/ENGINE=/' %{buildroot}%{_datadir}/%{name}/sql/*

# configuration
install -d -m 755 %{buildroot}%{_sysconfdir}
mv %{buildroot}%{_datadir}/%{name}/include/config.php \
    %{buildroot}%{_sysconfdir}/%{name}.conf
pushd %{buildroot}%{_datadir}/%{name}/include
ln -s ../../../..%{_sysconfdir}/%{name}.conf config.php
chmod 600 %{buildroot}%{_sysconfdir}/%{name}.conf
popd

perl -pi -e 's|\$url_path = "/";|\$url_path = "/cacti/";|' \
    %{buildroot}%{_sysconfdir}/cacti.conf

# data
install -d -m 755 %{buildroot}%{_localstatedir}/lib/%{name}
pushd %{buildroot}%{_datadir}/%{name}
ln -s ../../..%{_localstatedir}/lib/%{name} rra
popd

# apache configuration
install -d -m 755 %{buildroot}%{_webappconfdir}
cat > %{buildroot}%{_webappconfdir}/%{name}.conf <<EOF
# Cacti Apache configuration file
Alias /%{name} %{_datadir}/%{name}
<Directory %{_datadir}/%{name}>
    Order allow,deny
    Allow from all

    Options -FollowSymLinks

    <Files ~ "^(poller.*|cmd).php$">
        Order deny,allow
        Deny from all
    </Files>

    # recommanded value
    php_value memory_limit 128M
</Directory>

<Directory %{_datadir}/%{name}/scripts>
    Order deny,allow
    Deny from all
</Directory>

<Directory %{_datadir}/%{name}/cli>
    Order deny,allow
    Deny from all
</Directory>

<Directory %{_datadir}/%{name}/resource>
    Order deny,allow
    Deny from all
</Directory>

<Directory %{_datadir}/%{name}/lib>
    Order deny,allow
    Deny from all
</Directory>

<Directory %{_datadir}/%{name}/sql>
    Order deny,allow
    Deny from all
</Directory>
EOF

# cron task
install -d -m 755 %{buildroot}%{_sysconfdir}/cron.d
cat > %{buildroot}%{_sysconfdir}/cron.d/%{name} <<EOF
*/5 * * * *     apache     php %{_datadir}/%{name}/poller.php > /dev/null 2>&1
EOF

# logs
install -d -m 755 %{buildroot}%{_var}/log/%{name}
touch %{buildroot}%{_localstatedir}/log/%{name}/%{name}.log
install -d -m 755 %{buildroot}%{_sysconfdir}/logrotate.d
cat > %{buildroot}%{_sysconfdir}/logrotate.d/%{name} <<EOF
%{_var}/log/%{name}/*.log {
    missingok
    compress
}
EOF

rm -rf %{buildroot}%{_datadir}/%{name}/lib/adodb

cat > README.mdv <<EOF
Mandriva RPM specific notes

setup
-----
The setup used here differs from default one, to achieve better FHS compliance.
- the constant files are in %{_datadir}/%{name}
- the configuration file is /etc/cacti.conf
- the variable files are in %{_localstatedir}/lib/%{name}
- the log files are in %{_localstatedir}/log/%{name}

post-installation
-----------------
You have to create the MySQL database using the following files:
- /usr/share/cacti/sql/cacti.sql

Warning, apache will segfault if cacti is run with an empty database...

Additional useful packages
--------------------------
- a MySQL database, either locale or remote
EOF

%pre
if [ $1 = "2" ]; then
    # fix for old setup
    if [ -L %{_var}/www/%{name}/include ]; then
        rm -f %{_var}/www/%{name}/include
    fi
fi

%files
%defattr(-,root,root)
%doc LICENSE README.mdv docs/CHANGELOG docs/CONTRIB docs/README
%attr(640,root,apache) %config(noreplace) %{_webappconfdir}/%{name}.conf
%attr(640,root,apache) %%config(noreplace) %{_sysconfdir}/%{name}.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%{_sysconfdir}/cron.d/%{name}
%{_datadir}/%{name}
%attr(-,apache,apache) %{_localstatedir}/lib/%{name}
%attr(-,apache,apache) %{_localstatedir}/log/%{name}/%{name}.log


%changelog
* Thu Jan 19 2012 Oden Eriksson <oeriksson@mandriva.com> 0.8.7i-0.1mdv2011.0
+ Revision: 762385
- also actually make it work with external adodb (phew!)

* Thu Jan 19 2012 Oden Eriksson <oeriksson@mandriva.com> 0.8.7i-2
+ Revision: 762384
- fix a small typo ;)

* Thu Jan 19 2012 Oden Eriksson <oeriksson@mandriva.com> 0.8.7i-1
+ Revision: 762355
- 0.8.7i (PIA-3.1)

* Fri Sep 30 2011 Oden Eriksson <oeriksson@mandriva.com> 0.8.7h-1
+ Revision: 702090
- 0.8.7h (fixes *a lot* of security issues)
- drop obsolete patches
- use the http://www.cacti.net/downloads/pia/cacti-plugin-0.8.7h-PA-v3.0.tar.gz source instead of fiddling with private patches and what not
- rediffed the cacti-0.8.7g-use-external-adodb.patch patch

* Wed Sep 21 2011 Alexander Barakin <abarakin@mandriva.org> 0.8.7g-6
+ Revision: 700715
- bump release
- fix permissions on cacti.conf

* Thu Jun 30 2011 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.7g-5
+ Revision: 688401
- create plugins directory, and fix default configuration

* Wed Jun 29 2011 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.7g-4
+ Revision: 688237
- re-enable plugin architecture
- fix SQL schemas syntaxe
- drop pre-2010.0 compatibility

* Thu Oct 21 2010 Nicolas Lécureuil <nlecureuil@mandriva.com> 0.8.7g-3mdv2011.0
+ Revision: 587172
- Do not add shebang in cron.d file
  CCBUG: 57855

* Tue Aug 24 2010 Oden Eriksson <oeriksson@mandriva.com> 0.8.7g-2mdv2011.0
+ Revision: 572677
- added upstream patches P10 - P14
- added backporting magic

* Mon Jul 12 2010 Oden Eriksson <oeriksson@mandriva.com> 0.8.7g-1mdv2011.0
+ Revision: 551281
- 0.8.7g

* Mon Jun 21 2010 Oden Eriksson <oeriksson@mandriva.com> 0.8.7g-0.0.beta2.1mdv2010.1
+ Revision: 548397
- 0.8.7g-beta2

* Wed Jun 02 2010 Oden Eriksson <oeriksson@mandriva.com> 0.8.7f-1mdv2010.1
+ Revision: 546991
- 0.8.7f
- drop upstream added patches
- rediffed one patch

* Thu May 13 2010 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.7e-12mdv2010.1
+ Revision: 544671
- fix SQL injection vulnerability (CVE-2010-1431)

* Thu May 06 2010 Oden Eriksson <oeriksson@mandriva.com> 0.8.7e-11mdv2010.1
+ Revision: 543015
- bump release
- make it backportable for cs4
- sync with the mes5 updates

* Mon Mar 01 2010 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.7e-10mdv2010.1
+ Revision: 513146
- ship an empty log file to avoid a big red error message terrifying users in installation wizard

* Fri Feb 26 2010 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.7e-9mdv2010.1
+ Revision: 512119
- fix dependencies
- refer to actual configuration file location in error message
- drop unapplied installer patch
- clean patch 1 from backup files
- make configuration file perms more restrictive

* Tue Jan 19 2010 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.7e-8mdv2010.1
+ Revision: 493903
- rely on filetrigger for reloading apache configuration begining with 2010.1, rpm-helper macros otherwise
- cleaner default apache configuration
- symlink rrd directory from %%{_datadir}/%%{name}

* Sun Jan 03 2010 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.7e-7mdv2010.1
+ Revision: 486049
- switch apache ACLs to open to all by default, as application does not allow
 local modifications
- add a note in README.mdv about segfault occuring with an empty database

* Thu Dec 17 2009 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.7e-6mdv2010.1
+ Revision: 479728
- add all available upstream patches, including the fix for XSS vuln (CVE-2009-4032)

* Tue Dec 15 2009 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.7e-5mdv2010.1
+ Revision: 478975
- don't apply patch to prevent php to segfault when the database is empty, it
  has too many side-effect with Plugin Architecture patch
- fix backporting

* Sun Dec 13 2009 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.7e-4mdv2010.1
+ Revision: 478245
- add patch to avoid php segfault with empty database (#56306)
- update Plugin Architecture patch to 2.6
- ship missing SQL file for Plugin Architecture
- move SQL files in a specific subdirectory

* Fri Dec 04 2009 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.7e-3mdv2010.1
+ Revision: 473525
- don't attempt to isolate web files from other files, to better match upstream
  setup
- enforce new default access policy
- better default apache configuration

* Sat Jul 25 2009 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.7e-2mdv2010.0
+ Revision: 399767
- additional php-sockets dependency
- fix default log file location

* Sat Jul 25 2009 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.7e-1mdv2010.0
+ Revision: 399675
- new version
- use symlinks instead of patch for FHS compliance
- move web files under %%{_datadir}/%%{name}/www
- update for new adodb package

* Thu Feb 19 2009 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.7d-1mdv2009.1
+ Revision: 342756
- new version
- rediff FHS patch
- update PA patch

* Thu Aug 07 2008 Thierry Vignaud <tv@mandriva.org> 0.8.7b-4mdv2009.0
+ Revision: 266444
- rebuild early 2009.0 package (before pixel changes)

  + Pixel <pixel@mandriva.com>
    - adapt to %%_localstatedir now being /var instead of /var/lib (#22312)

* Sat May 24 2008 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.7b-3mdv2009.0
+ Revision: 210979
- update FHS patch for missing included file (fix #40862)
- update FHS patch for upgrade scripts

* Mon Mar 31 2008 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.7b-2mdv2008.1
+ Revision: 191186
- don't make cron task executable

* Fri Feb 29 2008 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.7b-1mdv2008.1
+ Revision: 176798
- new version
  update FHS and PA patches

* Mon Feb 18 2008 Thierry Vignaud <tv@mandriva.org> 0.8.7a-4mdv2008.1
+ Revision: 170781
- rebuild
- fix "foobar is blabla" summary (=> "blabla") so that it looks nice in rpmdrake

* Wed Jan 23 2008 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.7a-3mdv2008.1
+ Revision: 157170
- fix default URL root (fix #36617)

* Thu Jan 17 2008 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.7a-2mdv2008.1
+ Revision: 154062
- rediff fhs patch
  ifix _adodb.patch (should fix #36617)

  + Olivier Blin <blino@mandriva.org>
    - restore BuildRoot

  + Thierry Vignaud <tv@mandriva.org>
    - kill re-definition of %%buildroot on Pixel's request

* Wed Nov 28 2007 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.7a-1mdv2008.1
+ Revision: 113789
- new version
  rediff FHS patch
  apply Plugin Architecture patch from http://cactiusers.org/downloads/plugins/

  + Buchan Milne <bgmilne@mandriva.org>
    - New version 0.8.7
    - Drop LDAP protocol patch (protocol version support added upstream)
    - Add plugin patch from cactiusers.org (and the tarball it ships in)

* Fri Aug 17 2007 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.6j-1mdv2008.0
+ Revision: 65370
- remove eol fixing, as done by spec-helper
- new version


* Sat Oct 21 2006 Jérôme Soyer <saispo@mandriva.org> 0.8.6i-1mdv2007.0
+ Revision: 71585
- New release 0.8.6i
- Import cacti

* Wed Jul 12 2006 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.6h-6mdv2007.0
- use herein document for README.mdv

* Sat Jul 01 2006 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.6h-5mdv2007.0
- relax buildrequires versionning

* Tue Jun 27 2006 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.6h-4mdv2007.0
- new webapps macros
- decompress all patches

* Fri Mar 17 2006 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.6h-3mdk
- add patch to allow to select LDAP protocol
- fix included adodb removal
- backport compatible apache configuration file

* Mon Feb 27 2006 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.6h-2mdk
- fixes from J.P. Pasnak <pasnak@warpedsystems.sk.ca> (fix bug #21125)
 - rediff patch 0
 - move some additional files out of webroot

* Tue Jan 10 2006 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.6h-1mdk
- New release 0.8.6h
- rediff patch 0

* Mon Dec 05 2005 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.6g-3mdk
- move new poller scripts to /usr/share/cacti (fix bug #20065)
- rediff patch 0
- don't backup files before patching

* Thu Dec 01 2005 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.6g-2mdk
- rediff patch 0 (fix 0.8.6f -> 0.8.6g upgrade)

* Sun Nov 06 2005 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.6g-1mdk
- New release 0.8.6g
- rediff and merge patches 0, 2 and 3

* Wed Aug 17 2005 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.6f-3mdk
- rediff patch 3 to avoid false automatic pear dependencies

* Wed Aug 17 2005 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.6f-2mdk
- fix remaining wrong includes (fix bug #5423)

* Wed Jul 20 2005 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.6f-1mdk 
- new version
- fix upgrade
- fix include path
- mv upgrade libraries outside of www root

* Thu Jun 30 2005 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.6e-3mdk 
- use new rpm apache macros
- rediff patch 1 for new adodb
- only fix encoding for text files
- let rpm compute dependencies

* Thu Jun 23 2005 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.6e-2mdk 
- drop redundant requires 
- drop additional sources, herein documents are used
- safer %%post and %%postun
- don't use dos2unix
- use patch instead of symlinks for FHS compliance
- split include between /usr/share/cacti and /var/www/cacti
- remove script from webroot

* Thu Jun 23 2005 Oden Eriksson <oeriksson@mandriva.com> 0.8.6e-1mdk
- 0.8.6e (Major security fixes)
- fix apache changes
- use the %%mkrel macro

* Mon May 16 2005 Oden Eriksson <oeriksson@mandriva.com> 0.8.6d-4mdk
- don't trash images

* Mon May 16 2005 Oden Eriksson <oeriksson@mandriva.com> 0.8.6d-3mdk
- fix config
- fix reload

* Fri May 13 2005 Guillaume Rousse <guillomovitch@mandriva.org> 0.8.6d-2mdk 
- fix upgrading from 0.8.6c-5mdk and prior releases

* Wed May 11 2005 Oden Eriksson <oeriksson@mandriva.com> 0.8.6d-1mdk
- 0.8.6d
- rediff P0, P1 & P2
- fix deps
- use better anti ^M stripper

* Sat Apr 09 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 0.8.6c-10mdk
- fix #13964

* Sat Apr 09 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 0.8.6c-9mdk
- fix #13963

* Fri Feb 18 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 0.8.6c-8mdk
- spec file cleanups, remove the ADVX-build stuff
- fix rpmlint errors

* Mon Jan 31 2005 Guillaume Rousse <guillomovitch@mandrake.org> 0.8.6c-7mdk 
- fix configuration patch

* Sat Jan 29 2005 Guillaume Rousse <guillomovitch@mandrake.org> 0.8.6c-6mdk 
- fix inclusion pathes (Gilles Mocellin <cooker@gmocellin.dyndns.org>)
- move include and lib to /usr/share/cacti
- fix post-install and post-uninstall

* Thu Jan 27 2005 Guillaume Rousse <guillomovitch@mandrake.org> 0.8.6c-5mdk 
- top-level dir is now /var/www/cacti
- config is now in /etc
- reload apache instead of restarting it
- herein document instead of external source for apache config
- don't tag executables in /etc as config
- README.mdk

* Wed Jan 12 2005 Guillaume Rousse <guillomovitch@mandrake.org> 0.8.6c-4mdk 
- move resource out of web dir too
- rediff P0 accordingly
- make cron task run with webserver uid
- use herein document instead of additional source

* Thu Jan 06 2005 Guillaume Rousse <guillomovitch@mandrake.org> 0.8.6c-3mdk 
- fix scripts encoding and perms
- rediff P0 for additional path problems in xml files

* Mon Dec 20 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.8.6c-2mdk
- fix url

* Mon Dec 20 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.8.6c-1mdk
- 0.8.6c
- fix deps
- fix P0

* Sat Oct 09 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.8.6b-1mdk
- 0.8.6b
- fix P0
- bring back perms on the scripts, duh!

* Mon Oct 04 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.8.6-3mdk
- fix P0 and S1

* Mon Oct 04 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.8.6-2mdk
- fix strange perms

* Mon Oct 04 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.8.6-1mdk
- 0.8.6
- rediffed P0 & P1
- misc spec file fixes

* Mon May 31 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.8.5a-1mdk
- 0.8.5a
- fixed P0
- added P1

* Tue Mar 02 2004 Tibor Pittich <Tibor.Pittich@mandrake.org> 0.8.5-1mdk
- 0.8.5
- rediff patch1
- add logrotate script
- macroszification

* Thu Nov 27 2003 Guillaume Rousse <guillomovitch@mandrake.org> 0.8.4-2mdk
- add missing lib directory

* Tue Nov 25 2003 Guillaume Rousse <guillomovitch@linux-mandrake.com> 0.8.4-1mdk
- 0.8.4
- ADVX macros
- fix files list

