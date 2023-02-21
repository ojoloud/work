""" Script to modify network configuration """
import re
import sys
import time
import subprocess

EXCLUDE_LIST = ["Admin State",
                "State",
                "Type",
                "Interface Name",
                "-------------------------------------------------------------------------"]


def execute_command(command: str):
    """ Method to execute any command """
    if command is None:
        raise ValueError("Command needs to be specified")
    code, res = subprocess.getstatusoutput(command)
    if code:
        raise Exception(f"command failed to execute with error code {code} and error message {res}")
    return res


def execute_netsh_show_command() -> list:
    """ netsh command executor, reporting interface status """
    run_command = 'netsh interface show interface'
    res_per_interface = {}
    res = []
    cleared_res = []
    res_raw = execute_command(run_command).strip()
    if res_raw:
        for token in re.split(r"\s{3,20}|\n", res_raw):
            if token in EXCLUDE_LIST:
                continue
            cleared_res.append(token)
        while len(cleared_res) > 0:
            res_per_interface["name"] = cleared_res.pop()
            res_per_interface["type"] = cleared_res.pop()
            res_per_interface["state"] = cleared_res.pop()
            status = cleared_res.pop()
            if status.lower() == 'disabled':
                res_per_interface["status"] = False
            else:
                res_per_interface["status"] = True

            res.append(res_per_interface)
            res_per_interface = {}

    return res


def execute_netsh_update_command(name: str, enable: bool):
    """execute netsh command to enable/disable interface"""
    if name is None:
        raise Exception("Valid interface name required")
    if len(name) == 0:
        raise Exception("Valid interface name required")
    if enable:
        run_command = f'netsh interface set interface "{name}" enabled'
    else:
        run_command = f'netsh interface set interface "{name}" disabled'
    res_raw = execute_command(run_command)
    if res_raw:
        raise Exception(f'Execution encountered an error {res_raw}')


def print_help():
    """ Print help message"""
    print('required command line parameters')
    print('Usage:\n\n ' + sys.argv[0] + '\t-s | -n | -r\n')


def main(args):
    """ main method that performs required test options"""
    # return True if at least one network adapter is enabled
    # return Index and Name of all enabled adapters
    # disables enabled adapters
    # enables back previously disabled adapters

    if len(args) < 1:
        print_help()
        sys.exit()
    if '-s' in args:
        res = execute_netsh_show_command()
        if not res:
            raise Exception('No interfaces returned')
        for interface in res:
            if interface["status"]:
                print(f'At least one network adapter enabled: {True}')
                break
    elif '-n' in args:
        print('\tINDEX , \tNAME\n')
        print('___________________')
        res = execute_netsh_show_command()
        for i in range(0, len(res)):
            if res[i]["status"]:
                print(f'\t{i}\t{res[i]["name"]}')
    elif '-r' in args:
        res = execute_netsh_show_command()
        interface_to_enable = []
        for interface in res:
            if interface["status"]:
                execute_netsh_update_command(interface["name"], False)
                interface_to_enable.append(interface["name"])

        time.sleep(20)
        # print intermittent result to verify that all adapters disabled
        interim_res = execute_netsh_show_command()
        print('\tNAME\tSTATUS')
        print('_________________________')
        for interface in interim_res:
            print(f'\t{interface["name"]}\t{interface["status"]}\n')

        for disabled_interface in interface_to_enable:
            execute_netsh_update_command(disabled_interface, True)

        interim_res = execute_netsh_show_command()

        # print intermittent result to verify that all adapters enabled
        print('\tNAME\tSTATUS')
        print('_________________________')
        for interface in interim_res:
            print(f'\t{interface["name"]}\t{interface["status"]}\n')

    else:
        print_help()
        sys.exit()


if __name__ == '__main__':
    main(sys.argv[1:])
