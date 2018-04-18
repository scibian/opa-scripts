# BEGIN_ICS_COPYRIGHT8 ****************************************
#
# Copyright (c) 2015, Intel Corporation
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Intel Corporation nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# END_ICS_COPYRIGHT8   ****************************************

#[ICS VERSION STRING: unknown]
#
# spec file for package opa
#

Summary:        Omnipath Fabric initialization
Name:           opa-scripts
Version:        1.1
Release:        1
License:        GPL-2.0+
Group:          System Environment/Base
Source:         %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch

%if 0%{?rhel} && 0%{?rhel} < 7
Requires(post): /sbin/chkconfig
Requires(preun): /sbin/chkconfig
%else
BuildRequires:  systemd %{?systemd_requires}
Requires(post): systemd %{?systemd_requires}
Requires(preun): systemd %{?systemd_requires}
Requires(postun): systemd %{?systemd_requires}
%endif
Requires:       rdma
Requires:       irqbalance

%description
User space initialization scripts for the Omnipath Fabric

#for SuSE SLES12 & UP
%if 0%{?suse_version} >= 1315
%define ALLOW_MODULES "/etc/modprobe.d/10-unsupported-modules.conf"
%define ALLOW_MODULES_BACKUP "/var/cache/unsupported-modules.conf"
%endif

%prep
[ "${RPM_BUILD_ROOT}" != "/" -a -d ${RPM_BUILD_ROOT} ] && rm -rf $RPM_BUILD_ROOT
%setup -q -n %{name}-%{version}

%install
rm -rf $RPM_BUILD_ROOT

cd $RPM_BUILD_DIR/%{name}-%{version}

# We're using the existing rdma.conf file instead.
#install -d $RPM_BUILD_ROOT/etc/opa
#install -m 0644 opa.conf $RPM_BUILD_ROOT/etc/opa/opa.conf

%if 0%{?rhel} && 0%{?rhel} < 7
install -d $RPM_BUILD_ROOT%{_sysconfdir}/init.d
install -D -m 0755 opa-scripts.init $RPM_BUILD_ROOT%{_sysconfdir}/init.d/opa
%else
install -d $RPM_BUILD_ROOT%{_unitdir}
install -m 0644 opa.service $RPM_BUILD_ROOT%{_unitdir}/opa.service
%endif

install -d $RPM_BUILD_ROOT%{_sbindir}
install -m 0755 opad.sbin $RPM_BUILD_ROOT%{_sbindir}/opa-init-kernel

install -d $RPM_BUILD_ROOT/etc/init.d
install -m 0755 arptbl_tuneup $RPM_BUILD_ROOT%{_sbindir}/opa-arptbl-tuneup

install -d $RPM_BUILD_ROOT/etc/init.d

install -d $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/opa
install -m 0644 limits.conf $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/opa
install -m 0644 udev.permissions $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/opa
install -m 0644 udev.rules $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/opa

install -d $RPM_BUILD_ROOT/sbin
install -m 0755 opaautostartconfig $RPM_BUILD_ROOT/sbin/opaautostartconfig
install -m 0755 opasystemconfig $RPM_BUILD_ROOT/sbin/opasystemconfig

install -d $RPM_BUILD_ROOT%{_mandir}/man1
install -m 0644 opa-arptbl-tuneup.1 $RPM_BUILD_ROOT%{_mandir}/man1
install -m 0644 opa-init-kernel.1 $RPM_BUILD_ROOT%{_mandir}/man1
install -m 0644 opaautostartconfig.1 $RPM_BUILD_ROOT%{_mandir}/man1

install -d $RPM_BUILD_ROOT%{_prefix}/lib/opa
install -m 0755 .comp_ofed_delta.pl $RPM_BUILD_ROOT%{_prefix}/lib/opa

install -d $RPM_BUILD_ROOT/%{_sysconfdir}/opa
install -m 0644 version_delta $RPM_BUILD_ROOT%{_sysconfdir}/opa/version_delta

%clean

%post
%if 0%{?suse_version} >= 1315
if [[ $1 = 1 ]]; then
	if [[ -e %{ALLOW_MODULES} ]]; then
		cp -f %{ALLOW_MODULES}  %{ALLOW_MODULES_BACKUP}
		sed -i 's/^allow_unsupported_modules 0/allow_unsupported_modules 1/' %{ALLOW_MODULES}
	fi
fi
%endif

%if 0%{?rhel} && 0%{?rhel} < 7
if [[ $1 = 1 ]]; then
	/sbin/chkconfig --add opa
fi
%else
if [ $1 = 1 ]; then
    if [ $(command -v systemctl) ]; then
	systemctl enable opa
    fi
fi
%endif

# Post-install configuration -- environment variables set by INSTALL script
# Only 0 or 1 value supported; will use default config if set to anything else
# Default configuration is performed by else statement for each condition
if [ “$OPA_INSTALL_CALLER” != “0” ]; then
 if [ “$OPA_UDEV_RULES” == “0” ]; then
   /sbin/opasystemconfig --disable Udev_Access
 else /sbin/opasystemconfig --enable Udev_Access
 fi
 if [ “$OPA_LIMITS_CONF” == “0” ]; then
   /sbin/opasystemconfig --disable Memory_Limit
 else /sbin/opasystemconfig --enable Memory_Limit
 fi
 grep -q '^ARPTABLE_TUNING=' /etc/rdma/rdma.conf || echo 'ARPTABLE_TUNING=' >> /etc/rdma/rdma.conf
 if [ “$OPA_ARPTABLE_TUNING” == “0” ]; then
   /sbin/opaautostartconfig  --disable ARPTABLE_TUNE
 else /sbin/opaautostartconfig --enable ARPTABLE_TUNE
 fi
 if [ “$OPA_SRP_LOAD” == “1” ]; then
   /sbin/opaautostartconfig  --enable SRP
 else /sbin/opaautostartconfig --disable SRP
 fi
 if [ “$OPA_SRPT_LOAD” == “1” ]; then
   /sbin/opaautostartconfig  --enable SRPT
 else /sbin/opaautostartconfig --disable SRPT
 fi
 if [ “$OPA_IRQBALANCE” == “0” ]; then
   /sbin/opasystemconfig --disable Irq_Balance
 else /sbin/opasystemconfig --enable Irq_Balance
 fi
fi

%preun
%{_sbindir}/opa-arptbl-tuneup stop

%if 0%{?rhel} && 0%{?rhel} < 7
if [[ $1 = 0 ]]; then
	/sbin/chkconfig --del opa
fi
%else
if [ $1 = 0 ]; then
    if [ $(command -v systemctl) ]; then
	systemctl disable opa
    fi
fi
%endif

# Pre-uninstall configuration -- environment variables set by INSTALL script
# Only 0 or 1 value supported; will use default config if set to anything else
if [ “$OPA_INSTALL_CALLER” != “0” ]; then
 if [ “$OPA_UDEV_RULES” != “1” ]; then
   /sbin/opasystemconfig --disable Udev_Access
 fi
 if [ “$OPA_LIMITS_CONF” != “1” ]; then
   /sbin/opasystemconfig --disable Memory_Limit
 fi
 if [ “$OPA_ARPTABLE_TUNING” != “1” ]; then
   /sbin/opaautostartconfig  --disable ARPTABLE_TUNE
 fi
 sed -i -- '/^ARPTABLE_TUNING=[^ ]*/ d' /etc/rdma/rdma.conf
 if [ “$OPA_SRP_LOAD” != “1” ]; then
   /sbin/opaautostartconfig --disable SRP
 fi
 if [ “$OPA_SRPT_LOAD” != “1” ]; then
   /sbin/opaautostartconfig --disable SRPT
 fi
 if [ “$OPA_IRQBALANCE” != “1” ]; then
   /sbin/opasystemconfig --disable Irq_Balance
 fi
fi

%postun
%if 0%{?suse_version} >= 1315
if [[ $1 = 0 ]]; then
	if [[ -e %{ALLOW_MODULES_BACKUP} ]]; then
		mv -f %{ALLOW_MODULES_BACKUP} %{ALLOW_MODULES}
	fi
fi
%endif

%files
%defattr(-,root,root,-)
#%config(noreplace) /etc/opa/opa.conf
%{_sbindir}/opa-arptbl-tuneup
%{_sbindir}/opa-init-kernel
%{_sysconfdir}/sysconfig/opa/limits.conf
%{_sysconfdir}/sysconfig/opa/udev.permissions
%{_sysconfdir}/sysconfig/opa/udev.rules
/sbin/opaautostartconfig
/sbin/opasystemconfig
%{_prefix}/lib/opa/.comp_ofed_delta.pl
%{_sysconfdir}/opa/version_delta
%if 0%{?rhel} && 0%{?rhel} < 7
%{_sysconfdir}/init.d/opa
%else
%{_unitdir}/opa.service
%endif
%{_mandir}/man1/opa-arptbl-tuneup.1*
%{_mandir}/man1/opa-init-kernel.1*
%{_mandir}/man1/opaautostartconfig.1*
