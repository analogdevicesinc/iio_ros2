#!/usr/bin/env bash

LIBIIO_VERSION=${LIBIIO_VERSION:-libiio-v0}
STAGING_DIR=${STAGING_DIR:-$HOME/src}

# Ensure that the STAING_DIR exists
if [ ! -d "$STAGING_DIR" ]; then
    echo "Creating staging directory at: $STAGING_DIR"
    mkdir -p "$STAGING_DIR"
fi

install_packages() {
    echo "Installing packages"
    sudo apt-get update -y
    apt_packages=(
        # Libiio dependencies
        ## Basic system setup
        build-essential
        ## Install Prerequisites
        bison cmake flex git libcdk5-dev libxml2-dev libzstd-dev
        ## Backend deps
        libaio-dev libavahi-client-dev libserialport-dev libusb-1.0-0-dev
    )
    sudo apt-get install --no-install-recommends -y "${apt_packages[@]}"
}

install_libiio() {
    echo "Building libiio v${LIBIIO_VERSION}"
    pushd "${STAGING_DIR}"
    git clone \
        --depth 1 \
        --branch "${LIBIIO_VERSION}" \
        https://github.com/analogdevicesinc/libiio.git \
        libiio_"${LIBIIO_VERSION}"
    cd libiio_"${LIBIIO_VERSION}"
    mkdir build_"${LIBIIO_VERSION}" && cd build_"${LIBIIO_VERSION}"
    cmake .. \
        -Werror=dev \
        -DCOMPILE_WARNING_AS_ERROR=ON
    sudo cmake --build . --target install
    popd
}

install_all() {
    install_packages
    install_libiio
}

install_all
