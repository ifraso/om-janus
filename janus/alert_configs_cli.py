import copy
import json

import questionary
import requests
import typer
from requests.auth import HTTPDigestAuth
from typer_config import use_yaml_config

from janus.logging import logger
from janus.projects import fetch_projects

app = typer.Typer(help="Import/Export Alert Configs")


@app.command()
@use_yaml_config()  # TODO find a way to not load this if running with --help
def export(
    sourceUrl: str = typer.Option(
        ...,
        "--sourceUrl",
        help="Source Ops Manager URL e.g. https://opsmanager.example.com",
    ),
    sourceUsername: str = typer.Option(
        ..., "--sourceUsername", help="Source Ops Manager Username"
    ),
    sourceApiKey: str = typer.Option(
        ..., "--sourceApiKey", help="Source Ops Manager API Key"
    ),
    outputFile: str = typer.Option(
        ..., "--outputFile", help="Output file (can be used in import process)"
    ),
) -> None:
    """Export Alert Configs to the specified output file using an Organization Key. The process will first obtain all the Projects in the Organization and provide the user a choice of which Project to export the Alert Configs from."""
    source_verify_ssl = config.get("source", {}).get("verify_ssl", True)
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
        "Select projects to export Alert Configs from", choices=choices
    ).ask()

    source_verify_ssl = config.get("source", {}).get("verify_ssl", True)
    export_alert_configs(
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
        help="Destination Ops Manager URL e.g. https://opsmanager.example.com",
    ),
    destinationUsername: str = typer.Option(
        ..., "--destinationUsername", help="Destination Ops Manager Username"
    ),
    destinationApiKey: str = typer.Option(
        ..., "--destinationApiKey", help="Destination Ops Manager API Key"
    ),
    inputFile: str = typer.Option(
        ..., "--inputFile", help="Input file generated from the export process"
    ),
    detectAndSkipDuplicates: bool = typer.Option(
        True,
        "--detectAndSkipDuplicates",
        help="Detect already existing Alert Configs created on the destination project i.e. avoid creation of duplicate Alert Configs",
    ),
) -> None:
    """Import Alert Configs from the specified input file. The process will first obtain all the Projects in the destination Organization on the Destination Ops Manager and using this information, will allow the user to import Alert Configs into the same project (if it exists) or a different one"""
    import_alert_configs(
        inputFile,
        destinationUrl,
        destinationUsername,
        destinationApiKey,
        detectAndSkipDuplicates,
    )


def fetch_alert_configs(host, group, username, apikey, verify_ssl=True):
    response = requests.get(
        host + "/api/public/v1.0/groups/" + group + "/alertConfigs",
        auth=HTTPDigestAuth(username, apikey),
        verify=verify_ssl,
    )
    response.raise_for_status()
    alert_configs = response.json()
    logger.debug("Fetched Alert Configs ...")
    logger.debug(alert_configs)
    return alert_configs


def export_alert_configs(
    host, groups, groupNameDict, username, apikey, outputFile, verify_ssl=True
):
    output = []
    for group in groups:
        alert_configs = fetch_alert_configs(host, group, username, apikey, verify_ssl)
        element = {
            "project": {"id": group, "name": groupNameDict[group]},
            "alertConfigs": [],
        }
        element["alertConfigs"] = alert_configs["results"]
        output.append(element)

    json_object = json.dumps(output, indent=4)
    with open(outputFile, "w") as outfile:
        outfile.write(json_object)


def import_alert_configs(
    inputFile,
    destinationUrl,
    destinationUsername,
    destinationApikey,
    detectAndSkipDuplicates,
    continueOnError=True,
):
    with open(inputFile, "r") as openfile:
        import_data = json.load(openfile)

    destProjects = fetch_projects(
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

    for alert_config_import in import_data:
        logger.info(
            "Import Alert Configs for originally Project - %s (%s)",
            alert_config_import["project"]["name"],
            alert_config_import["project"]["id"],
        )

        if alert_config_import["project"]["id"] in destProjectIdNameDict:
            # destination project exists
            answer = questionary.select(
                "Found destination Project with same Id. Importing Alert Configs into same project?",
                instruction="Simply choose a different project",
                choices=choices,
                default=choicesDict[alert_config_import["project"]["id"]],
            ).ask()
        else:
            answer = questionary.select(
                "Destination Project with same Id not found. Select project to import Alert Configs to",
                choices=choices,
            ).ask()

        if answer == "Skip":
            logger.info(
                "Skipping import of Alert Configs for originally Project - %s (%s)",
                alert_config_import["project"]["name"],
                alert_config_import["project"]["id"],
            )
            continue

        __post_alert_configs(
            alert_config_import["alertConfigs"],
            destinationUrl,
            answer,
            destinationUsername,
            destinationApikey,
            detectAndSkipDuplicates,
            continueOnError,
        )


def __alert_configs_create_payload_from_export_payload(alert_configs):
    response = []

    for alert in alert_configs:
        new_alert = copy.deepcopy(alert)

        del new_alert["links"]
        del new_alert["id"]
        del new_alert["created"]
        del new_alert["updated"]
        del new_alert["groupId"]

        response.append(new_alert)

    return response


def __post_alert_configs(
    alert_configs,
    destinationUrl,
    destinationGroupId,
    destinationUsername,
    destinationApikey,
    skipDuplicates,
    continueOnError,
):
    migrated_alerts = 0
    skipped_alerts = 0
    failed_migrations = 0

    alert_configs_to_import = __alert_configs_create_payload_from_export_payload(
        alert_configs
    )

    if skipDuplicates:
        dest_verify_ssl = config.get("destination", {}).get("verify_ssl", True)
        currentDestinationAlertConfigs = fetch_alert_configs(
            destinationUrl,
            destinationGroupId,
            destinationUsername,
            destinationApikey,
            dest_verify_ssl,
        )
        current_alert_configs = __alert_configs_create_payload_from_export_payload(
            currentDestinationAlertConfigs["results"]
        )

    logger.info(
        "Attempting to import %d Alert Configs to %s with Project Id %s",
        len(alert_configs_to_import),
        destinationUrl,
        destinationGroupId,
    )
    for alert in alert_configs_to_import:
        if skipDuplicates:
            # first check for possible existance of rule
            for ac in current_alert_configs:
                if ac == alert:
                    logger.debug("Found duplicate Alert Config")
                    logger.debug("To Import : %s", alert)
                    logger.debug("Existing  : %s", ac)
                    break
            else:
                ac = None

            if ac is not None:
                skipped_alerts += 1
                continue

        url = (
            destinationUrl
            + "/api/public/v1.0/groups/"
            + destinationGroupId
            + "/alertConfigs/"
        )
        headers = {"Content-Type": "application/json"}
        logger.debug("===================================================")
        logger.debug("Posting Request to create new Alert Config ...")
        logger.debug("%s", json.dumps(alert))
        logger.debug("---------------")

        dest_verify_ssl = config.get("destination", {}).get("verify_ssl", True)
        response = requests.post(
            url,
            auth=HTTPDigestAuth(destinationUsername, destinationApikey),
            data=json.dumps(alert),
            headers=headers,
            verify=dest_verify_ssl,
        )
        logger.debug("Response ...")
        logger.debug("%s", vars(response))
        logger.debug("===================================================")

        if continueOnError and (response.status_code != requests.codes.created):
            logger.error(
                "Unable to create new Alert Config - %s %s"
                % (response.status_code, response.reason)
            )
            print("Failed migration alert JSON:")
            print(json.dumps(alert))
            failed_migrations += 1
        else:
            response.raise_for_status()
            migrated_alerts += 1
    logger.info(
        "Import Alert Configs to %s with Project Id %s Complete. Imported: %d, Skipped(duplicates): %d, Failed: %d"
        % (
            destinationUrl,
            destinationGroupId,
            migrated_alerts,
            skipped_alerts,
            failed_migrations,
        )
    )


### TOOD
### verify integrations - import failing due to missing webhook config
