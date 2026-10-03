import cv2
import numpy as np

IMAGE_X, IMAGE_Y = 140, 230

def preview_geometry(shape):
    height, width = shape[:2]
    scale = min(960 / width, 540 / height, 1)
    return round(width * scale), round(height * scale)


def click_to_center(x, y, shape):
    width, height = preview_geometry(shape)
    if y < 105 or not 0 <= x < width + 280 or not y < height + 300:
        return None
    return ((x - IMAGE_X) / width, (y - IMAGE_Y) / height)


def draw_preview(rgb, centers, result, selected, paused, trial=None, dirty=False, live=False):
    height, width = rgb.shape[:2]
    w, h = preview_geometry(rgb.shape)
    display = np.full((h + 300, w + 280, 3), 28, dtype=np.uint8)
    display[IMAGE_Y:IMAGE_Y+h, IMAGE_X:IMAGE_X+w] = cv2.resize(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), (w, h))

    def screen(point):
        return tuple(np.rint(np.array(point) * [w, h] + [IMAGE_X, IMAGE_Y]).astype(int))

    origin = None if result['origin'] is None else screen(result['origin'] / [width, height])
    for device, point in centers.items():
        center = screen(point)
        color = (0,255,0) if device == result['candidate'] else (0,220,255)
        if origin is not None:
            cv2.line(display, origin, center, color, 1)
        cv2.drawMarker(display, center, color, cv2.MARKER_CROSS, 20, 2)
        angle = result['angles'].get(device)
        label = 'ALL LIGHTS / CEILING' if device == 'LIGHT' else device
        text = label if angle is None else f'{label}: {angle:.1f} deg'
        cv2.putText(display, text, (max(5,min(center[0]+10,w+80)),max(120,center[1])), 0, .55, color, 1)
    if origin is not None:
        vector = (result['tip'] - result['origin']) * [w / width, h / height]
        length = np.linalg.norm(vector)
        if length >= 1:
            end = tuple(np.rint(np.array(origin) + vector / length * 2 * max(w,h)).astype(int))
            cv2.arrowedLine(display, origin, end, (255,255,0), 3, tipLength=.03)
        cv2.circle(display, origin, 5, (255,255,255), -1)
        cv2.circle(display, screen(result['tip'] / [width,height]), 5, (255,255,0), -1)
    last = trial.last_event if trial else None
    count = trial.event_count if trial else 0
    title = "HGHC CONTROL | HAND DIRECTION ONLY" if live else "SIMULATION - NO DEVICE COMMANDS | HAND DIRECTION ONLY"
    lines = [title,
             f"{result['gesture']} | CANDIDATE: {result['candidate'] or 'None'} | LAST EVENT #{count}: {last or 'None'}",
             f"Edit: {selected} {'* UNSAVED' if dirty else ''} | {'PAUSED' if paused else 'PLAYING'} | click center, [ ] device, S save, X remove",
             'Space: pause | N: next frame | Q/Esc: quit | outside centers are provisional']
    if live:
        lines[2:] = ['Centers: edit in pointing_preview.py, then restart HGHC', 'Q/Esc: quit | center points are provisional']
    cv2.rectangle(display, (0,0), (w+280,105), (20,20,20), -1)
    for i,text in enumerate(lines):
        cv2.putText(display, text, (10,22+i*24), 0, .55, (255,255,255), 1)
    return display

