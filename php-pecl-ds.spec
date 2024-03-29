#
# Conditional build:
%bcond_without	tests		# build without tests

%define		php_name	php%{?php_suffix}
%define		modname	ds
Summary:	Data Structures
Name:		%{php_name}-pecl-%{modname}
Version:	1.4.0
Release:	1
License:	MIT
Group:		Development/Languages/PHP
Source0:	https://pecl.php.net/get/%{modname}-%{version}.tgz
# Source0-md5:	d7e64fbb53b567908d63155ec2a8f548
URL:		https://pecl.php.net/package/ds/
BuildRequires:	%{php_name}-cli
BuildRequires:	%{php_name}-devel >= 4:7.0
BuildRequires:	%{php_name}-json
BuildRequires:	%{php_name}-pcre
BuildRequires:	%{php_name}-spl
BuildRequires:	rpmbuild(macros) >= 1.666
%if %{with tests}
%endif
%{?requires_php_extension}
Requires:	%{php_name}-json
Requires:	%{php_name}-spl
Provides:	php(%{modname}) = %{version}
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
Data Structures for PHP 7.

%prep
%setup -qc
mv %{modname}-%{version}/* .

cat <<'EOF' > run-tests.sh
#!/bin/sh
export NO_INTERACTION=1 REPORT_EXIT_STATUS=1 MALLOC_CHECK_=2
exec %{__make} test \
	PHP_EXECUTABLE=%{__php} \
	PHP_TEST_SHARED_SYSTEM_EXTENSIONS="\
%if "%php_major_version.%php_minor_version" < "8.0"
	json \
%endif
%if "%php_major_version.%php_minor_version" < "7.4"
	pcre spl \
%endif
	" \
	RUN_TESTS_SETTINGS="-q $*"
EOF
chmod +x run-tests.sh

%build
phpize
%configure
%{__make}

# simple module load test
%{__php} -n -q -d display_errors=off \
	-d extension_dir=modules \
%if "%php_major_version.%php_minor_version" < "7.4"
	-d extension=%{php_extensiondir}/pcre.so \
	-d extension=%{php_extensiondir}/spl.so \
%endif
%if "%php_major_version.%php_minor_version" < "8.0"
	-d extension=%{php_extensiondir}/json.so \
%endif
	-d extension=%{modname}.so \
	-m > modules.log
grep %{modname} modules.log

%if %{with tests}
./run-tests.sh --show-diff
%endif

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT%{php_sysconfdir}/conf.d
install -d $RPM_BUILD_ROOT{%{php_sysconfdir}/conf.d,%{php_extensiondir}}

%{__make} install \
	EXTENSION_DIR=%{php_extensiondir} \
	INSTALL_ROOT=$RPM_BUILD_ROOT

install -d $RPM_BUILD_ROOT%{php_sysconfdir}/conf.d
%if "%php_major_version.%php_minor_version" >= "7.4"
# order after ext-json
cat <<'EOF' > $RPM_BUILD_ROOT%{php_sysconfdir}/conf.d/01_%{modname}.ini
%else
cat <<'EOF' > $RPM_BUILD_ROOT%{php_sysconfdir}/conf.d/json_%{modname}.ini
%endif
; Enable %{modname} extension module
extension=%{modname}.so
EOF

%clean
rm -rf $RPM_BUILD_ROOT

%post
%php_webserver_restart

%postun
if [ "$1" = 0 ]; then
	%php_webserver_restart
fi

%files
%defattr(644,root,root,755)
%doc LICENSE
%config(noreplace) %verify(not md5 mtime size) %{php_sysconfdir}/conf.d/*%{modname}.ini
%attr(755,root,root) %{php_extensiondir}/%{modname}.so
