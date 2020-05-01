
# Phenotyping Sensor Network: Logger
PSN is a network of wireless battery-powered sensing nodes designed specifically for the phenotyping domain. This codebase contains the program that coordinates the network by receiving and responding to MQTT messages from sensor nodes, and logs the reported data from nodes in a MySQL database.

# Usage
- Install the dependencies (see the Dependencies section)
- Create the database (see the Database section)
- Ensure the MariaDB time zone is set to UTC
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
- `[alarms]`
- `email_server=` -- Address of the SMTP server to send alarm emails from (e.g. `smtp.gmail.com`)
- `email_address=` -- Email address to send alarm emails from
- `email_password=` -- Password of the above email address account
- `min_trigger_interval=` -- Do not send another email if an alarm triggers again within this number of minutes

# Database
The following SQL code should be used to create the required database tables:

    CREATE TABLE nodes (
        node_id INT NOT NULL AUTO_INCREMENT,
        mac_address CHAR(17) NOT NULL,
        PRIMARY KEY(node_id),
        UNIQUE KEY(mac_address)
    ) ENGINE = INNODB;
    
    CREATE TABLE sessions (
        session_id INT NOT NULL AUTO_INCREMENT,
        user_id VARCHAR(64) NOT NULL,
        name VARCHAR(128) NOT NULL,
        description VARCHAR(255) NULL DEFAULT NULL,
        PRIMARY KEY(session_id)
    ) ENGINE = INNODB;
    
    CREATE TABLE session_nodes (
        session_id INT NOT NULL,
        node_id INT NOT NULL,
        location VARCHAR(128) NOT NULL,
        start_time DATETIME NOT NULL,
        end_time DATETIME NULL DEFAULT NULL,
        `interval` TINYINT NOT NULL,
        batch_size TINYINT NOT NULL,
        FOREIGN KEY(session_id) REFERENCES sessions(session_id)
            ON UPDATE CASCADE ON DELETE CASCADE,
        FOREIGN KEY(node_id) REFERENCES nodes(node_id)
            ON UPDATE CASCADE ON DELETE CASCADE,
        PRIMARY KEY(session_id, node_id)
    ) ENGINE = INNODB;

    CREATE TABLE session_alarms (
        alarm_id INT NOT NULL AUTO_INCREMENT,
        session_id INT NOT NULL,
        node_id INT NOT NULL,
        parameter CHAR(4) NOT NULL,
        minimum DECIMAL(5,2) NOT NULL,
        maximum DECIMAL(5,2) NOT NULL,
        last_triggered DATETIME NULL DEFAULT NULL,
        FOREIGN KEY(session_id) REFERENCES sessions(session_id)
            ON UPDATE CASCADE ON DELETE CASCADE,
        FOREIGN KEY(node_id) REFERENCES nodes(node_id)
            ON UPDATE CASCADE ON DELETE CASCADE,
            PRIMARY KEY(alarm_id)
    ) ENGINE = INNODB;

    CREATE TABLE reports (
        report_id INT NOT NULL AUTO_INCREMENT,
        session_id INT NOT NULL,
        node_id INT NOT NULL,
        time DATETIME NOT NULL,
        airt DECIMAL(3,1) NULL DEFAULT NULL,
        relh DECIMAL(4,1) NULL DEFAULT NULL,
        batv DECIMAL(3,2) NULL DEFAULT NULL,
        PRIMARY KEY(report_id),
        FOREIGN KEY(session_id, node_id) REFERENCES
            session_nodes(session_id, node_id)
            ON UPDATE CASCADE ON DELETE CASCADE,
        UNIQUE KEY(node_id, time)
    ) ENGINE = INNODB;

    CREATE TABLE login_sessions (
        session_id CHAR(16) NOT NULL,
        user_id VARCHAR(64) NOT NULL,
        login_time DATETIME NOT NULL,
        UNIQUE KEY(session_id)
    ) ENGINE = INNODB;

# Dependencies
- Python 3
- python-daemon (for Python)
- paho-mqtt (for Python)
- pymysql (for Python)
- MariaDB (MySQL)
