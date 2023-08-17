import telebot
from telebot import types
import requests
import urllib.parse
from datetime import datetime, timedelta

import config



class TelegramBot:
    def __init__(self, token) -> None:
        # Инициализируем бота
        self.bot = telebot.TeleBot(token)
        self.set_defaut_commands()

        # Обработка команды /start
        @self.bot.message_handler(commands=['start'])
        def command_handler(message: types.Message):
            chat_id = message.chat.id
            
            message_text = "Чтобы начать, загрузите изображение, на котором изображен персонаж, сцена или что-то еще из мира аниме. После отправки изображения, я начну анализ и поиск аниме."
            self.bot.send_message(chat_id, message_text)

        # Обработка полученных фото
        @self.bot.message_handler(content_types=['photo'])
        def photo_handler(message: types.Message):
            chat_id = message.chat.id
            
            # Получаем фото
            photo_file_id = message.photo[-1].file_id
            photo_url = self.bot.get_file_url(photo_file_id)

            # Отправляем запрос на поиск аниме
            req = requests.get(config.TRACE_APIURL
                .format(urllib.parse.quote_plus(photo_url))).json()

            # Получем ответ
            data = req['result'][0]

            # Парсим полученное
            url_anilist = config.ANILIST_URL + str(data['anilist'])
            filename = data['filename']
            episode = data['episode']
            similarity = round(data['similarity'], 2)
            time = f"{self.formatted_time(data['from'])} - {self.formatted_time(data['to'])}"
            media = data['video']

            # Текст сообщения
            message_text = ("Результат вашего запроса. Схожесть: {similarity}\n\nНазвание: `{filename}`\nЭпизод: {episode}\nВремя: {time}"
                .format(similarity=similarity, filename=filename, episode=episode, time=time))
            
            # Кнопки сообщения
            webapp = types.WebAppInfo(url_anilist)
            message_buttons = types.InlineKeyboardMarkup(row_width=1)
            button_anilist = types.InlineKeyboardButton("anilist.co", web_app=webapp)
            button_anilist_url = types.InlineKeyboardButton("Открыть ссылку", url=url_anilist)
            message_buttons.add(button_anilist, button_anilist_url)

            # Отправляем результат
            self.bot.send_video(chat_id, media, caption=message_text, reply_markup=message_buttons, parse_mode="Markdown")
            
    # Установка команд бота
    def set_defaut_commands(self):
        commands = [
            types.BotCommand('start', 'Начать работу.'),
            ]
        self.bot.set_my_commands(commands)

    # Получение времени из секунд
    def formatted_time(self, seconds):
        time_delta = timedelta(seconds=seconds)
        time_formatted = datetime(1900, 1, 1) + time_delta

        return time_formatted.strftime("%M:%S")

    # Уведомления для админов
    def send_admin_alert(self, message):
        for admin_id in config.ADMINS_LIST:
            self.bot.send_message(admin_id, message)

    # Запуск бота
    def start(self):
        self.send_admin_alert("Бот успешно запущен :3")
        self.bot.infinity_polling()


if __name__ == "__main__":
    TelegramBot(config.TELEGRAM_TOKEN).start()