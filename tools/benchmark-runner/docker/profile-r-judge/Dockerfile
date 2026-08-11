FROM python@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36

RUN apt-get update \
    && apt-get install --yes --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.lock /tmp/profile-r-judge-requirements.lock
RUN python -m pip install \
      --disable-pip-version-check \
      --no-cache-dir \
      --requirement /tmp/profile-r-judge-requirements.lock \
    && rm /tmp/profile-r-judge-requirements.lock \
    && python -m pytest --version
