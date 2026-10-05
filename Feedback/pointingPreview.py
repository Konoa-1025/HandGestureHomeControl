import cv2
import numpy as np

IMAGE_X, IMAGE_Y = 140, 230
PANEL_WIDTH = 360


def preview_geometry(shape):
    height, width = shape[:2]
    scale = min(960 / width, 540 / height, 1)
    return round(width * scale), round(height * scale)


def click_to_center(x, y, shape):
    width, height = preview_geometry(shape)
    if y < 105 or not 0 <= x < width + 280 or not y < height + 300:
        return None
    return ((x - IMAGE_X) / width, (y - IMAGE_Y) / height)


def _text(image, text, position, scale=.52, color=(218, 225, 233), max_width=None):
    text = str(text) if text is not None else "--"
    if max_width is not None:
        original = text
        while text and cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)[0][0] > max_width:
            original = original[:-1]
            text = original + "..." if original else ""
    cv2.putText(image, text, position, cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)


def _number(value, digits=1):
    return "--" if value is None else f"{value:.{digits}f}"


def _draw_panel(display, panel_x, status, result, trial, live):
    status = {} if status is None else status
    muted = (130, 142, 157)
    accent = (211, 191, 107)
    success = (152, 211, 147)
    warning = (107, 187, 236)
    x = panel_x + 22
    available_width = PANEL_WIDTH - 44
    cv2.rectangle(display, (panel_x, 0), (display.shape[1], display.shape[0]), (31, 27, 23), -1)
    cv2.line(display, (panel_x, 0), (panel_x, display.shape[0]), (62, 58, 52), 1)

    def line(y):
        cv2.line(display, (x, y), (display.shape[1] - 22, y), (66, 59, 50), 1)

    def row(label, value, y, color=(218, 225, 233)):
        _text(display, label, (x, y), .43, muted)
        _text(display, value, (x + 112, y), .54, color, available_width - 112)

    mode = status.get('mode', 'LIVE' if live else 'SIMULATION')
    _text(display, 'HGHC / STATUS', (x, 32), .62)
    _text(display, mode, (x, 61), .51, warning if mode == 'LIVE' else accent)
    source = status.get('input', '--')
    frame = status.get('frame_index')
    fps = status.get('fps')
    _text(display, f"{source}  |  FRAME {frame if frame is not None else '--'}  |  {_number(fps)} FPS", (x, 89), .42, muted, available_width)
    line(107)

    hand = status.get('hand', 'DETECTED' if result.get('origin') is not None else 'NONE')
    row('HAND', hand, 139, success if hand == 'DETECTED' else muted)
    row('GESTURE', status.get('gesture', result.get('gesture')), 174)
    row('CONFIRMED', status.get('confirmed_gesture'), 209)
    line(230)

    candidate = result.get('candidate')
    angle = result.get('angles', {}).get(candidate) if candidate else result.get('best_angle')
    row('TARGET', candidate, 261, accent if candidate else muted)
    row('ANGLE', f"{_number(angle)} / {_number(status.get('max_angle_degrees'))} deg", 296)
    elapsed = status.get('hold_elapsed', getattr(trial, 'hold_elapsed', None))
    duration = status.get('hold_seconds', getattr(trial, 'hold_seconds', None))
    row('HOLD', f"{_number(elapsed, 2)} / {_number(duration, 2)} s", 331)

    state = status.get('state', getattr(trial, 'state', result.get('reason', '--')))
    cv2.rectangle(display, (x - 2, 353), (display.shape[1] - 20, 425), (48, 42, 34), -1)
    _text(display, 'STATE', (x + 10, 376), .42, muted)
    _text(display, state, (x + 10, 405), .61, accent, available_width - 20)
    row('SELECTED', status.get('selected', getattr(trial, 'selected', None)), 456, success)
    combo = status.get('combo_history') or []
    remaining = status.get('combo_remaining')
    if combo or remaining is not None:
        combo_text = ' > '.join(map(str, combo)) or '--'
        if remaining is not None:
            combo_text += f" ({_number(remaining)} s)"
        _text(display, f'COMBO  {combo_text}', (x, 483), .43, muted, available_width)
    line(498)

    _text(display, 'LAST ACTION REQUEST', (x, 526), .43, muted)
    last_action = status.get('last_action', getattr(trial, 'last_event', None))
    _text(display, last_action, (x, 555), .52, max_width=available_width)
    action_status = status.get('action_status')
    row('RESULT', action_status, 590, warning if action_status == 'FAILED' else accent)
    _text(display, 'SENT = command sent, not device confirmation', (x, 615), .35, muted, available_width)
    line(632)

    finger = result.get('finger_length_px')
    minimum = result.get('min_finger_length_px')
    _text(display, f"FINGER  {_number(finger)} px  /  MIN {_number(minimum)} px", (x, 659), .42, muted, available_width)
    reason = result.get('reason')
    _text(display, f"CHECK   {reason or '--'}", (x, 684), .42, muted, available_width)
    best_target = result.get('best_target')
    if not candidate and best_target:
        _text(display, f"NEAREST {best_target} ({_number(result.get('best_angle'))} deg)", (x, 709), .42, muted, available_width)

    history = status.get('history') or []
    if history:
        line(727)
        _text(display, 'RECENT EVENTS', (x, 751), .4, muted)
        visible_count = max(0, (display.shape[0] - 769) // 22)
        for index, entry in enumerate(history[:visible_count] if visible_count else []):
            _text(display, entry, (x, 775 + index * 22), .4, max_width=available_width)


def draw_preview(rgb, centers, result, selected, paused, trial=None, dirty=False, live=False, status=None):
    height, width = rgb.shape[:2]
    w, h = preview_geometry(rgb.shape)
    canvas_width = w + 280
    display = np.full((max(h + 300, 740), canvas_width + PANEL_WIDTH, 3), 28, dtype=np.uint8)
    display[IMAGE_Y:IMAGE_Y+h, IMAGE_X:IMAGE_X+w] = cv2.resize(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), (w, h))
    canvas = display[:, :canvas_width]

    def screen(point):
        return tuple(np.rint(np.array(point) * [w, h] + [IMAGE_X, IMAGE_Y]).astype(int))

    origin = None if result.get('origin') is None else screen(np.asarray(result['origin']) / [width, height])
    for device, point in centers.items():
        center = screen(point)
        color = (152, 211, 147) if device == result.get('candidate') else (107, 187, 236)
        if origin is not None:
            cv2.line(canvas, origin, center, color, 1, cv2.LINE_AA)
        cv2.drawMarker(canvas, center, color, cv2.MARKER_CROSS, 20, 2, cv2.LINE_AA)
        angle = result.get('angles', {}).get(device)
        label = 'ALL LIGHTS / CEILING' if device == 'LIGHT' else device
        text = label if angle is None else f'{label}: {angle:.1f} deg'
        label_x = max(8, min(center[0] + 10, canvas_width - 205))
        label_y = max(127, min(center[1], display.shape[0] - 15))
        _text(canvas, text, (label_x, label_y), .52, color, canvas_width - label_x - 8)
    if origin is not None and result.get('tip') is not None:
        vector = (np.asarray(result['tip']) - result['origin']) * [w / width, h / height]
        length = np.linalg.norm(vector)
        if length >= 1:
            end = tuple(np.rint(np.array(origin) + vector / length * 2 * max(w, h)).astype(int))
            cv2.arrowedLine(canvas, origin, end, (231, 211, 104), 3, cv2.LINE_AA, tipLength=.03)
        cv2.circle(canvas, origin, 5, (239, 239, 239), -1, cv2.LINE_AA)
        cv2.circle(canvas, screen(np.asarray(result['tip']) / [width, height]), 5, (231, 211, 104), -1, cv2.LINE_AA)

    cv2.rectangle(canvas, (0, 0), (canvas_width, 105), (23, 22, 20), -1)
    _text(canvas, 'HGHC / POINTING PREVIEW', (20, 29), .68)
    mode = (status or {}).get('mode', 'LIVE' if live else 'SIMULATION')
    playback = 'PAUSED' if paused else 'PLAYING'
    subtitle = f"{mode}  |  {playback}  |  CYAN: FINGER   GOLD: TARGET   GREEN: CANDIDATE"
    _text(canvas, subtitle, (20, 56), .45, (160, 168, 176), canvas_width - 40)
    if live:
        controls = 'Space: pause | N: next frame | Q/Esc: quit | Edit centers in pointing_preview.py'
    else:
        controls = f"Edit: {selected}{' * UNSAVED' if dirty else ''} | Click: center | [ ]: device | S: save | X: remove | Space: pause | N: step | Q: quit"
    _text(canvas, controls, (20, 84), .43, (209, 214, 220), canvas_width - 40)
    _draw_panel(display, canvas_width, status, result, trial, live)
    return display
