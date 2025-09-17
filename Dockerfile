FROM mambaorg/micromamba:2.0.4

WORKDIR /app
COPY . .
COPY s1ifr /app/
COPY pyproject.toml /app/
COPY README.md /app/

# Set environment variables
ENV MAMBA_ROOT_PREFIX=/opt/app-s1ifr \
    PATH=/opt/app-s1ifr/micromamba-env/bin:$PATH \
    DEBIAN_FRONTEND=noninteractive

# Create the target directory with correct permissions
USER root
RUN mkdir -p /opt/app-s1ifr/ && chmod 777 -R /opt/app-s1ifr

# Clean Micromamba cache
RUN micromamba clean --all --yes

# Copy and install environment
ARG MAMBA_DOCKERFILE_ACTIVATE=1
COPY --chown=$MAMBA_USER:$MAMBA_USER env.yaml /tmp/env.yaml
RUN micromamba env create --file /tmp/env.yaml && micromamba clean --all --yes

# Set default Python environment
RUN ln -sf /opt/app-s1ifr/micromamba-env/bin/python /usr/bin/python

# Install dependencies inside the correct environment
RUN micromamba run -n envs1ifr pip install .
RUN micromamba run -n envs1ifr python -c "import s1ifr; print(s1ifr.__version__)"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    unzip \
    bash \
    && apt-get clean && rm -rf /var/lib/apt/lists/*


# Ensure shell uses the correct environment
SHELL ["/bin/bash", "-c"]
SHELL ["micromamba", "shell", "init", "--shell", "bash", "--root-prefix=~/.local/share/mamba"]
SHELL ["source", "~/.bashrc"]
SHELL ["micromamba", "activate", "/opt/app-s1ifr/envs/envs1ifr"]
SHELL ["micromamba", "run", "-p", "/opt/app-s1ifr/envs/envs1ifr", "/bin/bash", "-c"]
# Copy localconfig file
# COPY s1ifr/localconfig.yml /opt/app-s1ifr/envs/envs1ifr/lib/python3.12/site-packages/s1ifr/localconfig.yml
RUN if [ -f s1ifr/localconfig.yml ]; then \
      cp s1ifr/localconfig.yml /opt/app-s1ifr/envs/envs1ifr/lib/python3.12/site-packages/s1ifr/localconfig.yml; \
    fi
ENV PATH /opt/app-s1ifr/envs/envs1ifr/bin:$PATH
# another trick test to make sure the micromamba env will be set as default
#RUN echo "micromamba activate /opt/app-s1ifr/envs/envs1ifr" > ~/.bashrc


# Default command
CMD ["python", "--version"]
