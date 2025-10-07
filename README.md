# FacIT - Server monitoring application

<img width="1146" height="600" alt="facIT-1" src="https://github.com/user-attachments/assets/e2805342-f766-4fd8-84c2-c2bb4411f697" />


## Purpose
FacIT is a tool designed for development teams that use shared servers to test their applications. It enables users to efficiently manage a pool of predefined servers, allocate resources, and monitor server usage in real time. The system simplifies coordination between developers by providing an overview of server availability and ownership.

## Project Scope
FacIT was originally developed for the Israel Air Force (IAF) to assist development teams in identifying available servers on which they can deploy and test their applications. The tool provides an automated and collaborative environment for managing shared computing resources without the need for a centralized server installation.


## Installation
FacIT runs on Windows, Linux, and macOS systems that support:
* Python 3.10+
* PySide6 (Qt for Python)

Clone the repository and install dependencies:
`pip install -r requirements.txt`

## Running
Run the application with:
`python main.py`

When launched, FacIT automatically:
1. Starts the backend in dedicated threads (handling network communication and data synchronization).
2. Launches the frontend interface (built with PySide6).

Both layers share data in real time through PySide6’s signal-slot mechanism.