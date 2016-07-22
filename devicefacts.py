#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Cisco Clerk

Attributes:
    HOSTNAME_REGEX (str):
      Regex to extract the device hostname.

      Matches: HOSTNAME#sh version

      Assumes the `show version` command is used in the `show` command files,
      and the hostname is the name before the # symbol.

    SERIAL_NUMBER_REGEX (str):
      Regex to extract the device serial number.

      Matches: System serial number            : ABC2016XYZ

    MODEL_SW_PATTERN (str):
      Regex to extract device model number, software version and software image.

      Matches: WS-C2960C-8PC-L    15.0(2)SE5            C2960c405-UNIVERSALK9-M
      Matches: WS-C3650-24TD      03.03.03SE        cat3k_caa-universalk9 INSTALL
"""

import os
import re
import json
from collections import namedtuple


SERIAL_NUMBER_REGEX = re.compile(
        r"""
        [Ss]ystem\s+[Ss]erial\s+[Nn]umber # system serial number pattern
        \s+:\s                            # separator
        (?P<sys_ser_num>[\w]+)            # capture serial number group
        """,
        re.VERBOSE)
MODEL_AND_SOFTWARE_REGEX = re.compile(
        r"""
        (?P<model_num>[\w-]+)               # capture model number group
        \s+                                 # separator
        (?P<sw_ver>\d{2}\.[\w\.)?(?]+)      # capture software version group
        \s+                                 # separator
        (?P<sw_image>\w+[-|_][\w-]+\-[\w]+) # capture software image group
        """,
        re.VERBOSE)



class Device:

    def __init__(self, show_file):
        self._source_file = show_file
        self._show_file_content = open(show_file).read()
        self._hn_sh_ver_regex = re.compile(
                r"(?P<hostname>\S+)\#sh[ow\s]+ver.*", re.IGNORECASE)
        self._hn_sh_inv_regex = re.compile(
                r"(?P<hostname>\S+)\#sh[ow\s]+inv.*", re.IGNORECASE)
        self._hn_sh_run_regex = re.compile(
                r"(?P<hostname>\S+)\#sh[ow\s]+run.*", re.IGNORECASE)
        self._hn_hn_regex = re.compile(
                r"hostname\s(?P<hostname>.*)", re.IGNORECASE)

    def source(self):
        return self._source_file

    def hostname(self):
        """
        Fetches device hostname.

        Args:
            fin (str): Cisco `show` file

        Returns:
            hostname (tuple(str)): Device Hostname

        Example:
        """
        hn_switch = {
            "hn_ver":
            self._hn_sh_ver_regex.search(self._show_file_content),
            "hn_inv":
            self._hn_sh_inv_regex.search(self._show_file_content),
            "hn_run":
            self._hn_sh_run_regex.search(self._show_file_content),
            "hn_hn":
            self._hn_hn_regex.search(self._show_file_content),
        }
        if hn_switch.get("hn_hn") != None:
            return hn_switch.get("hn_hn").group("hostname")
        elif hn_switch.get("hn_ver") != None:
            return hn_switch.get("hn_ver").group("hostname")
        elif hn_switch.get("hn_inv") != None:
            return hn_switch.get("hn_inv").group("hostname")
        elif hn_switch.get("hn_run") != None:
            return hn_switch.get("hn_run").group("hostname")
        else:
            return "No Hostname Found"
    def serial_numbers(self):
        """
        Fetches device serial number(s)

        Args:
            fin (str): Cisco show file

        Returns:
            serial_numbers (tuple(str)): Device Serial Numbers

        Example:
        """
        sn_matches = re.findall(SERIAL_NUMBER_REGEX, self._show_file_content)
        # Use a list comprehension rather than a set as we need to keep the order
        # the serial numbers are found in so we can accurately match them to
        # the correct hostname
        sn_list = []
        [sn_list.append(item) for item in sn_matches if item not in sn_list]
        return sn_list


    def _model_and_software_info(self):
        """
        Fetches model number, software version and software image.

        Args:
            fin (str): Cisco show file.

        Returns:
            model_and_software (tuple(tuple(str))): Device model number, software version and software image

        Example:
        """
        number_of_devices = len(self.serial_numbers())
        total_matches = re.findall(MODEL_AND_SOFTWARE_REGEX, self._show_file_content)
        return total_matches[:number_of_devices]


    def model_numbers(self):
        model_and_software_info = self._model_and_software_info()
        mns = [item[0] for item in model_and_software_info]
        return list(set(mns))


    def software_versions(self):
        model_and_software_info = self._model_and_software_info()
        svs = [item[1] for item in model_and_software_info]
        return list(set((svs)))


    def software_images(self):
        model_and_software_info = self._model_and_software_info()
        sis = [item[2] for item in model_and_software_info]
        return (list(set(sis)))


def collate(directory):
    """
    Creates a list of named tuples. Each named tuple contains the
    hostname, serial number, model number, software version and
    software image for each device within the `show` files
    within the given directory.

    Args:
        directory (str): Directory containing the Cisco show files

    Returns:
        devices (tuple(Device(str))): tuple of named tuples containing device attributes

    Example:
        >>> collate('./test_data')
        (Device(hostname='elizabeth_cotton', serial_number='ANC1111A1AB', model_number='WS-C2960C-8PC-L', software_version='15.0(2)SE5', software_image='C2960c405-UNIVERSALK9-M'), Device(hostname='howlin_wolf', serial_number='ABC2222A2AB', model_number='WS-C2960C-8PC-L', software_version='15.0(2)SE5', software_image='C2960c405-UNIVERSALK9-M'), Device(hostname='lightning_hopkins', serial_number='ABC3333A33A', model_number='WS-C2960X-48FPD-L', software_version='15.0(2)EX5', software_image='C2960X-UNIVERSALK9-M'), Device(hostname='lightning_hopkins', serial_number='ABC4444A44A', model_number='WS-C2960X-48FPD-L', software_version='15.0(2)EX5', software_image='C2960X-UNIVERSALK9-M'), Device(hostname='lightning_hopkins', serial_number='ABC5555A555', model_number='WS-C2960X-24PD-L', software_version='15.0(2)EX5', software_image='C2960X-UNIVERSALK9-M'), Device(hostname='sister_rosetta_tharpe', serial_number='ABC6666A6AB', model_number='WS-C3650-24TD', software_version='03.03.03SE', software_image='cat3k_caa-universalk9'))
    """
    device_list = []
    Device = namedtuple('Device',
                        '''hostname
                           serial_number
                           model_number
                           software_version
                           software_image''')
    for fin in sorted(os.listdir(directory)):
        with open(os.path.join(directory, fin)) as show_f:
            content = show_f.read()
            hostname = fetch_hostname(content)
            serial_numbers = fetch_serial_nums(content)
            model_sw_result = fetch_model_sw(content)
            i = 0
            while i < len(serial_numbers):
                device_list.append(
                    Device(
                        hostname[0],
                        serial_numbers[i],
                        model_sw_result[i][0],
                        model_sw_result[i][1],
                        model_sw_result[i][2]))
                i += 1
    devices = tuple(device_list)
    return devices


def csv_inventory(collated_records):
    """
    Creates a CSV formatted string containing Cisco device attributes from
    a given list of named tuples.

    Args:
        collated_records (iter(Device(str))): iterable of named tuples.

    Returns:
        output (str): CSV formatted string

    Example:
        >>> csv_inventory(collate('./test_data'))
        'hostname,serial_number,model_number,software_version,software_image\\nelizabeth_cotton,ANC1111A1AB,WS-C2960C-8PC-L,15.0(2)SE5,C2960c405-UNIVERSALK9-M\\nhowlin_wolf,ABC2222A2AB,WS-C2960C-8PC-L,15.0(2)SE5,C2960c405-UNIVERSALK9-M\\nlightning_hopkins,ABC3333A33A,WS-C2960X-48FPD-L,15.0(2)EX5,C2960X-UNIVERSALK9-M\\nlightning_hopkins,ABC4444A44A,WS-C2960X-48FPD-L,15.0(2)EX5,C2960X-UNIVERSALK9-M\\nlightning_hopkins,ABC5555A555,WS-C2960X-24PD-L,15.0(2)EX5,C2960X-UNIVERSALK9-M\\nsister_rosetta_tharpe,ABC6666A6AB,WS-C3650-24TD,03.03.03SE,cat3k_caa-universalk9'
    """
    headers = ','.join(list(collated_records[0]._fields))
    rows = [','.join(list(record)) for record in collated_records]
    content = '{0}\n{1}'.format(headers, '\n'.join(rows))
    return content


def json_inventory(collated_records):
    """
    Creates a JSON formatted string containing Cisco device attributes from
    a given list of named tuples.

    Args:
        collated_records (iter(Device(str))): iterable of named tuples.

    Returns:
        output (str): JSON formatted string

    Example:
        >>> json_inventory(collate('./test_data'))
        '[{"software_image": "C2960c405-UNIVERSALK9-M", "serial_number": "ANC1111A1AB", "model_number": "WS-C2960C-8PC-L", "software_version": "15.0(2)SE5", "hostname": "elizabeth_cotton"}, {"software_image": "C2960c405-UNIVERSALK9-M", "serial_number": "ABC2222A2AB", "model_number": "WS-C2960C-8PC-L", "software_version": "15.0(2)SE5", "hostname": "howlin_wolf"}, {"software_image": "C2960X-UNIVERSALK9-M", "serial_number": "ABC3333A33A", "model_number": "WS-C2960X-48FPD-L", "software_version": "15.0(2)EX5", "hostname": "lightning_hopkins"}, {"software_image": "C2960X-UNIVERSALK9-M", "serial_number": "ABC4444A44A", "model_number": "WS-C2960X-48FPD-L", "software_version": "15.0(2)EX5", "hostname": "lightning_hopkins"}, {"software_image": "C2960X-UNIVERSALK9-M", "serial_number": "ABC5555A555", "model_number": "WS-C2960X-24PD-L", "software_version": "15.0(2)EX5", "hostname": "lightning_hopkins"}, {"software_image": "cat3k_caa-universalk9", "serial_number": "ABC6666A6AB", "model_number": "WS-C3650-24TD", "software_version": "03.03.03SE", "hostname": "sister_rosetta_tharpe"}]'
    """
    dict_records = [__named_tuple_to_dict(record) for record in collated_records]
    return json.dumps(dict_records)

# private function to transform a named tuple into a dictionary
def __named_tuple_to_dict(nt):
    return dict(zip(nt._fields, list(nt)))


def ascii_table_inventory(collated_records):
    """
    Creates an ascii table formatted string containing Cisco device attributes from
    a given list of named tuples.

    Args:
        collated_records (iter(Device(str))): iterable of named tuples.

    Returns:
        output (str): Ascii table formatted string

    Example:
        >>> ascii_table_inventory(collate('./test_data'))

          +-----------------------+---------------+-------------------+-------------------------+------------------+
          | Hostname              | Serial Number | Model Number      | Software Image          | Software Version |
          +-----------------------+---------------+-------------------+-------------------------+------------------+
          | elizabeth_cotton      |  ANC1111A1AB  | WS-C2960C-8PC-L   | C2960c405-UNIVERSALK9-M |    15.0(2)SE5    |
          | howlin_wolf           |  ABC2222A2AB  | WS-C2960C-8PC-L   | C2960c405-UNIVERSALK9-M |    15.0(2)SE5    |
          | lightning_hopkins     |  ABC3333A33A  | WS-C2960X-48FPD-L | C2960X-UNIVERSALK9-M    |    15.0(2)EX5    |
          | lightning_hopkins     |  ABC4444A44A  | WS-C2960X-48FPD-L | C2960X-UNIVERSALK9-M    |    15.0(2)EX5    |
          | lightning_hopkins     |  ABC5555A555  | WS-C2960X-24PD-L  | C2960X-UNIVERSALK9-M    |    15.0(2)EX5    |
          | sister_rosetta_tharpe |  ABC6666A6AB  | WS-C3650-24TD     | cat3k_caa-universalk9   |    03.03.03SE    |
          +-----------------------+---------------+-------------------+-------------------------+------------------+

    """
    hn_col = __width_of_column(collated_records, "hostname", 8)
    sn_col = __width_of_column(collated_records, "serial_number", 13)
    mn_col = __width_of_column(collated_records, "model_number", 12)
    si_col = __width_of_column(collated_records, "software_image", 14)
    sv_col = __width_of_column(collated_records, "software_version", 16)
    table_structure = " | {0:<{hn_col}} | {1:^{sn_col}} | {2:<{mn_col}} | {3:<{si_col}} | {4:^{sv_col}} |"
    table_divider = " +-{0:-^{hn_col}}-+-{1:-^{sn_col}}-+-{2:-^{mn_col}}-+-{3:-^{si_col}}-+-{4:-^{sv_col}}-+".format(
        "", "", "", "", "", hn_col=hn_col, sn_col=sn_col, mn_col=mn_col, si_col=si_col, sv_col=sv_col)
    output = '\n'
    output += table_divider
    output += '\n'

    output += table_structure.format(
        "Hostname",
        "Serial Number",
        "Model Number",
        "Software Image",
        "Software Version",
        hn_col=hn_col,
        sn_col=sn_col,
        mn_col=mn_col,
        si_col=si_col,
        sv_col=sv_col)

    output += '\n'
    output += table_divider
    output += '\n'

    for entry in collated_records:
        output += table_structure.format(
            entry.hostname,
            entry.serial_number,
            entry.model_number,
            entry.software_image,
            entry.software_version,
            hn_col=hn_col,
            sn_col=sn_col,
            mn_col=mn_col,
            si_col=si_col,
            sv_col=sv_col)
        output += '\n'

    output += table_divider
    output += '\n'
    return output

# private function to work out the max width of each table column
def __width_of_column(collated_records, column, init_length):
    for entry in collated_records:
        col_length = len(getattr(entry, column))
        if col_length > init_length:
            init_length = col_length
    return init_length
