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

import sys
import json
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver


class FirewallDB(object):
    def __init__(self):
        self.name = ""
        self.allowed = []
        self.network = ""
        self.source_ranges = []
        self.source_tags = None
        self.target_tags = []

    def __repr__(self):
        return 'name = ' + str(self.name) + \
               ' allowed = ' + str(self.allowed) + '\n'


def load_config_from_db(filename):
    json_data = None
    rules = []
    with open(filename) as data_file:
        json_data = json.load(data_file)

    for rulejson in json_data:
        rule = FirewallDB()
        rule.name = rulejson['name']
        rule.allowed = rulejson['allowed']
        rule.network = rulejson['network']

        if rulejson['source_ranges']:
            rule.source_ranges = rulejson['source_ranges']
        else:
            rule.source_ranges = None

        if rulejson['source_tags']:
            rule.source_tags = rulejson['source_tags']
        else:
            rule.source_tags = None

        if rulejson['target_tags']:
            rule.target_tags = rulejson['target_tags']
        else:
            rule.target_tags = None

        rules.append(rule)

    return rules


def load_rules_from_gcp(driver):
    gcp_firewall_rules = driver.ex_list_firewalls()
    return gcp_firewall_rules


def add_firewall_rules(driver, rules):
    for rule in rules:
        name = rule.name
        allowed = rule.allowed
        network = rule.network
        source_ranges = rule.source_ranges
        source_tags = rule.source_tags
        target_tags = rule.target_tags
        try:
            new_rule = driver.ex_create_firewall(
                name,
                allowed,
                network,
                source_ranges,
                source_tags,
                target_tags)
            print 'Rule succesfully added', str(new_rule.id), \
                str(new_rule.name), str(new_rule.network.name)
        except:
            print >> sys.stderr, 'Failed to add', str(name), \
                str(network), str(target_tags)


def remove_firewall_rules(driver, rules):
    for rule in rules:
        try:
            driver.ex_destroy_firewall(rule)
            print 'Rule succesfully removed', str(rule.id), \
                str(rule.name), str(rule.network.name)
        except:
            print >> sys.stderr, 'Failed to remove', str(rule.id), \
                str(rule.name), str(rule.network.name)


def update_firewall_rules(driver, rules):
    for gcp_rule, rule in rules:
        try:
            gcp_rule.allowed = rule.allowed
            gcp_rule.source_ranges = rule.source_ranges
            gcp_rule.source_tags = rule.source_tags
            gcp_rule.target_tags = rule.target_tags
            driver.ex_update_firewall(gcp_rule)
            print 'Rule succesfully updated', str(gcp_rule.id), \
                str(gcp_rule.name), str(gcp_rule.network.name)
        except:
            print >> sys.stderr, 'Failed to update', str(gcp_rule.id), \
                str(gcp_rule.name), str(gcp_rule.network.name)


def compare_rules(a, b):
    return (a.name == b.name and a.network == b.network.name)


def compare_rule_settings(a, b):
    return (a.allowed == b.allowed and
            a.source_ranges == b.source_ranges and
            a.source_tags == b.source_tags and
            a.target_tags == b.target_tags)


def diff_rules(db_rules, gcp_firewall_rules):
    rules_to_remove = []
    rules_to_add = []
    rules_to_update = []
    for gcp_firewall_rule in gcp_firewall_rules:
        match = False
        for db_rule in db_rules:
            if compare_rules(db_rule, gcp_firewall_rule):
                match = True
                break

        if not match:
            rules_to_remove.append(gcp_firewall_rule)

    for db_rule in db_rules:
        match = False
        for gcp_firewall_rule in gcp_firewall_rules:
            if compare_rules(db_rule, gcp_firewall_rule):
                if not compare_rule_settings(db_rule, gcp_firewall_rule):
                    rules_to_update.append((gcp_firewall_rule, db_rule))
                match = True
                break

        if not match:
            rules_to_add.append(db_rule)

    return rules_to_add, rules_to_update, rules_to_remove


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

    # go through the project list and push firewall rules
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

        db_firewall_rules = load_config_from_db(db_filename)
        gcp_firewall_rules = load_rules_from_gcp(driver)

        rules_to_add, rules_to_update, rules_to_remove = diff_rules(
            db_firewall_rules,
            gcp_firewall_rules)

        print 'rules to add for project ' + project_name
        print rules_to_add
        print 'rules to update for project ' + project_name
        print rules_to_update
        print 'rules to remove for project ' + project_name
        print rules_to_remove

        remove_firewall_rules(driver, rules_to_remove)
        add_firewall_rules(driver, rules_to_add)
        update_firewall_rules(driver, rules_to_update)

    sys.exit(0)


if __name__ == '__main__':
    main()
