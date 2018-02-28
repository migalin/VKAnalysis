# -*- coding: utf-8 -*-
"""
@author: migalin
@contact: https://migalin.ru
@license Apache License, Version 2.0, see LICENSE file
Copyright (C) 2018
"""

import pymorphy2
import vk_api
import re
import io
import os


# TODO: РЕФАКТОРИНГ ЭТОГО КОДА!!!

class VKTextAnalysis:
    """
    Класс для работы с текстовой информацией
    """

    API_MAX_GET_WALL = 100  # максимальное количество закгружаемых постов за 1 запрос к API
    russian_regex = re.compile('[^а-яА-ЯёЁ ]')  # только русские буквы

    DICTS_FOLDER_PREFIX = 'dicts/'  # папка со словарями

    def __init__(self, vk_session, dicts_need):
        """Инициализирует класс
        :param vk_session: Сессия ВК, полученная от vk_api.Vk_Api()
        :param dicts_need: Необходимые словари
        """
        self.api = vk_session.get_api()
        self.tools = vk_api.VkTools(vk_session)
        self.morphology = pymorphy2.MorphAnalyzer()
        self.dicts = {}
        self.dicts_need = dicts_need
        self.init_dicts()
        # заголовок поста в HTML
        self.header = '''<html><head><style>.bred {background: #FF0000;} .bblue {background: #70a6ff;} .byellow {background: #9df940;} .bgrey {background: #a39fa3;} .bpurple {background: #f736f7;} .bcyan {background: #7e6e9e;} </style></head><p>'''
        # шаблон выделения цветом в HTML
        self.template = '<span class="{}">{}</span >'
        # футер поста в HTML
        self.footer = '</p></html>'
        # цвета выделения
        self.colors = ['bred', 'bblue', 'byellow', 'bgrey', 'bpurple', 'bcyan']

    def init_dicts(self):
        """
        Инициализация словарей в память.
        :return: None
        """
        for dictionary in os.listdir(os.path.join(os.path.dirname(__file__), self.DICTS_FOLDER_PREFIX)):
            if dictionary not in self.dicts_need:
                continue
            self.dicts.update({dictionary: []})
            file = io.open(os.path.join(os.path.dirname(__file__), VKTextAnalysis.DICTS_FOLDER_PREFIX, dictionary))
            for line in file:
                self.dicts[dictionary].append(self.russian_word_preprocess(line))

    @staticmethod
    def russian_word_preprocess(text=''):
        """Преобразует слово, оставляя только русские буквы и заменяет ё на е
        :param text: слово для преобразования
        :return: преобразованное слово
        :type: str
        """
        return VKTextAnalysis.russian_regex.sub('', text.replace('ё', 'е'))

    @staticmethod
    def text_preprocess(text=''):
        """Преобразует текст, заменяя знаки препинания на пробелы, для исключения ситуаций 'привет.нах'
        :param text: текст для преобразования
        :return: преобразованный текст
        :type: str
        """
        return VKTextAnalysis.russian_regex.sub(' ', text)

    def check_wall_iterable(self, owner_id=0, filter='owner', limit=2500):
        """Генератор, который возвращает результаты проверки записей со стены пользователя
        :param owner_id: id владельца стены. Для сообществ отрицательное
        :type: int
        :param filter: Дает возможность получить записи всех пользователей на стене
        :type: str ('owner', 'other', 'all')
        :param limit: ограничение по количеству записей (минимум 2500)
        :type: int
        :return: генератор результатов проверки записей на стене
        :type: dict {'id': post_id, 'from_id': from_id, 'info': [( int REASON, str word )] }
        """
        if owner_id > 0:
            user = self.api.users.get(user_id=owner_id)[0]
        else:
            # TODO: нормальная идентификация сообщества
            user = {"first_name": 'Сообщество', "last_name": str(owner_id)}
        count = min(limit, self.api.wall.get(filter=filter, owner_id=owner_id)['count'])
        for i, entry in enumerate(self.tools.get_all_iter('wall.get',
                                                          VKTextAnalysis.API_MAX_GET_WALL,
                                                          values={'filter': filter, 'owner_id': owner_id},
                                                          key='items',
                                                          limit=limit), 1):
            # self.check_text(entry['text'])
            if i > limit:
                break
            preprocessed_text = VKTextAnalysis.text_preprocess(entry['text'])
            checked = self.check_text(preprocessed_text)
            yield {'id': entry['id'],
                   'from_id': entry['from_id'],
                   'info': checked,
                   'text': preprocessed_text,
                   'html': self.html_highlight(preprocessed_text, checked),
                   'link': "http://vk.com/wall"+str(entry['owner_id'])+"_"+str(entry['id']),
                   'user': user,
                   'current': i,
                   'count': count}

    def html_highlight(self, text, checked):
        """
        Заграшивает фон теста HTML у "плохих" слов
        :param text: текст
        :param checked: кортеж проверенных слов подходящего формата
        :return: отформатированный в html текст поста
        """
        for el in checked:
            text = text.replace(el[3], self.template.format(*(self.colors[el[0] % len(self.colors)], el[3])))
        return self.header + text + self.footer

    def check_text(self, text=''):
        """Проверяет текст по словарям
        :param text: текст для проверки
        :type: str
        :return: Список кортежей с результатами проверки
        :type: list [( int REASON, str word )]
        """
        warning = []
        current_position = 0
        for word_unreq in text.split(' '):
            if word_unreq == '':
                current_position += 1
                continue
            word = self.morphology.parse(self.russian_word_preprocess(word_unreq).lower())[0].normal_form
            for num, dictionary in enumerate(self.dicts.items()):
                if word in dictionary[1]:
                    warning.append((num,
                                    current_position,
                                    current_position + len(word_unreq) + 1,
                                    word_unreq,
                                    dictionary[0]))
                # print(num, current_position, current_position + len(word_unreq) + 1, word)
            current_position += len(word_unreq) + 1

        return warning




