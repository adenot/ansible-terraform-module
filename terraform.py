#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Allan Denot <adenot@gmail.com>
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
module: terraform
version_added: "1.9"
short_description: Create or delete a terraform stack
description:
  - Manages Terraform stacks and return state and output variables to Ansible
options:
  dir:
    description:
      - Directory where terraform configuration files are
    required: true
  terraform_bin:
    description:
      - Path to terraform binary (example: /usr/bin/terraform)
    required: false
    default: "terraform"
  vars:
    description:
      - A list of hashes of all variables for the stack
    required: false
    default: {}
  action:
    description:
      - Terraform command to execute. Use "apply" to create or update stack
        and "destroy" to delete stack.
    default: "apply"
    choices: [ "apply", "destroy" ]
    required: false

author:
  - Allan Denot (github.com/adenot)
  - John Heller  <john@heller.com.au>
'''

EXAMPLES = '''
# Basic example
- terraform:
    dir: "/path/to/terraform/stack"
    action: "apply"
    vars:
     var1: "value1"
  register: tfvars

- debug: var="{{tfvars.outputs}}"
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
            vars=dict(type='dict', required=False, default={}),
            action=dict(required=False, default="apply")
        )
    )
    module = AnsibleModule(
        argument_spec = argument_spec,
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
    terraform_action = module.params.get('action')
    vars = module.params.get('vars')

    if terraform_action == "destroy":
      terraform_command = "%s destroy -force" % terraform_bin
    else:
      terraform_command = "%s %s -input=false" % (terraform_bin, terraform_action)

    for var_key in vars:
      os.environ["TF_VAR_"+var_key] = vars[var_key]

    os.chdir(project_dir)

    startd = datetime.datetime.now()

    rc, out, err = module.run_command(terraform_command)

    endd = datetime.datetime.now()
    delta = endd - startd

    try:
        with open('terraform.tfstate') as data_file:    
            state = json.load(data_file)
    except:
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
        outputs  = state['modules'][0]['outputs'],
        resources= state['modules'][0]['resources']
    )

#<<INCLUDE_ANSIBLE_MODULE_COMMON>>
from ansible.module_utils.ec2 import *
main()
