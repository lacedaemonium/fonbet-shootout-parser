from datetime import datetime, timedelta
import json
import random
from json import JSONDecodeError
import requests
import sqlite3
import time

url = 'https://shootout-api.rupr.upsl-tech.ru/twirp/duels.shootout.api.Api/GetGame'
headers = {
    'Host': 'shootout-api.rupr.upsl-tech.ru',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Accept': 'application/json',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://shootout-web.rupr.upsl-tech.ru/',
    'Content-Type': 'application/json',
    'Content-Length': '2',
    'Origin': 'https://shootout-web.rupr.upsl-tech.ru',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'TE': 'trailers'
}

connection = sqlite3.connect('/opt/fonbet/fonbet.db')
cursor = connection.cursor()

match_id_in_day = 0
first_team_result = ''
second_team_result = ''

# один раз при запуске достаем вчерашние матчи смерти
today_init = datetime.now()
today_format_init = today_init.strftime("%Y-%m-%d")
yesterday_init = today_init - timedelta(days=1)
yesterday_format_init = yesterday_init.strftime("%Y-%m-%d")

cursor.execute('SELECT match_no,date_time FROM fonbet WHERE (date_time) > (?) AND (date_time) < (?) AND (death_match) = "1"',
               [yesterday_format_init, today_format_init])
death_matches_yesterday_fetch = cursor.fetchall()

death_matches_yesterday_ids = []
death_matches_yesterday_time = []
for dm in death_matches_yesterday_fetch:
    death_matches_yesterday_ids.append(dm[0])
    temp = dm[1].replace("-", "/")
    death_matches_yesterday_time.append(temp)

print(f"Вчерашние (за {yesterday_format_init}) матчи смерти: {death_matches_yesterday_ids}")

# основной цикл
while(True):
    # загружаем свежий json
    try:
        response_orig = requests.post(url, json=headers)
    except JSONDecodeError:
        print(f"Ошибка загрузки файла #1! Ждем и пробуем снова...")
        time.sleep(5)
        continue

    if response_orig.status_code != 200:
        print(f"Ошибка загрузки файла #2! Ждем и пробуем снова...")
        time.sleep(5)
        continue

    response = json.loads(response_orig.text)

    try:
       response_main = response['contest']
    except KeyError:
       print(f"Ошибка загрузки файла #3! Ждем и пробуем снова...")
       time.sleep(5)
       continue

    # если в свежем json новый id
    if match_id_in_day != response['contest']['order']:

        # проверяем не начался ли новый день
        if response['contest']['order'] < match_id_in_day:
            print(f"Новый id матча меньше предыдущего. Похоже, что начался новый игровой день!")
            today = datetime.now()
            today_format = today.strftime("%Y-%m-%d")
            yesterday = today - timedelta(days=1)
            yesterday_format = yesterday.strftime("%Y-%m-%d")
            print(yesterday_format)

            cursor.execute('SELECT match_no,date_time FROM fonbet WHERE (date_time) > (?) AND (death_match) = "1"',
                           [yesterday_format])
            death_matches_yesterday_fetch = cursor.fetchall()

            death_matches_yesterday_ids = []
            death_matches_yesterday_time = []
            for dm in death_matches_yesterday_fetch:
                death_matches_yesterday_ids.append(dm[0])
                temp = dm[1].replace("-", "/")
                death_matches_yesterday_time.append(temp)

            yesterday_to_tlg = yesterday.strftime("%Y/%m/%d")
            analyzer_message_part1 = f"По итогу дня {yesterday_to_tlg} было *{len(death_matches_yesterday_ids)}* матчей смерти:"

            analyzer_message_part2 = ''
            i = 0
            for match in death_matches_yesterday_ids:
                analyzer_message_part2 = analyzer_message_part2 + "*№" + str(
                    death_matches_yesterday_ids[i]) + "* \\- " + str(death_matches_yesterday_time[i]) + "%0A"
                i += 1

            analyzer_message_part3 = 'Выигрышные матчи сегодня ' + ', '.join(
                str(x) for x in death_matches_yesterday_ids)

            analyzer_message_to_tlg = (
                f"{analyzer_message_part1}%0A{analyzer_message_part2}%0A{analyzer_message_part3}")
            requests.get(
                f"https://api.telegram.org/bot******:AA***********Cafk/sendMessage?chat_id=-4*******84&parse_mode=MarkdownV2&text={analyzer_message_to_tlg}")
            # конец операций при начале нового игрового дня

        # проверяем результаты предыдущего матча на соответствие матчу смерти
        if (first_team_result == '100') and (second_team_result == '000'):
            print(f"Матч {match_id_in_day} - матч смерти, тип #1!")
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('UPDATE fonbet SET death_match = ? WHERE id = ?',
                           ('1', cursor.lastrowid))
            connection.commit()
        if (first_team_result == '011') and (second_team_result == '111'):
            print(f"Матч {match_id_in_day} - матч смерти, тип #2!")
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('UPDATE fonbet SET death_match = ? WHERE id = ?',
                           ('1', cursor.lastrowid))
            connection.commit()

        # переключаемся на новый id
        print('-----')
        match_id_in_day = response['contest']['order']
        print(f"Начался новый матч №{match_id_in_day}")
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Дата и время начала матча: {now}")
        cursor.execute('INSERT INTO fonbet (match_no, date_time, death_match) VALUES (?, ?, ?)',
                       (match_id_in_day, now, '0'))
        connection.commit()
        # проверяем нужно ли алертить что следующий матч соответствует вчерашнему номеру матчей смерти
        match_id_in_day_plus_one = match_id_in_day+1
        match_id_in_day_plus_one = str(match_id_in_day_plus_one)
        if match_id_in_day_plus_one in death_matches_yesterday_ids:
            print(f"Матч №№{match_id_in_day_plus_one} найден во вчерашнем списке смертельных матчей ({death_matches_yesterday_ids})! Алертим")
            alert_message_to_tlg = f"Начинается матч {match_id_in_day}\\. Следующий матч {match_id_in_day_plus_one} выигрышный\\!"
            requests.get(
                f"https://api.telegram.org/bot7*****5:A***************afk/sendMessage?chat_id=-4*******84&parse_mode=MarkdownV2&text={alert_message_to_tlg}")
        else:
            print(f"Матча №{match_id_in_day_plus_one} во вчерашнем списке смертельных матчей ({death_matches_yesterday_ids}) не найдено")

    else:
        # в загруженом json тот же id что и был ранее
        print(f"Продолжает идти матч №{match_id_in_day}")

    try:
        status_value = response['contest']['status']
        if status_value == "LIVE":
            print(f"Игра в матче №{match_id_in_day} в статусе LIVE")
            try:
                response_value = response['contest']['rounds'][0]['result']
                print('Есть результаты матча')
                rounds_array = response['contest']['rounds']
                k = 0
                first_team_result = ''
                second_team_result = ''
                for round in rounds_array:
                    if round['order'] % 2 != 0:
                        #print(f"В раунде {k+1} результат пойдет первой команде, проверяем есть ли он")
                        try:
                            response_round_result = round['result']
                            print(f"Результат раунда {k+1}: {round['result']}")
                            if round['result'] == "GOAL": round['result'] = '1'
                            elif round['result'] == "MISS": round['result'] = '0'
                            first_team_result = first_team_result + round['result']
                        except KeyError:
                            print(f"Результат раунда {k+1}: <- пока нет ->")
                        k = k+1
                    else:
                        #print(f"В раунде {k+1} результат пойдет второй команде, проверяем есть ли он")
                        try:
                            response_round_result = round['result']
                            print(f"Результат раунда {k+1}: {round['result']}")
                            if round['result'] == "GOAL": round['result'] = '1'
                            elif round['result'] == "MISS": round['result'] = '0'
                            second_team_result = second_team_result + round['result']
                        except KeyError:
                            print(f"Результат раунда {k+1}: <- пока нет ->")
                        k = k+1
                print(f"Результаты первой команды: {first_team_result}")
                print(f"Результаты второй команды: {second_team_result}")
                cursor.execute('UPDATE fonbet SET result_match = ? WHERE id = ?', (first_team_result+'-'+second_team_result, cursor.lastrowid))
                connection.commit()
            except KeyError:
                print('Игра в статусе LIVE - но результатов пока нет')
        else:
            print(f"Матч №{match_id_in_day} идет, но игра не в статусе LIVE")
    except KeyError:
        print(f"Технический перерыв в матче №{match_id_in_day}")
    print('-')
    time.sleep(random.randint(2,3))
