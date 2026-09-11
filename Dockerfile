FROM mcr.microsoft.com/dotnet/sdk:6.0

ENV FLIT_ROOT_INSTALL=1
ENV PATH="$PATH:/root/.dotnet/tools"
ENV PATH="$PATH:/root/.local/bin"

WORKDIR /toolbelt

RUN mkdir "/root/.config"

COPY . /toolbelt

# Debian 11(bullseye) 보안 지원이 끝나 bullseye-security 의 Release 파일이 만료됐다.
#   apt 는 만료된 Release 를 기본 거부하므로 `apt-get update` 가 exit 100 으로 죽고,
#   그 뒤 install 은 시작조차 못 한다. 2026-09-07 경 만료 → 이후 모든 빌드가 실패한다.
#   (증상: "E: Release file for .../bullseye-security/InRelease is expired")
#
#   suite 가 동결돼 더 받을 보안 업데이트가 없으므로, 만료 검사를 끄는 것이 실제로
#   놓치는 패치를 만들지 않는다. 근본 해결은 EOL 인 .NET 6/bullseye 베이스 교체인데,
#   bookworm 으로 가면 openjdk-11 이 없어 17 로 바뀌고 Python 도 3.9→3.11 이 된다.
#   이 이미지는 CodeSignTool 로 런처 바이너리에 서명하는 경로라 런타임 교체는
#   검증이 필요하다 → 별건으로 분리한다.
RUN apt-get -o Acquire::Check-Valid-Until=false update && \
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

RUN mkdir "/temp"

RUN curl https://www.ssl.com/download/codesigntool-for-linux-and-macos/ -o /temp/CodeSignTool.zip && \
    unzip "/temp/CodeSignTool.zip" -d "/temp" && \
    rm "/temp/CodeSignTool.zip" && \
    mv "/temp" "/codesign" && \
    chmod +x "/codesign/CodeSignTool.sh" && ln -s "/codesign/CodeSignTool.sh" "/usr/bin/codesign"

ENV ESIGNER_PATH=/codesign
ENV CODE_SIGN_TOOL_PATH=/codesign

RUN python3 -m venv .venv && \
    . .venv/bin/activate && \
    python3 -m pip install --upgrade -r /toolbelt/requirements.txt --no-cache-dir && \
    flit install --extras all

RUN dotnet tool install -g Libplanet.Tools

ENTRYPOINT ["bash", "/toolbelt/entrypoint.sh"]
