#
# frontier_tomcat :   RPM Spec file for frontier tomcat distribution
#
Summary: Frontier Tomcat distribution
Name: frontier-tomcat

# Version signifies the apache-tomcat version, concatenated (by underscore)
#     with the version of frontier-servlet
# The version of frontier-servlet is taken from http://frontier.cern.ch/dist/
%define version_tomcat 11.0.7
%define version_servlet 4.0
%define major_version %(echo %{version_tomcat} | cut -d '.' -f 1)
# Would like to use Version: %{version_tomcat}_%{version_servlet}
#  but rpm2web.sh can't parse that
Version: 11.0.7_4.0

# disables brp-java-repack-jars which can take a long time
%define __jar_repack 0

Release: 1
License: GPL
Group: System/Server
Packager: Dave Dykstra <dwd@fnal.gov>
Source0: %{name}.tar.gz
BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version_tomcat}-%{release}-root
Prefix: /usr/share/frontier-tomcat
# If somebody wants to use a newer version of java they can but they'll
#  still need to also have this version installed.  I don't know what
#  else to do because Requires: java-openjdk >= 1.8.0 just doesn't work.
Requires: java-21.0.7-openjdk
Requires: unzip
Requires: python3
Obsoletes: frontier-servlet
%define etcdir /etc/tomcat/
%define initdTomcatScript /etc/init.d/frontier-tomcat
%define servletsPasswd %{etcdir}servlets.passwd
#%define prefix_etcdir %{prefix}/etc/
#%define servlets_conf_util %{prefix}/sbin/servletsConfUtil.py
%define sourceConfig \
	export CONFIG_FILE=/etc/tomcat/tomcat.conf;\
	export FRONTIER_USER=tomcat;\
	if [ -s ${CONFIG_FILE} ]; then\
		source ${CONFIG_FILE};\
	fi
%define serviceconfdir /usr/lib/systemd/system
%define tmpfilesconfdir /usr/lib/tmpfiles.d

%description
Frontier-Tomcat server distribution, including its servlets.
See: http://frontier.cern.ch/dist/rpms/frontier-tomcatREADME

%prep
%setup -c %{name} -n %{name}

%build

### wget http://frontier.cern.ch/dist/Frontier_%{version_servlet}.war

# Download the WAR file from GitLab Maven Registry
curl --header "Private-Token: ${GITLAB_TOKEN}" -O \
     "https://gitlab.cern.ch/api/v4/projects/209928/packages/maven/gov/fnal/Frontier/%{version_servlet}/Frontier-%{version_servlet}.war"

# Verify checksum (optional)
curl --header "Private-Token: ${GITLAB_TOKEN}" -o expected_sha256  \
     "https://gitlab.cern.ch/api/v4/projects/209928/packages/maven/gov/fnal/Frontier/%{version_servlet}/Frontier-%{version_servlet}.war.sha256"

# Calculate and compare checksums
calculated_sha256=$(sha256sum Frontier-%{version_servlet}.war | awk '{print $1}')
expected_sha256=$(cat expected_sha256)

if [ "$calculated_sha256" != "$expected_sha256" ]; then
    echo "Checksum verification failed!"
    echo "Expected: $expected_sha256"
    echo "Got: $calculated_sha256"
    exit 1
fi

# Kludge to debug frontier code that has not been submitted:
# - set the name of the code to be used at $FRONTIER_WAR_TO_DEBUG
# - uncomment the following line, build the rpm and test with it:
# cp $FRONTIER_WAR_TO_DEBUG ./Frontier_%{version_servlet}.war

%install

/bin/rm -rf $RPM_BUILD_ROOT
mkdir -p %{buildroot}%{prefix}/sbin %{buildroot}%{etcdir}

# wget the apache-tomcat tarball
wget  -O $RPM_BUILD_ROOT%{prefix}/apache-tomcat-%{version_tomcat}.tar.gz http://archive.apache.org/dist/tomcat/tomcat-%{major_version}/v%{version_tomcat}/bin/apache-tomcat-%{version_tomcat}.tar.gz

# Extract files from the tar ball
pushd $RPM_BUILD_ROOT%{prefix}
tar zxf $RPM_BUILD_ROOT%{prefix}/apache-tomcat-%{version_tomcat}.tar.gz
rm -f $RPM_BUILD_ROOT%{prefix}/apache-tomcat-%{version_tomcat}.tar.gz
popd

#rm things that are in the standard apache-tomcat package:
# everything in tomcat/webapps (and tomcat/conf/Catalina/localhost/)
rm -r $RPM_BUILD_ROOT%{prefix}/apache-tomcat-%{version_tomcat}/webapps

rm $RPM_BUILD_ROOT%{prefix}/apache-tomcat-%{version_tomcat}/conf/server.xml
rm $RPM_BUILD_ROOT%{prefix}/apache-tomcat-%{version_tomcat}/conf/logging.properties
rmdir $RPM_BUILD_ROOT%{prefix}/apache-tomcat-%{version_tomcat}/logs

#TBD: consider using unproto here, if possible
cp %{_builddir}/%{name}/unproto.sh $RPM_BUILD_ROOT%{prefix}/
cp -R %{_builddir}/%{name}/* $RPM_BUILD_ROOT%{prefix}/

# for servlets.conf
mv %{_builddir}/%{name}%{etcdir}/servlets.confConstants $RPM_BUILD_ROOT%{prefix}/etc
chmod 444 $RPM_BUILD_ROOT%{prefix}/etc/servlets.confConstants

sed -e '1,$ {s:@@@version_servlet@@@:'%{version_servlet}':g}' %{_builddir}/%{name}/sbin/servletsConfUtil.py.proto> $RPM_BUILD_ROOT%{prefix}/sbin/servletsConfUtil.py
chmod 755 $RPM_BUILD_ROOT%{prefix}/sbin/servletsConfUtil.py
sed -e '1,$ {s:@@@version@@@:'%{version_tomcat}':g}' %{_builddir}/%{name}/etc/frontier-tomcat-configurator.proto> $RPM_BUILD_ROOT%{prefix}/etc/frontier-tomcat-configurator
chmod 700 $RPM_BUILD_ROOT%{prefix}/etc/frontier-tomcat-configurator

rm -rf `find $RPM_BUILD_ROOT%{prefix}|grep '/\.svn'`

# this is created at post-install time but need placeholder for the
#   %ghost.  %ghost is used so it will be removed at uninstall time
mkdir -p $RPM_BUILD_ROOT/etc/cron.d
touch $RPM_BUILD_ROOT/etc/cron.d/frontier-tomcat.cron
mkdir -p $RPM_BUILD_ROOT%{tmpfilesconfdir}
touch $RPM_BUILD_ROOT%{tmpfilesconfdir}/frontier-tomcat.conf

# make systemd service file
mkdir -p ${RPM_BUILD_ROOT}%{serviceconfdir}
cat >${RPM_BUILD_ROOT}%{serviceconfdir}/%{name}.service <<!EOF!
[Unit]
Description=The Frontier Tomcat server
After=network.target remote-fs.target nss-lookup.target

[Service]
Type=forking
ExecStart=/etc/init.d/%{name} start
ExecReload=/etc/init.d/%{name} reload
ExecStop=/etc/init.d/%{name} stop
TimeoutStopSec=15
# We want systemd to give tomcat some time to finish gracefully, but still want
# it to kill tomcat after TimeoutStopSec if something went wrong during the
# graceful stop. Normally, Systemd sends SIGTERM signal right after the
# ExecStop, which would kill tomcat. We are sending useless SIGCONT here to give
# tomcat time to finish.
KillSignal=SIGCONT

[Install]
WantedBy=multi-user.target
!EOF!

# The %pre step uses a temporary file to tell the %post step if
#  the service was running.  It can't be in world-writable /tmp
#  because of the risk of race conditions.
%define wasrunningfile %{etcdir}/.%{name}-wasrunning

%pre

if [ ${RPM_INSTALL_PREFIX} == '/' ]; then
	echo "ERROR: RPM_INSTALL_PREFIX can not be '/'. Try another directory."
	exit 1
fi

%sourceConfig
if ! getent passwd ${FRONTIER_USER} >/dev/null 2>&1 ; then
	# user is missing, add it

	if ! getent group ${FRONTIER_USER} >/dev/null 2>&1 ; then
		# corresponding group is also missing, add it first
		if ! /usr/sbin/groupadd -r ${FRONTIER_USER} ; then
			echo "ERROR: failed to groupadd ${FRONTIER_USER}"
			exit 1
		fi
	fi

	if ! /usr/sbin/useradd -r -s /sbin/nologin -g ${FRONTIER_USER} ${FRONTIER_USER} ; then
		echo "ERROR: failed to useradd ${FRONTIER_USER}"
		exit 1
	fi
fi

## End: Handle FRONTIER_USER

mkdir -p %{etcdir}
rm -f %{wasrunningfile}
if [ $1 -gt 1 ]; then
   # an upgrade
   if /sbin/service frontier-tomcat status 1>/dev/null; then
      # already running. stop it before any files are installed because
      #  some of them are owned by root
      echo "Stopping the frontier-tomcat service"
      /sbin/service frontier-tomcat stop
      if [ ! $? -eq 0 ]; then
	 echo "ERROR: Failed to stop frontier-tomcat: rc: $?"
	 exit 1
      fi
      touch %{wasrunningfile}
   fi
fi

%post
%sourceConfig
if [ -f %{wasrunningfile} ]; then
   rm -f %{wasrunningfile}
   STARTSERVICE=true
else
   STARTSERVICE=false
fi

SPOOLCRONFILE=/var/spool/cron/${FRONTIER_USER}
if [ -s ${SPOOLCRONFILE} ]; then
	# clean up crontab entries from older rpm
	sed -i '/^0 0 .*\/tomcat_rotate/d' ${SPOOLCRONFILE}
	sed -i '/^0 9 .*\/updatetnsnames.sh/d' ${SPOOLCRONFILE}
	if [ ! -s ${SPOOLCRONFILE} ]; then
		rm -f ${SPOOLCRONFILE}
	fi
fi

export FRONTIER_PREFIX=${RPM_INSTALL_PREFIX} # TBD: get rid of this
if [ -z "${FRONTIER_TOMCAT_LOGS}" ]; then
	export FRONTIER_TOMCAT_LOGS="/var/log/tomcat"
fi

if [ -z "${PID_DIR}" ]; then
	export PID_DIR="/var/run/tomcat"
fi

export UNPROTO_SH="${RPM_INSTALL_PREFIX}/unproto.sh"

cd ${RPM_INSTALL_PREFIX}
./etc/frontier-tomcat-configurator
status=$?
if [ $status -eq 0 ]; then

   /bin/cp ${RPM_INSTALL_PREFIX}/etc/frontier-tomcat %{initdTomcatScript}
   /bin/chown root:root %{initdTomcatScript}
   /bin/chmod 755 %{initdTomcatScript}

   /sbin/chkconfig --add frontier-tomcat

   if $STARTSERVICE; then
      echo "Restarting the frontier-tomcat service"
      /sbin/service frontier-tomcat start
      if [ ! $? -eq 0 ]; then
	 echo "ERROR: failed to start frontier-tomcat. Dangling installation. Consider: rpm -e %{name}-%{version}-%{release}"
	 exit 1
      fi
   fi
else
   echo "ERROR: failed to install %{name}. Dangling installation. PLEASE DO: rpm -e %{name}-%{version}-%{release}. If previous release was installed, it may still be running"
   exit 1
fi

%preun
%sourceConfig
if [ $1 -eq 0 ]; then
	/sbin/service frontier-tomcat status 1>/dev/null
	status=$?
	if [ ${status} -eq 0 ]; then
		echo "Stopping the frontier-tomcat service"
		/sbin/service frontier-tomcat stop
		if [ ! $? -eq 0 ]; then
			echo "ERROR: failed to stop frontier-tomcat. Will unstall %{name}-%{version}-%{release}. Verify that there are no dangling processes (ps -efw|grep tomcat)"
			exit 0
		fi
	fi
	serv=`eval chkconfig --list frontier-tomcat 2>/dev/null | awk -F" " '{print $1}'`
	if [ "x${serv}" = "xfrontier-tomcat" ]; then
		echo "Removing the frontier-tomcat service from chkconfig"
		/sbin/chkconfig --del frontier-tomcat
	fi

#Do I want to support multiple releases, may it be important to keep the order for this scenario?
fi

%postun
%sourceConfig
if [ $1 -eq 0 ]; then
	/bin/rm -f %{initdTomcatScript}
	/bin/rm -f ${RPM_INSTALL_PREFIX}/etc/modifiedqueries_rotate.sh
	/bin/rm -f ${RPM_INSTALL_PREFIX}/etc/cron
	/bin/rm -f ${RPM_INSTALL_PREFIX}/etc/tomcat.logrotate
	/bin/rm -f ${RPM_INSTALL_PREFIX}/etc/modifiedqueries.logrotate
	/bin/rm -f ${RPM_INSTALL_PREFIX}/etc/frontier-tomcat
	/bin/rm -f ${RPM_INSTALL_PREFIX}/etc/tomcat_rotate.sh
	/bin/rm -f ${RPM_INSTALL_PREFIX}/etc/updatetnsnames.sh
	/bin/rm -f ${RPM_INSTALL_PREFIX}/etc/tnsnames.ora
	/bin/rm -f ${RPM_INSTALL_PREFIX}/etc/tnsnames.ora.new
	/bin/rm -f ${RPM_INSTALL_PREFIX}/bin/findmodifiedqueries
	# Removing all pointed to by symbolic link and itself
	/bin/rm -fr ${RPM_INSTALL_PREFIX}/apache-tomcat-%{version_tomcat} # Beware: rm -r
	/bin/rm -f ${RPM_INSTALL_PREFIX}/tomcat
	# Remove hostcert & hostkey if they were automatically copied in
	for k in cert key; do
	  if cmp -s /etc/grid-security/host$k.pem %{etcdir}/host$k.pem; then
	    /bin/rm -f %{etcdir}/host$k.pem
	  fi
	done
	# Remove empty directories
	for d in ${RPM_INSTALL_PREFIX}/etc ${RPM_INSTALL_PREFIX}/bin ${RPM_INSTALL_PREFIX} %{etcdir}; do
	  rmdir $d 2>/dev/null || true
	done
else
	# Not the last uninstall.
	# Remove anything left in non-current versions of apache-tomcat
	current="`readlink -f ${RPM_INSTALL_PREFIX}/tomcat`"
	if [ -n "$current" ]; then
	  for dir in ${RPM_INSTALL_PREFIX}/apache-tomcat-*; do
	    if [ "$dir" != "$current" ]; then
	      /bin/rm -fr "$dir"
	    fi
	  done
	fi
fi

%clean
%{__rm} -rf %{buildroot}

%files
%verify(not user group) %{prefix}/
%ghost /etc/cron.d/frontier-tomcat.cron
%ghost %{tmpfilesconfdir}/frontier-tomcat.conf
%{serviceconfdir}/%{name}.service

%changelog
# change log is in doc/frontier-tomcatRELEASE_NOTES
