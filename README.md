![Build Status](https://github.com/igroykt/letsencrypt-nic/actions/workflows/letsencrypt-nic.yml/badge.svg?branch=master)
![GitHub](https://img.shields.io/github/license/igroykt/letsencrypt-nic)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/igroykt/letsencrypt-nic)

# LetsEncrypt NIC

Приложение для выписывания wildcard сертификатов используя NIC.RU DNS API.

## Зависимости
* Python 3.9+
* Certbot

## Unix
### Сборка и установка 
```
dnf install patchelf
pip3 install certbot
pip3 install -r requirements.txt
mv config.sample.ini config.ini
# подправить config.ini
python3 setup.py build
mkdir $HOME/letsencrypt-nic
mv build/exe.[platform]/* $HOME/letsencrypt-nic
cp config.ini $HOME/letsencrypt-nic
$HOME/letsencrypt-nic/main -a
```
Ключ шифрования меняется при каждой сборке.

### Настройка
Для генерации CLIENT_ID и CLIENT_SECRET необходимо зарегистировать приложение по ссылке https://www.nic.ru/manager/oauth.cgi?step=oauth.app_register.

SERVICE_ID можно найти в личном кабинете в разделе "Услуги/DNS-хостинг" в столбце "Услуга".

Запустить "./main -a" и ввести данные аутентификации. 

Дополнительную информацию о настройке OAuth можно найти по ссылке https://www.nic.ru/help/api-dns-hostinga_3643.html.

Инфо по конфигурации смотрите в wiki.

### Конфиденциальность
В NIC так повелось, что чтобы получить доступ к OAuth необходимо указывать данные от учетной записи, что ни разу не секьюрно (особенно если к серверу имеют доступ другие лица). Отсюда и компиляция Python скриптов в бинарники, чтобы скрыть учетные данные и защитить от модификации.

### Примеры
Первый запуск:
```
$HOME/main -v -n
```
Тестовый запуск:
```
$HOME/main -v -t
```
Обновление сертификатов:
```
$HOME/main -v
```

### Очистка TXT
Удаляются все найденные (попадающие под критерий поиска) записи. Так что можно не беспокоиться, что где-то останется лишняя запись _acme-challenge.

### Cron
```
#m      #h      #dom    #mon    #dow    #command
0 	    0 	    1 	    * 	    * 	    $HOME/letsencrypt-nic/main
```

## Windows
### Сборка и установка 
```
# установить certbot https://dl.eff.org/certbot-beta-installer-win32.exe
pip install -r requirements.txt
move config.sample.ini config.ini
# подправить config.ini
python setup.py build
mkdir c:\letsencrypt-nic
move build\* c:\letsencrypt-nic
copy config.ini c:\letsencrypt-nic
c:\letsencrypt-nic\main.exe -a
```

## Проблема истекшего сертификата 30.09.21
Читайте инфу в wiki.
