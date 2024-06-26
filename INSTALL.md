# Install Milvus from Source Code

<!-- TOC -->

-   [Build from source](#build-from-source)

    - [Requirements](#requirements)

    - [Compilation](#compilation)

    - [Launch Milvus server](#launch-milvus-server)

-   [Compile Milvus on Docker](#compile-milvus-on-docker)  

    - [Step 1 Pull Milvus Docker images](#step-1-pull-milvus-docker-images)

    - [Step 2 Start the Docker container](#step-2-start-the-docker-container)

    - [Step 3 Download Milvus source code](#step-3-download-milvus-source-code)

    - [Step 4 Compile Milvus in the container](#step-4-compile-milvus-in-the-container)

-   [Troubleshooting](#troubleshooting)

    - [Error message: `protocol https not supported or disabled in libcurl`](#error-message-protocol-https-not-supported-or-disabled-in-libcurl)

    - [Error message: `internal compiler error`](#error-message-internal-compiler-error)

    - [Error message: `error while loading shared libraries: libmysqlpp.so.3`](#error-message-error-while-loading-shared-libraries-libmysqlppso3)

    - [CMake version is not supported](#cmake-version-is-not-supported)

<!-- /TOC -->

## Build from source

### Requirements

-   Operating system

  - Ubuntu 18.04 or higher

  - CentOS 7

    > Note: If your Linux operating system does not meet the requirements, we recommend that you pull a Docker image of [Ubuntu 18.04](https://docs.docker.com/install/linux/docker-ce/ubuntu/) or [CentOS 7](https://docs.docker.com/install/linux/docker-ce/centos/) as your compilation environment.
  
-   GCC 7.0 or higher to support C++ 17

-   CMake 3.14 or higher

-   Git

For GPU-enabled version, you will also need:

-   CUDA 10.x (10.0, 10.1, 10.2)

-   NVIDIA driver 418 or higher

### Compilation

#### Step 1 Download Milvus source code and specify version 

Download Milvus source code, change directory and specify version (for example, 1.1):

```shell
$ git clone https://github.com/milvus-io/milvus
$ cd ./milvus/core
$ git checkout 1.1
```

#### Step 2 Install dependencies

##### Install in Ubuntu

```shell
$ ./ubuntu_build_deps.sh
```

##### Install in CentOS

```shell
$ ./centos7_build_deps.sh
```

#### Step 3 Build Milvus source code

If you want to use CPU-only:

run `build.sh`:

```shell
$ ./build.sh -t Release
```

If you want to use GPU-enabled:

1. Add cuda library path to `LD_LIBRARY_PATH`:

```shell
$ export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
```

2. Add cuda binary path to `PATH`:

```shell
$ export PATH=/usr/local/cuda/bin:$PATH
```

3. Add a `-g` parameter to run `build.sh`:

```shell
$ ./build.sh -g -t Release
```

When the build completes, everything that you need to run Milvus is under `[Milvus root path]/core/milvus`.

### Launch Milvus server

```shell
$ cd [Milvus root path]/core/milvus
```

Add `lib/` directory to `LD_LIBRARY_PATH`

```shell
$ export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:[Milvus root path]/core/milvus/lib
```

Then start Milvus server:

```shell
$ cd scripts
$ ./start_server.sh
```

To stop Milvus server, run:

```shell
$ ./stop_server.sh
```

## Compile Milvus on Docker

With the following Docker images, you should be able to compile Milvus on any Linux platform that runs Docker. To build a GPU supported Milvus, you need to install [NVIDIA Docker](https://github.com/NVIDIA/nvidia-docker/) first.

### Step 1 Pull Milvus Docker images

#### Ubuntu 18.04

Pull CPU-only image:

```shell
$ docker pull milvusdb/milvus-cpu-build-env:v0.7.0-ubuntu18.04
```

Pull GPU-enabled image:

```shell
$ docker pull milvusdb/milvus-gpu-build-env:v0.7.0-ubuntu18.04
```

#### CentOS 7

Pull CPU-only image:

```shell
$ docker pull milvusdb/milvus-cpu-build-env:v0.7.0-centos7
```

Pull GPU-enabled image:

```shell
$ docker pull milvusdb/milvus-gpu-build-env:v0.7.0-centos7
```

### Step 2 Start the Docker container

Start a CPU-only container:

```shell
$ docker run -it -p 19530:19530 -d <milvus_cpu_docker_image>
```

Start a GPU container:

- For nvidia docker 2:

```shell
$ docker run --runtime=nvidia -it -p 19530:19530 -d <milvus_gpu_docker_image>
```

- For nvidia container toolkit:

```shell
docker run --gpus all -it -p 19530:19530 -d <milvus_gpu_docker_image>
```

To enter the container:

```shell
$ docker exec -it [container_id] bash
```

### Step 3 Download Milvus source code

Download Milvus source code:

```shell
$ git clone https://github.com/milvus-io/milvus
```

To enter its core directory:

```shell
$ cd ./milvus/core
```

Specify version (for example, 1.1):

```shell
$ git checkout 1.1
```

### Step 4 Compile Milvus in the container

If you are using a CPU-only image:

1. run `build.sh`:

```shell
$ ./build.sh -t Release
```

2. Start Milvus server：

```shell
$ ./start_server.sh
```

If you are using a GPU-enabled image:

1. Add cuda library path to `LD_LIBRARY_PATH`:

```shell
$ export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
```

2. Add cuda binary path to `PATH`:

```shell
$ export PATH=/usr/local/cuda/bin:$PATH
```

3. Add a `-g` parameter to run `build.sh`:

```shell
$ ./build.sh -g -t Release
```

4. Start Milvus server：

```shell
$ ./start_server.sh
```

## Troubleshooting

### Error message: `protocol https not supported or disabled in libcurl`

Follow the steps below to solve this problem:

1.  Make sure you have `libcurl4-openssl-dev` installed in your system.
2.  Try reinstalling the latest CMake from source with `--system-curl` option:

   ```shell
   $ ./bootstrap --system-curl
   $ make
   $ sudo make install
   ```

   If the `--system-curl` command doesn't work, you can also reinstall CMake in **Ubuntu Software** on your local computer.

### Error message: `internal compiler error`

Try increasing the memory allocated to Docker. If this doesn't work, you can reduce the number of threads in CMake build in `[Milvus root path]/core/build.sh`.

```shell
make -j 8 install || exit 1 # The default number of threads is 8.
```

Note: You might also need to configure CMake build for faiss in `[Milvus root path]/core/src/index/thirdparty/faiss`.

### Error message: `error while loading shared libraries: libmysqlpp.so.3`

Follow the steps below to solve this problem:

1.  Check whether `libmysqlpp.so.3` is correctly installed.
2.  If `libmysqlpp.so.3` is installed, check whether it is added to `LD_LIBRARY_PATH`.

### CMake version is not supported

Follow the steps below to install a supported version of CMake:

1.  Remove the unsupported version of CMake.
2.  Get CMake 3.14 or higher. Here we get CMake 3.14.

    ```shell
    $ wget https://cmake.org/files/v3.14/cmake-3.14.7-Linux-x86_64.tar.gz
    ```

3.  Extract the file and install CMake.

    ```shell
    $ tar zxvf cmake-3.14.7-Linux-x86_64.tar.gz
    $ mv cmake-3.14.7-Linux-x86_64 /opt/cmake-3.14.7
    $ ln -sf /opt/cmake-3.14.7/bin/* /usr/bin/
    ```
