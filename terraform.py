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

import os
import datetime

def main():
    module = AnsibleModule(
        argument_spec = dict(
            dir=dict(required=True, default=None),
            terraform_bin=dict(required=False, default="terraform"),
            vars=dict(type='dict', required=False, default={}),
            action=dict(required=False, default="apply")
        ),
        supports_check_mode=False
    )
    project_dir = module.params.get('dir')
    terraform_bin = module.params.get('terraform_bin')
    terraform_action = module.params.get('action')
    vars = module.params.get('vars')

    if terraform_action == "destroy":
      terraform_command = "%s destroy -force" % terraform_bin
    else:
      terraform_command = "%s apply -input=false" % terraform_bin

    for var_key in vars:
      os.environ["TF_VAR_"+var_key] = vars[var_key]

    os.chdir(project_dir)

    startd = datetime.datetime.now()

    rc, out, err = module.run_command(terraform_command)

    endd = datetime.datetime.now()
    delta = endd - startd

    with open('terraform.tfstate') as data_file:    
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
main()
