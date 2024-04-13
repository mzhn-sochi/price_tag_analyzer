FROM python:3.11-slim as base
ARG VERSION="cpu"

COPY requirements/prod.${VERSION}.txt /code/requirements.txt

WORKDIR /code
RUN pip install --user -r requirements.txt

COPY . .
# TODO: replace url
ADD https://download.slipenko.com/mzhn-team-sochi/yolov8-price-tag-detection.pt yolov8-price-tag-detection.pt
ADD https://download.slipenko.com/mzhn-team-sochi/EasyOCR/model/cyrillic_g2.pth /root/.EasyOCR/model/cyrillic_g2.pth
ADD https://download.slipenko.com/mzhn-team-sochi/EasyOCR/model/craft_mlt_25k.pth /root/.EasyOCR/model/craft_mlt_25k.pth

FROM python:3.11-slim

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install \
        libgl1 \
        libgl1-mesa-glx \
        libglib2.0-0 \
    -y && rm -rf /var/lib/apt/lists/*

COPY --from=base /root/.local /root/.local
COPY --from=base /code/price_tag_analyzer/ /app/price_tag_analyzer
COPY --from=base /code/yolov8-price-tag-detection.pt /app/yolov8-price-tag-detection.pt
COPY --from=base /root/.EasyOCR /root/.EasyOCR

ENV PYTHONPATH "${PYTHONPATH}:/app/"

WORKDIR /app

CMD python -m price_tag_analyzer