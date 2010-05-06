%define name    cacti
%define version 0.8.7e
%define release %mkrel 11

%if %mdkversion > 200910
%define _requires_exceptions pear(/usr/share/php/adodb/adodb.inc.php)
%else
%define _requires_exceptions pear(/usr/share/php-adodb/adodb.inc.php)
%endif

%if %mdkversion < 200610
%define _localstatedir %{_var}
%define _webappconfdir %{_sysconfdir}/httpd/conf/webapps.d
%endif

Name:       %{name}
Version:    %{version}
Release:    %{release}
Summary:    Php frontend for rrdtool
License:    GPL
Group:      System/Servers
URL:        http://www.cacti.net
Source0:    http://www.cacti.net/downloads/%{name}-%{version}.tar.gz
Source1:    pa.sql
Patch0:     cacti-0.8.7e-PA-v2.6.patch
Patch1:     cacti-0.8.7e-fhs.patch
Patch2:     cacti-0.8.7e-use-external-adodb.patch
Patch3:     cacti-0.8.7e-use-external-adodb-old.patch
Patch10:    cli_add_graph.patch
Patch11:    snmp_invalid_response.patch
Patch12:    template_duplication.patch
Patch13:    cross_site_fix.patch
Requires:   apache-mod_php >= 2.0.54
Requires:   php-adodb >= 1:4.64-1mdk
Requires:   php-cli
Requires:   php-gd
Requires:   php-mysql
Requires:   php-snmp
Requires:   php-xml
Requires:   php-sockets
Requires:   net-snmp-utils
Requires:   net-snmp
Requires:   rrdtool
%if %mdkversion < 201010
Requires(post):   rpm-helper
Requires(postun):   rpm-helper
%endif
BuildArch:  noarch
BuildRoot:  %{_tmppath}/%{name}-%{version}

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
%setup -q
%patch0 -p1
%patch1 -p1
# location of adodb changed after 
%if %mdkversion > 200910
%patch2 -p1
%else
%patch3 -p1
%endif

# upstream patches
%patch10 -p 1
%patch11 -p 1
%patch12 -p 1
%patch13 -p 1

# fix perms
find . -type d | xargs chmod 755
find . -type f | xargs chmod 644
chmod +x scripts/*.{pl,sh}
chmod +x poller.php cmd.php

# no .htaccess file
rm -f cli/.htaccess

%build

%install
rm -rf %{buildroot}

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
install -m 644 %{SOURCE1} %{buildroot}%{_datadir}/%{name}/sql

# configuration
install -d -m 755 %{buildroot}%{_sysconfdir}
mv %{buildroot}%{_datadir}/%{name}/include/config.php \
    %{buildroot}%{_sysconfdir}/%{name}.conf
pushd %{buildroot}%{_datadir}/%{name}/include
ln -s ../../../..%{_sysconfdir}/%{name}.conf config.php
popd

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
#!/bin/sh
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
- /usr/share/cacti/sql/pa.sql

Warning, apache will segfault if cacti is run with an empty database...

Additional useful packages
--------------------------
- a MySQL database, either locale or remote
EOF

%clean
rm -rf %{buildroot}

%pre
if [ $1 = "2" ]; then
    # fix for old setup
    if [ -L %{_var}/www/%{name}/include ]; then
        rm -f %{_var}/www/%{name}/include
    fi
fi

%post
%if %mdkversion < 201010
%_post_webapp
%endif

%postun
%if %mdkversion < 201010
%_postun_webapp
%endif

%files
%defattr(-,root,root)
%doc LICENSE README.mdv docs/CHANGELOG docs/CONTRIB docs/README
%attr(640,root,apache) %config(noreplace) %{_webappconfdir}/%{name}.conf
%config(noreplace) %{_sysconfdir}/%{name}.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%{_sysconfdir}/cron.d/%{name}
%{_datadir}/%{name}
%attr(-,apache,apache) %{_localstatedir}/lib/%{name}
%attr(-,apache,apache) %{_localstatedir}/log/%{name}
%attr(-,apache,apache) %{_localstatedir}/log/%{name}/%{name}.log
