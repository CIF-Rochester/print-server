from typing import Any, Dict

import toml

'''
Sample config:

```toml
# How to authenticate users. 'ldap' to talk to an LDAP server, or 'test' for
# DB test users.
auth_mode = 'ldap'
secret_key = 'RANDOM_STRING'

[printing]
max_copies = 5
printer_bw = 'black and white printer device name'
printer_color = 'color printer device name'

[ldap]
host = 'ldap://ldap.host.com'
base_dn = 'cn=baseDnForUsers,dn=ldap,dn=host,dn=com'
```
'''

def require_field(config: Dict, location: str, key: str, message='') -> Any:
  if key not in config:
    raise ValueError(f'{location} is missing a required field: {key}. {message}')
  return config[key]

class PrintingConfig:
  max_copies: int
  printer_bw: str
  printer_color: str

  def __init__(self, printing_config: Dict) -> None:
    self.max_copies = require_field(printing_config, 'config.toml#printing', 'max_copies')
    self.printer_bw = require_field(printing_config, 'config.toml#printing', 'printer_bw')
    self.printer_color = require_field(printing_config, 'config.toml#printing', 'printer_color')

class LDAPConfig:
  host: str
  base_dn: str

  def __init__(self, ldap_config: Dict) -> None:
    self.host = require_field(ldap_config, 'config.toml#ldap', 'host')
    self.base_dn = require_field(ldap_config, 'config.toml#ldap', 'base_dn')

class Config:
  auth_mode: str
  secret_key: str
  printing: PrintingConfig
  ldap: LDAPConfig

  def __init__(self, config: Dict) -> None:
    self.auth_mode = require_field(config, 'config.toml', 'auth_mode')
    if self.auth_mode not in ['test', 'ldap']:
      raise ValueError(f'config.toml#auth_mode specifies an invalid value "{self.auth_mode}", expected one of "test", "ldap"')

    self.secret_key = require_field(config, 'config.toml', 'secret_key')
    
    self.printing = PrintingConfig(require_field(config, 'config.toml', 'printing'))

    if self.auth_mode == 'ldap':
      self.ldap = LDAPConfig(require_field(config, 'config.toml', 'ldap', message='This field is required because auth_mode is set to \'ldap\'.'))

global_config: Config = None

def get_config() -> Config:
  '''
  Read and validate the config stored in `config.toml`. Caches the results to
  only read the file once.

  '''

  global global_config

  if global_config is None:
    config_data = toml.load('config.toml')
    global_config = Config(config_data)

  return global_config
