#!/usr/bin/python

# Copyright: (c) 2020, Victor Santiago <vsantiago113sec@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: github_download_files

short_description: Download individual files from a repo.

version_added: "0.1"

description:
    - "The module connect to a repo and download individual files. We created this module to be able to download config
    files from an organization repo where we store all config files from all our systems like ntp servers, smtp servers
    , global configs and more."

options:
    base_url:
        description:
            -  If you are using the Enterprise version on a custom domain for example: https://github.example.com
        required: false
    access_token:
        description:
            - Your API access token, you get this from your Gitbub account.
        required: true
    verify:
        description:
            - This is used if you are using the enterprise version for example and you don't want to verfy the ssl cert.
        required: false
    organization:
        description:
            - If want to connect to an organization instead of your user where your repos are located.
        required: false
    repo:
        description:
            - The repository.
        required: true
    files:
        description:
            - list of files to download, you can pass the remote file and local filename path separeted by comma.
        required: true

extends_documentation_fragment:
    - source_control

author:
    - Victor Santiago (@vsantiago113)
'''

EXAMPLES = '''
- name: Download config file from Github
  github_download_files:
    access_token: 1234567890asdfghjkqwertyuiopmnbvcxz
    repo: AnsibleModules
    files:
      - README.md
      
- name: Download config file from Github
  github_download_files:
    access_token: 1234567890asdfghjkqwertyuiopmnbvcxz
    repo: AnsibleModules
    files:
      - README.md, /tmp/README.md

- name: Download config file from Github
  github_download_files:
    base_url: https://github.mechanize.com
    access_token: 1234567890asdfghjkqwertyuiopmnbvcxz
    verify: False
    organization: NetOps
    repo: Configurations
    files:
      - configs/global_smtp_servers.yml
      
- name: Download config file from Github
  github_download_files:
    base_url: https://github.mechanize.com
    access_token: 1234567890asdfghjkqwertyuiopmnbvcxz
    verify: False
    organization: NetOps
    repo: Configurations
    files:
      - configs/global_smtp_servers.yml, smtp.yaml
'''

RETURN = '''
message:
    description: Returns the list of files you downloaded.
    type: list
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule

from github import Github
import requests
import urllib3

# This is going to disable all request warnings.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def run_module():
    module_args = dict(
        base_url=dict(type='str', required=False),
        access_token=dict(type='str', required=True, no_log=True),
        verify=dict(type='bool', required=False, default=True),
        organization=dict(type='str', required=False),
        repo=dict(type='str', required=True),
        files=dict(type='list', required=True)
    )

    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    if module.check_mode:
        module.exit_json(**result)

    try:
        if module.params['base_url']:
            g = Github(base_url=f'{module.params["base_url"]}/api/v3', login_or_token=module.params['access_token'],
                       verify=module.params['verify'])
        else:
            g = Github(login_or_token=module.params['access_token'], verify=module.params['verify'])

        if module.params['organization']:
            handle = g.get_organization(module.params['organization'])
        else:
            handle = g

        repo = handle.get_repo(module.params['repo'])
        for file_path in module.params['files']:
            file_path = [x.strip() for x in file_path.split(',')]
            if len(file_path) == 2:
                file_path, filename = file_path
            elif len(file_path) == 1:
                filename = file_path[0].split('/')[-1]
                file_path = file_path[0]

            file = repo.get_contents(file_path)

        with requests.get(file.download_url, stream=True, verify=module.params['verify']) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except Exception as error:
        module.fail_json(msg=str(error), **result)
    else:
        result['changed'] = True
        result['message'] = module.params['files']

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
