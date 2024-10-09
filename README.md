# TV Filter

**TV Filter** is a [Python](https://www.python.org) package that retrieves a list of IP addresses from a file stored in an [S3](https://aws.amazon.com/s3/) bucket using the [Boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) library, filters them, and converts them into commands to be announced to [ExaBGP](https://github.com/Exa-Networks/exabgp) for BGP route advertisement in order to be blackholed by routers.

**TV Filter** operates within a [Docker](https://www.docker.com) container, making it easy to deploy and manage.

## Information

> **⚠️ Warning ⚠️**
> 
> **TV Filter** has been tested with **Python 3.11**. However, it is not compatible with **Python 3.12** and above for now due to an issue in **ExaBGP** ([#1177](https://github.com/Exa-Networks/exabgp/issues/1177)). This issue has been solved and merged into version **4.2.22** of **ExaBGP**, which has not yet been released.

## Prerequisites

Before you begin, ensure you have the following:

- A server environment. While installation is possible on physical servers, we recommend using a virtual machine for better manageability and flexibility.

- A modern Linux distribution. We recommend [Debian 12](https://www.debian.org/releases/bullseye/) or [Rocky Linux 9](https://rockylinux.org).

- **Docker**: Follow the official Docker installation guide for your Linux distribution.
   
   - [Docker Installation Guide for Debian](https://docs.docker.com/engine/install/debian/)
   - [Docker Installation Guide for Rocky Linux](https://docs.rockylinux.org/gemstones/containers/docker/)

- Minimum hardware requirements:
    - CPU: 2 vCPU
    - RAM: 4 GB
    - Disk space: 20 GB

## Installation

1. **Clone the Repository**:

    ```bash
    git clone https://github.com/zoreole-services/tvfilter.git
    ```

2. **Build Docker Image**:

    The build process for the Docker image can be specified in the `docker-compose.yaml` file.

    ```yaml
    services:
      tvfilter:
        build: ./build
        image: tvfilter:latest
        ...
    ```

    Then you can simply run the following command to build the image:

    ```bash
    docker compose build tvfilter
    ```

    Alternatively building the Docker image for **TV Filter** can be done manually using the following command:

    ```bash
    docker buildx build --no-cache --tag tvfilter:latest .
    ```
    > ℹ Here, `.` refers to the directory where the `Dockerfile` is located.

## Configuration

1. **Docker Compose Configuration**:

    We recommend using [Docker Compose](https://docs.docker.com/compose/) for managing the TV Filter service. An example configuration is available in `docker-compose.yaml.example`. You can copy this file to `docker-compose.yaml` and modify it to adjust settings such as ports, volumes, or environment variables.

    To configure TV Filter, you'll need to add the following environment variables:

    | Variable Name          | Default Value    | Required | Description                                      |
    |------------------------|------------------|----------|--------------------------------------------------|
    | `AWS_ACCESS_KEY_ID`    | -                | Yes      | Your AWS access key ID for accessing the S3 bucket. |
    | `AWS_SECRET_ACCESS_KEY`| -                | Yes      | Your AWS secret access key for accessing the S3 bucket. |
    | `AWS_REGION`           | `eu-west-1`      | No       | The AWS region where the S3 bucket is located.   |
    | `S3_BUCKET_NAME`       | -                | Yes      | The name of the S3 bucket where the IP list is stored. |
    | `S3_OBJECT_KEY_PATH`   | -                | Yes      | The path within the S3 bucket where IP list is located. |
    | `S3_OBJECT_FILE_NAME`  | -                | Yes      | The name of the file containing IP addresses to blackhole. |
    | `MY_SUPERNETS`         | -                | Yes      | Your public network's supernets. |
    | `MAX_PREFIXES`         | `2000`           | No       | Maximum number of routes to accept.        |
    | `BLACKHOLE_COMMUNITY`  | `65535:666`      | No       | BGP community value for blackhole routes.        |
    | `POLLING_INTERVAL`     | `30`             | No       | Interval (in seconds) for polling changes from S3 bucket. |

    You can add these environment variables to the `environment` section of the `tvfilter` service in the `docker-compose.yaml` file.

    > ℹ If you are unsure about how to determine your public network's supernets, you can use tools like [bgpq3](https://github.com/snar/bgpq3) with the following command:

    For IPv4, use:

    ```bash
    bgpq3 -JH4 AS65000
    ```

    For IPv6, use:

    ```bash
    bgpq3 -JH6 AS65000
    ```

    Replace `AS65000` with your own [ASN](https://en.wikipedia.org/wiki/Autonomous_system_(Internet)).

2. **ExaBGP Configuration**:

    Additionally, you'll need to create an `exabgp.conf` file with your desired configuration. An example configuration file is provided in `exabgp.conf.example` for reference.

    To customize this configuration, make sure to modify the following settings in your `exabgp.conf`:

    - `router-id`: The IP address of the ExaBGP router.
    - `local-as`: The AS number of the ExaBGP router.
    - `peer-as`: Your own AS number.
    - `neighbor`: The IP address of your router.
    - `local-address`: The local IP address your peer will use to establish the BGP connection with ExaBGP.
    - `description` (optional): A description to identify your router.

    Also, make sure to modify the family settings based on what your peer supports. For instance, you can specify `ipv4 unicast` and `ipv6 unicast` if your peer supports both IPv4 and IPv6 unicast.

    Make sure to bind the `exabgp.conf` file to the container at `/etc/exabgp/exabgp.conf`. You can specify this in your `docker-compose.yaml` file under the `volumes` section for the `tvfilter` service like this:

    ```yaml
    services:
      tvfilter:
        ...
        volumes:
          - ./exabgp.conf:/etc/exabgp/exabgp.conf:ro
        ...
    ```

    For more advanced configurations and additional parameters, refer to the documentation of ExaBGP.

## Usage

Once the installation is complete and the configuration files are set up, you can use the following commands:

**Starting the Docker container**:

```bash
docker compose up -d
```

**Stopping the Docker container**:

```bash
docker compose down
```

**Rebuilding the Docker image**:

```bash
docker compose build tvfilter
docker compose down && docker compose up -d
```

## License

This project is licensed under the [GNU Affero General Public License v3.0](https://www.gnu.org/licenses/agpl-3.0.txt).

## Issue

If you encounter any issues or have questions, please [submit an issue](https://github.com/zoreole-services/tvfilter/issues) on the GitHub repository.
