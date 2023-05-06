import bpy
import os
import cv2
import numpy as np

#HDRI switching function
def update_hdri(scene):
    current_frame = scene.frame_current
    hdri_index = (current_frame // switch_interval) % len(hdri_files)
    hdri_path = os.path.join(hdri_folder, hdri_files[hdri_index])
    environment_node.image = bpy.data.images.load(hdri_path)

#folder containing the HDRI textures
hdri_folder = "G://GhostRider//Maps//hdri"

#load HDRI 
hdri_files = [f for f in os.listdir(hdri_folder) if f.lower().endswith(('.hdr', '.exr', '.hdri'))]

#set the world shading to use nodes
bpy.context.scene.world.use_nodes = True
world_nodes = bpy.context.scene.world.node_tree.nodes
world_links = bpy.context.scene.world.node_tree.links  # Add this line

#add an Environment Texture node if it doesn't exist
if 'Environment Texture' not in world_nodes:
    environment_node = world_nodes.new(type='ShaderNodeTexEnvironment')
else:
    environment_node = world_nodes['Environment Texture']

#connect the Environment Texture node to the Background node
world_links.new(environment_node.outputs[0], world_nodes['Background'].inputs[0])  # Modify this line


#set the number of frames between HDRI switches
switch_interval = 200


#register the handler function with Blender
bpy.app.handlers.frame_change_pre.append(update_hdri)



def setup_compositor_nodes(scene, mask_output_path):
    scene.use_nodes = True
    nodes = scene.node_tree.nodes
    links = scene.node_tree.links
    
    for node in nodes:
        nodes.remove(node)
        
    render_layers_node = nodes.new(type='CompositorNodeRLayers')
    viewer_node = nodes.new(type='CompositorNodeViewer')
    id_mask_node = nodes.new(type='CompositorNodeIDMask')
    file_output_node = nodes.new(type='CompositorNodeOutputFile')
    
    id_mask_node.index = 1  #change this to match the object's Pass Index
    
    links.new(render_layers_node.outputs['IndexOB'], id_mask_node.inputs['ID value'])
    links.new(id_mask_node.outputs['Alpha'], viewer_node.inputs['Image'])
    links.new(id_mask_node.outputs['Alpha'], file_output_node.inputs['Image'])

    file_output_node.base_path = mask_output_path
    file_output_node.format.file_format = 'PNG'

def find_bounding_boxes(mask_image):
    contours, _ = cv2.findContours(mask_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    bounding_boxes = [cv2.boundingRect(contour) for contour in contours if cv2.contourArea(contour) >= 10 * 10]
    return bounding_boxes

def convert_to_yolo_format(width, height, x, y, w, h):
    x_center = (x + w/2) / width
    y_center = 1 - (y + h/2) / height # flip y the mask image is represented in a NumPy array with the origin (0, 0) at the top-left corner, while the YOLO format assumes the origin to be at the bottom-left corner.
    w_norm = w / width
    h_norm = h / height
    return f"0 {x_center} {y_center} {w_norm} {h_norm}"

#set render settings
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.context.scene.render.engine = 'CYCLES'

#create output directories
output_dir = bpy.path.abspath('G://GhostRider//dataset//test')
os.makedirs(output_dir, exist_ok=True)
image_dir = os.path.join(output_dir, 'images')
os.makedirs(image_dir, exist_ok=True)
label_dir = os.path.join(output_dir, 'labels')
os.makedirs(label_dir, exist_ok=True)
mask_output_dir = os.path.join(output_dir, 'masks')
os.makedirs(mask_output_dir, exist_ok=True)


start_frame = bpy.context.scene.frame_start
end_frame = bpy.context.scene.frame_end

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


bpy.app.handlers.frame_change_pre.remove(update_hdri)

print("Processing finished.")
