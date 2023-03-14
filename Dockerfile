FROM mcr.microsoft.com/dotnet/sdk:6.0

ENV FLIT_ROOT_INSTALL=1
ENV PATH="$PATH:/root/.dotnet/tools"
ENV PATH="$PATH:/root/.local/bin"

WORKDIR /toolbelt

RUN mkdir "/root/.config"

COPY . /toolbelt

RUN apt-get update && \
    apt-get install -y \
    curl \
    wget \
    gcc \
    gnupg \
    unzip \
    openjdk-11-jdk \
    python3-dev \
    python3-pip \
    python3-venv && \
	rm -rf /var/lib/apt/lists/*

RUN curl https://www.ssl.com/download/codesigntool-for-linux-and-macos/ -o /tmp/CodeSignTool.zip && \
    unzip "/tmp/CodeSignTool.zip" -d "/tmp" && \
    rm "/tmp/CodeSignTool.zip" && \
    mkdir /codesign && \
    mv "/tmp/CodeSignTool-v1.2.7" "/codesign" && \
    chmod +x "/codesign/CodeSignTool.sh" && ln -s "/codesign/CodeSignTool.sh" "/usr/bin/codesign"

ENV CODE_SIGN_TOOL_PATH=/codesign

RUN python3 -m venv .venv && \
    . .venv/bin/activate && \
    python3 -m pip install --upgrade -r /toolbelt/requirements.txt --no-cache-dir && \
    flit install --extras all

RUN dotnet tool install -g Libplanet.Tools

ENTRYPOINT ["bash", "/toolbelt/entrypoint.sh"]
