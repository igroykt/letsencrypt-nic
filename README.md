# LetsEncrypt NIC

Приложение для выписывания wildcard сертификатов используя NIC.RU DNS API для Linux.

## Зависимости
* Python 3.x
* Golang 1.x
* Certbot 1.x

## Установка
```
pip3 install -r requirements.txt
go get gopkg.in/ini.v1
mv config.sample.ini config.ini
# подправить config.ini
./compile.py
rm -f auth.py clean.py clean_all.py main.go
```

## Настройка
Для генерации CLIENTID и CLIENTSECRET необходимо зарегистировать приложение по ссылке https://www.nic.ru/manager/oauth.cgi?step=oauth.app_register.

SERVICE_ID можно найти в личном кабинете в разделе "Услуги/DNS-хостинг" в столбце "Услуга".

USERNAME, PASSWORD, CLIENTID и CLIENTSECRET прописать в main.go в "Configuration section".

Дополнительную информацию о настройке OAuth можно найти по ссылке https://www.nic.ru/help/api-dns-hostinga_3643.html.

**[GENERAL]**

| Function      | Description                                                            | Default value    |
|---------------|------------------------------------------------------------------------|------------------|
| SERVICE_ID    | Идентификатор услуги                                                   | None             |
| ZONE          | Список доменных зон (разделенных запятыми)                             | None             |
| ADMIN_EMAIL   | E-mail администратора certbot                                          | None             |
| TTL           | Время жизни TXT записей                                                | 10               |
| SLEEP         | Время ожидания пока TXT запись подхватится публичными DNS серверами    | 120              |
| RETRIES       | Количество попыток подтверждения TXT записи в DNS                      | 3                |
| OS_SHELL      | Shell операционной системы                                             | /bin/bash        |
| LE_CONFIG_DIR | Путь к директории для хранения конфигураций и сертификатов LetsEncrypt | /etc/letsencrypt |
| PYTHON        | Путь к интерпретатору Python                                           | /usr/bin/python3 |

LE_CONFIG_DIR полезен в том случае, когда для некоторых ресурсов надо выписывать сертификаты по http challenge, а некоторые по dns challenge. В таком случае для dns challenge можно указать путь скажем /etc/letsencrypt-dns, тогда будет создана эта директория и аккаунты, конфиги, сертификаты для dns challenge будут храниться там.

Путь к интерпретатору Python требуется, чтобы запускать бинарные файлы.

**[WEBSERVER]**

| Function      | Description                                   | Default value             |
|---------------|-----------------------------------------------|---------------------------|
| ENABLED       | Флаг активации опции                          | false                     |
| TEST_CONFIG   | Команда тестирования конфигуарции веб-сервера | /usr/sbin/nginx -t        |
| RELOAD_CONFIG | Команда перезапуска веб-сервера               | /usr/sbin/nginx -s reload |

**[SMTP]**

| Function | Description                      | Default value |
|----------|----------------------------------|---------------|
| ENABLED  | Флаг активации опции             | false         |
| SERVER   | Адрес сервера                    | 127.0.0.1     |
| PORT     | Порт сервера                     | 25            |
| USERNAME | Логин                            | None          |
| PASSWORD | Пароль                           | None          |
| FROM     | Исходящий адрес почты            | None          |
| TO       | Реципиент (разделенные запятыми) | None          |

Если MTA без аутентификации, то оставьте пустыми значения USERNAME и PASSWORD.

**[POSTHOOK]**

| Function | Description                  | Default value |
|----------|------------------------------|---------------|
| ENABLED  | Флаг активации опции         | false         |
| SCRIPT   | Путь до исполняемого скрипта | None          |

POSTHOOK позволяет в конце запустить ваш скрипт. Может пригодится, если например захотите синхронизировать сертификаты на другие сервера.

## Сборка
Перед сборкой убедитесь, что в compile.py в строке shebang указан верный путь к интерпретатору (обычно должен совпадать с значением PYTHON в config.ini). Далее можно запустить ./compile.py.

## Конфиденциальность
В NIC так повелось, что чтобы получить доступ к OAuth необходимо указывать данные от учетной записи, что ни разу не секьюрно (особенно если к серверу имеют доступ другие лица). Отсюда и компиляция Python скриптов в бинарники, чтобы нельзя было модифицировать просто так и основное приложение на Golang, чтобы скрыть учетные данные и также защитить от модификации.

## Тест
Тестовый запуск:
```
./main -v -t
```

## Очистка TXT
Удаляются все найденные (попадающие под критерий поиска) записи. Так что можно не беспокоиться, что где-то останется лишняя запись _acme-challenge.

## Cron
```
#m      #h      #dom    #mon    #dow    #command
0 	0 	1 	* 	* 	/path/to/letsencrypt-nic/main
```
