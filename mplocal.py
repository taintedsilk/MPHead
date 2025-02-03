import cv2
import mediapipe as mp
import asyncio
import json
import sys
import threading
import time
import numpy as np
import math
from tcp_sender import TCPSender
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# --- Constants and Configuration ---
MODEL_PATH = 'face_landmarker.task'
FPS = 20
FRAME_DELAY = 1 / FPS
HOST = "127.0.0.1"
PORT = 12345
RESIZE_FACTOR = 1
CAMERA_SOURCE = 0  # CHANGE THIS FOR DIFFERENT CAMERAS AAAA IDK HOW TO USE URL

# --- Global Variables ---
tcp_sender = None
cap = None  

# --- Head Pose Estimation Variables ---
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

initial_point = None
button_pressed = False
delta_x = 0
delta_y = 0
delta_z = 0
initial_yaw = 0
initial_pitch = 0
initial_roll = 0

# --- Calibration parameters ---
# to normalize, idk how the values from facial_transformation_matrixes scales...
x_min = -50
x_max = 50
y_min = -40
y_max = 40
z_min = -100
z_max = 0

# --- Button dimensions ---
button_x1 = 10
button_y1 = 200
button_x2 = button_x1 + 140
button_y2 = button_y1 + 75

# --- Helper Functions ---
def connection_failed_callback():
    print("Connection failed permanently. Exiting.")
    exit(1)

def euler_from_matrix(matrix):
    """Convert a rotation matrix to Euler angles (roll, pitch, yaw) in radians."""
    R00, R01, R02 = matrix[0, 0], matrix[0, 1], matrix[0, 2]
    R10, R11, R12 = matrix[1, 0], matrix[1, 1], matrix[1, 2]
    R20, R21, R22 = matrix[2, 0], matrix[2, 1], matrix[2, 2]

    # Calculate pitch (theta)
    yaw = -math.asin(R20)

    # Calculate roll and pitch
    if math.fabs(math.cos(yaw)) > 0.001:  # Avoid division by zero
        pitch = math.atan2(R21 / math.cos(yaw), R22 / math.cos(yaw))
        roll = math.atan2(R10 / math.cos(yaw), R00 / math.cos(yaw))
    else: 
        pitch = 0  # Set roll to 0
        roll = math.atan2(-R12, R11)  # Use alternative formula for yaw

    return yaw, pitch, roll


def y_poly(x):
  """ This is caliberated from my own face, idk if it works for u"""
  coefficients = [10.94, 0.01819, -11.95, -7.608, 0] 
  return np.polyval(coefficients, x)
  
def roll_poly(x):
    # yaw effect's on roll?
    coefficients = [-0.1121, 0.08556,  0.2624, 0.1843, 0]  
    return np.polyval(coefficients, x)

def calculate_head_pose_and_position(facial_transformation_matrix, landmarks):
    if facial_transformation_matrix is None or landmarks is None:
        return None

    # Extract the rotation and translation
    rotation_matrix = facial_transformation_matrix[:3, :3]
    translation_vector = facial_transformation_matrix[:3, 3]

    yaw, pitch, roll = euler_from_matrix(rotation_matrix)

    # Idea: Maybe someone could get livelink data to caliberate this better, i'm just working on assumptions 
    # works fine without it, but head posititon accuracy will be worse
    # Apply the transformation to the translation vector
    temp_val = translation_vector.copy()
    # undo yaw's effect on head pos
    temp_val[0] += np.cos(yaw * np.pi / 2 + np.pi /2) * 3.65
    # undo pitch's effect on head pos
    temp_val[1] -= y_poly(pitch)

    
    # Normalize x, y, z to [-1, 1]
    x_norm = (temp_val[0] - x_min) / (x_max - x_min) * 2 - 1
    y_norm = (temp_val[1] - y_min) / (y_max - y_min) * 2 - 1
    z_norm = (temp_val[2] - z_min) / (z_max - z_min) * 2 - 1

    return x_norm, y_norm, z_norm, yaw, pitch, roll

def mouse_callback(event, x, y, flags, param):
    """
    Handles mouse events, specifically for the button press.
    """
    global button_pressed, initial_point, initial_yaw, initial_pitch, initial_roll

    if event == cv2.EVENT_LBUTTONDOWN:
        if button_x1 <= x <= button_x2 and button_y1 <= y <= button_y2:
            button_pressed = True
            print("Button pressed! Initial point set.")

def clamp(value, min_value, max_value):
    """Clamps a value within a specified range."""
    return max(min(value, max_value), min_value)

# --- brah ---
async def video_processing_task():
    global tcp_sender, cap, frame,  optical_center, landmarker, button_pressed, initial_point, initial_yaw, initial_pitch, initial_roll, delta_x, delta_y, delta_z
    tcp_sender = TCPSender(HOST, PORT, connection_failed_callback)
    # tcp_sender = None
    base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_faces=1,
        output_face_blendshapes=True,
        output_facial_transformation_matrixes=True,
        min_face_detection_confidence=0.4,
        min_face_presence_confidence=0.4,
        min_tracking_confidence=0.4
    )
    landmarker = vision.FaceLandmarker.create_from_options(options)

    with mp_face_mesh.FaceMesh(
        max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5
    ) as face_mesh:
        cv2.namedWindow('MP Send')
        cv2.setMouseCallback("MP Send", mouse_callback)

        try:
            print(f"Attempting to open camera source: {CAMERA_SOURCE}")
            cap = cv2.VideoCapture(CAMERA_SOURCE)

            if not cap.isOpened():
                print(f"Failed to open camera source {CAMERA_SOURCE}.")
                return

            while True:
                if cap is not None:
                    start_time = time.time()
                    ret, frame = cap.read()
                    frame = cv2.flip(frame, 1)
                    if not ret:
                        print("Frame read failed, reinitializing camera...")
                        cap.release()
                        cap = None
                        continue

                    # Get the actual frame dimensions
                    frame_height, frame_width, _ = frame.shape
                    # print(frame_height, frame_width)

                    display_frame = frame.copy()

                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

                    timestamp_ms = int(time.time() * 1000)
                    result = landmarker.detect_for_video(mp_image, timestamp_ms)
                    
                    # --- Head Pose Estimation ---
                    if result.facial_transformation_matrixes and result.face_landmarks:
                        for facial_transformation_matrix, landmarks in zip(result.facial_transformation_matrixes, result.face_landmarks):
                            head_pose = calculate_head_pose_and_position(facial_transformation_matrix, landmarks)

                            if head_pose:
                                x_norm, y_norm, z_norm, yaw, pitch, roll = head_pose
                                
                                # --- Set initial point and pose if button is pressed ---
                                if button_pressed:
                                    initial_point = (x_norm, y_norm, z_norm)
                                    initial_yaw, initial_pitch, initial_roll = yaw, pitch, roll
                                    button_pressed = False

                                # --- Calculate delta from the initial point ---
                                if initial_point:
                                    delta_x = x_norm - initial_point[0]
                                    delta_y = y_norm - initial_point[1]
                                    delta_z = z_norm - initial_point[2]
                                    delta_yaw = yaw - initial_yaw
                                    delta_pitch = pitch - initial_pitch
                                    delta_roll = roll - initial_roll

                                    # Clamp delta values
                                    delta_x = clamp(delta_x, -1, 1)
                                    delta_y = clamp(delta_y, -1, 1)
                                    delta_z = clamp(delta_z, -1, 1)
                                    delta_yaw = clamp(delta_yaw, -1, 1)
                                    delta_pitch = clamp(delta_pitch, -1, 1)
                                    delta_roll = clamp(delta_roll, -1, 1)
                                else:
                                    delta_x = 0
                                    delta_y = 0
                                    delta_z = 0
                                    delta_yaw = 0
                                    delta_pitch = 0
                                    delta_roll = 0

                                # --- Draw and display information ---
                                x_px = int((x_norm + 1) / 2 * display_frame.shape[1])
                                y_px = int((1 - y_norm) / 2 * display_frame.shape[0])
                                cv2.circle(display_frame, (x_px, y_px), 10, (0, 255, 0), -1)

                                text_current = f"Current: X: {x_norm:.2f}, Y: {y_norm:.2f}, Z: {z_norm:.2f}"
                                text_pose = f"Pose: Yaw: {yaw:.2f}, Pitch: {pitch:.2f}, Roll: {roll:.2f}"
                                text_delta = f"Delta: X: {delta_x:.2f}, Y: {delta_y:.2f}, Z: {delta_z:.2f}"
                                text_delta_pose = f"Delta Pose: Yaw: {delta_yaw:.2f}, Pitch: {delta_pitch:.2f}, Roll: {delta_roll:.2f}"

                                cv2.putText(
                                    display_frame,
                                    text_current,
                                    (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.7,
                                    (0, 255, 0),
                                    2,
                                )
                                cv2.putText(
                                    display_frame,
                                    text_pose,
                                    (10, 60),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.7,
                                    (0, 255, 0),
                                    2,
                                )
                                cv2.putText(
                                    display_frame,
                                    text_delta,
                                    (10, 90),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.7,
                                    (0, 255, 0),
                                    2,
                                )
                                cv2.putText(
                                    display_frame,
                                    text_delta_pose,
                                    (10, 120),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.7,
                                    (0, 255, 0),
                                    2,
                                )


                    # --- Draw a button to set intial pos---
                    cv2.rectangle(display_frame, (button_x1, button_y1), (button_x2, button_y2), (255, 0, 0), -1)
                    cv2.putText(
                        display_frame,
                        "Set Initial",
                        (button_x1 + 10, button_y1 + 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 255),
                        1,
                    )
                    # --- End Head Pose Estimation ---

                    if result.face_landmarks:
                        blendshapes = result.face_blendshapes[0]
                        blendshape_dict = {entry.category_name: entry.score for entry in blendshapes}
                        blendshape_dict["headX"] = delta_x
                        blendshape_dict["headY"] = delta_y
                        blendshape_dict["headZ"] = delta_z
                        blendshape_dict["headYaw"] = delta_yaw
                        blendshape_dict["headPitch"] = delta_pitch
                        blendshape_dict["headRoll"] = delta_roll

                        # Send data over TCP
                        json_data = (json.dumps(blendshape_dict) + '\n').encode('utf-8')
                        if tcp_sender:
                            await tcp_sender.send(json_data)

                    cv2.imshow('MP Send', display_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                    processing_time = time.time() - start_time
                    sleep_duration = max(FRAME_DELAY - processing_time, 0)
                    await asyncio.sleep(sleep_duration)

        finally:
            if cap is not None:
                cap.release()
            cv2.destroyAllWindows()
            landmarker.close()
            if tcp_sender:
                await tcp_sender.close()

# --- Main Function ---
def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    video_thread = threading.Thread(target=loop.run_until_complete, args=(video_processing_task(),), daemon=True)
    video_thread.start()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting program...")
    finally:
        if tcp_sender:
            loop.run_until_complete(tcp_sender.close())
        loop.close()

# --- Entry Point ---
if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
