# Trixel Service Bridges

*Trixel Service Bridges (TSBs)* integrate multiple existing sensors from different resources into the trixel-based
sensor network.
Bridges spawn multiple *Trixel Service Clients (TCSs)* which can have different settings and configurations.
For each virtual measurement stations environmental observations are contributed to the sensor network.

## The synthetic bridge

The *synthetic bridge* is an exception as it does not strictly bridge from a different sensor network, but rather
creates virtual clients which contribute (randomly) generated sensors/measurements.
It's main purposes are testing and evaluation of privatizers within the TMS.
