import numpy as np
import asyncio
import logging


from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli
import sys
import cv2


# Load environment variables
load_dotenv()


async def entrypoint(job: JobContext):
    await job.connect()

    # ? From local camera
    # Initialize video capture from default camera (usually 0)
    cap = cv2.VideoCapture(0)

    # Check if camera opened successfully
    if not cap.isOpened():
        logging.error("Could not open camera")
        sys.exit(1)

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # ? From livekit
    room = job.room
    source = rtc.VideoSource(frame_width, frame_height)
    track = rtc.LocalVideoTrack.create_video_track("single-color", source)
    options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_CAMERA)
    publication = await room.local_participant.publish_track(track, options)
    logging.info("published track", extra={"track_sid": publication.sid})

    async def handle_video(track: rtc.Track):
        video_stream = rtc.VideoStream(track)
        async for event in video_stream:
            video_frame = event.frame
            current_type = video_frame.type
            frame_as_bgra = video_frame.convert(rtc.VideoBufferType.BGRA).data

            # Convert to a NumPy array
            frame_np = np.frombuffer(frame_as_bgra, dtype=np.uint8)
            frame_np = frame_np.reshape(
                (video_frame.height, video_frame.width, 4)
            )  # BGRA has 4 channels

            cv2.imshow("Camera Stream", frame_np)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        await video_stream.aclose()

    @room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.TrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        if track.kind == rtc.TrackKind.KIND_VIDEO:
            asyncio.create_task(handle_video(track))

    async def _draw_frame():
        argb_frame = bytearray(frame_width * frame_height * 4)

        try:
            while True:
                await asyncio.sleep(0.01)  # 100ms

                # Capture frame-by-frame
                ret, frame = cap.read()

                # If frame is read correctly, ret is True
                if not ret:
                    logging.error("Can't receive frame (stream end?). Exiting..")
                    break

                # Display the frame
                logging.info("Camera Stream", extra={"frame length": len(frame)})

                # Convert the frame to RGBA
                # TODO: Consider conversion to NV12 or I420
                argb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                frame = rtc.VideoFrame(
                    frame_width, frame_height, rtc.VideoBufferType.RGBA, argb_frame
                )
                source.capture_frame(frame)
        finally:
            # Clean up
            cap.release()

    await _draw_frame()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
