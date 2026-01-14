# This file is used to run the ssi-agent on a reproducible environment 
# eliminating system inconsistencies, simplify DX and testing.

# We are using the latest Ubuntu release image
FROM ubuntu:latest

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    systemd \
    systemd-sysv \
    python3 \
    python3-venv \
    python3-pip \
    python-is-python3 \
    curl \
    git \
    sudo \
    acl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Setup a working directory
WORKDIR /opt/ssi-agent

# Create a non-root admin user for development
RUN useradd -m -s /bin/bash admin \
    && usermod -aG sudo admin \
    && echo "admin ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# cleanup systemd services that might conflict with containerization
# (Standard practice for systemd inside containers to avoid mounting errors)
RUN cd /lib/systemd/system/sysinit.target.wants/ \
    && rm -f $(ls | grep -v systemd-tmpfiles-setup) \
    && rm -f /lib/systemd/system/multi-user.target.wants/* \
    && rm -f /etc/systemd/system/*.wants/* \
    && rm -f /lib/systemd/system/local-fs.target.wants/* \
    && rm -f /lib/systemd/system/sockets.target.wants/*udev* \
    && rm -f /lib/systemd/system/sockets.target.wants/*initctl* \
    && rm -f /lib/systemd/system/basic.target.wants/* \
    && rm -f /lib/systemd/system/anaconda.target.wants/*

# Configure root's bash to automatically switch to 'admin' for interactive sessions.
# This ensures 'podman exec -it ... bash' lands you as admin,
# while the container itself runs as root (PID 1) for systemd.
RUN echo 'if [[ $- == *i* ]]; then exec su admin; fi' >> /root/.bashrc

# Set the default command to start systemd
CMD ["/sbin/init"]