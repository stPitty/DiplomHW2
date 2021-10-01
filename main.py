import vkbot
from config import club_token, user_token

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from random import randrange


def write_msg(user_id, message, vk):
    vk.method('messages.send', {'user_id': user_id,
                                'message': message,
                                'random_id': randrange(10 ** 7), })


def main():
    vk = vk_api.VkApi(token=club_token)
    longpoll = VkLongPoll(vk)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                response = event.text.lower()
                if response == "старт":
                    one = vkbot.Bot_front(user_token,
                                          event.user_id,
                                          vk,
                                          longpoll,
                                          VkEventType)
                    one.run()
                else:
                    write_msg(event.user_id, "Не поняла вашего ответа\n"
                                             "Используйте команду 'старт' для начала работы", vk)


if __name__ == '__main__':
    main()
