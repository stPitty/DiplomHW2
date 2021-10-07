import vk_api
from vk_api.exceptions import ApiError
from random import randrange
import difflib

from data.info import relations_dict
from data import db


class Bot_back(vk_api.VkApi):

    def get_user_name(self, vk_id):
        params = {
            'user_ids': vk_id,
            'name_case': 'nom'
        }
        user = self.method('users.get', params)
        return f"{user[0]['first_name']} {user[0]['last_name']}"

    def search(self, user_object):
        users_list = []
        params = {'sex': user_object.sex,
                  'age_from': user_object.age_from,
                  'age_to': user_object.age_to,
                  'city': user_object.city,
                  'status': user_object.status,
                  'count': 1000,
                  'has_photo': 1
                  }
        search = self.method('users.search', params)
        for user in search['items']:
            if not user['is_closed']:
                users_list.append(user['id'])
        return users_list

    def get_photo(self, vk_id):
        params = {'owner_id': vk_id,
                  'album_id': 'profile',
                  'extended': 1,
                  'count': 1000,
                  'photo_sizes': 1
                  }
        return self.method('photos.get', params)

    def compare(self, photos):
        photos_list = []
        for photo in photos['items']:
            photos_list.append({'url': f"photo{photo['owner_id']}_{photo['id']}",
                                'likes': photo['likes']['count'],
                                'comments': photo['comments']['count']
                                })
        photos_list.sort(key=lambda item: item['likes'] + item['comments'], reverse=True)
        urls_list = [photo['url'] for photo in photos_list[0:3]]
        return ','.join(urls_list)

    def cities(self, city_name):
        params = {'country_id': 1,
                  'q': city_name,
                  'need_all': 0,
                  'count': 1}
        return self.method('database.getCities', params)


class Bot_front:
    def __init__(self, user_token, user_id, vk, longpoll, VkEventType):
        self.user_id = user_id
        self.name = 'name'
        self.session = db.create_connect()[0]
        self.params = self.session.query(db.User).get(self.user_id)
        self.vk = vk
        self.vk_back = Bot_back(token=user_token)
        self.longpoll = longpoll
        self.VkEventType = VkEventType

    def listen(self):
        for event in self.longpoll.listen():
            if event.type == self.VkEventType.MESSAGE_NEW:
                if event.to_me:
                    return event.text.lower()

    def write_msg(self, message=None, attach=None):
        params = {'user_id': self.user_id,
                  'message': message,
                  'random_id': randrange(10 ** 7),
                  'attachment': attach
                  }
        self.vk.method('messages.send', params)

    def change_sex(self):
        while True:
            self.write_msg("Пожалуйста, введите пол партнера (м или ж) 💃🕺")
            response = self.listen()
            if response in ("м", "мужской", "мужчина", "ж", "женский", "женщина"):
                if response in ("м", "мужской", "мужчина"):
                    self.params.sex = 2
                    self.write_msg("Пол партнера для поиска изменен на: 'Мужской'")
                else:
                    self.params.sex = 1
                    self.write_msg("Пол партнера для поиска изменен на: 'Женский'")
                break

    def change_age(self):
        while True:
            self.write_msg("Пожалуйста, введите диапазон возраста для поиска (начало:конец) 📅")
            response = self.listen()
            try:
                age_from = int(response.split(':')[0])
                age_to = int(response.split(':')[1])
                if age_from <= age_to:
                    self.params.age_from = age_from
                    self.params.age_to = age_to
                    self.write_msg(f"Диапазон возраста поиска изменен на: "
                                   f"'c {self.params.age_from} до {self.params.age_to} лет'")
                    break
                else:
                    self.write_msg("Данные некорретны (возраст 'от' не может быть выше возраста 'до')")
            except ValueError:
                pass

    def change_city(self):
        self.write_msg("Пожалуйста, введите город для поиска 🌍")
        city = None
        while True:
            response = self.listen()
            if response in ('да', 'верно', 'потдверждаю', 'это мой город') and city:
                self.params.city = city['items'][0]['id']
                self.write_msg(f"Город поиска изменен на: '{city['items'][0]['title']}' ✅")
                break
            else:
                city = self.vk_back.cities(response)
                try:
                    self.write_msg(f"Город для поиска: '{city['items'][0]['title']}'\n"
                                   f"Верно?")
                except IndexError:
                    self.write_msg("Упс, к сожалению мы не смогли найти данный город 😰\n"
                                   "Пожалуйста, попробуйте ввести еще раз")

    def change_relations(self):
        self.write_msg("Пожалуйста, введите семейное положение партнера 👪")
        status = ''
        while True:
            response = self.listen()
            if response in ('да', 'верно', 'потдверждаю') and status:
                status_num = relations_dict[status]
                if status_num // 11:
                    status_num = status_num // 11
                self.params.status = status_num
                self.write_msg(f"Семейное положение для поиска изменено на:\n '{status.capitalize()}' ✅")
                break
            else:
                try:
                    status = difflib.get_close_matches(response, relations_dict)[0]
                except IndexError:
                    status = ''
                    available_status = '\n'.join(list(relations_dict.keys()))
                    self.write_msg("Упс, мы не смогли найти семейное положение согласно Вашему запросу 😰\n")
                    self.write_msg(f"Доступные семейные положения:\n {available_status}")
                if status:
                    self.write_msg(f"Предпочтительное семейное положение для поиска:\n '{status.capitalize()}'\n"
                                   f"Верно?")

    def change_search_list(self):
        search_delete = self.session.query(db.Search).filter(db.Search.user_id == self.user_id).all()
        [self.session.delete(user) for user in search_delete]
        self.session.commit()
        vk_users_id = self.vk_back.search(self.params)
        for vk_id in vk_users_id:
            search_line = db.Search()
            search_line.user_id = self.user_id
            search_line.vk_id = vk_id
            self.update_db(search_line)
        return True

    def change_params(self):
        self.change_sex()
        self.change_age()
        self.change_city()
        self.change_relations()
        self.update_db()
        self.change_search_list()
        self.write_msg("Параметры поиска успешно изменены ✅")
        return True

    def update_db(self, *args, delete=False):
        if delete:
            self.session.delete(*args)
        else:
            self.session.add_all([self.params, *args])
        self.session.commit()
        return True

    def show_people(self):
        """Приветствую тебя в режиме поиска!
        Здесь ты можешь использовать следующие команды для навигации:
        &#9989; Дальше => перемещение по списку
        &#9989; Выйти => выход в главное меню
        &#9989; Лайк => поставить лайк данному пользователю
        &#9989; Черный список => заблокировать текущего пользователя"""
        self.write_msg("Начинаем поиск 🔍")
        while True:
            if not self.params:
                self.write_msg("Для начала поиска необходимо задать параметры 📋")
                self.params = db.User()
                self.params.id = self.user_id
                self.change_params()
            user = self.session.query(db.Search).outerjoin(db.Blacklist,
                                                           db.Search.vk_id == db.Blacklist.vk_id).filter(
                                                        db.Search.user_id == self.user_id,
                                                        db.Search.showed == False,
                                                        db.Blacklist.vk_id == None).first()
            if not user:
                self.write_msg("Упс! К сожалению больше мы ничего не смогли найти по Вашим параметрам 📝\n"
                               "Вы всегда можете задать новые параметры командой: 'Изменить параметры'")
                return
            photos = self.vk_back.get_photo(user.vk_id)
            attach = self.vk_back.compare(photos)
            try:
                self.write_msg(attach=attach)
            except ApiError:
                pass
            self.write_msg(f"https://vk.com/id{user.vk_id}")
            while True:
                response = self.listen()
                if response == 'выйти':
                    return
                elif response in ['дальше', 'лайк', 'черный список']:
                    if response == 'лайк':
                        likes_list = [user[0] for user in self.session.query(db.Likes.vk_id).filter(
                                                               db.Likes.user_id == self.user_id).all()]
                        if user.vk_id not in likes_list:
                            like_line = db.Likes()
                            like_line.user_id = self.user_id
                            like_line.vk_id = user.vk_id
                            self.update_db(like_line)
                            self.write_msg("Лайк поставлен ❤")
                        else:
                            self.write_msg("Лайк этому пользователю уже поставлен")
                    elif response == 'черный список':
                        black_list_line = db.Blacklist()
                        black_list_line.user_id = self.user_id
                        black_list_line.vk_id = user.vk_id
                        self.write_msg("Пользователь добавлен в черный список ⛔")
                        self.update_db(black_list_line)
                    user.showed = True
                    self.update_db(user)
                    break
                elif response == 'помощь':
                    self.write_msg(self.show_people.__doc__)
                else:
                    self.write_msg("Упс! К сожалению, я не поняла вашего ответа 😰\n"
                                   "Пожалуйста, используйте команду: 'Помощь', чтобы вывезти меню с командами")

    def show_likes(self):
        """Приветствую тебя в режиме работы со списком лайков!
        Здесь ты можешь использовать следующие команды для навигации:
        &#9989; Дальше => перемещение по списку
        &#9989; Удалить => удаление пользователя из списка лайков
        &#9989; Стоп => возврат в главное меню"""
        likes_list = self.session.query(db.Likes).filter(
            db.Likes.user_id == self.user_id).all()
        if not likes_list:
            self.write_msg("Ваш список лайков пуст ❤")
        for user in likes_list:
            photos = self.vk_back.get_photo(user.vk_id)
            attach = self.vk_back.compare(photos)
            try:
                self.write_msg(attach=attach)
            except ApiError:
                pass
            self.write_msg(f"https://vk.com/id{user.vk_id}")
            while True:
                response = self.listen()
                if response == 'дальше' and user != likes_list[-1]:
                    break
                elif response == 'дальше' and user == likes_list[-1]:
                    self.write_msg("На этом список закончился! ❤\n"
                                   "Вы можете удалить этого пользователя из списка или вернуться "
                                   "в главное меню командой: 'стоп'")
                elif response == 'удалить':
                    self.update_db(user, delete=True)
                    self.write_msg("Лайк убран!")
                    break
                elif response == 'стоп':
                    return
                elif response == 'помощь':
                    self.write_msg(self.show_likes.__doc__)
                else:
                    self.write_msg("Упс! К сожалению, я не поняла вашего ответа 😰\n"
                                   "Пожалуйста, используйте команду: 'Помощь', чтобы вызвать меню с командами")

    def black_list(self):
        while True:
            black_list = self.session.query(db.Blacklist).filter(
                db.Blacklist.user_id == self.user_id).all()
            if not black_list:
                self.write_msg("Ваш черный список пуст ⛔")
                return
            self.write_msg("В черном списке следующие пользователи:")
            show_black_list = [f"https://vk.com/id{user.vk_id}" for user in black_list]
            self.write_msg('\n'.join(show_black_list))
            self.write_msg("Для удаления пользователя введите его id\n"
                           "Для выхода из черного списка: 'Выйти'")
            while True:
                response = self.listen()
                try:
                    response = int(response)
                except ValueError:
                    pass
                if response in [user.vk_id for user in black_list]:
                    user_del = self.session.query(db.Blacklist).filter(
                        db.Blacklist.user_id == self.user_id,
                        db.Blacklist.vk_id == response).first()
                    self.update_db(user_del, delete=True)
                    self.write_msg(f"Пользователь: https://vk.com/id{response} \n"
                                   f"Успешно убран из черного спика")
                    break
                elif response == 'выйти':
                    return
                else:
                    self.write_msg("Упс! К сожалению, я не поняла вашего ответа 😰\n")

    def run(self):
        """Приветствую тебя в главном меню!
        Здесь ты можешь использовать следующие команды для навигации:
        &#9989; Изменить параметры => настройка параметров поиска
        &#9989; Показать лайки => просмотр списка лайков
        &#9989; Начать поиск => начало процесса поиска партнера
        &#9989; Черный список => просмотр и управления заблокированными пользователями
        &#9989; Помощь => вызов меню с командами в режиме поиска и просмотра лайков
        &#9989; Пока => завершение работы"""
        self.name = self.vk_back.get_user_name(self.user_id)
        self.write_msg(f"Приветствую тебя, {self.name} в VKinder 🙋‍♀️\n"
                       f"Для вызова помощи напиши: 'Помощь'")
        while True:
            response = self.listen()
            if response == 'изменить параметры':
                self.change_params()
            elif response == 'показать лайки':
                self.show_likes()
                self.write_msg("Вы вернулись в главное меню")
            elif response == 'начать поиск':
                self.show_people()
                self.write_msg("Поиск окончен.\n"
                               "Вы вернулись в главное меню")
            elif response == 'черный список':
                self.black_list()
                self.write_msg("Вы вернулись в главное меню")
            elif response == 'помощь':
                self.write_msg(self.run.__doc__)
            elif response == 'пока':
                self.write_msg("Работа программы завершена!\n"
                               "Всего хорошего!")
                break
            else:
                self.write_msg("Упс! К сожалению, я не поняла вашего ответа 😰\n"
                               "Пожалуйста, используйте команду: 'Помощь', чтобы вызвать меню с командами")
