# OpenSpeedTest CLI для Home Assistant

Кастомная интеграция для [Home Assistant](https://www.home-assistant.io/), которая запускает [OpenSpeedTest CLI](https://openspeedtest.ru/cli/) и публикует результаты замеров в виде сущностей.

## Возможности

- Сенсоры: **Download**, **Upload**, **Ping**, **Jitter**
- Кнопка **Run speed test** для ручного запуска
- Периодические автоматические тесты (по умолчанию каждые 6 часов)
- Настройка сервера, потоков, длительности теста
- Опциональная отправка результатов на OpenSpeedTest.ru
- Автоматическая установка CLI в директорию `config` при первой настройке

## Требования

1. Home Assistant **2023.8+**
2. [OpenSpeedTest CLI](https://openspeedtest.ru/cli/) — Python 3, без внешних зависимостей

## Где хранить CLI

### Home Assistant Container / HA OS (рекомендуется)

При обновлении Home Assistant **контейнер пересоздаётся**. Всё, что установлено внутри контейнера (`/usr/local/bin`, пакеты через apt и т.д.), **пропадает**.

Единственная постоянная директория — **`/config`** (volume с вашей конфигурацией). Поэтому CLI нужно хранить там:

```
/config/openspeedtest-cli
```

При добавлении интеграции путь по умолчанию уже указывает на `/config/openspeedtest-cli`. Можно включить галочку **«Скачать CLI в директорию config»** — интеграция сама загрузит скрипт при настройке.

### Обычная установка (venv / Core)

Директория config тоже сохраняется между обновлениями, поэтому тот же путь `{config_dir}/openspeedtest-cli` — надёжный вариант. Альтернатива: установить CLI системно в `PATH`, если удобнее.

## Установка через HACS

1. Установите [HACS](https://hacs.xyz/)
2. Добавьте custom repository:
   - Repository: `https://github.com/thebestbaduser/openspeedtest-homeassistant`
   - Category: **Integration**
3. Установите **OpenSpeedTest CLI** через HACS
4. Перезагрузите Home Assistant
5. **Settings → Devices & Services → Add Integration** → **OpenSpeedTest CLI**
6. Оставьте путь `/config/openspeedtest-cli` и включите автозагрузку CLI, если файла ещё нет

## Ручная установка CLI (опционально)

Если не используете автозагрузку из интеграции:

```bash
# На хосте — скопируйте файл в смонтированную директорию config
curl -sLo openspeedtest-cli https://openspeedtest.ru/cli/openspeedtest-cli
chmod +x openspeedtest-cli
mv openspeedtest-cli /path/to/your/homeassistant/config/openspeedtest-cli
```

## Настройка

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| Path to CLI | Путь к исполняемому файлу | `/config/openspeedtest-cli` |
| Download CLI | Скачать скрипт в config при настройке | вкл., если файла нет |
| Scan interval | Интервал автотестов (сек) | `21600` (6 ч) |
| Server ID | ID сервера OpenSpeedTest | автовыбор |
| Threads | Потоки теста | `8` |
| Duration | Длительность download/upload (сек) | `10` |
| Submit results | Отправка на openspeedtest.ru | `false` |
| API key | Ключ из личного кабинета | — |

Минимальный интервал автотестов — **15 минут** (тесты нагружают канал).

## Сущности

| Entity | Описание |
|--------|----------|
| `sensor.*_download` | Скорость скачивания (Mbit/s) |
| `sensor.*_upload` | Скорость отдачи (Mbit/s) |
| `sensor.*_ping` | Ping (ms) |
| `sensor.*_jitter` | Jitter (ms) |
| `button.*_run_test` | Запуск теста вручную |

## Устранение неполадок

### `/usr/bin/env: 'python3\r': No such file or directory`

Скрипт скачан с Windows-переводами строк (CRLF). Linux не может запустить shebang `#!/usr/bin/env python3\r`.

Исправление:

```bash
sed -i 's/\r$//' /config/openspeedtest-cli
chmod +x /config/openspeedtest-cli
```

Или через `dos2unix`:

```bash
dos2unix /config/openspeedtest-cli
chmod +x /config/openspeedtest-cli
```

Проверка:

```bash
./openspeedtest-cli --help
```


## Лицензия

MIT — см. [LICENSE](LICENSE).
