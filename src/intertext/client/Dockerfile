# From official Debian 12 Bookworm image pinned by its name bookworm-slim
FROM debian:bookworm-slim

# Install dependencies
## deb packages
RUN apt-get update && \
    apt-get install -y \
        nodejs npm && \
    rm -rf /var/lib/apt/lists/* && \
    npm install --global yarn

WORKDIR /workdir
