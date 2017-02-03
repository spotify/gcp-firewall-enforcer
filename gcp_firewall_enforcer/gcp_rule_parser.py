#!/usr/bin/env python

# Copyright (c) 2016-2017 Spotify AB.
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import json
import sys
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver


def convert_to_list(rules, filename):
    keep_keys = ['name', 'allowed', 'source_ranges',
                 'source_tags', 'target_tags']
    fwlist = []
    for rule in rules:
        fw = {}
        fw['network'] = rule.network.name
        for key in keep_keys:
            fw[key] = getattr(rule, key)
        fwlist.append(fw)

    return fwlist


def main():
    key_values = ['project', 'firewall_db', 'keyfile']
    if(len(sys.argv) != 2):
        sys.exit(1)

    # parse config.json
    config_file = sys.argv[1]
    config_content = json.load(open(config_file))
    projects = []

    for value in config_content:
        temp = []
        for key in key_values:
            temp.append(value[key])
        projects.append(temp)

    for project in projects:
        project_name = project[0]
        db_filename = project[1]
        key_file = project[2]
        key_content = json.load(open(key_file))

        ComputeEngine = get_driver(Provider.GCE)
        driver = ComputeEngine(
            key_content['client_email'],
            key_file,
            project=project_name)
        gcp_firewall_rules = driver.ex_list_firewalls()
        firewall_list = convert_to_list(gcp_firewall_rules, db_filename)

        with open(db_filename, 'w') as f:
            json.dump(firewall_list, f, indent=2)
    sys.exit(0)


if __name__ == '__main__':
    main()
