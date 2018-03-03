import datetime
import json
import logging
import operator
import os
from collections import defaultdict
from datetime import date

import vk_api
import vk_api.exceptions
from vk_api import execute

#from .TimeActivityAnalysis import VKOnlineGraph
from .VKFilesUtils import check_and_create_path, DIR_PREFIX


class VKActivityAnalysis:
    """
    Модуль, связанный с исследованием активности пользователей
    """

    def __init__(self, vk_session):
        """
        Конструктор
        :param vk_session: объект сессии класса VK
        """
        self.api = vk_session.get_api()
        self.tools = vk_api.VkTools(vk_session)
        self.logger = logging.getLogger("ActivityAnalysis")

    # функция получения лайков по 25 штук
    vk_get_all_likes_info = vk_api.execute.VkFunction(
        args=('user_id', 'owner_id', 'item_ids', 'type'),
        code='''

                    var item_ids = %(item_ids)s;
                    var result = [];
                    var i = 0;
                    while(i <= 25 && item_ids.length > i){
                        var params = {"user_id":%(user_id)s,
                                      "owner_id": %(owner_id)s,
                                      "item_id": item_ids[i],
                                      "type": %(type)s
                                      };
                        result = result + [API.likes.isLiked(params) + {"owner_id": params["owner_id"], 
                                                                        "user_id": params["user_id"], 
                                                                        "type": params["type"],
                                                                        "item_id": params["item_id"]} ];
                        i = i+1;
                    }

                    return {result: result, count: item_ids.length};
                ''')

    # функция получения общих друзей по 25 друзей проверяет
    vk_get_all_common_friends = vk_api.execute.VkFunction(
        args=('source_uid', 'target_uids'),
        code='''

                        var source_uid = %(source_uid)s;
                        var target_uids = %(target_uids)s;
                        var result = [];
                        var i = 0;
                        while(i <= 25 && target_uids.length > i*100){
                            var sliced = 0;
                            if ( (i+1)*100 > target_uids.length) {
                                sliced  = target_uids.slice(i*100,target_uids.length);
                            } else {
                                sliced = target_uids.slice(i*100,(i+1)*100);
                            }
                            var params = {"source_uid":%(source_uid)s,
                                          "target_uids": sliced,
                                          };
                            result = result + API.friends.getMutual(params);
                            i = i+1;
                        }

                        return {result:result};
                    ''')

    def is_online(self, uid):
        """
        Проверяет онлайн пользователя
        :param uid: id пользователя
        """
        resp = self.api.users.get(user_id=uid, fields='online')
        self.logger.debug("is_online: " + str(uid) + '; ' + str(resp))
        if len(resp) > 0 and 'online' in resp[0]:
            return resp[0]['online']
        else:
            return None

    def likes_iter(self, uid, friend_uid, count, method, max_count, values, type='post', limit=100):
        """
        Генератор инфомации о лайках
        :param uid: id пользователя которого проверяем
        :param friend_uid: id друга пользователя
        :param count: количество ??? TODO: че я тут написал, фигня какая-то
        :param method: метод VKApi
        :param max_count: Максимальное количество элментов, которое можно загрузить 1м методом за раз
        :param values: Параметры метода
        :param type: Тип записей (пост, фото)
        :param limit: максимальное количство записей
        """
        self.logger.debug("likes_iter: " + str(uid) + '; ' + str(friend_uid))
        item_ids = []
        entries = []
        iterations = count // 25
        tail = count % 25
        iterations_count = 0
        for key, entry in enumerate(self.tools.get_all_iter(method, max_count, values=values,
                                                            limit=limit)
                                    ):
            if key > limit:
                break
            if iterations_count < iterations:
                if key != 0 and key % 25 != 0:
                    item_ids += [entry['id']]
                    entries += [entry]
                else:
                    for i, like_info in enumerate(self.vk_get_all_likes_info(self.api, user_id=uid,
                                                                owner_id=friend_uid,
                                                                item_ids=item_ids,
                                                                type=type).get('result')):
                        entries[i].update(like_info)
                        yield entries[i]
                    item_ids = []
                    entries = []
                    iterations_count += 1
            else:
                if key % 25 != tail - 1:
                    item_ids += [entry['id']]
                    entries += [entry]
                else:
                    for i, like_info in enumerate(self.vk_get_all_likes_info(self.api, user_id=uid,
                                                                owner_id=friend_uid,
                                                                item_ids=item_ids,
                                                                type=type).get('result')):
                        entries[i].update(like_info)
                        yield entries[i]
                    item_ids = []
                    entries = []

    def likes_friend_photos(self, uid, friend_uid, limit=100):
        """
        Генератор лайков на фотографиях
        :param uid: id пользователя, которого проверяем
        :param friend_uid: id друга
        :param limit: максимальное количество загруженных записей
        """
        self.logger.debug("likes_friend_photos: " + str(uid) + '; ' + str(friend_uid))
        count = self.api.photos.getAll(owner_id=friend_uid, count=1)['count']
        values = {'owner_id': friend_uid, 'extended': 1, 'no_service_albums': 0}
        for like_info in self.likes_iter(uid=uid,
                                         friend_uid=friend_uid,
                                         count=count,
                                         method='photos.getAll',
                                         max_count=200,
                                         values=values,
                                         type='photo',
                                         limit=limit):
            yield like_info

    def likes_friend_wall(self, uid, friend_uid, limit=100):
        """
        Генератор лайков на стене TODO: может, совместить фото и стену? А то код почти одинковый
        :param uid: id пользователя, которого проверяем
        :param friend_uid: id друга
        :param limit: максимально число записей для загрузки
        """
        self.logger.debug("likes_friend_wall: " + str(uid) + '; ' + str(friend_uid))
        count = self.api.wall.get(owner_id=friend_uid, count=1)['count']
        values = {'owner_id': friend_uid, 'filter': 'all'}
        for like_info in self.likes_iter(uid=uid,
                                         friend_uid=friend_uid,
                                         count=count,
                                         method='wall.get',
                                         max_count=100,
                                         values=values,
                                         type='post',
                                         limit=limit):
            yield like_info

    def likes_group_wall(self, uid, group_id, limit=100):
        """
        Генератор лайков на стене СООБЩЕСТВА
        :param uid: id пользователя
        :param group_id: id группы
        :param limit: максимальное число записей для обработки
        """
        self.logger.debug("likes_group_wall: " + str(uid) + '; ' + str(group_id))
        return self.likes_friend_wall(uid, -abs(group_id), limit)

    def friends_common_iter(self, uid, friends_ids):
        """
        Генератор информации об общих друзьях
        :param uid: id пользователя, которого проверяем
        :param friends_ids: массив id друзей
        """
        self.logger.debug("friends_common_iter: " + str(uid) + '; ' + str(friends_ids))
        steps = len(friends_ids) // 2500 + 1
        for i in range(steps):
            commmon_friends = self.vk_get_all_common_friends(self.api,
                                                             source_uid=uid,
                                                             target_uids=friends_ids[
                                                                         i * 2500: min(
                                                                             (i + 1) * 2500,
                                                                             len(friends_ids)
                                                                         )
                                                                         ]).get('result')
            if not commmon_friends:
                continue
            for friend in commmon_friends:
                yield friend

    def friends_all_ids(self, uid, friends_full=None):
        """
        Получить id всех АКТИВНЫХ (не собачек) друзей пользователя
        :param uid: id пользователя
        :param friends_full: массив полной информации о друзьях
        """
        self.logger.debug("friends_all_ids: " + str(uid))
        if friends_full is None:
            friends_full = self.friends_all_full(uid=uid)
        return [el['id'] for el in friends_full]

    def friends_all_full(self, uid, friends_full=None):
        """
        Получает подробную информацию по всем АКТИВНЫМ (не собачкам) друзьям пользователя
        :param uid: id пользователя
        :param friends_full: массив полной информации о друзьях
        """
        self.logger.debug("friends_all_full: " + str(uid))
        if friends_full is not None:
            return friends_full
        # TODO: надо посмотреть, есть ли битовая маска scop'а друзей
        scope = 'nickname, domain, sex, bdate, city, country, timezone, photo_50, photo_100, photo_200_orig, has_mobile, contacts, education, online, relation, last_seen, status, can_write_private_message, can_see_all_posts, can_post, universities';
        return [el for el in self.tools.get_all('friends.get', 5000, values={'user_id': uid, 'fields': scope})['items']
                if 'deactivated' not in el]

    def common_city_score(self, uid, friends_full=None, result_type='first'):
        """
        Возвращает очки за общий город.
        Если пользователь совпадает городом с другом, то  +3 очка
        Если количество людей с таким городом максимально, то +3 очка первым 10%, +2 -- првым 20%
        :param uid: id пользователя, которого проверяем
        :param friends_full: массив полной информации о друзьях
        :param result_type: Тип позвращаемого результата. 'count' - все результаты
        :type result_type: any('first', 'count')
        :return: все результаты или первые 20%
        """
        self.logger.debug("common_city_score: " + str(uid))
        res = {}
        friends_full = self.friends_all_full(uid=uid, friends_full=friends_full)
        for friend in friends_full:
            if 'city' in friend:
                if friend['city']['title'] in res:
                    res[friend['city']['title']] += 1
                else:
                    res.update({friend['city']['title']: 1})
        res = sorted(res.items(), key=operator.itemgetter(1), reverse=True)
        if result_type == 'count':
            return dict(res)
        first_10p = {city[0]: 3 for city in res[:int(len(res) * 0.1)]}
        first_30p = {city[0]: 2 for city in res[int(len(res) * 0.1):int(len(res) * 0.3)]}
        first_10p.update(first_30p)
        return first_10p

    def score_common_age(self, uid, friends_full=None, result_type='first'):
        """
        Очки за общий возраст
        :param uid: id пользователя
        :param friends_full: массив полной информации о друзьях
        :param result_type: Тип позвращаемого результата. 'count' - все результаты
        :type result_type: any('first', 'count')
        :return: все результаты или первые 20%
        """
        self.logger.debug("score_common_age: " + str(uid))
        res = defaultdict(lambda: 0)
        friends_full = self.friends_all_full(uid=uid, friends_full=friends_full)
        for friend in friends_full:
            if 'bdate' in friend:
                bdate = friend['bdate'].split('.')
                if len(bdate) > 2:
                    res[int(bdate[2])] += 1
        res = sorted(res.items(), key=operator.itemgetter(1), reverse=True)
        if result_type == 'count':
            return dict(res)
        first_10p = {city[0]: 3 for city in res[:int(len(res) * 0.1)]}
        first_30p = {city[0]: 2 for city in res[int(len(res) * 0.1):int(len(res) * 0.3)]}
        first_10p.update(first_30p)
        if len(first_10p) == 0:
            first_10p = {res[0][0]: 1}
        return first_10p

    def search_user_by_age(self, user_info, group_id, age=(1, 100)):
        """
        Вычислить год рождения пользователя через группу
        :param user_info: информация о пользователе, которого проверяем
        :param group_id: id любой группы у пользователя
        :param age: диапазон предполагаемых возрастов
        :return: точный год рождения, который указал пользователь
        """

        info = self.api.users.search(q=user_info['first_name'] + ' ' + user_info['last_name'],
                                     group_id=group_id,
                                     age_from=age[0],
                                     age_to=age[1],
                                     count=1000)['items']
        for user in info:
            if user['id'] == user_info['id']:
                if age[0] == age[1]:
                    return date.today().year - age[0]
                return self.search_user_by_age(user_info=user_info,
                                               group_id=group_id,
                                               age=(age[0], (age[1] - age[0]) // 2 + age[0]))
        if age[0] == age[1]:
            return date.today().year - age[0] - 1
        return self.search_user_by_age(user_info=user_info,
                                       group_id=group_id,
                                       age=(age[1], (age[1] - age[0]) * 2 + age[0]))

    def user_age(self, uid, friends_full=None):
        """
        Вычислить предполагаемый возраст пользователя 2мя способами:
        -максимальное кол-во по друзьям (для <25 лет вполне точный рез-т)
        -по поиску в группе (точный результат указанного пользователем)
        :param uid: id пользователя, которого проверяем
        :param friends_full: массив полной информации о друзьях
        :return: словарь с результатами
        """
        res = {'user_defined': -1, 'friends_predicted': -1}
        user_info = self.api.users.get(user_ids=uid, fields='bdate')[0]
        if 'bdate' in user_info:
            bdate = user_info['bdate'].split('.')
            if len(bdate) > 2:
                res['user_defined'] = bdate[2]
            else:
                user_group = self.api.groups.get(user_id=uid, count=1)['items']
                if 0 in user_group:
                    user_group = user_group[0]
                    res['user_defined'] = self.search_user_by_age(user_info=user_info,
                                                                  group_id=user_group)
        else:
            user_group = self.api.groups.get(user_id=uid, count=1)['items']
            if 0 in user_group:
                user_group = user_group[0]
                res['user_defined'] = self.search_user_by_age(user_info=user_info,
                                                              group_id=user_group)
        common_age = int(list(self.score_common_age(uid=uid).items())[0][0])
        res['friends_predicted'] = common_age
        return res

    def check_friends_online(self, uid):
        """
        Проверяет онлайн всех друзей пользователя
        :param uid: id пользователя, которого проверяем
        :return: результат friends.getOnline
        """
        return self.api.friends.getOnline(user_id=uid)

    def likes_friends(self, uid, limit_entries=100, friends_full=None):
        """
        Генератор информации о лайках у друзей на фото и стене
        :param uid: id пользователя, которого проверяем
        :param limit_entries: максимальное кол-во записей на каждом друге
        :param friends_full: массив полной информации о друзьях
        """
        friends_full = self.friends_all_full(uid=uid, friends_full=friends_full)
        friends = self.friends_all_ids(uid=uid, friends_full=friends_full)
        count = len(friends)
        for i, friend in enumerate(friends, 1):
            for like in self.likes_friend_wall(uid=uid, friend_uid=friend, limit=limit_entries):
                if like['liked'] or like['copied']:
                    r = like
                    r.update({"count": count,
                              "current": i,
                              "name": friends_full[i-1]['first_name'] + ' ' + friends_full[i-1]['last_name']})
                    yield r
            for like in self.likes_friend_photos(uid=uid, friend_uid=friend, limit=limit_entries):
                if like['liked'] or like['copied']:
                    r = like
                    r.update({"count": count,
                              "current": i,
                              "name": friends_full[i-1]['first_name'] + ' ' + friends_full[i-1]['last_name']})
                    yield r
            yield {"count": len(friends), "current": i, "inf": 0}

    def likes_groups(self, uid, limit=100, groups=None):
        """
        Генератор информации о лайках в сообществах
        :param uid: id пользователя, которого проверяем
        :param limit: максимальное число записей с каждой группы
        :param groups: массив id групп
        """
        # TODO: здесь бы хорошо убрать повторное использование кода из likes_friends
        if groups is None:
            groups = self.tools.get_all('users.getSubscriptions', 200, values={"extended": 1, "user_id": uid})
        for i, group in enumerate(groups['items'], 1):
            try:
                for like in self.likes_group_wall(uid=uid, group_id=group['id'], limit=limit):
                    if like['liked'] or like['copied']:
                        r = like
                        r.update({"count": groups['count'],
                                  "current": i,
                                  "name": groups['items'][i-1]['name']})
                        yield r
            except vk_api.exceptions.ApiError as error:
                # TODO: обработать это по-нормальному
                if error.code == 13:
                    self.logger.error("Size is too big, skipping group_id=" + str(group['id']))
                elif error.code == 15:
                    self.logger.warning("Wall is disabled, skipping group_id=" + str(group['id']))
                else:
                    raise error
            except vk_api.exceptions.ApiHttpError as error:
                # TODO: не понятная фигня, надо разобраться
                self.logger.error("Server 500 error, skipping group_id=" + str(group['id']))
            yield {"count": groups['count'], "current": i, "inf": 0}

    def likes_friends_and_groups(self, uid, limit=100, friends_need=False, groups_need=False, friends_full=None, groups=None):
        """
        Генератор информации о лайках в группах и сообществах
        :param uid: id пользователя, которого проверяем
        :param limit: количество записей, которые нужно загружать на каждом элементе
        :param friends_need: необходима проверка у друзй
        :param groups_need: необходима проверка у групп
        :param friends_full: массив полной информации о друзьях
        :param groups: массив подписок
        :return:
        """
        friends_full = self.friends_all_full(uid, friends_full)
        if groups is None:
            # TODO: subsriptions может содержать людей, надо доработать, возможны баги
            groups = self.tools.get_all('users.getSubscriptions', 200, values={"extended": 1, "user_id": uid})
        friends_count = friends_need*len(friends_full)
        groups_count = groups_need*groups['count']
        count = friends_count + groups_need*groups['count']
        if friends_need:
            for like in self.likes_friends(uid=uid, limit_entries=limit, friends_full=friends_full):
                r = like
                r.update({"count": count})
                yield r
        if groups_need:
            for like in self.likes_groups(uid=uid, limit=limit, groups=groups):
                r = like
                r.update({"count": count, "current": like['current'] + friends_count})
                yield r

    def score_likes_friends(self, uid, limit=100, friends_full=None):
        """
        Возвращает баллы за лайки друзьям
        :param uid: id пользователя, которого проверяем
        :param limit: количество записей загружаемых на каждой странице
        :param friends_full: массив полной информации о друзтях
        """
        score = 0
        for post_info in self.likes_friends(uid=uid,
                                            limit_entries=limit,
                                            friends_full=friends_full):
            if 'liked' in post_info:
                if post_info['liked'] == 1:
                    score += 1
            if 'copied' in post_info:
                if post_info['copied'] == 1:
                    score += 10
            if 'inf' in post_info:
                temp = score
                score = 0
                yield 'likes_friends', post_info['current']-1, temp

    def score_likes_self(self, uid, limit=100, friends_full=None):
        """
        Возвращает очки за лайки друзей у пользователя на странице
        :param uid: id пользователя, которого проверяем
        :param limit: максимальное число записей
        :param friends_full: массив полной информации о друзьях
        """
        friends = self.friends_all_ids(uid=uid, friends_full=friends_full)
        res = [0]*len(friends)

        for key, post in enumerate(self.tools.get_all_iter(method='wall.get', max_count=100, values={'owner_id': uid},
                                                            limit=limit)):
            if key > limit:
                break
            post_likes = self.tools.get_all(method='likes.getList', max_count=100, values={'type': 'post',
                                                                                           'skip_own':1,
                                                                                           'owner_id': uid,
                                                                                           'item_id': post['id']})['items']
            post_reposts = self.tools.get_all(method='likes.getList', max_count=100, values={'type': 'post',
                                                                                           'skip_own': 1,
                                                                                           'owner_id': uid,
                                                                                           'filter': 'copies',
                                                                                           'item_id': post['id']})['items']
            for user in post_likes:
                if user in friends:
                    res[friends.index(user)] += 1
            for user in post_reposts:
                if user in friends:
                    if user in friends:
                        res[friends.index(user)] += 10

        for key, photo in enumerate(self.tools.get_all_iter(method='photos.getAll',
                                             max_count=200,
                                             values={'owner_id': uid, 'extended': 1, 'no_service_albums': 0})):
            if key>limit:
                break
            photo_likes = self.tools.get_all(method='likes.getList', max_count=100, values={'type': 'photo',
                                                                                           'skip_own':1,
                                                                                           'owner_id': uid,
                                                                                           'item_id': photo['id']})['items']
            for user in photo_likes:
                if user in friends:
                    if user in friends:
                        res[friends.index(user)] += 1

        for i, friend in enumerate(res):
            yield 'likes_self', i, friend

    def score_mutual_friends(self, uid, friends_full=None):
        """
        Возвращает очки за общих друзей
        :param uid: id пользователя, которого проверяем
        :param friends_full: массив полной информации о друзьях
        """
        res = []
        friends = self.friends_all_ids(uid=uid, friends_full=friends_full)
        for mutual in self.friends_common_iter(uid=uid, friends_ids=friends):
            res.append(mutual['common_count'])
        res_sorted = sorted(list(set(res)))
        count = len(res_sorted)
        for i, friend in enumerate(res):
            yield 'friends', i, res_sorted.index(friend)*10//count

    def score_all_common_age(self, uid, friends_full=None):
        """
        Возвращает очки за общий возраст
        :param uid: id пользователя, которого проверяем
        :param friends_full: массив полной информации о друзьях
        """
        friends_full = self.friends_all_full(uid=uid, friends_full=friends_full)
        user_age = self.user_age(uid=uid, friends_full=friends_full)

        def get_user_real_age(age):
            if age[0] == age[1]:
                return age[0],1,2
            elif age[0] == -1:
                return age[1],2,3
            elif age[1] == -1:
                return age[0],2,3
            else:
                return (int(age[0])+int(age[1]))//2, -1, abs(int(age[0])-int(age[1]))

        user_real_age = get_user_real_age((user_age['user_defined'], user_age['friends_predicted']))
        for i, friend in enumerate(friends_full):
            score = 0
            if 'bdate' in friend:
                date = friend['bdate'].split('.')
                if len(date)>2:
                    if int(date[2]) - user_real_age[1] <= user_real_age[0] <= int(date[2]) + user_real_age[1]:
                        score = 3
                    elif int(date[2]) - user_real_age[2] <= user_real_age[0] <= int(date[2]) + user_real_age[2]:
                        score = 1
            yield 'age', i, score

    def score_all_common_city(self, uid, friends_full=None):
        """
        Возвращает очки за общий город
        :param uid: id пользователя, которого проверяем
        :param friends_full: массив полной информации о друзьях
        """
        friends_full = self.friends_all_full(uid=uid, friends_full=friends_full)
        common_city_score = self.common_city_score(uid=uid, friends_full=friends_full, result_type='first')
        user = self.api.users.get(user_id=uid,fields='city')[0]
        user_city = ''
        if 'city' in user:
            user_city = user['city']['title']

        for i, friend in enumerate(friends_full):
            score = 0
            if 'city' in friend:
                friend_city = friend['city']['title']
                if friend_city in common_city_score:
                    score = common_city_score[friend_city]
                score += (friend_city==user_city)*3
            yield 'city', i, score

    def score_all(self,
                  uid,
                  limit=100,
                  likes_friends_need=False,
                  likes_self_need=False,
                  common_friends_need=False,
                  common_age_need=False,
                  common_city_need=False,
                  friends_full=None):
        """
        Генератор информации о круге общения
        :param uid: id пользователя, которого проверяем
        :param limit: максимальное количество загружаемых каждый раз записей
        :param likes_friends_need: необходимо проверять лайки друзьям
        :param likes_self_need:  необходимо проверять лайки друзей
        :param common_friends_need: проверять общих друзей
        :param common_age_need: проверять общий возраст
        :param common_city_need: проверять общий город
        :param friends_full: массив полной информации о друзьях
        """
        friends_full = self.friends_all_full(uid=uid, friends_full=friends_full)
        if common_age_need:
            for element in self.score_all_common_age(uid=uid, friends_full=friends_full):
                yield element
        if common_city_need:
            for element in self.score_all_common_city(uid=uid, friends_full=friends_full):
                yield element
        if common_friends_need:
            for element in self.score_mutual_friends(uid=uid, friends_full=friends_full):
                yield element
        if likes_self_need:
            for element in self.score_likes_self(uid=uid, limit=limit, friends_full=friends_full):
                yield element
        if likes_friends_need:
            for element in self.score_likes_friends(uid=uid, limit=limit, friends_full=friends_full):
                yield element

