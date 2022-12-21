FROM --platform=arm64 mcr.microsoft.com/dotnet/sdk:6.0

ENV FLIT_ROOT_INSTALL=1
ENV PATH="$PATH:/root/.dotnet/tools"

WORKDIR /action

RUN mkdir /root/.config

COPY . /action

RUN apt-get update && \
    apt-get install -y \
    curl \
    wget \
    gcc \
    gnupg \
    python3-dev \
    python3-pip && \
	rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install -r requirements-dev.txt && \
    flit install

RUN dotnet tool install -g Libplanet.Tools

ENTRYPOINT ["bash", "entrypoint.sh"]
