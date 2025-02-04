FROM mambaorg/micromamba:2.0.4

WORKDIR /app
COPY . .
COPY s1ifr /app/
COPY pyproject.toml /app/
COPY README.md /app/
CMD ls -R /app && sleep 5
# Set environment variables
ENV MAMBA_ROOT_PREFIX=/opt/app-s1ifr/ \
    PATH=/opt/app-s1ifr/micromamba-env/python/bin:$PATH

# Create the target directory with correct permissions
USER root
RUN mkdir -p /opt/app-s1ifr/
RUN chmod 777 -R /opt/app-s1ifr


# Create the Python environment
#RUN micromamba create --yes -p /opt/app-s1ifr/micromamba-env python=3.12
RUN micromamba clean --all --yes
ARG MAMBA_DOCKERFILE_ACTIVATE=1  # (otherwise python will not be found)
COPY --chown=$MAMBA_USER:$MAMBA_USER env.yaml /tmp/env.yaml
#RUN micromamba install --yes --file /tmp/env.yaml
RUN micromamba env create --file /tmp/env.yaml
RUN micromamba clean --all --yes


#RUN micromamba shell init --shell  --root-prefix=~/.local/share/mamba
#RUN micromamba shell reinit --shell
#RUN micromamba activate /opt/app-s1ifr/micromamba-env
#RUN pip install .
RUN micromamba run -n envs1ifr pip install .
RUN micromamba run -n envs1ifr python -c "import s1ifr;print(s1ifr.__version__)"
# Set environment variables for non-interactive apt installations
ENV DEBIAN_FRONTEND=noninteractive

# Install unzip and other tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    unzip \
    bash \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
# Default command
CMD ["python", "--version"]
