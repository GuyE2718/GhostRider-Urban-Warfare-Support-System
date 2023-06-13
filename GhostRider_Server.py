from ultralytics import YOLO
import cv2
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import importlib
socket = importlib.import_module('socket')


class GhostRiderServer:
    def __init__(self, video_path, model_path, host, port, passcode, key=None, iv=None):
        self.video_path = video_path
        self.model_path = model_path
        self.host = host
        self.port = port
        self.passcode = passcode
        self.key = key
        self.iv = iv

    def encrypt_data(self, data):
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        padded_data = pad(data, AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        return encrypted_data

    def decrypt_data(self, data):
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        decrypted_data = cipher.decrypt(data)
        unpadded_data = unpad(decrypted_data, AES.block_size)
        return unpadded_data

    def get_drone_position(self, frame_num):
        square_positions = [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2), (3, 3), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7),
                            (3, 7), (4, 7)]
        position_index = (frame_num // 24) % len(square_positions)
        return square_positions[position_index]

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen()

        cap = cv2.VideoCapture(self.video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_num = 0

        while True:
            print('Waiting for a client to connect...')
            client_socket, client_address = server_socket.accept()
            print(f'Client connected: {client_address}')

            passcode = client_socket.recv(1024)
            if passcode.decode() != self.passcode:
                print('Authentication failed. Closing connection.')
                client_socket.close()
                continue

            print('Client authenticated.')

            try:
                while True:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                    ret, frame = cap.read()

                    if not ret:
                        print(f"Error reading frame {frame_num}")
                        break

                    if frame_num % 24 == 0:
                        image = frame

                    model = YOLO(self.model_path)
                    results = model.predict(source=image, vid_stride=False, conf=0.8, device=0)
                    for result in results:
                        print(len(result.boxes))

                    annotated_frame = results[0].plot()

                    if len(result.boxes) == 0:
                        data = str("x")
                        data = data.encode('utf-8')
                    else:
                        data = str(self.get_drone_position(frame_num))
                        data = data.encode('utf-8')

                    encrypted_data = self.encrypt_data(data)
                    client_socket.sendall(encrypted_data)

                    frame_num += 24

                    response = client_socket.recv(1024)
                    if not response:
                        break

                    cv2.namedWindow("YOLOv8 Inference", cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO | cv2.WINDOW_GUI_EXPANDED)
                    cv2.setWindowProperty("YOLOv8 Inference", cv2.WND_PROP_TOPMOST, 1)
                    cv2.imshow("YOLOv8 Inference", annotated_frame)

                    cv2.waitKey(2000)

                    decrypted_response = self.decrypt_data(response)

            except ConnectionResetError:
                print("Connection forcibly closed by the remote host.")
            except Exception as e:
                print(f"Error: {e}")

            print('Closing connection.')
            client_socket.close()

            cap.release()
            cv2.destroyAllWindows()


# Usage:
video_path = "dronevid.mp4"
model_path = 'best.pt'
host = 'localhost'
port = 12345
passcode = 'mypassword'

# Prompt the user for the key and iv
key = input("Enter the encryption key: ").encode('utf-8')
iv = input("Enter the IV: ").encode('utf-8')[:16].ljust(16, b'\x00')


server = GhostRiderServer(video_path, model_path, host, port, passcode, key, iv)
server.start()
