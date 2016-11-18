# **This directory contains an Ansible playbook that will deploy a alerting, telemetry and correlation monitoring solution.**

## CONTRIBUTING


1. Fork it.
2. Create your feature branch (`git checkout -b my-new-feature`).
3. Commit your changes (`git commit -am 'Add some feature'`).
4. Push to the branch (`git push origin my-new-feature`).
5. Create new Pull Request.


Overview
--------

This demo leverages the Cumulus [reference topology](https://github.com/cumulusnetworks/cldemo-vagrant). In order to use this demo, follow these high level steps:
1. install Vagrant and Virtualbox/Libvirt on the host
2. Clone the reference topology
3. Launch the reference topology using vagrant
4. SSH into the oob-mgmt-server
5. Clone the [monitoring-project repo](https://github.com/CumulusNetworks/monitoring-project)
6. Run the demo using run-demo.yml

This demo requires the network to be provisioned. Without the networking being provisioned, it will not provide reliable output.

## Tools and Terminology
------------------------
Telegraf - An agent that runs on the switches that exports data to InfluxDB
InfluxDB - A timeseries database that stores the data using tags and values. Uses a flexible schema and SQL-like query language.
Grafana - A Graphical dashboard that integrates with multiple databases. A live demo can be seen here http://play.grafana.org/ Also a great way to figure out queries.

Quickstart: Run the demo
------------------------
(This works best with Ansible 2.1.0.0 and Vagrant 1.8.4 on your host.)

# Create the virtual network:
    git clone https://github.com/cumulusnetworks/cldemo-vagrant
    cd cldemo-vagrant
    vagrant up oob-mgmt-server oob-mgmt-switch leaf01 leaf02 leaf03 leaf04 spine01 spine02 server01 server02 server03 server04
    vagrant ssh oob-mgmt-server
    sudo su - cumulus
### (OPTIONAL) Setting up the base network. This monitoring demo requires the network to be provisioned to pass traffic. The following repo will provision the network to pass traffic:
    git clone https://github.com/CumulusNetworks/cldemo-automation-ansible.git
    cd cldemo-automation-ansible
    ansible-playbook run-demo.yml
# Provision the network with the monitoring solution
    git clone https://github.com/cumulusnetworks/monitoring-project
    cd monitoring-project
    ansible-playbook run-demo.yml
### (OPTIONAL)
# Getting to the Dashboard:
    With VirtualBox or Vagrant, forward port 3000 on the NAT enabled NIC for the Grafana dashboard. Also port forward 8083 for the influxDB dashboard and 8086 for the influxDB API if you plan on accessing influxDB with the browser.
    Open a web browser on your local machine, navigate to http://localhost:3000 . Once logged in, click on the grafana logo in the top right of the browser. Navigate the drop down menu to dashboards, then import.

## Detailed Steps to Install
Clone the cldemo-vagrant repo and launch a reference topology simulation.

The cldemo-vagrant demo will require Vagrant, Virtualbox and Ansible.

Set up the network to pass traffic. This can be done easily by cloning the cldemo-automation-ansible repo, changing to the full-reference-topology branch and running the playbook to provision BGP unnumbered throughout the network.

Clone the health-monitoring-checks repo and change to the influx-grafana branch. Run the playbook in the cldemo directory to provision the following things:
1 Installs InfluxDB on the oob-mgmt-server
1a Creates new database on InfluxDB
2 Installs Grafana on the oob-mgmt-server
2a Creates an API key for Grafana to leverage HTTP API
2b Adds InfluxDB as a datasource
2c Uploads dashboard to Grafana
3 Installs Telegraf and all leafs and spines and copies over all the checks.
3a Configures Telegraf to run all the scripts and upload data to InfluxDB
To access the Grafana GUI, set up port forwarding on VirtualBox so that port 3000 is accessible.
![Vagrant](Vagrant.png)

The Vagrantfile can be edit as an alternative to changing port forwarding in VirtualBox via teh GUI. This edit takes place under the oob-mgmt-server settings:
    # link for eth1 --> oob-mgmt-switch:swp1
    device.vm.network "private_network", virtualbox__intnet: "#{wbid}_net54", auto_config: false , :mac => "44383900005f"
    device.vm.network "forwarded_port", guest: 3000, host:3000
    device.vm.network "forwarded_port", guest: 8083, host:8083
    device.vm.network "forwarded_port", guest: 8086, host:8086


Once the playbook has run, access the Grafana homepage on http://localhost:3000
This should return the following page:
![GrafanaLogin](GrafanaLogin.png)


The username and password are admin/admin

Uploading Custom Dashboard
--------------------------
Any dashboards can be manually imported after Grafana and Influxdb are installed. This is useful to exporting and importing dashboards from other sources. Be aware to properly populate the "datasource" field in the dashboard.json file being imported.


To import another custom dashboard, use the following steps:
![GrafanaDashboard](GrafanaDashboard.png)

![GrafanaImport](GrafanaImport.png)


## License and Authors

* Author:: Cumulus Networks Inc.

* Copyright:: 2015 Cumulus Networks Inc.

Licensed under the MIT License.

---

![Cumulus icon](http://cumulusnetworks.com/static/cumulus/img/logo_2014.png)

### Cumulus Linux

Cumulus Linux is a software distribution that runs on top of industry standard
networking hardware. It enables the latest Linux applications and automation
tools on networking gear while delivering new levels of innovation and
ﬂexibility to the data center.

For further details please see:
[cumulusnetworks.com](http://www.cumulusnetworks.com)

