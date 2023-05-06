from ultralytics import YOLO
import cv2
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import importlib
socket = importlib.import_module('socket')

#path to the input video file
video_path = "dronevid.mp4"

model = YOLO('best.pt')

#server address and port number
HOST = 'localhost'
PORT = 12345

#passcode for client authentication
PASSCODE = 'mypassword'

KEY = b'mysecretkey1234' + b'0'  # 16 bytes long (128-bit key)
IV = b'myiv12345'[:16].ljust(16, b'\x00')  #16 bytes long

# function for encrypting data
def encrypt_data(data):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    padded_data = pad(data, AES.block_size)
    encrypted_data = cipher.encrypt(padded_data)
    return encrypted_data

#function for decrypting data
def decrypt_data(data):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    decrypted_data = cipher.decrypt(data)
    unpadded_data = unpad(decrypted_data, AES.block_size)
    return unpadded_data

#function that calculates the drone position on the grid based on frame number
def get_drone_position(frame_num):
    #list of square positions drone goes through
    square_positions = [(0,0),(1,0),(2,0),(3,0),(3,1),(3,2),(3,3),(2,3),(2,4),(2,5),(2,6),(2,7),(3,7),(4,7)]

    #get the index of the current position in the list
    position_index = (frame_num // 24) % len(square_positions)

    #return the current position
    return square_positions[position_index]


#create a TCP/IP socket and bind it to the server address and port number
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))

#listen for incoming connections
server_socket.listen()


#initialize the video capture object
cap = cv2.VideoCapture(video_path)

#get the total number of frames in the video
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

#initialize a variable to keep track of the current frame number
frame_num = 0

while True:
    print('Waiting for a client to connect...')
    
    #accept an incoming connection
    client_socket, client_address = server_socket.accept()
    
    print(f'Client connected: {client_address}')
    
    #authenticate the client using a passcode
    passcode = client_socket.recv(1024)
    if passcode.decode() != PASSCODE:
        print('Authentication failed. Closing connection.')
        client_socket.close()
        continue
    
    print('Client authenticated.')

    
    try:
        while True:
            #set the frame position to the current frame number
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            
            #read the frame
            ret, frame = cap.read()

            #check if the frame was read successfully
            if not ret:
                print(f"Error reading frame {frame_num}")
                break

            #check if this is the 24th frame
            if frame_num % 24 == 0:
                #save the frame to an image variable
                image = frame

            
            
            results = model.predict(source=image, vid_stride = False, conf = 0.8, device = 0)  #save predictions as labels
            for result in results:
                print(len(result.boxes))
            
           
            annotated_frame = results[0].plot()
            
            
            #check if the results are empty, if they are not get the position of the drone and put it in data
            if len(result.boxes) == 0:
                data = str("x")
                data = data.encode('utf-8')
            else:
                data = str(get_drone_position(frame_num))
                data = data.encode('utf-8')
            
            
            

            
            #encrypt the data
            encrypted_data = encrypt_data(data)

            #send the encrypted data to the client
            client_socket.sendall(encrypted_data)
            
            frame_num += 24

            #receive a response from the client
            response = client_socket.recv(1024)
            if not response:
                break
            

            # create named window with window flags
            cv2.namedWindow("YOLOv8 Inference", cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO | cv2.WINDOW_GUI_EXPANDED)
            # set the window property to always be on top
            cv2.setWindowProperty("YOLOv8 Inference", cv2.WND_PROP_TOPMOST, 1)
            #display prediction
            cv2.imshow("YOLOv8 Inference", annotated_frame)
            
            cv2.waitKey(2000)

            #decrypt the response
            decrypted_response = decrypt_data(response)


    except ConnectionResetError:
        print("Connection forcibly closed by the remote host.")
    except Exception as e:
        print(f"Error: {e}")

    print('Closing connection.')
    client_socket.close()

    cap.release()
    cv2.destroyAllWindows()
