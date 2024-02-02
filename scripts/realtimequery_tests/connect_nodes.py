from fabric import Connection
from invoke.exceptions import UnexpectedExit
import re
import json
import time
from api_func import *


class Host:
    def __init__(self, host, user, sudo_password, password):
        self.host = host
        self.user = user
        self.sudo_password = sudo_password
        self.password = password
        self.conn = self.get_connection()
        

    def get_connection(self):
            if self.password:
                return Connection(host=self.host, user=self.user, connect_kwargs={'password': self.password})
            else:
                return Connection(host=self.host, user=self.user)
        
    def check_connection(self):
        try:
            self.conn.create_session()
        except:
            return False
        return True

    def execute_command(self, cmd):
        try:
            result = self.conn.run(cmd, hide='both')
            return (result.stdout)
        except UnexpectedExit as e:
            print(e)
            if not re.search("Exit code: 1\n", str(e)):
                raise
        

    # def execute_command_through_api(self, cmd, timeout=120):
    #     url = "http://%s:%s/issue" % (self.host, PORT)
    #     req = {"cmd": cmd}
    #     resp = requests.post(url, json=req, timeout=timeout)
    #     return resp.json()

    def execute_sudo_command(self, cmd):
        res = self.conn.sudo(cmd, password=self.sudo_password, hide='stderr')
        return (res.stdout)
     


if __name__ == "__main__":
    h = Host('protectum-pnode11a', 'areddy', '', '')
    print(h.execute_command('uptime -p'))

