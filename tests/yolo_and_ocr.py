import ultralytics
from ultralytics import YOLO
import supervision as sv
import cv2
import easyocr

ultralytics.checks()


model = YOLO('yolov8-price-tag-detection.pt')

img = cv2.imread('tests/test_images/full-test2.png')

results = model(img)

detections = sv.Detections.from_ultralytics(results[0])

labels = [
    f"{model.names[class_id]} {confidence:.2f}"
    for class_id, confidence in zip(detections.class_id, detections.confidence)
]

bounding_box_annotator = sv.LabelAnnotator()
annotated_frame = bounding_box_annotator.annotate(
    scene=img.copy(),
    detections=detections, labels=labels
)

bounding_box_annotator = sv.BoundingBoxAnnotator()
annotated_frame = bounding_box_annotator.annotate(
    scene=annotated_frame,
    detections=detections
)

reader = easyocr.Reader(['ru', 'en'])

price = ''

description = False
price_whole = False
price_fraction = False


detections = [list(z) for z in zip(detections.xyxy, detections.confidence, detections.class_id)]

sorted_detections = sorted(detections, key=lambda x: x[1], reverse=True)

N = 10

for bbox, confidence, class_id in sorted_detections:
    class_name = model.names[class_id]  # Assuming 'model.names' maps class IDs to class names
    # print(f"BBox: {bbox}, Confidence: {confidence}, Class Name: {class_name}")
    x_min, y_min, x_max, y_max = map(int, bbox[:4])

    x_min = max(x_min - N, 0)  # Убедитесь, что новые координаты не выходят за границы изображения
    y_min = max(y_min - N, 0)
    x_max = min(x_max + N, img.shape[1])  # img.shape[1] - ширина изображения
    y_max = min(y_max + N, img.shape[0])  # img.shape[0] - высота изображения

    cropped_image = img[y_min:y_max, x_min:x_max]

    ocr_result = reader.readtext(cropped_image)

    print(class_name, ocr_result)

    if len(ocr_result) > 0:
        if class_name == 'description' and not description:
            description = ''
            
            for r in ocr_result:
                description += r[1] + ' '

            description = description.strip()

        if class_name == 'price_whole' and not price_whole:
            print('!!!price_whole!!!')
            price_whole = ocr_result[0][1]
    
        if class_name == 'price_fraction' and not price_fraction:
            price_fraction = ocr_result[0][1]

if not price_fraction:
    price_fraction = '00'

price = f'{price_whole}.{price_fraction}'

print('Description:', description)
print('Price:', price)

cv2.imwrite('test-out.jpg', annotated_frame)