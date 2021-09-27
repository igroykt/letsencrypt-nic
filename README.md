![GitHub Workflow Status](https://img.shields.io/github/workflow/status/igroykt/letsencrypt-nic/letsencrypt-nic%20build)
![GitHub](https://img.shields.io/github/license/igroykt/letsencrypt-nic)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/igroykt/letsencrypt-nic)

# LetsEncrypt NIC

Приложение для выписывания wildcard сертификатов используя NIC.RU DNS API.

## Зависимости
* Python 3.8
* Certbot

## Unix
### Сборка и установка 
```
pip3 install certbot
pip3 install -r requirements.txt
mv config.sample.ini config.ini
# подправить config.ini
python setup.py build
mkdir /root/bin/letsencrypt-nic
mv build/* /root/bin/letsencrypt-nic
cp config.ini /root/bin/letsencrypt-nic
```
Ключ шифрования меняется при каждой сборке.

### Настройка
Для генерации CLIENTID и CLIENTSECRET необходимо зарегистировать приложение по ссылке https://www.nic.ru/manager/oauth.cgi?step=oauth.app_register.

SERVICE_ID можно найти в личном кабинете в разделе "Услуги/DNS-хостинг" в столбце "Услуга".

Запустить "./main -a" и ввести данные аутентификации. 

Дополнительную информацию о настройке OAuth можно найти по ссылке https://www.nic.ru/help/api-dns-hostinga_3643.html.


### Конфиденциальность
В NIC так повелось, что чтобы получить доступ к OAuth необходимо указывать данные от учетной записи, что ни разу не секьюрно (особенно если к серверу имеют доступ другие лица). Отсюда и компиляция Python скриптов в бинарники, чтобы скрыть учетные данные и защитить от модификации.

### Тест
Тестовый запуск:
```
./main -v -t
```

### Очистка TXT
Удаляются все найденные (попадающие под критерий поиска) записи. Так что можно не беспокоиться, что где-то останется лишняя запись _acme-challenge.

### Cron
```
#m      #h      #dom    #mon    #dow    #command
0 	0 	1 	* 	* 	/path/to/letsencrypt-nic/main
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
```