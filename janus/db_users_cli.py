import csv
import json
import secrets
import string
from datetime import datetime
from typing import Any, Union

import questionary
import requests
import typer
import yaml
from requests.auth import HTTPDigestAuth
from typer_config import use_yaml_config

from janus.logging import logger


def load_config_file() -> dict:
    """Load config from config.yaml file as fallback for PyInstaller builds."""
    try:
        with open("config.yaml", "r") as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        logger.warning("No config.yaml file found, using defaults")
        return {}
    except Exception as e:
        logger.warning(f"Failed to load config.yaml: {e}, using defaults")
        return {}


def get_verify_ssl_config(config: dict, key: str = "source") -> bool:
    """Get verify_ssl config from either nested or root level configuration."""
    # First try nested format: config["source"]["verify_ssl"]
    nested_config = config.get(key, {})
    if isinstance(nested_config, dict) and "verify_ssl" in nested_config:
        return nested_config["verify_ssl"]

    # Fall back to root level: config["verify_ssl"]
    return config.get("verify_ssl", True)


from janus.projects import fetch_projects

# Type aliases for common data structures
JsonDict = dict[str, Any]
RoleDict = dict[str, Any]
UserDict = dict[str, Any]
ProjectDict = dict[str, Any]

app = typer.Typer(help="Import/Export Database Users and Roles")


@app.command()
@use_yaml_config()
def export(
    sourceUrl: str = typer.Option(
        ...,
        "--sourceUrl",
        help="Source Ops Manager/Cloud Manager URL e.g. https://cloud.mongodb.com or http://localhost:8080",
    ),
    sourceUsername: str = typer.Option(
        ...,
        "--sourceUsername",
        help="Source Username",
    ),
    sourceApiKey: str = typer.Option(
        ...,
        "--sourceApiKey",
        help="Source API Key",
    ),
    outputFile: str = typer.Option(
        ...,
        "--outputFile",
        help="Output file (can be used in import process)",
    ),
) -> None:
    """Export Database Users and Custom Roles from Ops Manager/Cloud Manager to a JSON file."""
    try:
        source_verify_ssl = get_verify_ssl_config(config, "source")
    except NameError:
        # Fallback for PyInstaller builds where @use_yaml_config() may not work
        config = load_config_file()
        source_verify_ssl = get_verify_ssl_config(config, "source")
    projects = fetch_projects(
        sourceUrl, sourceUsername, sourceApiKey, source_verify_ssl
    )

    choices = []
    projectIdNameDict = {}
    choice_template = "{} ({})"
    for project in projects["results"]:
        choices.append(
            questionary.Choice(
                title=choice_template.format(project["name"], project["id"]),
                value=project["id"],
                checked=True,
            )
        )
        projectIdNameDict[project["id"]] = project["name"]

    answer = questionary.checkbox(
        "Select projects to export Database Users and Roles from", choices=choices
    ).ask()

    export_db_users_and_roles(
        sourceUrl,
        answer,
        projectIdNameDict,
        sourceUsername,
        sourceApiKey,
        outputFile,
        source_verify_ssl,
    )


@app.command(name="import")
@use_yaml_config()
def import_(
    destinationUrl: str = typer.Option(
        ...,
        "--destinationUrl",
        help="Destination Atlas URL e.g. https://cloud.mongodb.com",
    ),
    destinationUsername: str = typer.Option(
        ...,
        "--destinationUsername",
        help="Destination Atlas Username",
    ),
    destinationApiKey: str = typer.Option(
        ...,
        "--destinationApiKey",
        help="Destination Atlas API Key",
    ),
    inputFile: str = typer.Option(
        ...,
        "--inputFile",
        help="Input file generated from the export process",
    ),
    passwordOutputFile: str = typer.Option(
        ...,
        "--passwordOutputFile",
        help="CSV file to export generated passwords",
    ),
    skipExisting: bool = typer.Option(
        True,
        "--skipExisting",
        help="Skip existing users and roles to avoid duplicates",
    ),
) -> None:
    """Import Database Users and Custom Roles to Atlas. Generates random passwords for all users and exports them to a CSV file."""
    import_db_users_and_roles(
        inputFile,
        destinationUrl,
        destinationUsername,
        destinationApiKey,
        passwordOutputFile,
        skipExisting,
    )


@app.command()
@use_yaml_config()
def migrate(
    sourceUrl: str = typer.Option(
        ...,
        "--sourceUrl",
        help="Source Ops Manager/Cloud Manager URL e.g. https://cloud.mongodb.com or http://localhost:8080",
    ),
    sourceUsername: str = typer.Option(
        ...,
        "--sourceUsername",
        help="Source Username",
    ),
    sourceApiKey: str = typer.Option(
        ...,
        "--sourceApiKey",
        help="Source API Key",
    ),
    destinationUrl: str = typer.Option(
        ...,
        "--destinationUrl",
        help="Destination Atlas URL e.g. https://cloud.mongodb.com",
    ),
    destinationUsername: str = typer.Option(
        ...,
        "--destinationUsername",
        help="Destination Atlas Username",
    ),
    destinationApiKey: str = typer.Option(
        ...,
        "--destinationApiKey",
        help="Destination Atlas API Key",
    ),
    outputFile: str = typer.Option(
        "dbUsers.json",
        "--outputFile",
        help="Intermediate file for export/import",
    ),
    passwordOutputFile: str = typer.Option(
        "passwords.csv",
        "--passwordOutputFile",
        help="CSV file to export generated passwords",
    ),
    skipExisting: bool = typer.Option(
        True,
        "--skipExisting",
        help="Skip existing users and roles to avoid duplicates",
    ),
) -> None:
    """Export from Ops Manager/Cloud Manager and Import to Atlas in one step. Generates random passwords and exports them to CSV."""

    logger.info("")
    logger.info("=" * 80)
    logger.info("  STEP 1: EXPORT from Source")
    logger.info("=" * 80)
    logger.info("")

    # Export phase
    try:
        source_verify_ssl = get_verify_ssl_config(config, "source")
    except NameError:
        # Fallback for PyInstaller builds where @use_yaml_config() may not work
        config = load_config_file()
        source_verify_ssl = get_verify_ssl_config(config, "source")
    projects = fetch_projects(
        sourceUrl, sourceUsername, sourceApiKey, source_verify_ssl
    )

    choices = []
    projectIdNameDict = {}
    choice_template = "{} ({})"
    for project in projects["results"]:
        choices.append(
            questionary.Choice(
                title=choice_template.format(project["name"], project["id"]),
                value=project["id"],
                checked=True,
            )
        )
        projectIdNameDict[project["id"]] = project["name"]

    answer = questionary.checkbox(
        "Select projects to export Database Users and Roles from", choices=choices
    ).ask()

    export_db_users_and_roles(
        sourceUrl,
        answer,
        projectIdNameDict,
        sourceUsername,
        sourceApiKey,
        outputFile,
        source_verify_ssl,
    )

    logger.info("")
    logger.info("=" * 80)
    logger.info("  STEP 2: IMPORT to Destination")
    logger.info("=" * 80)

    # Import phase
    import_db_users_and_roles(
        outputFile,
        destinationUrl,
        destinationUsername,
        destinationApiKey,
        passwordOutputFile,
        skipExisting,
    )

    logger.info("")
    logger.info("=" * 80)
    logger.info("  ✓ MIGRATION COMPLETE")
    logger.info("=" * 80)
    logger.info("")


def fetch_automation_config(
    host: str, group: str, username: str, apikey: str, verify_ssl: bool = True
) -> JsonDict:
    """Fetch automation configuration from Ops Manager/Cloud Manager."""
    response = requests.get(
        host + "/api/public/v1.0/groups/" + group + "/automationConfig",
        auth=HTTPDigestAuth(username, apikey),
        verify=verify_ssl,
    )
    response.raise_for_status()
    automation_config: JsonDict = response.json()
    logger.debug("Fetched Automation Config for project %s", group)
    logger.debug(json.dumps(automation_config, indent=2))
    return automation_config


def extract_custom_roles(automation_config: JsonDict) -> list[RoleDict]:
    """Extract custom roles from automation configuration."""
    custom_roles: list[RoleDict] = []

    # Custom roles are in the 'roles' array at the root level
    roles: list[Any] = automation_config.get("roles", [])

    for role in roles:
        # Extract custom roles
        custom_role = {
            "role": role.get("role"),
            "db": role.get("db"),
            "privileges": role.get("privileges", []),
            "roles": role.get("roles", []),
        }
        custom_roles.append(custom_role)
        logger.debug(
            "Extracted custom role: %s on database %s",
            custom_role["role"],
            custom_role["db"],
        )

    return custom_roles


def extract_database_users(automation_config: JsonDict) -> list[UserDict]:
    """Extract password-based database users from automation configuration."""
    database_users: list[UserDict] = []

    auth: JsonDict = automation_config.get("auth", {})
    users_wanted: list[Any] = auth.get("usersWanted", [])

    for user in users_wanted:
        # Extract user information (passwords will be generated on import)
        db_user = {
            "username": user.get("user"),
            "databaseName": user.get("db"),
            "roles": [],
        }

        # Convert roles format
        for role in user.get("roles", []):
            db_user["roles"].append({"role": role.get("role"), "db": role.get("db")})

        database_users.append(db_user)
        logger.debug(
            "Extracted user: %s on database %s with %d roles",
            db_user["username"],
            db_user["databaseName"],
            len(db_user["roles"]),
        )

    return database_users


def export_db_users_and_roles(
    host: str,
    groups: list[str],
    groupNameDict: dict[str, str],
    username: str,
    apikey: str,
    outputFile: str,
    verify_ssl: bool = True,
) -> None:
    """Export database users and custom roles for selected projects."""
    output: list[ProjectDict] = []

    for group in groups:
        logger.info(
            "Exporting Database Users and Roles from project: %s (%s)",
            groupNameDict[group],
            group,
        )

        try:
            automation_config = fetch_automation_config(
                host, group, username, apikey, verify_ssl
            )

            custom_roles = extract_custom_roles(automation_config)
            database_users = extract_database_users(automation_config)

            element = {
                "project": {"id": group, "name": groupNameDict[group]},
                "customRoles": custom_roles,
                "databaseUsers": database_users,
            }

            output.append(element)
            logger.info(
                "Exported %d custom roles and %d database users from project %s",
                len(custom_roles),
                len(database_users),
                groupNameDict[group],
            )

        except requests.exceptions.HTTPError as e:
            logger.error(
                "Failed to fetch automation config for project %s: %s", group, str(e)
            )
            logger.error(
                "This may occur if the project doesn't have automation enabled"
            )
            continue
        except Exception as e:
            logger.error("Error exporting from project %s: %s", group, str(e))
            continue

    # Save to file
    json_object = json.dumps(output, indent=4)
    with open(outputFile, "w") as outfile:
        outfile.write(json_object)

    total_users = sum(len(p.get("databaseUsers", [])) for p in output)
    total_roles = sum(len(p.get("customRoles", [])) for p in output)
    logger.info("")
    logger.info("✓ Export complete: %s", outputFile)
    logger.info(
        "  → %d user(s), %d custom role(s) from %d project(s)",
        total_users,
        total_roles,
        len(output),
    )


def generate_secure_password(length: int = 20) -> str:
    """Generate a secure random password."""
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = "!@#$%^&*-_=+"

    # Ensure at least one character from each set
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special),
    ]

    # Fill the rest with random characters from all sets
    all_characters = lowercase + uppercase + digits + special
    password.extend(secrets.choice(all_characters) for _ in range(length - 4))

    # Shuffle to avoid predictable patterns
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)

    return "".join(password_list)


def fetch_atlas_custom_roles(
    atlasUrl: str, groupId: str, username: str, apikey: str
) -> list[RoleDict]:
    """Fetch existing custom roles from Atlas."""
    headers = {
        "Accept": "application/vnd.atlas.2023-02-01+json",
    }
    response = requests.get(
        atlasUrl + "/api/atlas/v2/groups/" + groupId + "/customDBRoles/roles",
        auth=HTTPDigestAuth(username, apikey),
        headers=headers,
    )
    response.raise_for_status()
    roles_data: JsonDict = response.json()
    # roles_data might be a list directly or a dict with 'results'
    if isinstance(roles_data, list):
        return roles_data
    elif isinstance(roles_data, dict):
        return roles_data.get("results", [])
    else:
        return []


def create_atlas_custom_role(
    atlasUrl: str,
    groupId: str,
    username: str,
    apikey: str,
    rolePayload: RoleDict,
) -> requests.Response:
    """Create a custom role in Atlas."""
    url = atlasUrl + "/api/atlas/v2/groups/" + groupId + "/customDBRoles/roles"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/vnd.atlas.2023-02-01+json",
    }

    logger.debug("Creating custom role: %s", rolePayload.get("roleName"))
    logger.debug("Payload: %s", json.dumps(rolePayload, indent=2))

    response = requests.post(
        url,
        auth=HTTPDigestAuth(username, apikey),
        headers=headers,
        data=json.dumps(rolePayload),
    )

    return response


def fetch_atlas_database_users(
    atlasUrl: str, groupId: str, username: str, apikey: str
) -> list[UserDict]:
    """Fetch existing database users from Atlas."""
    headers = {
        "Accept": "application/vnd.atlas.2023-02-01+json",
    }
    response = requests.get(
        atlasUrl + "/api/atlas/v2/groups/" + groupId + "/databaseUsers",
        auth=HTTPDigestAuth(username, apikey),
        headers=headers,
    )
    response.raise_for_status()
    users_data: JsonDict = response.json()
    return users_data.get("results", [])


def create_atlas_database_user(
    atlasUrl: str,
    groupId: str,
    username: str,
    apikey: str,
    userPayload: UserDict,
) -> requests.Response:
    """Create a database user in Atlas."""
    url = atlasUrl + "/api/atlas/v2/groups/" + groupId + "/databaseUsers"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/vnd.atlas.2023-02-01+json",
    }

    logger.debug("Creating database user: %s", userPayload.get("username"))
    logger.debug("User payload: %s", json.dumps(userPayload, indent=2))
    logger.debug("URL: %s", url)

    response = requests.post(
        url,
        auth=HTTPDigestAuth(username, apikey),
        data=json.dumps(userPayload),
        headers=headers,
    )

    logger.debug("Response status code: %s", response.status_code)
    logger.debug("Response body: %s", response.text)

    return response


def transform_role_to_atlas_format(role: RoleDict) -> RoleDict:
    """Transform role from Ops Manager format to Atlas format."""
    atlas_role: RoleDict = {
        "roleName": role.get("role"),
        "inheritedRoles": [],
    }

    # Only include privileges if they exist and are not empty
    privileges: list[Any] = role.get("privileges", [])
    if privileges:
        atlas_role["privileges"] = privileges

    # Transform inherited roles
    inherited_roles_list: list[RoleDict] = []
    for inherited_role in role.get("roles", []):
        inherited_roles_list.append(
            {"role": inherited_role.get("role"), "db": inherited_role.get("db")}
        )
    atlas_role["inheritedRoles"] = inherited_roles_list

    return atlas_role


def transform_user_roles_to_atlas_format(
    roles: list[RoleDict],
) -> list[RoleDict]:
    """Transform user roles from Ops Manager format to Atlas format."""
    atlas_roles: list[RoleDict] = []
    for role in roles:
        atlas_roles.append(
            {"roleName": role.get("role"), "databaseName": role.get("db")}
        )
    return atlas_roles


def import_db_users_and_roles(
    inputFile: str,
    destinationUrl: str,
    destinationUsername: str,
    destinationApikey: str,
    passwordOutputFile: str,
    skipExisting: bool,
) -> None:
    """Import database users and custom roles to Atlas."""

    # Read input file
    with open(inputFile, "r") as openfile:
        import_data: list[ProjectDict] = json.load(openfile)

    # Fetch destination projects
    destProjects: JsonDict = fetch_projects(
        destinationUrl, destinationUsername, destinationApikey
    )

    choices = []
    choicesDict = {}
    destProjectIdNameDict = {}
    choice_template = "{} ({})"

    for project in destProjects["results"]:
        choice = questionary.Choice(
            title=choice_template.format(project["name"], project["id"]),
            value=project["id"],
        )
        choices.append(choice)
        destProjectIdNameDict[project["id"]] = project["name"]
        choicesDict[project["id"]] = choice

    skipChoice = questionary.Choice(title="Skip", value="Skip")
    choices.append(skipChoice)

    # Prepare CSV for passwords
    password_records = []
    password_records.append(
        [
            "timestamp",
            "source_project",
            "source_project_id",
            "destination_project",
            "destination_project_id",
            "username",
            "auth_database",
            "password",
            "roles",
        ]
    )

    timestamp = datetime.now().isoformat()

    # Process each project
    for project_data in import_data:
        source_project_name = project_data["project"]["name"]
        source_project_id = project_data["project"]["id"]

        logger.info("")
        logger.info(
            "→ Processing project: %s (%s)", source_project_name, source_project_id
        )

        # Ask user which destination project to use
        if source_project_id in destProjectIdNameDict:
            answer = questionary.select(
                "Found destination Project with same Id. Import into this project?",
                instruction="Or choose a different project",
                choices=choices,
                default=choicesDict[source_project_id],
            ).ask()
        else:
            answer = questionary.select(
                "Destination Project with same Id not found. Select destination project:",
                choices=choices,
            ).ask()

        if answer == "Skip":
            logger.info("Skipping project: %s", source_project_name)
            continue

        destination_project_id = answer
        destination_project_name = destProjectIdNameDict[destination_project_id]

        logger.info(
            "  → Target: %s (%s)", destination_project_name, destination_project_id
        )

        # Import custom roles first
        custom_roles = project_data.get("customRoles", [])
        if custom_roles:
            logger.info("  → Creating %d custom role(s)...", len(custom_roles))
            import_custom_roles(
                destinationUrl,
                destination_project_id,
                destinationUsername,
                destinationApikey,
                custom_roles,
                skipExisting,
            )

        # Import database users
        database_users = project_data.get("databaseUsers", [])
        if database_users:
            logger.info("  → Creating %d database user(s)...", len(database_users))
            user_passwords: list[UserDict] = import_database_users(
                destinationUrl,
                destination_project_id,
                destinationUsername,
                destinationApikey,
                database_users,
                skipExisting,
            )

            # Add to password records
            for user_pass in user_passwords:
                user_roles: Any = user_pass.get("roles", [])
                roles_str = ";".join(
                    [f"{r['roleName']}@{r['databaseName']}" for r in user_roles]
                )
                password_records.append(
                    [
                        timestamp,
                        source_project_name,
                        source_project_id,
                        destination_project_name,
                        destination_project_id,
                        user_pass["username"],
                        user_pass["databaseName"],
                        user_pass["password"],
                        roles_str,
                    ]
                )

    # Write passwords to CSV
    with open(passwordOutputFile, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(password_records)

    logger.info("")
    logger.info("✓ Migration completed successfully")
    logger.info("  → Users and roles imported to Atlas")
    logger.info("  → Passwords saved to: %s", passwordOutputFile)
    logger.info("")
    logger.warning("⚠  Security reminder: Rotate all passwords immediately!")


def import_custom_roles(
    atlasUrl: str,
    groupId: str,
    username: str,
    apikey: str,
    custom_roles: list[RoleDict],
    skipExisting: bool,
) -> None:
    """Import custom roles to Atlas project."""

    created_count = 0
    skipped_count = 0
    failed_count = 0

    # Fetch existing roles if skipExisting is True
    existing_roles = []
    if skipExisting:
        try:
            existing_roles_data = fetch_atlas_custom_roles(
                atlasUrl, groupId, username, apikey
            )
            # existing_roles_data is a list of role objects
            if isinstance(existing_roles_data, list):
                existing_roles = [
                    r.get("roleName")
                    for r in existing_roles_data
                    if isinstance(r, dict)
                ]
            else:
                existing_roles = []
            logger.debug(
                "Found %d existing custom roles in destination", len(existing_roles)
            )
        except Exception as e:
            logger.warning("Could not fetch existing roles: %s", str(e))

    for role in custom_roles:
        role_name = role.get("role")

        # Check if role already exists
        if skipExisting and role_name in existing_roles:
            logger.info("Skipping existing role: %s", role_name)
            skipped_count += 1
            continue

        # Transform to Atlas format
        atlas_role_payload = transform_role_to_atlas_format(role)

        try:
            response = create_atlas_custom_role(
                atlasUrl, groupId, username, apikey, atlas_role_payload
            )

            if response.status_code in [201, 202]:
                logger.debug("✓ Created custom role: %s", role_name)
                created_count += 1
            elif response.status_code == 409:
                logger.debug("Role already exists: %s", role_name)
                skipped_count += 1
            else:
                logger.error(
                    "Failed to create role %s: %s %s",
                    role_name,
                    response.status_code,
                    response.text,
                )
                failed_count += 1

        except Exception as e:
            logger.error("Error creating role %s: %s", role_name, str(e))
            failed_count += 1

    if created_count > 0 or failed_count > 0:
        logger.info(
            "     Custom roles: %d created, %d skipped, %d failed",
            created_count,
            skipped_count,
            failed_count,
        )


def import_database_users(
    atlasUrl: str,
    groupId: str,
    username: str,
    apikey: str,
    database_users: list[UserDict],
    skipExisting: bool,
) -> list[UserDict]:
    """Import database users to Atlas project. Returns list of user credentials."""

    created_count = 0
    skipped_count = 0
    failed_count = 0

    user_credentials = []

    # Fetch existing users if skipExisting is True
    existing_users: list[tuple[Any, Any]] = []
    if skipExisting:
        try:
            existing_users_data = fetch_atlas_database_users(
                atlasUrl, groupId, username, apikey
            )
            existing_users = [
                (u.get("username"), u.get("databaseName")) for u in existing_users_data
            ]
            logger.debug(
                "Found %d existing database users in destination", len(existing_users)
            )
        except Exception as e:
            logger.warning("Could not fetch existing users: %s", str(e))

    for user in database_users:
        user_name = user.get("username")
        db_name = user.get("databaseName")

        # Check if user already exists (Atlas always uses admin database)
        if skipExisting and (user_name, "admin") in existing_users:
            logger.info("Skipping existing user: %s@admin", user_name)
            skipped_count += 1
            continue

        # Generate secure password
        password = generate_secure_password()

        # Transform roles to Atlas format
        atlas_roles: list[RoleDict] = transform_user_roles_to_atlas_format(
            user.get("roles", [])
        )

        # Create user payload
        # Atlas requires all users to be created on the admin database
        user_payload: UserDict = {
            "username": user_name,
            "password": password,
            "databaseName": "admin",  # Force admin database for Atlas
            "roles": atlas_roles,
        }

        try:
            response = create_atlas_database_user(
                atlasUrl, groupId, username, apikey, user_payload
            )

            if response.status_code == 201:
                logger.info("✓ Created user: %s@%s", user_name, db_name)

                # Verify the user was actually created
                try:
                    verify_users = fetch_atlas_database_users(
                        atlasUrl, groupId, username, apikey
                    )
                    user_exists = any(
                        u.get("username") == user_name
                        and u.get("databaseName") == "admin"
                        for u in verify_users
                    )
                    if user_exists:
                        created_count += 1

                        # Store credentials
                        user_credentials.append(
                            {
                                "username": user_name,
                                "databaseName": "admin",
                                "password": password,
                                "roles": atlas_roles,
                            }
                        )
                    else:
                        logger.error(
                            "⚠ User creation returned 201 but user not found in Atlas: %s@admin",
                            user_name,
                        )
                        logger.error("Response body: %s", response.text)
                        failed_count += 1
                except Exception as verify_error:
                    logger.warning(
                        "Could not verify user creation: %s", str(verify_error)
                    )
                    # Still count as created since we got 201
                    created_count += 1
                    user_credentials.append(
                        {
                            "username": user_name,
                            "databaseName": "admin",
                            "password": password,
                            "roles": atlas_roles,
                        }
                    )

            elif response.status_code == 409:
                logger.debug("User already exists: %s@admin", user_name)
                skipped_count += 1

            else:
                logger.error(
                    "Failed to create user %s@admin: %s %s",
                    user_name,
                    response.status_code,
                    response.text,
                )
                failed_count += 1

        except Exception as e:
            logger.error("Error creating user %s@admin: %s", user_name, str(e))
            failed_count += 1

    if created_count > 0 or failed_count > 0:
        logger.info(
            "     Database users: %d created, %d skipped, %d failed",
            created_count,
            skipped_count,
            failed_count,
        )

    return user_credentials
