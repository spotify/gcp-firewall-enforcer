
# GCP Firewall Enforcer

A toolbox to enforce firewall rules across multiple GCP projects.

The package is comprised of the following:

 * `gcp_firewall_enforcer`: which is the main tool used to enforce firewall rules
 * `gcp_rule_parser`: a helper to retrieve the current rules set from GCP projects

`gcp-firewall-enforcer` is currently in alpha status.
We are actively improving it and Spotify's production environment is our
current test suite.

## Installation

Run `pip install git+https://github.com/spotify/gcp-firewall-enforcer.git`.


## Prerequisites

Supported Python versions: 2.7+

## Development

To contribute and develop, clone the project inside a virtualenv and install
all the dependencies with `pip install -r requirements.txt`.

## Usage

First you need to [generate a json key](https://support.google.com/cloud/answer/6158862)
via the GCP console for every project.

Save the file somewhere the scripts can read it, for example:

```
$ mkdir -p /etc/gcloud/keys
$ mv your-gcp-keyfile.json /etc/gcloud/keys/
```

Next you need to build a master config file.
The master config is first  used by `gcp_rule_parser` to retrieve the project's firewall rules
and build a local database, and then by `gcp_firewall_enforcer` to push/enforce the local firewall databases.

The config file structure is the following:

```
[
 {
     "project_name" : "GCP Project Name",
     "project" : "gcp-project-name-12345",
     "firewall_db" : "/absolute/path/to/gcp-project-name-firewall-db.json",
     "keyfile" : "/absolute/path/to/gcp-project-name-keyfile-12345.json"
 },
 {
     "project_name" : "GCP Project Name #2",
     "project" : "second-gcp-project-name-54321",
     "firewall_db" : "/absolute/path/to/second-gcp-project-name-firewall-db.json",
     "keyfile" : "/absolute/path/to/second-gcp-project-name-keyfile-54321.json"
 }
]
```

The meaning of the fields in the json blob are the following:

-   `project_name`: the descriptive name we used for the
    project
-   `project`: internal GCP name (the one you see in the
    URL, for example `gcp-project-name-12345`)
-   `firewall_db`: the absolute path to the json that
    contains all the firewall rules, this is where
    `gcp_rule_parser` write the rules and
    `gcp_firewall_enforcer` reads them
-   `keyfile`: the absolute path to the json file that
    contains the GCP service key

Once you've properly compiled the master config file, you can use
`gcp_rule_parser` to pull the rules, for example:

```
$ gcp_rule_parser config.json
```

This will create a json files containing all the firewall rules in the
location specified by `firewall_db`.

Finally you can start enforcing the rules through
`gcp_firewall_enforcer`. The script will delete all rules
that are not in the database.

```
$ gcp_firewall_enforcer config.json
```

The script is intended to be run as a cron job.

## Code of Conduct
This project adheres to the [Open Code of Conduct][code-of-conduct].
By participating, you are expected to honor this code.

[code-of-conduct]: https://github.com/spotify/code-of-conduct/blob/master/code-of-conduct.md
