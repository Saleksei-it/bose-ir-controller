# Bose 3-2-1 IR Controller

Python GUI-приложение для Raspberry Pi 5 / Twister OS, которое управляет музыкальным центром Bose 3-2-1 по ИК через GPIO.

Сейчас проект рассчитан на два сценария:
- `test mode` для отладки интерфейса без ИК-железа
- `live mode` для реальной отправки ИК-команд через `ir-ctl` и `/dev/lirc0`

## Возможности

- графический интерфейс на `tkinter`
- кнопки `Power On`, `Volume +`, `Volume -`
- тестовый режим без передачи ИК
- конфиг ИК-команд через `JSON`
- работа через стандартный Linux IR stack на Raspberry Pi

## Структура проекта

- `app.py` - основное GUI-приложение
- `bose_ir_config.json` - конфиг устройства и ИК-команд
- `requirements.txt` - Python-зависимости

## Python requirements

Библиотек из PyPI проект почти не требует. GUI сделан на стандартной библиотеке Python.

Установка:

```bash
python3 -m pip install -r requirements.txt
```

На Raspberry Pi также нужны системные пакеты:

```bash
sudo apt update
sudo apt install -y python3 python3-tk v4l-utils
```

## Быстрый запуск на Raspberry Pi

1. Скопировать проект на Raspberry Pi.
2. Установить зависимости:

```bash
sudo apt update
sudo apt install -y python3 python3-tk v4l-utils
python3 -m pip install -r requirements.txt
```

3. Запустить приложение:

```bash
python3 app.py
```

## Тестовый режим

По умолчанию в `bose_ir_config.json` включено:

```json
"test_mode": true
```

В этом режиме:
- интерфейс полностью работает
- нажатия кнопок отображаются в окне журнала
- реальные ИК-команды не отправляются

Это удобно, пока модуль передатчика/приемника еще не подключен.

## Включение live mode на Raspberry Pi

Когда ИК-модуль будет подключен, нужно включить Linux overlay для передачи.

Для Raspberry Pi OS / Twister OS обычно используется:
- `/boot/firmware/config.txt`

Добавьте строку:

```ini
dtoverlay=gpio-ir-tx,gpio_pin=18
```

Если система использует старый путь, проверьте:
- `/boot/config.txt`

После этого:

```bash
sudo reboot
```

Проверка:

```bash
ls /dev/lirc*
ir-ctl --features -d /dev/lirc0
```

Затем можно выключить тестовый режим:
- прямо в интерфейсе
- или поставить `"test_mode": false` в `bose_ir_config.json`

## Пример ручной отправки ИК-команды

```bash
ir-ctl --device /dev/lirc0 --send nec:0x887703FC
```

## Настройка команд

Команды хранятся в `bose_ir_config.json`.

Вариант через scancode:

```json
{
  "protocol": "nec",
  "scancode": "0x887703FC"
}
```

Вариант через raw-последовательность:

```json
{
  "protocol": "raw",
  "raw": [9000, 4500, 560, 560, 560, 1690]
}
```

`raw` задается в микросекундах: импульс, пауза, импульс, пауза.

## Стартовые коды

Текущие коды в конфиге добавлены как предварительные. Они не подтверждены замером именно вашего пульта Bose 3-2-1.

Когда приедет ИК-плата, правильный путь такой:
- считать реальные коды с оригинального пульта
- обновить `bose_ir_config.json`
- протестировать команды в `live mode`

## Разработка

Проверка синтаксиса:

```bash
python3 -m py_compile app.py
```

## Источники по Bose IR

- [Bose IR Receiver Spec 2.2 preview](https://www.eserviceinfo.com/preview_html.php?fileid=60272&previewid=31152)
- [Bose Serial Interface guide snippet with key codes](https://www.scribd.com/document/566423184/BoseSerialProtocol-2010-11-09-V1-01)
