![logoorange](https://user-images.githubusercontent.com/121691820/236648539-0ce47275-0938-4d05-a1b8-63b8df8b1bff.png)


<br/>
<br/>
<p align="center">
 <img width="750" src="https://user-images.githubusercontent.com/121691820/236647339-a474ee47-37bb-49e0-aedf-e801f18b567f.gif">
</p>
<br/>
<br/>

**GhostRider** is a system designed to assist soldiers operating in urban environments on foot, enhancing their situational awareness and improving decision-making capabilities. This is my final project for a 12th grade Computer Science class, it showcases a wide range of my skills. the system has three main components: a drone, an on-ground computer(server), and a tablet carried by the soldiers. The drone patrols the intended path of the soldiers, sending a live video feed to the on-ground computer. The computer processes this feed using a custom-trained object detection model to identify potential threats, aka people. Once detected, the drone's position is transmitted to the tablet, which displays the information on an interactive map. This allows soldiers to make informed decisions based on real-time data and helps to ensure their safety during operations.


lets dive to how this project works.

# Dataset 
As you may know, training a neural network requires a large number of annotated images of the subject you want to detect, this is a problem because i can't fly a drone in urban warfare zones. so i did the next best thing i can, I utilized 3D rendering software, Blender. Blender is a 3D software with a built-in Python module (bpy), which allows me to control the software through code. This lets me write code to generate labels without manually drawing them.

To create a realistic dataset, I needed 3D models of urban cities. I found a Discord group of CSGO modders who had access to .fbx files of maps from the game, that are based in Middle Eastern street design, which was just what I needed. I imported these models into Blender, added realistic lighting using HDRI textures, and began working on the script. my plan was to write a blender script that takes a camera on a path in the map like a drone, rendr images, generate the labels, and save the images to my computer. 

![Screenshot 2023-05-07 004458](https://user-images.githubusercontent.com/121691820/236647944-34ef1070-676b-482c-a4a9-d7d8076de8f3.png)

I needed models of people, including civilians and armed soldiers. To find them, I searched websites like Sketchfab, which offer a bunch 3D models. Once I found the models I needed, I used Blender to pose them and make them hold guns.

![Screenshot 2023-05-07 005034](https://user-images.githubusercontent.com/121691820/236647958-eb34fbe7-2af7-40e5-8dad-5f65eb468b6d.png)
![Screenshot 2023-05-07 005054](https://user-images.githubusercontent.com/121691820/236647963-b8948f97-f0e1-4694-80bd-aa2abdf2e83a.png)



`GhostRider_Labeler.py` works like this: <br/>
A good dataset requires multiple examples of the subject in various conditions and variations. The script switches the HDRI of the scene every set number of frames, creating variation in the dataset.
```python
def update_hdri(scene):
    current_frame = scene.frame_current
    hdri_index = (current_frame // switch_interval) % len(hdri_files)
    hdri_path = os.path.join(hdri_folder, hdri_files[hdri_index])
    environment_node.image = bpy.data.images.load(hdri_path)
```

The code creates folders for images, labels, and masks.

```python
output_dir = bpy.path.abspath('G://GhostRider//dataset//test')
os.makedirs(output_dir, exist_ok=True)
image_dir = os.path.join(output_dir, 'images')
os.makedirs(image_dir, exist_ok=True)
label_dir = os.path.join(output_dir, 'labels')
os.makedirs(label_dir, exist_ok=True)
mask_output_dir = os.path.join(output_dir, 'masks')
os.makedirs(mask_output_dir, exist_ok=True)
```

In the main loop, the code goes through every 5 frames, rendering the image and an object index mask. Blender has a feature that allows assigning an index number to objects and then rendering an object mask, where every pixel is black unless it has the object index specified, making it a white pixel. The code takes this mask, checks for a cluster of white pixels, calculates its position, width, and length relative to the image size, and writes a label for that image in the Darknet format. It then saves it with the same name as the image in the image folder. If the image does not have any white pixels, an empty label is created. In Blender, all human models have an index of 1, so if a cluster of white pixels is detected, it is a person.

```python
for frame in range(start_frame, end_frame + 1, 5):
    print(bpy.context.scene.frame_current)
    #render the image
    render_image_path = os.path.join(image_dir, f'rendered_image_{bpy.context.scene.frame_current}.png')
    bpy.context.scene.render.filepath = render_image_path
    bpy.ops.render.render(write_still=True)
    
    #set up the IndexOB layer
    bpy.context.scene.view_layers["View Layer"].use_pass_object_index = True
    
    #set up compositor nodes to extract the IndexOB pass and save it
    mask_output_path = os.path.join(mask_output_dir, f'mask{bpy.context.scene.frame_current}.png')
    setup_compositor_nodes(bpy.context.scene, mask_output_path)
    
    #render the mask
    bpy.ops.render.render()
    
    #access the mask image in memory 
    mask_image = bpy.data.images['Viewer Node'].pixels[:]
    width = bpy.data.images['Viewer Node'].size[0]
    height = bpy.data.images['Viewer Node'].size[1]
    mask_image_np = np.array(mask_image[:width*height*4:4]).reshape(height, width).astype(np.uint8)
    
    bounding_boxes = find_bounding_boxes(mask_image_np)
    
    #check if there are any white pixels
    if bounding_boxes:
        #write labels for each bounding box in the same file
        label_file_path = os.path.join(label_dir, f'rendered_image_{bpy.context.scene.frame_current}.txt')
        with open(label_file_path, 'w') as label_file:
            for idx, (x, y, w, h) in enumerate(bounding_boxes):
                yolo_data = convert_to_yolo_format(width, height, x, y, w, h)
                label_file.write(yolo_data)
                if idx < len(bounding_boxes) - 1:
                    label_file.write('\n')
    else:
        #write an empty YOLO label if no white clusters are detected
        empty_label_file_path = os.path.join(label_dir, f'rendered_image_{bpy.context.scene.frame_current}.txt')
        with open(empty_label_file_path, 'w') as empty_label_file:
            pass

    bpy.context.scene.frame_set(frame)
```

![maskes](https://user-images.githubusercontent.com/121691820/236648269-d882bdaf-c8b8-4d65-8d2f-5ae5ff1c7956.png)

After a lot of rendering, I managed to produce approximately 4500 images with corresponding labels from 4 different maps. It is now time to start the training process for the object detection model.

# Training
When it comes to object detection, it's generally more effective to fine-tune an existing model rather than training one from scratch. In my case, I needed a model that could detect both civilian and soldier from the perspective of a drone in real-time. To achieve this, I searched for a model that met my requirements and found the [YOLOv8 model by Ultralytics](https://github.com/ultralytics/ultralytics), which demonstrated high performance and ease of training. To learn more about the training process and settings, you can refer to the `GhostRider_train.py` and `GhostRider_config.yaml` files.

![results](https://user-images.githubusercontent.com/121691820/236648372-1e8999fa-96c5-41e6-b2ce-6325fd380e44.png)


The model's overall performance is impressive, with a mean average precision (mAP) score of 0.9 on the mAP50-95 metric. This indicates that the model has achieved a high degree of accuracy in detecting and classifying objects in the training data.

# Server
The server has been developed using Python and is designed to communicate with a Unity client that has been coded in C#. Its primary function is to examine images, detect any individuals in the image, and then transmit the drone's coordinates to the client if a person is detected. For security purposes, all data is encrypted using the AES encryption standard.

Although GPS technology would be utilized in a real-world scenario, for the sake of simplicity, coordinates are represented using a hypothetical grid of 2x2 squares that is superimposed on the map. The drone's starting position is located at square zero.

The code utilizes a predefined list of coordinates that the drone passes over sequentially. In the future, I plan to develop a tool that will automatically generate this list of coordinates so you dont have to do that manually.

# Client
In the Unity project, I have created a blockout of the buildings using simple shapes and shading, along with a camera that can be controlled through the use of a script called `CameraMovement.cs`. This allows for easy camera movement and control within the scene.

Additionally, I have included a canvas with a user interface (UI) that I designed, complete with buttons that, when clicked, execute a script that changes the active camera and provides different views of the map.

![Screenshot 2023-05-07 010900](https://user-images.githubusercontent.com/121691820/236648410-fe5efb23-00b7-4c1f-94ae-336fe10c247b.png)

I have also created a client game object with a client script that functions similarly to the server, receiving data and running it on a separate thread to prevent UI lag. To place the marker, I call a function on an object within the scene using [PimDeWitte's UnityMainThreadDispatcher](https://github.com/PimDeWitte/UnityMainThreadDispatcher). This tool enables me to call functions on the main thread from within the script, allowing for smooth and efficient execution. For more information on how the client script operates, you can refer to the comments in the GhostRider_client.cs script.

<br/>
<br/>

Thank you for taking the time to read about my project. This system demonstrates the power of technology in enhancing situational awareness and safety for soldiers operating in urban environments. I am grateful for the support I received from the CSGO modding community. I hope this project inspires others to explore the potential of technology and its applications in real-world scenarios. Please feel free to reach out with any questions, feedback, or suggestions for improvement. Your input is greatly appreciated!
