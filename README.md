# Price Tag Analyzer Service

## ENV переменные 

| Название переменной | Значение                | Описание          |
|---------------------|-------------------------|-------------------|
| `NATS_URL`          | `nats://localhost:4222` | NATS              |
| `LOG_LEVEL`         | `DEBUG`                 | Уровень лога      |
| `ENVIRONMENT`       | `production`            | NATS              |
| `YOLO_IMAGE_SIZE`   | `320`                   | Yolo Image Size   |  

## Ошибки

Информация об ошибках передается в виде JSON-строки, содержащей информацию о шаге (`step`), на котором произошла ошибка, а также, в зависимости от случая, дополнительную информацию.

Пример:

```json
{
  "step": "yolo"
}
```

Возможное значение поля `step`:
- `yolo` - ошибка YOLO;
- `ocr` - ошибка с распознаванием текста;
- `spell` - ошибка с spellchecker;
- `ner` - ошибка с извлечением товара из описания.

Дополнительные поля `ocr`:
- `reason` - возможные значения: 
  - `description_or_price_not_found`
  - `price_is_not_float`
  - `ocr_error` - неопределенная ошибка (скорее всего внутренняя)
- `description` - описание товара, string
- `price` - string

Дополнительные поля `spell`:
- `description` - string
- `price` - float

Дополнительные поля `ner`:
- `description` - string
- `price` - float

---

Ссылка на `yolov8-price-tag-detection.pt`:

[direct](https://download.slipenko.com/yolov8-price-tag-detection.pt) или [Gdrive](https://drive.google.com/file/d/1dySk7_7n0ufE0ZtEmu91fATpK7bRaRbF/view?usp=drive_link)

dev:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/dev.txt
```