# Home Assistant Bose 3-2-1 Remote

Готовый набор файлов для Home Assistant, чтобы управлять Bose 3-2-1 через ИК-передатчик на Raspberry Pi.

## Что внутри

- `packages/bose_321_ir_remote.yaml` - команды и скрипты Home Assistant
- `lovelace/bose_321_remote.yaml` - карточка пульта для дашборда

## Как это работает

Текущая реализация использует `shell_command` и вызывает `ir-ctl`:

- `Power On`
- `Volume +`
- `Volume -`

Команды используют те же стартовые scancode, что и в Python-приложении:

- `power_on` -> `nec:0x88774CB3`
- `volume_up` -> `nec:0x887703FC`
- `volume_down` -> `nec:0x887702FD`

## Предпосылки на Raspberry Pi с Home Assistant

Нужно, чтобы на хосте или в окружении Home Assistant были доступны:

- устройство `/dev/lirc0`
- утилита `ir-ctl`
- overlay:

```ini
dtoverlay=gpio-ir-tx,gpio_pin=18
```

## Подключение в Home Assistant

### Вариант 1. Через packages

В `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Потом скопировать:

- `packages/bose_321_ir_remote.yaml` -> `/config/packages/bose_321_ir_remote.yaml`

Перезапустить Home Assistant.

### Вариант 2. Вставить вручную

Содержимое `packages/bose_321_ir_remote.yaml` можно вставить прямо в ваш `configuration.yaml`.

## Карточка в Lovelace

Файл `lovelace/bose_321_remote.yaml` можно:

- вставить в `Manual card`
- или использовать как отдельный view/section

Интерфейс повторяет концепцию предыдущего пульта:

- черный фон
- белый текст
- две кнопки громкости сверху
- кнопка питания снизу

Для стилизации используется `custom:button-card`, поэтому нужен ресурс:

- [button-card](https://github.com/custom-cards/button-card)

Если хотите обойтись без кастомных карточек, можно использовать scripts + стандартный Grid card, но внешний вид будет проще.

## Следующий шаг

Как только будет актуальный доступ к Home Assistant на Raspberry Pi 3, эти файлы можно:

- положить в `/config`
- перезапустить HA
- проверить вызов `shell_command`
- вывести пульт на дашборд
