# Trixel Service Bridges

*Trixel Service Bridges (TSBs)* integrate multiple existing sensors from different resources into the trixel-based
sensor network.
Bridges spawn multiple *Trixel Service Clients (TCSs)* which can have different settings and configurations.
Each virtual measurement station contributes environmental observations to the sensor network.

This repository currently only contains the synthetic bridge but provides the space and foundations for future bridge implementations.

## Running a bridge

Bridges can be run by invoking the corresponding module, which may or may not accept parameters, like this:

```cli
python -m trixelservicebridges.synthetic_bridge -c config/test_config.toml
```

The synthetic bridge requires a configuration file, the path of which can be configure with command line arguments.

## The synthetic bridge

The *synthetic bridge* is an exception as it does not strictly bridge from a different sensor network, but rather
creates virtual clients which contribute (randomly) generated sensors/measurements.
It's main purposes are testing and evaluation of privatizers within the TMS.

Simulation clients are generated based on the provided configuration file and their client-configurations are persisted in a pickle file for future use.
Thus, the same clients can be used repeatedly to test different TMS configurations.

The command line interface of the synthetic bridge requires a configuration `config_name.toml` file which describes how simulated clients behave.
Additionally, the following options are supported.

```cli
  -c CONFIG_FILE, --config_file CONFIG_FILE
                        Path which points the to the configuration file which should be used!
  -r, --reset           If set to true, an existing pickle file will be ignored.
  -d, --delete          Delete existing clients gracefully by deleting them from their TMSs.
```

A minimal configuration file may look like this:

```toml
target_client_count=5
log_level=5

[client_simulation_config]
client_class = "blank"
k=3

tls_host="tls.home.fleisch.dev"
retry_interval=1
polling_interval=10
```

Bridge configuration options:

* `log_level`, int: Logging level which is used by the bridge and simulated clients.
* `pickle_file_path`, Path: The path where the pickle file is stored which contains the configurations of all simulated clients. (Defaults to "config/multi.pkl")
* `target_client_count`, int: The number of client to simulate. If already present, the number of clients will be loaded from an existing pickle file. Missing clients will be generated according to the provided configuration file.
* `client_simulation_config`: Key which contains simulation client specific configuration options.

### `client_simulation_config`

General configuration options include:

* `client_class`, str: The client class which is used for simulated clients. One of `blank`, `coordinate_gradient`, `skewed_coordinate_gradient`, `diurnal_approximation`,`skewed_diurnal_approximation`. Each client type can have it's own configurations (see below).
* `tls_host`, str, required: Address of the TLS where clients gather further information.
* `tls_use_ssl`, bool: Determines if clients use https when communicating with the TLS. (Defaults to `True`)
* `tms_use_ssl`, bool: Determines if clients use https when communicating with the TMS. (Defaults to `True`)
* `tms_address_override`, str: Overrides the host address of the TMS (for all clients), which is provided by the TLS
* `retry_interval`, Time: The retry interval of the polling clients. (Default to 30 seconds)
* `max_retries`, int: Number of connection attempts which clients make before aborting.
* `polling_interval`, Time: Time Interval between value transmission. (Defaults to 60 seconds)

Specific simulation client configuration options are [documented here](src/trixelservicebridges/synthetic_bridge/config_schema.py).
Some of the options allow for the generation of random values. An example configuration-excerpt for this scenario looks like this:

```toml
[client_simulation_config.noise_generation]
type="normal_random"
mean=0
deviation=0.5
```

The additive noise is defined as a normally distributed random value, with a standard deviation of $0.5$ around $0$.
Further examples can be found [here: example_configuration/synthetic_bridge/](example_configuration/synthetic_bridge/).

Since the bridge is always "filling up missing simulation clients" if the `target_client_count` is increased, differently configured clients can be merged into a single pickle file.
This can be done by generating different client in succession (where the configuration file uses the same pickle path) with an increasing amount of clients.

## Development

[Pre-commit](https://pre-commit.com/) is used to enforce code-formatting, formatting tools are mentioned [here](.pre-commit-config.yaml).

The resulting python module can be built with pythons `build` module, which is also performed by the CI/CD pipeline.
