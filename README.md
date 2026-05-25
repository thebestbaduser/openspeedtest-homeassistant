# OpenSpeedTest CLI для Home Assistant

Кастомная интеграция для [Home Assistant](https://www.home-assistant.io/), которая запускает [OpenSpeedTest CLI](https://openspeedtest.ru/cli/) и публикует результаты замеров в виде сущностей.

## Возможности

- Сенсоры: **Download**, **Upload**, **Ping**, **Jitter**
- Кнопка **Run speed test** для ручного запуска
- Периодические автоматические тесты (по умолчанию каждые 6 часов)
- Настройка сервера, потоков, длительности теста
- Опциональная отправка результатов на OpenSpeedTest.ru

## Требования

1. Home Assistant **2023.8+**
2. Установленный [OpenSpeedTest CLI](https://openspeedtest.ru/cli/):

```bash
curl -sLo openspeedtest-cli https://openspeedtest.ru/cli/openspeedtest-cli
chmod +x openspeedtest-cli
sudo mv openspeedtest-cli /usr/local/bin/
```

> **Важно:** CLI должен быть доступен на той же машине, где работает Home Assistant (или в контейнере HA, если используете Docker/Supervised).

### Home Assistant OS / Container

Скопируйте `openspeedtest-cli` в директорию, доступную из контейнера, и укажите полный путь при настройке интеграции, например:

- `/config/openspeedtest-cli`
- `/usr/local/bin/openspeedtest-cli` (если установлен через SSH add-on)

## Установка через HACS

1. Установите [HACS](https://hacs.xyz/)
2. Добавьте custom repository:
   - Repository: `https://github.com/thebestbaduser/openspeedtest-homeassistant`
   - Category: **Integration**
3. Установите **OpenSpeedTest CLI** через HACS
4. Перезагрузите Home Assistant
5. **Settings → Devices & Services → Add Integration** → найдите **OpenSpeedTest CLI**

## Ручная установка

Скопируйте папку `custom_components/openspeedtest_cli` в `config/custom_components/` вашего Home Assistant и перезагрузите систему.

## Настройка

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| Path to CLI | Путь к исполняемому файлу | `openspeedtest-cli` |
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

У всех сенсоров есть атрибуты `server`, `last_run`, `error`.

## Автоматизация

Пример: уведомление при падении скорости ниже 50 Mbit/s:

```yaml
automation:
  - alias: "Low download speed alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.openspeedtest_cli_download
        below: 50
    action:
      - service: notify.mobile_app
        data:
          message: "Download speed dropped to {{ states('sensor.openspeedtest_cli_download') }} Mbit/s"
```

## Лицензия

MIT — см. [LICENSE](LICENSE).
