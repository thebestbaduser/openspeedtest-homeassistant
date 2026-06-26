# OpenSpeedTest CLI для Home Assistant

[![Validate](https://github.com/thebestbaduser/openspeedtest-homeassistant/actions/workflows/validate.yml/badge.svg)](https://github.com/thebestbaduser/openspeedtest-homeassistant/actions/workflows/validate.yml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/thebestbaduser/openspeedtest-homeassistant)](https://github.com/thebestbaduser/openspeedtest-homeassistant/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Кастомная интеграция для [Home Assistant](https://www.home-assistant.io/), которая
запускает скрипт [openspeedtest-cli](https://openspeedtest.ru/cli/openspeedtest-cli)
и публикует результаты замеров в виде сущностей.

**Репозиторий:** https://github.com/thebestbaduser/openspeedtest-homeassistant

## Как это работает

Интеграция **не встраивает** код замера в Home Assistant. Она:

1. Скачивает (или использует уже установленный) скрипт `openspeedtest-cli` в
   `/config/openspeedtest-cli`.
2. По расписанию или по кнопке запускает его как subprocess.
3. Парсит stdout (`Ping`, `Jitter`, `Download`, `Upload`, `Сервер`) и публикует
   сенсоры.

Так интеграция остаётся без внешних pip-зависимостей (`requirements: []` в
`manifest.json`), а обновления логики замера приходят с
[openspeedtest.ru](https://openspeedtest.ru/) вместе с CLI.

## Два инструмента на openspeedtest.ru

На странице [/cli/](https://openspeedtest.ru/cli/) сейчас продвигается
**enterprise-агент** (`openspeedtest-agent.py`). **Эта интеграция использует
другой файл** — простой speedtest-скрипт:

| | `openspeedtest-cli` | `openspeedtest-agent.py` |
|---|---|---|
| Назначение | Разовый/периодический замер скорости | Мониторинг серверов 24/7 |
| Зависимости | Только stdlib Python 3 | `requests`, `psutil`, systemd |
| Наша интеграция | ✅ | ❌ |

Прямая ссылка на скачивание скрипта, который нужен интеграции:

```
https://openspeedtest.ru/cli/openspeedtest-cli
```

## Возможности

- Сенсоры: **Download**, **Upload**, **Ping**, **Jitter**, **Last test**
- Кнопка **Запустить тест** для ручного замера
- Автоматические тесты по расписанию (по умолчанию каждые 6 часов)
- Настройка сервера, потоков и длительности теста через UI
- Автозагрузка CLI в директорию `config` при первой настройке
- Опциональная отправка результатов на [OpenSpeedTest.ru](https://openspeedtest.ru/)

## Требования

| Компонент | Версия |
|-----------|--------|
| Home Assistant | 2024.12.0+ |
| Python | 3 (уже есть в HA) |
| OpenSpeedTest CLI | [openspeedtest-cli](https://openspeedtest.ru/cli/openspeedtest-cli) |

CLI — один Python-скрипт без внешних зависимостей (версия 2.0 на сайте, июнь 2026).

---

## Установка через HACS

> После одобрения PR в [hacs/default](https://github.com/hacs/default) интеграция
> появится в официальном каталоге HACS. Пока репозиторий подключается как
> **Custom repository** (см. ниже).

1. Установите [HACS](https://hacs.xyz/)
2. **HACS → Integrations → ⋮ → Custom repositories**
3. Добавьте репозиторий:
   - URL: `https://github.com/thebestbaduser/openspeedtest-homeassistant`
   - Category: **Integration**
4. Найдите **OpenSpeedTest CLI** → **Download**
5. **Перезагрузите Home Assistant**
6. **Settings → Devices & Services → Add Integration** → **OpenSpeedTest CLI**

### Первая настройка

| Поле | Рекомендация |
|------|--------------|
| Path to CLI | `/config/openspeedtest-cli` (по умолчанию) |
| Download CLI | Включить, если файла ещё нет |
| Scan interval | `21600` (6 ч), минимум `900` (15 мин) |
| Submit results | Выключено, если не нужна отправка на сайт |
| API key | 64 hex-символа из [личного кабинета](https://openspeedtest.ru/) |

При включённой отправке результаты появляются в разделе **«Мониторинг CLI»**
личного кабинета OpenSpeedTest.

---

## Ручная установка интеграции

Скопируйте папку `custom_components/openspeedtest_cli` в:

```
/config/custom_components/openspeedtest_cli/
```

Перезагрузите Home Assistant.

---

## Где хранить CLI

### Что такое `/config`

`/config` — **постоянная директория конфигурации** Home Assistant. В ней лежат `configuration.yaml`, `.storage/`, `custom_components/` и другие данные.

| Тип установки | Путь внутри HA | Где на диске хоста |
|---------------|----------------|---------------------|
| Container / HA OS | `/config` | Volume, который вы смонтировали при установке |
| Core (venv) | `~/.homeassistant` или своя папка | Указана при установке |

**HACS обновляет интеграцию именно в `/config/custom_components/`**, а не по номеру коммита GitHub.

### Почему CLI должен быть в `/config`

При обновлении Home Assistant **контейнер пересоздаётся**. Всё внутри образа (`/usr/local/bin`, `apt install` и т.д.) **пропадает**. Директория `/config` — **единственная постоянная**.

Рекомендуемый путь:

```
/config/openspeedtest-cli
```

Интеграция может скачать CLI туда автоматически (галочка при настройке) или вручную:

```bash
curl -sLo /config/openspeedtest-cli https://openspeedtest.ru/cli/openspeedtest-cli
sed -i 's/\r$//' /config/openspeedtest-cli   # исправить CRLF, если нужно
chmod +x /config/openspeedtest-cli
/config/openspeedtest-cli --help
```

### CLI 2.0: полезные команды

Узнать ID сервера для поля **Server ID** в настройках интеграции:

```bash
/config/openspeedtest-cli --list-servers
```

Сохранить API-ключ в конфиг CLI (альтернатива полю в интеграции):

```bash
/config/openspeedtest-cli configure
```

Конфиг CLI хранится в `~/.config/openspeedtest-cli/config.json` (внутри
контейнера HA — в home пользователя, от которого запускается HA).

Ручной тест без отправки на сайт:

```bash
/config/openspeedtest-cli --no-submit --threads 8 --duration 10
```

---

## Настройки после установки

**Settings → Devices & Services → OpenSpeedTest CLI → Configure**

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| Path to CLI | Путь к исполняемому файлу | `/config/openspeedtest-cli` |
| Scan interval | Интервал автотестов (сек) | `21600` (6 ч) |
| Server ID | ID сервера (пусто = автовыбор) | — |
| Threads | Потоки теста | `8` |
| Duration | Длительность download/upload (сек) | `10` |
| Submit results | Отправка на openspeedtest.ru | `false` |
| API key | Ключ из личного кабинета (64 hex-символа) | — |

> Минимальный интервал — **900 секунд (15 минут)**. Тесты нагружают канал.
>
> Если **Submit results** включён, но API-ключ не задан, CLI автоматически
> выполнит тест с `--no-submit` и выведет предупреждение в лог.

При перезапуске HA **сразу показываются последние сохранённые результаты** — новый тест запускается только если истёк интервал обновления. Первый тест (если истории ещё нет) стартует через 30 секунд после загрузки.

---

## Сущности

| Entity ID | Описание |
|-----------|----------|
| `sensor.<имя>_download` | Скорость скачивания (Mbit/s) |
| `sensor.<имя>_upload` | Скорость отдачи (Mbit/s) |
| `sensor.<имя>_ping` | Ping (ms) |
| `sensor.<имя>_jitter` | Jitter (ms) |
| `sensor.<имя>_last_test` | Время последнего теста (timestamp) |
| `button.<имя>_run_test` | Запуск теста вручную |

На сенсорах скорости, пинга и джиттера доступен атрибут `server` (имя
выбранного сервера OpenSpeedTest).

---

## Автоматизация

Уведомление при падении скорости ниже 50 Mbit/s:

```yaml
automation:
  - alias: "Низкая скорость скачивания"
    trigger:
      - platform: numeric_state
        entity_id: sensor.openspeedtest_cli_download
        below: 50
    action:
      - service: notify.mobile_app
        data:
          message: >
            Скорость скачивания: {{ states('sensor.openspeedtest_cli_download') }} Mbit/s
            (сервер: {{ state_attr('sensor.openspeedtest_cli_download', 'server') }})
```

---

## Обновление через HACS

HACS смотрит **версию в `manifest.json` на ветке `main`**, а не номер коммита.

1. **HACS → Integrations → OpenSpeedTest CLI**
2. **Update** или **⋮ → Redownload**
3. При проблемах: **HACS → ⋮ → Clear cache**
4. **Перезагрузить Home Assistant**

Проверка установленной версии:

```bash
grep '"version"' /config/custom_components/openspeedtest_cli/manifest.json
```

---

## Устранение неполадок

### HACS не обновляет версию

Убедитесь, что файлы обновились **на диске HA**, а не только скачались на компьютер:

```bash
grep version /config/custom_components/openspeedtest_cli/manifest.json
```

Если версия старая — **Redownload** + **Clear cache** + перезагрузка HA.

Принудительное обновление одного файла:

```bash
wget -O /config/custom_components/openspeedtest_cli/config_flow.py \
  https://raw.githubusercontent.com/thebestbaduser/openspeedtest-homeassistant/main/custom_components/openspeedtest_cli/config_flow.py
```

### `/usr/bin/env: 'python3\r': No such file or directory`

Скрипт с Windows-переводами строк (CRLF):

```bash
sed -i 's/\r$//' /config/openspeedtest-cli
chmod +x /config/openspeedtest-cli
```

Интеграция при автозагрузке исправляет CRLF автоматически.

### Скачивание/отдача = 0,00 Mbit/s, пинг нормальный

1. Запустите тест вручную кнопкой **Запустить тест** и подождите ~60 сек
2. Проверьте CLI напрямую:

```bash
/config/openspeedtest-cli --no-submit --threads 8 --duration 10
```

Если и в CLI нули — проблема в сетевом доступе из контейнера HA до серверов OpenSpeedTest.

### Ошибка `invalid int value: '8.0'`

Обновите интеграцию до **1.0.3+** (исправлено приведение типов NumberSelector).

### Настройки не открываются (500 Internal Server Error)

Обновите интеграцию до **1.0.7+** (исправлен options flow).

### Актуальная версия

Текущий релиз — **1.3.2**. См. [Releases](https://github.com/thebestbaduser/openspeedtest-homeassistant/releases)
и [CHANGELOG.md](CHANGELOG.md).

---

## Иконка

- **HACS** — `icon.png` в корне репозитория
- **Home Assistant 2026.3+** — `custom_components/openspeedtest_cli/brand/icon.png` и `logo.png` (страница интеграций и устройств)

Подробный чеклист для подачи в официальный каталог HACS — в
[HACS_SUBMISSION.md](HACS_SUBMISSION.md). Готовый текст PR для
`hacs/default` — в [HACS_DEFAULT_PR.md](HACS_DEFAULT_PR.md).

## Лицензия

MIT — см. [LICENSE](LICENSE).
