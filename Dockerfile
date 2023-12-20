# Start with a base image that has the necessary dependencies
FROM ubuntu:latest

# Install curl and other necessary tools
RUN apt-get update && apt-get install -y curl unzip \
    && rm -rf /var/lib/apt/lists/*

# Define the version of the gn binary from https://chrome-infra-packages.appspot.com/p/gn/gn/linux-amd64
ENV INSTANCE_ID="H5CaqrpIqpNrv4oKyJ2F1YUXzYtp8BMgaiJKaiYXT9EC"

# Download the gn binary zip file and extract it
RUN mkdir -p /usr/local/bin \
    && curl -L "https://chrome-infra-packages.appspot.com/dl/gn/gn/linux-amd64/+/${INSTANCE_ID}" -o gn.zip \
    && unzip gn.zip -d /usr/local/bin \
    && chmod +x /usr/local/bin/gn \
    && rm gn.zip

# Set the working directory
WORKDIR /work

ENTRYPOINT ["/usr/local/bin/gn", "format"]
