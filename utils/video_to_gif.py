import os
import imageio.v2 as imageio


def convert_mp4_to_gif(
    mp4_path: str,
    gif_path: str = None,
    fps: int = 10,
) -> str:
    """
    Convert an MP4 file to GIF.
    Returns the output GIF path.
    """
    if not os.path.isfile(mp4_path):
        raise FileNotFoundError(f"MP4 not found: {mp4_path}")

    if gif_path is None:
        gif_path = os.path.splitext(mp4_path)[0] + ".gif"

    reader = imageio.get_reader(mp4_path)
    meta = reader.get_meta_data()
    source_fps = meta.get("fps", fps)

    frames = []
    step = max(1, round(source_fps / fps))

    for i, frame in enumerate(reader):
        if i % step == 0:
            frames.append(frame)

    if not frames:
        raise ValueError("No frames extracted from mp4.")

    imageio.mimsave(gif_path, frames, format="GIF", fps=fps)
    return gif_path