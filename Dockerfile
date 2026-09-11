FROM mcr.microsoft.com/dotnet/sdk:6.0

ENV FLIT_ROOT_INSTALL=1
ENV PATH="$PATH:/root/.dotnet/tools"
ENV PATH="$PATH:/root/.local/bin"

WORKDIR /toolbelt

RUN mkdir "/root/.config"

COPY . /toolbelt

# Debian 11(bullseye) EOL 대응. 베이스 `dotnet/sdk:6.0` 이 bullseye 기반인데 두 단계로 깨졌다.
#   1) bullseye-security 의 Release 파일 만료(2026-09-07 경) → apt 가 거부 → update 가 exit 100
#   2) deb.debian.org 에서 bullseye 패키지 풀이 제거됨 → .deb 받을 때 404
#        E: Failed to fetch .../bullseye-security/pool/updates/main/x/xz-utils/... 404 Not Found
#   1)만 고치면(만료 검사 끄기) 2)에서 다시 죽는다. 실제로 그렇게 재실패했다.
#
#   그래서 소스를 Debian 공식 영구 아카이브로 돌린다. bullseye main 에 이 Dockerfile 이
#   필요로 하는 9개 패키지가 전부 있음을 확인했다. security/updates 는 아카이브에 없고
#   (모든 경로 404) 어차피 동결된 suite 라 뺀다. 아카이브 Release 도 만료 상태이므로
#   Check-Valid-Until 은 계속 꺼둔다.
#
#   런타임은 마지막 성공 빌드(NineChronicles release/480.0.1, 2026-08-31)와 동일하게
#   유지된다 — Java 11 / Python 3.9 / .NET 6. 이 이미지는 CodeSignTool 로 런처 바이너리에
#   서명하는 경로라 런타임 교체엔 검증이 필요해서다.
#
#   근본 해결은 EOL 베이스 교체다. `6.0-bookworm-slim` 이 존재하지만 openjdk-11 이 없어
#   17 로 가야 하고, Python 3.9→3.11 이 되면서 `PyYAML ==6.0` 정확 핀이 3.11 에서
#   빌드가 깨진다(6.0.1 에서 수정). 베이스·JDK·의존성을 함께 올리는 작업이라 별건으로 분리.
RUN printf 'deb http://archive.debian.org/debian bullseye main\n' > /etc/apt/sources.list && \
    apt-get -o Acquire::Check-Valid-Until=false update && \
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
