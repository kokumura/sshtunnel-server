# SSHTunnel Server

SSH Tunnel as standalone server application

## Getting Started

### Prerequisites

- Python3.6.1 or higher
- Python packages refered in requirements.txt

### Installing

```
git clone {url to this repository}
```

```
pip install -r requirements.txt
```

### Configure

see [conf/sample.yml](conf/sample.yml)

Currently, only local forwarding is supported.

### Run server

```
python tunnel.py CONFIG_FILE [CONFIG_FILE ...]
```

To shutdown, press `Ctrl+C`.
