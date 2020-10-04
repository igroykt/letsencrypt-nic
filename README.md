# LetsEncrypt NIC

Приложение для выписывания wildcard сертификатов используя NIC.RU DNS API.

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
Путь к интерпретатору Python требуется, чтобы запускать бинарные файлы.

Для генерации CLIENTID и CLIENTSECRET необходимо зарегистировать приложение по ссылке https://www.nic.ru/manager/oauth.cgi?step=oauth.app_register.

SERVICE_ID можно найти в личном кабинете в разделе "Услуги/DNS-хостинг" в столбце "Услуга".

**[GENERAL]**

| Function      | Description                                                            | Default value    |
|---------------|------------------------------------------------------------------------|------------------|
| SERVICE_ID    | Идентификатор услуги                                                   | None             |
| ZONE          | Список доменных зон (разделенных запятыми)                             | None             |
| ADMIN_EMAIL   | E-mail администратора certbot                                          | None             |
| TTL           | Время жизни TXT записей                                                | 10               |
| SLEEP         | Время ожидания пока TXT запись подхватится публичными DNS серверами    | 120              |
| OS_SHELL      | Shell операционной системы                                             | /bin/bash        |
| LE_CONFIG_DIR | Путь к директории для хранения конфигураций и сертификатов LetsEncrypt | /etc/letsencrypt |

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

**[POSTHOOK]**

| Function | Description                  | Default value |
|----------|------------------------------|---------------|
| ENABLED  | Флаг активации опции         | false         |
| SCRIPT   | Путь до исполняемого скрипта | None          |

USERNAME, PASSWORD, CLIENTID и CLIENTSECRET прописать в main.go в "Configuration section". Дополнительную информацию о настройке OAuth можно найти по ссылке https://www.nic.ru/help/api-dns-hostinga_3643.html.

LE_CONFIG_DIR полезен в том случае, когда для некоторых ресурсов надо выписывать сертификаты по http challenge, а некоторые по dns challenge. В таком случае для dns challenge можно указать путь скажем /etc/letsencrypt-dns, тогда будет создана эта директория и аккаунты, конфиги, сертификаты для dns challenge будут храниться там.

Если MTA без аутентификации, то в config.ini оставьте пустыми значения USERNAME и PASSWORD в секции SMTP.

POSTHOOK позволяет в конце запустить ваш скрипт. Может пригодится, если например захотите синхронизировать сертификаты на другие сервера.

## Сборка
Перед сборкой убедитесь, что в compile.py в строке shebang указан верный путь к интерпретатору (обычно должен совпадать с значением PYTHON в config.ini). Далее можно запустить ./compile.py.

## Конфиденциальность
В NIC так повелось, что чтобы получить доступ к OAuth необходимо указывать данные от учетной записи, что ни разу не секьюрно (особенно если к серверу имеют доступ другие лица). Отсюда и компиляция Python скриптов в бинарники, чтобы нельзя было модифицировать просто так и основное приложение на Golang, чтобы скрыть учетные данные и также защитить от модификации.

## Тест
Тестирование производится при каждом выписывании сертификатов, но также можно запустить тест вручную:
```
./main -v -t
```

## Очистка TXT
Если надо удалить большое количество DNS challenge, то можно сделать следующее:
```
./main -v -cleanall
```
Эта операция удалит все TXT записи типа _acme-challenge.

## Cron
```
#m      #h      #dom    #mon    #dow    #command
0 	0 	1 	* 	* 	/path/to/letsencrypt-nic/main
```
