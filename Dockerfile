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
#   3) archive.debian.org 의 main 만 쓰면 이번엔 버전이 어긋난다 — 베이스 이미지엔 security
#      업데이트가 반영된 런타임이 이미 깔려 있는데 main 에는 구버전 -dev 밖에 없다:
#        libexpat1-dev : Depends: libexpat1 (= 2.2.10-2+deb11u5) but 2.2.10-2+deb11u6 is to be installed
#      bullseye-security 는 archive.debian.org 에 아직 없다(경로 전부 404).
#
#   그래서 snapshot.debian.org 의 **풀 제거 이전 시점**을 고정해 쓴다. main 과 security 를
#   같은 타임스탬프로 묶어야 위 skew 가 없다. 타임스탬프 고정이라 빌드가 재현 가능해지는
#   부수 효과도 있다. 아카이브 Release 는 만료 상태이므로 Check-Valid-Until 은 꺼둔다.
#
#   런타임은 마지막 성공 빌드(NineChronicles release/480.0.1, 2026-08-31)와 동일하다 —
#   Java 11 / Python 3.9 / .NET 6. 이 이미지는 CodeSignTool 로 런처 바이너리에 서명하는
#   경로라 런타임을 바꾸지 않는 쪽을 골랐다.
#   amd64 로컬 빌드로 검증함: openjdk 11.0.32+9-2~deb11u1, Python 3.9.2.
#
#   근본 해결은 EOL 베이스 교체다. `6.0-bookworm-slim` 이 존재하지만 openjdk-11 이 없어
#   17 로 가야 하고, Python 3.9→3.11 이 되면서 `PyYAML ==6.0` 정확 핀이 3.11 에서
#   빌드가 깨진다(6.0.1 에서 수정). 베이스·JDK·의존성을 함께 올리는 작업이라 별건으로 분리.
ARG DEBIAN_SNAPSHOT=20260815T000000Z
RUN printf '%s\n' \
      "deb http://snapshot.debian.org/archive/debian/${DEBIAN_SNAPSHOT}/ bullseye main" \
      "deb http://snapshot.debian.org/archive/debian-security/${DEBIAN_SNAPSHOT}/ bullseye-security main" \
      "deb http://snapshot.debian.org/archive/debian/${DEBIAN_SNAPSHOT}/ bullseye-updates main" \
      > /etc/apt/sources.list && \
#   4) 베이스 이미지의 CA 번들이 낡아 ssl.com 검증에 실패한다(아래 CodeSignTool 단계):
#        curl: (60) SSL certificate problem: self signed certificate in certificate chain
#      ssl.com 이 체인을 교체했는데 동결된 bullseye 베이스가 새 루트를 모른다.
#      apt 를 전혀 건드리지 않은 순정 `dotnet/sdk:6.0` 에서도 재현되므로 이 레이어와
#      무관한 외부 변화다(호스트에서는 같은 URL 이 200). 그래서 ca-certificates 를
#      명시적으로 올린다 — 스냅샷의 20250419~deb12u1~deb11u1 이면 200 으로 통과한다.
    apt-get -o Acquire::Check-Valid-Until=false update && \
    apt-get install -y \
    ca-certificates \
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
