%define name    cacti
%define version 0.8.7a
%define release %mkrel 3

%define _requires_exceptions pear(/usr/share/php-adodb/adodb.inc.php)

Name:       %{name}
Version:    %{version}
Release:    %{release}
Summary:    Cacti is a php frontend for rrdtool
License:    GPL
Group:      System/Servers
URL:        http://www.cacti.net
Source0:    http://www.cacti.net/downloads/%{name}-%{version}.tar.gz
Patch0:     cacti-0.8.7a-fhs.patch
Patch1:     cacti-0.8.6i-use_external_adodb.patch
Patch3:     cacti-0.8.7a-fhs-PA.patch
Requires:   apache-mod_php >= 2.0.54
Requires:   php-adodb >= 1:4.64-1mdk
Requires:   php-cli
Requires:   php-gd
Requires:   php-mysql
Requires:   php-snmp
Requires:   php-xml
Requires:   net-snmp-utils
Requires:   net-snmp
Requires:   rrdtool
# webapp macros and scriptlets
Requires(post):     rpm-helper >= 0.16-2mdv2007.0
Requires(postun):   rpm-helper >= 0.16-2mdv2007.0
BuildRequires:  rpm-helper >= 0.16-2mdv2007.0
BuildRequires:  rpm-mandriva-setup >= 1.23-1mdv2007.0
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

%prep
%setup -q
%patch0 -p1
%patch1 -p1
%patch3 -p1

# fix perms
find . -type d | xargs chmod 755
find . -type f | xargs chmod 644
chmod +x scripts/*.{pl,sh}
chmod +x poller.php cmd.php

%build

%install
rm -rf %{buildroot}

install -d -m 755 %{buildroot}%{_var}/www/%{name}
install -d -m 755 %{buildroot}%{_datadir}/%{name}
install -d -m 755 %{buildroot}%{_localstatedir}/%{name}
install -d -m 755 %{buildroot}%{_sysconfdir}

cp *.php %{buildroot}%{_var}/www/%{name}
# those are not required under web root
for file in {poller*,cmd}.php; do
    rm -f %{buildroot}%{_var}/www/%{name}/$file
    cp $file %{buildroot}%{_datadir}/%{name}
done
cp -pr docs %{buildroot}%{_var}/www/%{name}
cp -pr images %{buildroot}%{_var}/www/%{name}
cp -pr install %{buildroot}%{_var}/www/%{name}
cp -pr scripts %{buildroot}%{_datadir}/%{name}
cp -pr resource %{buildroot}%{_datadir}/%{name}
cp -pr lib %{buildroot}%{_datadir}/%{name}
cp -p cacti.sql %{buildroot}%{_datadir}/%{name}


# distribut include content
cp -p include/config.php %{buildroot}%{_sysconfdir}/%{name}.conf
find include -type f -a -name '*.php' -a -not -name 'config.php' | \
    tar --create --files-from - --remove-files | \
    (cd %{buildroot}%{_datadir}/%{name} && tar --preserve --extract)
find include -type f -a -not -name '*.php' -a -not -name 'config.php' | \
    tar --create --files-from - --remove-files | \
    (cd %{buildroot}%{_var}/www/%{name} && tar --preserve --extract)

# distribute install content
install -d -m 755 %{buildroot}%{_datadir}/%{name}/upgrade
mv %{buildroot}%{_var}/www/%{name}/install/*_to_*.php %{buildroot}%{_datadir}/%{name}/upgrade

# apache configuration
install -d -m 755 %{buildroot}%{_webappconfdir}
cat > %{buildroot}%{_webappconfdir}/%{name}.conf <<EOF
# Cacti Apache configuration file
Alias /%{name} %{_var}/www/%{name}
<Directory %{_var}/www/%{name}>
    Allow from all
</Directory>
EOF

# cron task
install -d -m 755 %{buildroot}%{_sysconfdir}/cron.d
cat > %{buildroot}%{_sysconfdir}/cron.d/%{name} <<EOF
#!/bin/sh
*/5 * * * *     apache     php %{_datadir}/%{name}/poller.php > /dev/null 2>&1
EOF
chmod 755 %{buildroot}%{_sysconfdir}/cron.d/%{name}

# logs
install -d -m 755 %{buildroot}%{_var}/log/%{name}
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
- the configuration file is /etc/cacti.conf
- the log files are in /var/log/cacti
- the files accessibles from the web are in /var/www/cacti
- the files non accessibles from the web are in /usr/share/cacti

post-installation
-----------------
You have to create the MySQL database using the file /usr/share/cacti/cacti.sql.

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
%_post_webapp

%postun
%_postun_webapp

%files
%defattr(-,root,root)
%doc LICENSE README.mdv docs/CHANGELOG docs/CONTRIB docs/README
%config(noreplace) %{_webappconfdir}/%{name}.conf
%config(noreplace) %{_sysconfdir}/%{name}.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%{_sysconfdir}/cron.d/%{name}
%{_var}/www/%{name}
%{_datadir}/%{name}
%attr(-,apache,apache) %{_localstatedir}/%{name}
%attr(-,apache,apache) %{_var}/log/%{name}


