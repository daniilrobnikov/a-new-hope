import logging
import cv2
import sys


def start_camera_stream():
    # Initialize video capture from default camera (usually 0)
    cap = cv2.VideoCapture(0)

    # Check if camera opened successfully
    if not cap.isOpened():
        logging.error("Could not open camera")
        sys.exit(1)

    # Get default window size
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    logging.info(f"Camera resolution: {frame_width}x{frame_height}")

    try:
        while True:
            # Capture frame-by-frame
            ret, frame = cap.read()

            # If frame is read correctly, ret is True
            if not ret:
                logging.error("Can't receive frame (stream end?). Exiting..")
                break

            # Display the frame
            logging.info("Camera Stream", extra={"frame length": len(frame)})
            logging.info("Camera Stream")
    finally:
        # Clean up
        cap.release()


if __name__ == "__main__":
    start_camera_stream()
