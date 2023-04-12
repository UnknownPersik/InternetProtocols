import argparse
import os
import re
from urllib.request import urlopen

ip_regex = r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+'
time_regex = r'[0-9]+ \w+ +[0-9]+ \w+ +[0-9]+ \w+'
as_and_provider_regex = r'(AS\d+) (.+)\"'
country_regex = r'country\": \"(\w+)'
ip_length = 15
as_length = 7
country_length = 7
provider_length = 30


def trace(hops, location):
    if hops:
        os.system(f'tracert -h {hops} {location} > info.txt')
    with open('info.txt', 'r') as input_file:
        text = input_file.read()
        ip_result = re.findall(ip_regex, text)
    result_string = f'NUM|       IP      |  AS   |COUNTRY|PROVIDER\n'
    for i in range(len(ip_result) - 1):
        result_string += f'{i + 1:>3}|'
        last_part = whois(ip_result[i + 1])
        result_string += last_part + '\n'
    return result_string


def whois(ip):
    result_string = f'{ip:>15}|'
    autonomous_system = ' ' * as_length
    country = ' ' * country_length
    provider = ' ' * provider_length
    if is_private(ip):
        result_string += f'{autonomous_system}|{country}|'
        return result_string
    temp_info = urlopen(f'https://ipinfo.io/{ip}/json').read().decode('utf-8', errors='ignore')
    temp_search = re.search(as_and_provider_regex, temp_info)
    if temp_search:
        autonomous_system = temp_search.group(1)
        provider = temp_search.group(2)
    country = re.search(country_regex, temp_info).group(1)
    result_string += f'{autonomous_system}|{country:^7}|{provider}'
    return result_string


def is_private(ip):
    temp = ip.split('.')
    first_number = int(temp[0])
    second_number = int(temp[1])
    if first_number == 10 or first_number == 127:
        return True
    if first_number == 172 and 16 <= second_number <= 31:
        return True
    if first_number == 192 and second_number == 168:
        return True
    return False


def main():
    parser = argparse.ArgumentParser(
        description='Tracing to the entered node (Using tracert).'
                    ' Only for windows users.\n')
    parser.add_argument('location', type=str, help='IP or domain address')
    parser.add_argument('-hops', type=int,
                        help='The maximum '
                             'number of jumps when searching for a node.')
    arguments = parser.parse_args()
    print(trace(arguments.hops, arguments.location))


if __name__ == '__main__':
    main()
