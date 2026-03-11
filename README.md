# Basics of Docker 

# Build Docker Image By Running the Following Command

$docker build -t jenkinsdemo . # -t = Tag 


# To Run Containers

$docker run -it -p 2222:8080 jenkinsdemo # -i = interactive ; -t terminal

# In host's browser type 

localhost:2222 for Jenkins Setup

# Some of the Docker Commands

docker images --> to list the images

docker ps  --> to see the running containers

docker ps -a --> to see all the containers which are exited 

docker run -it <image_tag> --> to run the image which will create containers 

docker run -it <image_tag> bash --> to run the image in bash

docker exec -it <container_tag> bash --> this is to log into the running container in bash (edited)

docker run -it -p 8080:8080 <image_tag> --> this is to run the image using the port 8080 in host(ubuntu) and 8080 in container 

DOCKER CHEATSHEET - https://github.com/wsargent/docker-cheat-sheet#dockerfile











A Flask-based web application for comparing AWS Security Groups between two AWS accounts (GEN2 vs GEN3). Provides side-by-side comparison of security group rules, CIDR blocks, ports, protocols, and highlights differences.

## Features

- List all security groups from two AWS accounts side-by-side
- Compare specific security groups between GEN2 and GEN3 accounts
- Detailed rule comparison with protocol, port, and service type display (SSH, HTTPS, etc.)
- Visual diff highlighting for missing and extra rules
- Interactive security group selection with floating panel
- AWS credential testing before comparison
- Support for CIDR blocks, prefix lists, IPv6, and security group references

## Prerequisites

### 1. AWS CLI and Credentials

You must have AWS CLI installed and configured with named profiles for both accounts.

```bash
# Install AWS CLI
pip install awscli

# Configure profiles
aws configure --profile gen2-profile
aws configure --profile gen3-profile
```

Your `~/.aws/credentials` file should contain:

```ini
[gen2-profile]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
region = us-east-1

[gen3-profile]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
region = us-east-1
```

### 2. AWSProxy

AWSProxy must be running before starting the application. This is required for routing AWS API calls through the corporate proxy.

```bash
# Start AWSProxy before running the application
awsproxy start
```

Verify AWSProxy is running:

```bash
awsproxy status
```

### 3. Python 3.8+

Ensure Python 3.8 or higher is installed:

```bash
python3 --version
```

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd <project-directory>
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Dependencies

- Flask==2.3.3
- boto3==1.28.85

## Usage

### 1. Start AWSProxy

```bash
awsproxy start
```

### 2. Run the Application

```bash
python app.py
```

The application starts on `http://localhost:5000`.

### 3. Open the Browser

Navigate to `http://localhost:5000` and use the tool:

- **Security Groups Comparison**: Enter profile names and security group IDs to compare specific security groups
- **List All Security Groups**: Enter profile names to list all security groups from both accounts, then select and compare

### 4. Corporate/SSL Environment

For environments with SSL certificate issues, set the environment variable:

```bash
DISABLE_SSL_VERIFICATION=true python app.py
```

Or use the corporate runner:

```bash
python run_corporate.py
```

## Project Structure

```
├── app.py                  # Main Flask application
├── run_corporate.py        # Corporate environment launcher (SSL handling)
├── run_simple.py           # Simple launcher
├── requirements.txt        # Python dependencies
├── templates/
│   ├── base.html           # Base HTML template
│   ├── index.html          # Main comparison UI
│   └── report.html         # Report template
└── README.md               # This file
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main UI |
| `/list-security-groups` | POST | List all security groups from both accounts |
| `/compare-security-groups` | POST | Compare specific security groups |
| `/test-credentials` | POST | Test AWS profile credentials |

## Troubleshooting

### AWSProxy not running
```
Error: Unable to locate credentials
```
Ensure AWSProxy is started before running the application: `awsproxy start`

### Invalid credentials
```
Error: The security token included in the request is invalid
```
Verify your AWS profiles are configured correctly: `aws sts get-caller-identity --profile <profile-name>`

### Security group not found
```
Error: The security group 'sg-xxx' does not exist
```
The security group ID may not exist in the target account. Use "List All Security Groups" to discover available security groups in each account.

### SSL certificate errors
Use the corporate runner or set the environment variable:
```bash
DISABLE_SSL_VERIFICATION=true python app.py
```

