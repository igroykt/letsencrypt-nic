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
rm auth.py clean.py main.go
```

## Настройка
Путь к интерпретатору Python требуется, чтобы запускать бинарные файлы. Для генерации CLIENTID и CLIENTSECRET необходимо зарегистировать приложение по ссылке https://www.nic.ru/manager/oauth.cgi?step=oauth.app_register. SERVICE_ID можно найти в личном кабинете в разделе "Услуги/DNS-хостинг" в столбце "Услуга".

[GENERAL]
* TOKEN_FILE -> файл, в котором будет хранится access token					(default: nic_token.json)
* SERVICE_ID -> идентификатор услуги								(default: none)
* ZONE -> список доменных зон (разделенные запятыми)						(default: none)
* ADMIN_EMAIL -> адрес email админа, который надо указывать для certbot				(default: none)
* TTL -> время жизни TXT записи									(default: 10)
* SLEEP -> время ожидания пока TXT запись подхватится публичными DNS серверами			(default: 60)
* LOG_FILE -> файл, в который будет записываться все происходящее во время работы приложения	(default: letsencrypt-nic.log)
* OS_SHELL -> shell операционной системы							(default: /bin/bash)
* LE_CONFIG_DIR -> путь к директории хранения конфигов и сертификатов letsencrypt		(default: /etc/letsencrypt)

[WEBSERVER]
* ENABLED -> флаг для проверки включена ли опция						(default: false)
* TEST_CONFIG -> команда для проверки конфигурации веб-сервера					(default: /usr/sbin/nginx -t)
* RELOAD_CONFIG -> команда для перезапуска веб-сервера						(default: /usr/sbin/nginx -s reload)

[SMTP]
* ENABLED -> флаг для проверки включена ли опция						(default: false)
* SERVER -> адрес сервера									(default: 127.0.0.1)
* PORT -> порт сервера										(default: 25)
* USERNAME -> имя пользователя									(default: none)
* PASSWORD -> пароль пользователя								(default: none)
* FROM -> адрес почты от имени которого будет отправлена почта					(default: none)
* TO -> адресат, которому должно уйти письмо							(default: none)

[POSTHOOK]
* ENABLED -> флаг для провеки включена ли опция							(default: false)
* SCRIPT -> путь до исполняемого скрипта							(default: none)

USERNAME, PASSWORD, CLIENTID и CLIENTSECRET прописать в main.go в "Configuration section". Дополнительную информацию о настройке OAuth можно найти по ссылке https://www.nic.ru/help/api-dns-hostinga_3643.html.

LE_CONFIG_DIR полезен в том случае, когда для некоторых ресурсов надо выписывать сертификаты по http challenge, а некоторые по dns challenge. В таком случае для dns challenge можно указать путь скажем /etc/letsencrypt-dns, тогда будет создана эта директория и аккаунты, конфиги и сертификаты для dns challenge будут храниться там.

Если MTA без аутентификации, то в config.ini оставьте пустыми значения USERNAME и PASSWORD в секции SMTP.

POSTHOOK позволяет в конце запустить ваш скрипт. Может пригодится, если например захотите синхронизировать сертификаты на другие сервера.

## Сборка
Перед сборкой убедитесь, что в compile.py в строке shebang указан верный путь к интерпретатору (обычно должен совпадать с значением PYTHON в config.ini). Далее можно запустить ./compile.py.

## Конфиденциальность
В NIC так повелось, что чтобы получить доступ к OAuth необходимо указывать данные от учетной записи, что ни разу не секьюрно (особенно если к серверу имеют доступ другие лица). Отсюда и компиляция Python скриптов в бинарники, чтобы нельзя было модифицировать просто так и основное приложение на Golang, чтобы скрыть учетные данные и также защитить от модификации.

## Тест
Тестирование производится при каждом выписывании сертификатов, но также можно запустить тест вручную:
```
./main -t
```

## Cron
```
#m      #h      #dom    #mon    #dow    #command
0 	0 	1 	* 	* 	/path/to/letsencrypt-nic/main
```
