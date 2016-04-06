#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, John Heller <john@heller.com.au>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: terraform_remote_state
version_added: "1.0"
short_description: Configure remote state for terraform
description:
     - Configure remote state for terraform
options:
  dir:
    description:
      - Directory containing the terraform stack
    required: true
    default: null
  terraform_bin:
    description:
      - Command to run terraform binary
    required: false
    default: 'terraform'
  backend:
    description:
      - Remote state backend type
    required: true
    default: null
    choices: ["artifactory", "atlas", "consul", "etcd", "http", "s3", "swift"]
  backend_config:
    description:
      - a dict of -backend-config parameters for 'terraform remote config'
    required: true
    default: null
author: "John Heller <john@heller.com.au>"
'''
import os
import datetime
try:
    import boto
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            dir=dict(required=True, default=None),
            terraform_bin=dict(required=False, default="terraform"),
            backend=dict(required=True, default=None),
            backend_config=dict(type='dict', required=False, default={})
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)

    # Put any passed access credentials into environment variables for terraform
    os.environ["AWS_ACCESS_KEY_ID"]     = aws_connect_kwargs['aws_access_key_id']
    os.environ["AWS_SECRET_ACCESS_KEY"] = aws_connect_kwargs['aws_secret_access_key']
    os.environ["AWS_SESSION_TOKEN"]     = aws_connect_kwargs['security_token']

    project_dir = module.params.get('dir')
    terraform_bin = module.params.get('terraform_bin')
    backend = module.params.get('backend')
    backend_config = module.params.get('backend_config')

    terraform_command = "%s remote config -backend=%s " % (terraform_bin, backend)
    
    for key in backend_config:
        terraform_command = "%s -backend-config=\"%s=%s\"" % (terraform_command, key, backend_config[key])

    os.chdir(project_dir)

    startd = datetime.datetime.now()

    rc, out, err = module.run_command(terraform_command)

    endd = datetime.datetime.now()
    delta = endd - startd

    with open('.terraform/terraform.tfstate') as data_file:    
        state = json.load(data_file)

    if out is None:
        out = ''
    if err is None:
        err = ''

    module.exit_json(
        stdout   = out.rstrip("\r\n"),
        stderr   = err.rstrip("\r\n"),
        rc       = rc,
        start    = str(startd),
        end      = str(endd),
        delta    = str(delta),
        changed  = True,
        remote   = state['remote'],
        outputs  = state['modules'][0]['outputs'],
        resources= state['modules'][0]['resources']
    )

#<<INCLUDE_ANSIBLE_MODULE_COMMON>>
from ansible.module_utils.ec2 import *
main()
