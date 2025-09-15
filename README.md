### monitorapp

This is a comprehensive README for the **monitorapp**, a system designed to monitor and visualize metrics from your database clusters. This document will guide you through the setup and configuration of the application on an Ubuntu aarch64 environment.

### Features

  * **Database Agnostic:** Monitors both MySQL and PostgreSQL database clusters.
  * **Scalable:** Designed to connect to single, double, or triple-node database clusters.
  * **Multi-Framework:** Utilizes both **Flask** for specific metric collection and **FastAPI** for a modern, asynchronous API.
  * **Interactive Dashboard:** Provides a web-based dashboard for real-time visualization of key metrics.

-----

### Prerequisites

To run this application, you must have the following installed on your Ubuntu aarch64 system:

  * **Docker:** For containerizing the database clusters.
  * **Docker Compose** (recommended): For easy orchestration of multi-node database setups.
  * **Python 3.8+**: The application is built with Python. I used python 3.12.3 .
  * **pip**: The Python package installer.

-----

### Database Configuration

The application is designed to connect to either a MySQL or PostgreSQL cluster running in Docker. The configuration files are set up for a three-node cluster by default. If you are using a single or double-node setup, you **must** update the configuration files listed below.

#### Docker Images

  * **MySQL:** `mysql:8.0.43`
  * **PostgreSQL:** `postgres:17`

> **Note:** The `mysql.connector` library may have compatibility issues with newer MySQL versions, so version `8.0.43` is specified to ensure stability.

-----

### Configuration and Setup

Before running the application, you need to update the configuration files to match your specific database setup (number of nodes, IP addresses, credentials, etc.).

1.  **Start your database clusters using Docker:**

      * Create your Docker network for the databases.
      * Start your MySQL or PostgreSQL containers on different VMs or as different services.
      * Ensure each container has a unique name and is reachable from your `monitorapp` host.

2.  **Update the configuration files:**

      * **`db_config.py`**: This file holds the connection strings for each database node.

          * Modify the IP addresses, port numbers, usernames, and passwords to match your Docker setup.
          * Remove or comment out the entries for any nodes you are not using (e.g., if you only have a single-node cluster, keep only one entry).

      * **`main_metrics.py`**: The Flask-based script.

          * This script connects to the databases to collect metrics. You may need to adjust the connection logic or remove connection attempts to nodes that don't exist.

      * **`app.py`**: The FastAPI-based script.

          * Similar to `main_metrics.py`, update the database connection logic to match your cluster's node count.

      * **`dashboard.html`**: The front-end dashboard.

          * This file may need minor adjustments to display the correct number of node status indicators or metrics.

      * **`dashboard.js`**: The JavaScript file for the dashboard.

          * This script sends API requests to your Flask/FastAPI backends. Ensure the API endpoints it calls are correct and the logic handles the number of nodes you have configured.

-----

### Usage

1.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

      * *Note: If a `requirements.txt` file is not present, create one with the necessary libraries like `Flask`, `FastAPI`, `uvicorn`, `mysql-connector-python`, `psycopg2-binary`, etc.*

2.  **Run the Flask application:**

    ```bash
    python3 main_metrics.py
    ```

3.  **Run the FastAPI application:**

    ```bash
    uvicorn app:app --host 0.0.0.0 --port 8000
    ```

4.  **Access the Dashboard:**

      * Open `dashboard.html` in your web browser to view the real-time metrics.
      * The dashboard will communicate with the running Flask and FastAPI services to fetch and display the data.

This README provides a clear and structured overview of your project. If you have a `requirements.txt` file or more specific instructions on how to start the database containers, you can add those details to make this even more comprehensive.

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# monitorapp instructions

my system is ubuntu arm64 (aarch64)
db  configuration setup in docker 

image: mysql:8.0.43 (if latest version select mysql.connector doesnt work with python flask or fastapi)
image: postgres:17

main_metric.py is flask based code

app.py is fastapi based code

 i have setup 3 node of both db in different docker vms, if you setup single node or double node of db cluster in docker make sure update the files as below :
 * db_config.py
 * main_metrics.py
 * app.py 
 * dashboard.html
 * dashboard.js
 
