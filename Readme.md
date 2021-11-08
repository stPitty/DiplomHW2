**Добрый день!**
Благодарю за интерес к данному проекту

Для полноценной функциональности проекта на сервере обязательно
должна быть установлена postgreSQL.  
При первой инициализации программы нужно выполнить несколько действий:
1. Необходимо создать бд и прописать данные (название, логин и пароль в 
   словарь <code>database</code> расположенном: <code>data.info</code>   
   Изначально в <code>database</code> уже заданы параметры по умолчанию.
   Вы можете просто создать бд с этими параметрами.
   Для этого выполните:  
   <code>CREATE USER vkinder_manager WITH PASSWORD 'manager29092021';</code>   
   <code>CREATE DATABASE vk_stankin WITH OWNER vkinder_manager;</code>   

   

2. Необходимо создать таблицу с данными в бд.
Для этого запустите один раз файл <code>data/db.py</code>
