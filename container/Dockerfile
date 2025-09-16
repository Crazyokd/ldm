FROM debian:latest

RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y --no-install-recommends build-essential patchelf ccache meson \
    iproute2 iputils-ping iputils-tracepath zstd tree wget git rsync file fd-find ripgrep neovim

RUN --mount=type=bind,target=/ref \
    tar -xf /ref/upx-4.2.4-amd64_linux.tar.xz -C /usr/bin/ --strip-components=1 upx-4.2.4-amd64_linux/upx && \
    tar -xf /ref/uv-x86_64-unknown-linux-gnu.tar.gz -C /usr/bin --strip-components=1 uv-x86_64-unknown-linux-gnu/

# resolve encoding issue
ENV LC_ALL="C.UTF-8"
