#!/usr/bin/env/python3

import os
from os import path
import shlex, subprocess, sys, errno

Debug=True


##### Shared #####
class QueryError(Exception):
  def __init__(self,msg):
    self.msg = msg
 
def get_nth_token(token_list,n):
  if n < 0:
    return ""

  for t in token_list:
    if t.strip() == "":
      continue
    if n == 0:
      return t.strip()
    n -= 1

  return "" 

def run_shell(cmd_text):
  if Debug:
    print("CMD {}".format(cmd_text))
  cmd = shlex.split(cmd_text)
  return subprocess.run(cmd, stdout=subprocess.PIPE)




##### DOCKERFILE #####

def get_prologue(base_img="centos", img_version="8.3.2011", nec_version="2.3.1"):
  docker_prologue="""
  FROM  {}:{}

  # Proxy settings
  ARG             host_proxy
  ENV             http_proxy=http://$host_proxy
  ENV             https_proxy=http://$host_proxy
  ENV             ftp_proxy=ftp://$host_proxy
  ENV             no_proxy=localhost,127.0.0.1
  
  # Basic build environment
  MAINTAINER      smoll
  ADD             dnf.conf /etc/dnf
  ADD             CentOS-Base.repo /etc/yum.repos.d
  ADD             CentOS-Extras.repo /etc/yum.repos.d
  ADD             CentOS-AppStream.repo /etc/yum.repos.d
  ADD             https://www.hpc.nec/repos/TSUBASA-soft-release-{}.noarch.rpm /tmp
  ADD             TSUBASA-repo.repo /tmp
  ADD             sxaurora.repo /tmp
  ARG             RELEASE_RPM=/tmp/TSUBASA-soft-release-*.noarch.rpm
  
  
  # Install GPG keys etc...
  RUN             yum -y install $RELEASE_RPM ; \
                  cp /tmp/*.repo /etc/yum.repos.d ; \
                  rm /tmp/*.repo /tmp/*.rpm 
  
  # Install host development packages
  RUN             yum -y install \
                      'dnf-command(versionlock)' \
                      binutils gcc-toolset-10 gcc-toolset-10-libstdc++-devel \
                      python39 python39-devel python39-pip \
                      perl-Data-Dumper perl-Digest-MD5 \
                      bison cmake elfutils-libelf-devel git glibc \
                      libarchive libgcc libstdc++ libxml2 ncurses-devel \
                      make unzip vim wget ; \
                  yum clean all ; rm -rf /var/cache/yum/* ; \
                  ln -s /usr/lib64/libstdc++.so.6 /usr/lib64/libstdc++.so
  
  # Auto-generated part (pinned RPM versions)
  """

  return docker_prologue.format(base_img, img_version, nec_version, nec_version)


pinned_rpms=["aurlic-lib", "binutils-ve", "glibc-ve", "glibc-ve-devel", "kheaders-ve", "veoffload-aveo-devel", "veoffload-aveorun-devel", "veos-devel", "veosinfo-devel", "veos-headers", "veos-libvepseudo-headers"]

docker_epilogue="""
RUN                yum clean all ; rm -rf /var/cache/yum/*
"""

def get_rpm_version(rpm):
  cmd = "yum list -C {}".format(rpm)
  lines = run_shell(cmd).stdout.decode('utf-8')
  split_lines = lines.split('\n')

  hit_list_header=False
  for line in lines.split('\n'):
    if line.strip().startswith("Installed Packages"):
      hit_list_header=True
    if not hit_list_header:
      continue
    if not line.strip().startswith(rpm):
      continue

    # PackageName       RPMVersionString   .. Junk
    parts = line.split(' ')
    version_txt = get_nth_token(parts, 1)
    if version_txt == "":
      return QueryError("Could not parse version for package: {}".format(rpm))

    return version_txt

def query_package_versions(rpms):
  res=dict()
  for rpm in rpms:
    version = get_rpm_version(rpm)
    res[rpm] = version
  return res

def get_version_number(version):
  parts = version.split("-")
  return parts[0]
    
def get_fixed_install_command(rpm, version_number):
  return "yum -y install {}-{} ; yum versionlock add {} ;".format(rpm, version_number, rpm)

def build_dockerfile(out, versions, base_img, img_version, nec_version):
  out.write(get_prologue(base_img, img_version, nec_version))
 
  # Fix and install package versions
  install_string="RUN "
  has_pred=False
  for rpm,version in versions.items():
    print(" {}   {}".format(rpm,version))
    if has_pred:
      install_string += " \\\n"
    version_number = get_version_number(version)
    install_string += get_fixed_install_command(rpm, version_number)
    has_pred=True

  out.write(install_string)
  out.write(docker_epilogue)



##### Repo file #####
repo_template="""
[veos-rhel{}]
name=Aurora VEOS RHEL specific
baseurl=https://sx-aurora.com/repos/veos/RHEL{}
gpgcheck=1
enabled=1
"""

def build_repofile(repo_out, centos_img_version):
  ver_parts = centos_img_version.split(".")[0:2]
  name = "".join(ver_parts)
  dot_name=".".join(ver_parts)
  repo_out.write(repo_template.format(name, dot_name))
  

##### Context Building #####

def build_pinned_context(versions, base_img, img_version, nec_version):
  with open("context/Dockerfile", 'w') as docker_out:
    build_dockerfile(docker_out, versions, base_img, img_version, nec_version)
  with open("context/sxaurora.repo", 'w') as repo_out:
    build_repofile(repo_out, img_version)


versions = query_package_versions(pinned_rpms)
base_img="centos"
centos_img_version="8.3.2011"

# TODO: Infer nec-version
nec_version="2.3-1"

build_pinned_context(versions, base_img, centos_img_version, nec_version)
