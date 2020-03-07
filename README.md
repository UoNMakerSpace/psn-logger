# Phenotyping Sensor Network: Logger
PSN is a network of wireless battery-powered sensing nodes designed specifically for the phenotyping domain. This codebase contains the program that coordinates the network by receiving and responding to MQTT messages from sensor nodes, and logs the reported data from nodes in a MySQL database.

# Usage
- Create the database (see the Database section)
- Create the configuration file (see the Configuration section)
- Run `main.py` with Python

# Configuration
A file called `config.ini` is required in the root directory of the codebase. It must follow the following format:

- `[broker]`
- `address=` -- Address of the server hosting the MQTT process (e.g. `localhost`)
- `port=` -- Port number used by the above MQTT process (usually `1883`)
- `[database]`
- `address=` -- Address of the server hosting the MySQL database process (e.g. `localhost`)
- `username=` -- Username to access the database with
- `password=` -- Password of the above username
- `database=` -- Name of the database to use for storing the data

# Database
The following SQL code can be used to create the required database tables:

TODO

# Dependencies
- Paho MQTT
- PyMySQL
