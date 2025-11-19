## Introduction
Janus is a small tool built with Python, typer and questionary to export resources from a [MongoDB Ops Manager](https://www.mongodb.com/docs/ops-manager/current/) or [Cloud Manager](https://www.mongodb.com/cloud/cloud-manager) instance and import them into [MongoDB Atlas](https://www.mongodb.com/atlas) using the respective APIs. 

Janus currently supports:
- **Alert Configurations** - Export/Import between Ops Manager instances
- **Database Users and Roles** - Export from Ops Manager/Cloud Manager and Import to Atlas

### About the name - Janus
In ancient Roman religion and myth, [Janus](https://en.wikipedia.org/wiki/Janus) is the god of beginnings, gates, transitions, time, duality, doorways, passages, frames, and endings.  We hope that Janus will look over the transition of the Alert Configurations.

## Python Versions

Developed and tested using:

- Python v3.14.0
- Pip v23.3.2+

## Installation

### Option 1: From Source (Development)

```bash
git clone https://github.com/edmallia/om-janus.git
cd om-janus
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Option 2: Standalone Executable (Recommended for Users)

If you have a pre-built executable:

```bash
# Make executable (macOS/Linux)
chmod +x dist/janus

# Test installation
./dist/janus version
```

## Running Janus

### Using Python (Source Installation)

#### Check version

```bash
python -m janus version
```

![version](./docs/img/version.png)

#### Show help

```bash
python -m janus --help
```

![help](./docs/img/help.png)

### Using Standalone Executable

```bash
# Check version
./dist/janus version

# Show help
./dist/janus --help
```

## Alert Configurations

### Show help for Alert Configs subcommand

```bash
# Python
python -m janus alert-configs --help

# Executable
./dist/janus alert-configs --help
```

![alertconfighelp](./docs/img/alertconfighelp.png)

### Export Alert Configs

You must provide either a configuration file or all required parameters via command line options:

**Using a Configuration file (recommended):**

```bash
# Python
python -m janus alert-configs export --config config.yaml

# Executable
./dist/janus alert-configs export --config config.yaml
```

![exportwithconfig](./docs/img/exportwithconfig.png)

**Using command line options:**

```bash
# Python
python -m janus alert-configs export \
  --sourceUrl https://opsmanager.example.com \
  --sourceUsername myuser \
  --sourceApiKey xxxx-xxxx-xxxx \
  --outputFile alertConfigs.json

# Executable
./dist/janus alert-configs export \
  --sourceUrl https://opsmanager.example.com \
  --sourceUsername myuser \
  --sourceApiKey xxxx-xxxx-xxxx \
  --outputFile alertConfigs.json
```

### Import Alert Configs

**Using a Configuration file (recommended):**

```bash
# Python
python -m janus alert-configs import --config config.yaml

# Executable
./dist/janus alert-configs import --config config.yaml
```

**Using command line options:**

```bash
# Python
python -m janus alert-configs import \
  --destinationUrl https://opsmanager.example.com \
  --destinationUsername myuser \
  --destinationApiKey yyyy-yyyy-yyyy \
  --inputFile alertConfigs.json \
  --detectAndSkipDuplicates true

# Executable
./dist/janus alert-configs import \
  --destinationUrl https://opsmanager.example.com \
  --destinationUsername myuser \
  --destinationApiKey yyyy-yyyy-yyyy \
  --inputFile alertConfigs.json \
  --detectAndSkipDuplicates true
```

![importwithconfig](./docs/img/importwithconfig.png)

### Sample Configuration file for Alert Configs

```yaml
sourceUrl: https://cloud.mongodb.com
sourceUsername: your-api-public-key
sourceApiKey: your-api-private-key
outputFile: alertConfigs.json

destinationUrl: https://cloud.mongodb.com
destinationUsername: your-atlas-api-public-key
destinationApiKey: your-atlas-api-private-key
detectAndSkipDuplicates: true
inputFile: alertConfigs.json
```

For more examples, see [docs/examples/config.yaml.example](./docs/examples/config.yaml.example).

## Database Users and Roles Migration

### Overview

Janus can export database users and custom roles from Ops Manager or Cloud Manager projects and import them into MongoDB Atlas projects. This is particularly useful when migrating from on-premise deployments to Atlas.

**Important Notes:**
- Only **password-based authentication** (SCRAM) users are supported
- Passwords **cannot be exported** from Ops Manager/Cloud Manager (they are hashed)
- New **random secure passwords** are generated during import to Atlas
- Generated passwords are exported to a **CSV file** for reference
- **Custom roles** are migrated along with users
- Works with both **Ops Manager** and **Cloud Manager** as source

### Security Considerations

⚠️ **IMPORTANT SECURITY WARNINGS:**
1. The generated password CSV file contains plaintext passwords - **keep it secure**
2. **Rotate passwords immediately** after migration using Atlas UI or API
3. Consider adding the password CSV file to `.gitignore`
4. Delete the password file after passwords have been rotated
5. Never commit configuration files with API keys to version control

### Show help for Database Users subcommand

```bash
# Python
python -m janus db-users --help

# Executable
./dist/janus db-users --help
```

### Migrate Database Users and Roles (Export + Import in one step)

The **migrate** command performs both export and import in a single operation, making the migration process simpler:

**Using a Configuration file (recommended):**

```bash
# Python
python -m janus db-users migrate --config config.yaml

# Executable
./dist/janus db-users migrate --config config.yaml
```

**Using command line options:**

```bash
# Python
python -m janus db-users migrate \
  --sourceUrl https://cloud.mongodb.com \
  --sourceUsername source-user \
  --sourceApiKey source-xxxx-xxxx \
  --destinationUrl https://cloud.mongodb.com \
  --destinationUsername atlas-user \
  --destinationApiKey atlas-yyyy-yyyy \
  --outputFile dbUsers.json \
  --passwordOutputFile passwords.csv \
  --skipExisting true

# Executable
./dist/janus db-users migrate \
  --sourceUrl https://cloud.mongodb.com \
  --sourceUsername source-user \
  --sourceApiKey source-xxxx-xxxx \
  --destinationUrl https://cloud.mongodb.com \
  --destinationUsername atlas-user \
  --destinationApiKey atlas-yyyy-yyyy \
  --outputFile dbUsers.json \
  --passwordOutputFile passwords.csv \
  --skipExisting true
```

The migrate command will:
1. Export database users and custom roles from source (with interactive project selection)
2. Automatically proceed to import into Atlas (with interactive project mapping)
3. Generate random passwords and save them to CSV
4. Complete the entire migration in one execution

### Export Database Users and Roles (Separate Step)

You must provide either a configuration file or all required parameters via command line options:

**Using a Configuration file (recommended):**

```bash
# Python
python -m janus db-users export --config config.yaml

# Executable
./dist/janus db-users export --config config.yaml
```

**Using command line options:**

```bash
# Python
python -m janus db-users export \
  --sourceUrl https://cloud.mongodb.com \
  --sourceUsername myuser \
  --sourceApiKey xxxx-xxxx-xxxx \
  --outputFile dbUsers.json

# Executable
./dist/janus db-users export \
  --sourceUrl https://cloud.mongodb.com \
  --sourceUsername myuser \
  --sourceApiKey xxxx-xxxx-xxxx \
  --outputFile dbUsers.json
```

The tool will:
1. Fetch all projects from your organization
2. Allow you to select which projects to export from (interactive)
3. Extract database users and custom roles from the automation configuration
4. Save the data to a JSON file

### Import Database Users and Roles to Atlas

You must provide either a configuration file or all required parameters via command line options:

**Using a Configuration file (recommended):**

```bash
# Python
python -m janus db-users import --config config.yaml

# Executable
./dist/janus db-users import --config config.yaml
```

**Using command line options:**

```bash
# Python
python -m janus db-users import \
  --destinationUrl https://cloud.mongodb.com \
  --destinationUsername atlasuser \
  --destinationApiKey yyyy-yyyy-yyyy \
  --inputFile dbUsers.json \
  --passwordOutputFile passwords.csv \
  --skipExisting true

# Executable
./dist/janus db-users import \
  --destinationUrl https://cloud.mongodb.com \
  --destinationUsername atlasuser \
  --destinationApiKey yyyy-yyyy-yyyy \
  --inputFile dbUsers.json \
  --passwordOutputFile passwords.csv \
  --skipExisting true
```

The tool will:
1. Read the exported users and roles
2. Fetch all Atlas projects
3. For each source project, ask you to select a destination Atlas project (interactive)
4. Create custom roles first (they must exist before users)
5. Create database users with randomly generated secure passwords
6. Export all generated passwords to a CSV file

### Sample Configuration file for Database Users

**For Migrate command (Export + Import in one step):**

```yaml
# Source: Ops Manager or Cloud Manager
sourceUrl: https://cloud.mongodb.com
sourceUsername: source-api-public-key
sourceApiKey: source-api-private-key

# Destination: MongoDB Atlas
destinationUrl: https://cloud.mongodb.com
destinationUsername: atlas-api-public-key
destinationApiKey: atlas-api-private-key

# Files
outputFile: dbUsers.json
passwordOutputFile: passwords.csv

# Options
skipExisting: true
```

**For separate Export/Import commands:**

```yaml
# Export from Ops Manager or Cloud Manager
sourceUrl: https://cloud.mongodb.com
sourceUsername: your-username
sourceApiKey: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
outputFile: dbUsers.json

# Import to Atlas
destinationUrl: https://cloud.mongodb.com
destinationUsername: atlas-username
destinationApiKey: yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
inputFile: dbUsers.json
passwordOutputFile: passwords.csv
skipExisting: true
```

For more configuration examples, see [docs/examples/config.migrate.example.yaml](./docs/examples/config.migrate.example.yaml).

### Password CSV Format

The generated password CSV file contains the following columns:

```csv
timestamp,source_project,source_project_id,destination_project,destination_project_id,username,auth_database,password,roles
2024-01-15T10:30:00,MyProject,5f8a1b2c3d4e5f6g7h8i9j0k,AtlasProject,6g7h8i9j0k1l2m3n4o5p6q7r,appUser,admin,Xk9$mP2nQ#vL8wR4,readWrite@myDB;read@admin
```

**What to do with the password file:**
1. Securely share passwords with application owners
2. Update application connection strings with new credentials
3. Test connectivity to Atlas clusters
4. **Rotate all passwords** using Atlas UI or API
5. **Delete the password file** after rotation

For an example, see [docs/examples/passwords.example.csv](./docs/examples/passwords.example.csv).

## Building Standalone Executable

If you want to build the standalone executable yourself:

### Prerequisites

```bash
# Install PyInstaller
pip install pyinstaller
```

### Build Process

```bash
# Full command (first time)
pyinstaller --onefile --name janus --console \
  --hidden-import yaml \
  --hidden-import pyyaml \
  --hidden-import questionary \
  --hidden-import typer \
  --hidden-import typer_config \
  --hidden-import requests \
  --hidden-import rich \
  --hidden-import click \
  --hidden-import json \
  --hidden-import csv \
  --hidden-import logging \
  janus/__main__.py

# Or use the spec file (after first build)
pyinstaller janus.spec
```

The executable will be created at `dist/janus` (~14MB).

### Test the Build

```bash
./dist/janus version
./dist/janus --help
```

## Configuration Examples

Sample configuration files are available in the [docs/examples/](./docs/examples/) directory:

- [config.yaml.example](./docs/examples/config.yaml.example) - Basic configuration
- [config.migrate.example.yaml](./docs/examples/config.migrate.example.yaml) - Migration configuration
- [dbUsers.example.json](./docs/examples/dbUsers.example.json) - Example exported users
- [passwords.example.csv](./docs/examples/passwords.example.csv) - Example password file

## Limitations

- Only password-based (SCRAM) authentication is supported
- x.509, AWS IAM, LDAP, and OIDC authentication methods are not supported
- User scopes (cluster-specific access) are not migrated
- Authentication restrictions are not migrated
- Passwords are randomly generated and cannot preserve original passwords
- Custom roles must not conflict with Atlas built-in roles

## Project Structure

```
om-janus/
├── dist/                  # Standalone executable
│   └── janus             # PyInstaller binary (~14MB)
├── janus/                # Python source code
├── docs/                 # Documentation and examples
│   ├── examples/         # Configuration examples
│   └── img/              # Documentation images
├── config.yaml           # Your configuration (create from examples)
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Security Notes

🔒 **IMPORTANT**: Never commit these files to version control:
- `config.yaml` (contains API keys)
- `passwords.csv` (contains generated passwords)
- `users.json` (contains exported user data)
- `*.log` files (may contain sensitive debug info)

The `.gitignore` file is configured to protect these sensitive files automatically.