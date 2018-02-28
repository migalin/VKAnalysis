import io
from .TextAnalysisCore import VKTextAnalysis


class MakeDictionary:
    """Класс для создания словарей"""

    FOLDER_PREFIX = 'mkdicts/'

    def __init__(self, vk_session):
        """Инициализация класса
        :param vk_session: Сессия ВК, полученная от vk_api.Vk_Api()
        """
        self.vkanalysis = VKTextAnalysis(vk_session)

    def write_all(self,
                  owner_id=0,
                  saved_file_name='saved.txt',
                  blacklist_file_name='blacklist.txt',
                  dictionary_file_name='dictionary.txt'):
        """Получает все записи пользователя owner_id, разбивает на слова,
        : преобразует их в нормальную форму и записывает результат работы в saved.txt
        :param owner_id: id владельца стены
        :param saved_file_name: имя файла буферизации
        :param blacklist_file_name: имя файла с ХОРОШИМИ словами
        :param dictionary_file_name: имя файла с текущим словарем
        :
        :type: int
        """
        file = open(MakeDictionary.FOLDER_PREFIX + saved_file_name, 'a+')
        for entry in self.vkanalysis.tools.get_all_iter('wall.get',
                                                        VKTextAnalysis.API_MAX_GET_WALL,
                                                        values={'filter': 'owner', 'owner_id': owner_id},
                                                        key='items',
                                                        ):
            # self.check_text(entry['text'])
            text = VKTextAnalysis.text_preprocess(entry['text'])
            self.make_words(text, file)
        file.close()

    def make_words(self, text, file=None):
        """Разбивает text на слова, записывает их в файл file
        :param text: текст для преобразования и записи
        :param file: файл для записи с методом .write
        """
        for word in text.split():
            word_prepared = self.vkanalysis.morphology.parse(self.vkanalysis.russian_word_preprocess(word)
                                                             )[0].normal_form
            if word_prepared != '':
                file.write(word_prepared + '\n')

    @staticmethod
    def make_dictionary(saved_file_name,
                        blacklist_file_name,
                        dictionary_file_name):
        """Открывает файл saved.txt и читает его построчно.
        :Если слово в строке найдено в файле blacklist.txt, то пропускаем слово
        :Если слово в строке найдено в файле dictionary.txt, то пропускаем слово
        :Иначе спрашиваем пользователя, стоит ли добавить слово в словарь
        :Если пользователь отвечает '1', то записываем слово в dictionary.txt
        :Иначе записываем в blacklist.txt
        """
        with io.open(MakeDictionary.FOLDER_PREFIX + saved_file_name) as file:
            for line_ in file:
                flag = 0
                line = VKTextAnalysis.russian_word_preprocess(line_).lower().strip()
                print(line)
                with io.open(MakeDictionary.FOLDER_PREFIX + dictionary_file_name) as dictionary:
                    for entry in dictionary:
                        if line in entry:
                            flag = 1
                            break
                if flag == 0:
                    blacklist_flag = 0
                    with io.open(MakeDictionary.FOLDER_PREFIX + blacklist_file_name) as blacklist:
                        for entry in blacklist:
                            if line in entry:
                                blacklist_flag = 1
                                break
                    if blacklist_flag == 0:
                        ans = input("Is " + line + " ? 1 or 0: ")
                        if ans == '1':
                            dictionary = open(MakeDictionary.FOLDER_PREFIX + dictionary_file_name, "a+")
                            dictionary.write(line + '\n')
                            dictionary.close()
                        else:
                            blacklist = open(MakeDictionary.FOLDER_PREFIX + blacklist_file_name, "a+")
                            blacklist.write(line + '\n')
                            blacklist.close()
