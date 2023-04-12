import argparse
import os
import requests

token = os.environ.get('VK_TOKEN')


def get_name_of_albums(owner_id):
    return requests.get('https://api.vk.com/method/photos.getAlbums',
                        params={
                            'access_token': token,
                            'owner_id': owner_id,
                            'v': 5.131
                        }).json()


def get_friends_id(user_id, count):
    return requests.get('https://api.vk.com/method/friends.get',
                        params={
                            'access_token': token,
                            'user_id': user_id,
                            'count': count,
                            'v': 5.131
                        }).json()


def get_info_about_user(ids):
    return requests.get('https://api.vk.com/method/users.get',
                        params={
                            'access_token': token,
                            'user_ids': ids,
                            'v': 5.131
                        }).json()


def friends_id_parser(data):
    number_of_friends = data['count']
    list_id = data['items']
    str_ids = ''
    for i in range(len(list_id)):
        if i < len(list_id) - 1:
            str_ids += str(list_id[i]) + ', '
        else:
            str_ids += str(list_id[i])
    return number_of_friends, str_ids


def friends_info_parser(data):
    result_string = f'     User ID    |   First Name   |    Last Name\n'
    for i in range(len(data)):
        result_string += f'{data[i]["id"]:^16}|{data[i]["first_name"]:^16}|{data[i]["last_name"]:^16}\n'
    return result_string


def main():
    parser = argparse.ArgumentParser(
        description='VK page parser for this user ID')
    parser.add_argument('id', type=int, help='User ID')
    parser.add_argument('-count', default=50, type=int, help='Number of output friends')
    parser.add_argument('-f', type=int, help='1 - if u want get info about friends\n'
                                             '2 - if u want get names of albums')
    arguments = parser.parse_args()

    if arguments.f == 1:
        first_friends_json = get_friends_id(arguments.id, arguments.count)['response']
        info_about_users = get_info_about_user(friends_id_parser(first_friends_json)[1])
        answer = friends_info_parser(info_about_users['response'])
        print(answer)

    if arguments.f == 2:
        answer = get_name_of_albums(arguments.id)['response']['items']
        result = f'{"№":>2}|Name of album\n'
        for i in range(len(answer)):
            result += f'{i + 1:>2}|{answer[i]["title"]}\n'
        print(result)


if __name__ == '__main__':
    main()
