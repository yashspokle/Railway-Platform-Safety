from ultralytics import YOLO

# Load the trained railway segmentation model
model = YOLO("models/railway_segmentation.pt")

# Run detection on the test image
results = model.predict(
    source="models/train.jpeg",
    save=True,
    show=True
)

print("Image detection completed.")