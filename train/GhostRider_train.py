from ultralytics import YOLO


if __name__ == '__main__':
    model = YOLO("yolov8n.yaml").load('yolov8n.pt')   #load a pretrained model 
    model.task = 'detect'


    model.train("GhostRider_config.yaml", epochs=100, batch = 16, resume = True, device = 0, pretrained = True, verbose = True)  # train the model
    results = model("https://ultralytics.com/images/bus.jpg")  # predict on an image
    success = model.export(format="onnx")  # export the model to ONNX format
