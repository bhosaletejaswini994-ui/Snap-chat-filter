# import cv2
# import mediapipe as mp
# import numpy as np
# import math

# # --- CONFIGURATION ---
# FILTER_IMAGE_PATH = "google.png"
# FILTER_SCALE = 2.8        # Scale relative to eye distance
# Y_OFFSET_FACTOR = 0.1     # Positive moves filter down

# # Initialize MediaPipe Face Mesh
# mp_face_mesh = mp.solutions.face_mesh
# face_mesh = mp_face_mesh.FaceMesh(
#     max_num_faces=1,
#     refine_landmarks=True,
#     min_detection_confidence=0.5,
#     min_tracking_confidence=0.5
# )


# def overlay_transparent_rotated(background, overlay, center_x, center_y, w, h, angle):
#     """
#     Overlays a transparent PNG onto `background`, centered at (center_x, center_y),
#     resized to (w, h) and rotated by `angle` degrees (positive = counter-clockwise).
#     """
#     # 1) Resize overlay to target size
#     overlay_resized = cv2.resize(overlay, (w, h), interpolation=cv2.INTER_AREA)

#     # 2) Rotate the overlay (with alpha) around its own center
#     #    Pad the canvas so the rotated corners are not clipped
#     diag = int(math.ceil(math.hypot(w, h)))
#     canvas = np.zeros((diag, diag, 4), dtype=np.uint8)
#     ox = (diag - w) // 2
#     oy = (diag - h) // 2
#     canvas[oy:oy + h, ox:ox + w] = overlay_resized

#     rot_mat = cv2.getRotationMatrix2D((diag / 2, diag / 2), angle, 1.0)
#     rotated = cv2.warpAffine(
#         canvas, rot_mat, (diag, diag),
#         flags=cv2.INTER_LINEAR,
#         borderMode=cv2.BORDER_CONSTANT,
#         borderValue=(0, 0, 0, 0)
#     )

#     # 3) Compute top-left corner so that the filter's CENTER lands at (center_x, center_y)
#     x = int(center_x - diag / 2)
#     y = int(center_y - diag / 2)

#     # 4) Bounds check
#     bg_h, bg_w = background.shape[:2]
#     if x >= bg_w or y >= bg_h or x + diag <= 0 or y + diag <= 0:
#         return background

#     x1, y1 = max(0, x), max(0, y)
#     x2, y2 = min(bg_w, x + diag), min(bg_h, y + diag)

#     ox1, oy1 = max(0, -x), max(0, -y)
#     ox2, oy2 = ox1 + (x2 - x1), oy1 + (y2 - y1)

#     roi = background[y1:y2, x1:x2]
#     overlay_crop = rotated[oy1:oy2, ox1:ox2]

#     overlay_rgb = overlay_crop[:, :, :3].astype(np.float32)
#     alpha = (overlay_crop[:, :, 3:4].astype(np.float32)) / 255.0

#     # Vectorized alpha blend
#     roi[:] = (alpha * overlay_rgb + (1.0 - alpha) * roi.astype(np.float32)).astype(np.uint8)
#     return background


# def main():
#     filter_img = cv2.imread(FILTER_IMAGE_PATH, cv2.IMREAD_UNCHANGED)
#     if filter_img is None:
#         print(f"Error: Could not load {FILTER_IMAGE_PATH}.")
#         return
#     if filter_img.ndim != 3 or filter_img.shape[2] != 4:
#         print("Error: Filter must have 4 channels (BGRA).")
#         return

#     cap = cv2.VideoCapture(0)

#     while cap.isOpened():
#         success, frame = cap.read()
#         if not success:
#             break

#         # Selfie mirror view
#         frame = cv2.flip(frame, 1)
#         h, w, _ = frame.shape

#         rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = face_mesh.process(rgb_frame)

#         if results.multi_face_landmarks:
#             for face_landmarks in results.multi_face_landmarks:
#                 def to_pixel(lm):
#                     return int(lm.x * w), int(lm.y * h)

#                 # Eye corner landmarks
#                 p_left_outer  = to_pixel(face_landmarks.landmark[33])
#                 p_left_inner  = to_pixel(face_landmarks.landmark[133])
#                 p_right_inner = to_pixel(face_landmarks.landmark[362])
#                 p_right_outer = to_pixel(face_landmarks.landmark[263])

#                 # Eye centers
#                 left_center  = ((p_left_outer[0]  + p_left_inner[0])  // 2,
#                                 (p_left_outer[1]  + p_left_inner[1])  // 2)
#                 right_center = ((p_right_outer[0] + p_right_inner[0]) // 2,
#                                 (p_right_outer[1] + p_right_inner[1]) // 2)

#                 # --- Roll angle of the face ---
#                 # Vector from left_center -> right_center
#                 dx = right_center[0] - left_center[0]
#                 dy = right_center[1] - left_center[1]
#                 # atan2 returns radians; convert to degrees.
#                 # NOTE: In image coordinates Y grows downward, so a positive
#                 #       dy means the right eye is LOWER on screen. We negate
#                 #       dy so that a "head tilt to the right" produces a
#                 #       positive rotation angle (CCW in OpenCV convention).
#                 angle = math.degrees(math.atan2(-dy, dx))

#                 # Eye distance (scale reference)
#                 eye_dist = math.hypot(dx, dy)

#                 # Filter size
#                 filter_w = max(1, int(eye_dist * FILTER_SCALE))
#                 aspect_ratio = filter_img.shape[0] / filter_img.shape[1]
#                 filter_h = max(1, int(filter_w * aspect_ratio))

#                 # Center of the filter (midpoint between eyes)
#                 mid_x = (left_center[0] + right_center[0]) // 2
#                 mid_y = (left_center[1] + right_center[1]) // 2

#                 # Vertical offset in the *rotated* frame:
#                 # shift downward along the face's "up" direction so the
#                 # offset stays consistent when the head tilts.
#                 rad = math.radians(angle)
#                 offset = filter_h * Y_OFFSET_FACTOR
#                 # "down" in face-local space => rotate (0, +offset) by angle
#                 offset_x = -math.sin(rad) * offset
#                 offset_y =  math.cos(rad) * offset
#                 mid_x += int(offset_x)
#                 mid_y += int(offset_y)

#                 # Apply rotated overlay
#                 frame = overlay_transparent_rotated(
#                     frame, filter_img,
#                     center_x=mid_x,
#                     center_y=mid_y,
#                     w=filter_w,
#                     h=filter_h,
#                     angle=angle
#                 )

#         cv2.imshow('Snapchat Filter - Google Eyes (Tilt-Aware)', frame)
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

#     cap.release()
#     cv2.destroyAllWindows()


# if __name__ == "__main__":
#     main()

# import cv2
# import mediapipe as mp
# import numpy as np
# import math

# # --- CONFIGURATION ---
# DOG_NEUTRAL_PATH   = "dog.png"
# DOG_SMILE_PATH     = "dog_smile.png"
# SUNGLASSES_PATH    = "sunglasses.png"

# DOG_WIDTH_FACTOR   = 1.9
# DOG_Y_OFFSET       = 0.42

# SUNGLASSES_SCALE   = 1.25
# SUNGLASSES_Y_OFF   = 0.02

# SMILE_THRESHOLD    = 0.32

# # --- TILT ---
# # TILT_FOLLOW: 1.0 = dog tilts exactly with face.
# #              <1.0 = subtler tilt.  >1.0 = exaggerated tilt.
# TILT_FOLLOW        = 1.0

# # Smoothing per element (0 = frozen, 1 = no smoothing). Lower = snappier.
# DOG_SMOOTHING      = 0.20
# GLASSES_SMOOTHING  = 0.30

# SHOW_DEBUG         = True   # prints tilt angle + smile ratio on screen

# # Landmark indices
# L_OUTER, L_INNER, R_INNER, R_OUTER = 33, 133, 362, 263
# MOUTH_L, MOUTH_R   = 61, 291
# LIP_UPPER, LIP_LOWER = 13, 14
# FOREHEAD, CHIN     = 10, 152


# def load_png(path):
#     img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
#     if img is None:
#         raise FileNotFoundError(f"Could not load {path}")
#     if img.ndim != 3 or img.shape[2] != 4:
#         raise ValueError(f"{path} must be a 4-channel BGRA PNG.")
#     return img


# def overlay_rotated(background, overlay, center_x, center_y, w, h, angle):
#     w, h = max(1, int(w)), max(1, int(h))
#     overlay_resized = cv2.resize(overlay, (w, h), interpolation=cv2.INTER_AREA)

#     diag = int(math.ceil(math.hypot(w, h)))
#     canvas = np.zeros((diag, diag, 4), dtype=np.uint8)
#     ox, oy = (diag - w) // 2, (diag - h) // 2
#     canvas[oy:oy + h, ox:ox + w] = overlay_resized

#     rot_mat = cv2.getRotationMatrix2D((diag / 2, diag / 2), angle, 1.0)
#     rotated = cv2.warpAffine(canvas, rot_mat, (diag, diag),
#                              flags=cv2.INTER_LINEAR,
#                              borderMode=cv2.BORDER_CONSTANT,
#                              borderValue=(0, 0, 0, 0))

#     x = int(center_x - diag / 2)
#     y = int(center_y - diag / 2)

#     bg_h, bg_w = background.shape[:2]
#     if x >= bg_w or y >= bg_h or x + diag <= 0 or y + diag <= 0:
#         return background

#     x1, y1 = max(0, x), max(0, y)
#     x2, y2 = min(bg_w, x + diag), min(bg_h, y + diag)
#     ox1, oy1 = max(0, -x), max(0, -y)
#     ox2, oy2 = ox1 + (x2 - x1), oy1 + (y2 - y1)

#     roi = background[y1:y2, x1:x2]
#     ov_crop = rotated[oy1:oy2, ox1:ox2]
#     rgb = ov_crop[:, :, :3].astype(np.float32)
#     a = (ov_crop[:, :, 3:4].astype(np.float32)) / 255.0
#     roi[:] = (a * rgb + (1.0 - a) * roi.astype(np.float32)).astype(np.uint8)
#     return background


# def is_smiling(landmarks, w, h):
#     def px(idx):
#         lm = landmarks[idx]
#         return lm.x * w, lm.y * h

#     ml_x, ml_y = px(MOUTH_L)
#     mr_x, mr_y = px(MOUTH_R)
#     lu_x, lu_y = px(LIP_UPPER)
#     fh_x, fh_y = px(FOREHEAD)
#     ch_x, ch_y = px(CHIN)

#     mouth_width = math.hypot(mr_x - ml_x, mr_y - ml_y)
#     face_height = math.hypot(ch_x - fh_x, ch_y - fh_y)
#     if face_height < 1e-3:
#         return False, 0.0

#     ratio = mouth_width / face_height
#     corner_y = (ml_y + mr_y) / 2
#     corners_raised = corner_y <= lu_y + 0.01 * face_height
#     smiling = (ratio > SMILE_THRESHOLD) or (ratio > SMILE_THRESHOLD * 0.85 and corners_raised)
#     return smiling, ratio


# def main():
#     dog_neutral = load_png(DOG_NEUTRAL_PATH)
#     dog_smile   = load_png(DOG_SMILE_PATH)
#     sunglasses  = load_png(SUNGLASSES_PATH)

#     mp_face_mesh = mp.solutions.face_mesh
#     face_mesh = mp_face_mesh.FaceMesh(
#         max_num_faces=1, refine_landmarks=True,
#         min_detection_confidence=0.5, min_tracking_confidence=0.5,
#     )

#     cap = cv2.VideoCapture(0)

#     # Separate smoothing states per element
#     s_dog_angle = None
#     s_dog_dist  = None
#     s_gl_angle  = None
#     s_gl_dist   = None

#     while cap.isOpened():
#         ok, frame = cap.read()
#         if not ok:
#             break

#         frame = cv2.flip(frame, 1)
#         h, w, _ = frame.shape
#         rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = face_mesh.process(rgb)

#         smiling_now = False
#         debug_angle = 0.0
#         debug_ratio = 0.0

#         if results.multi_face_landmarks:
#             lm = results.multi_face_landmarks[0].landmark

#             def px(i):
#                 return int(lm[i].x * w), int(lm[i].y * h)

#             p_lo, p_li = px(L_OUTER), px(L_INNER)
#             p_ri, p_ro = px(R_INNER), px(R_OUTER)
#             lc = ((p_lo[0] + p_li[0]) // 2, (p_lo[1] + p_li[1]) // 2)
#             rc = ((p_ro[0] + p_ri[0]) // 2, (p_ro[1] + p_ri[1]) // 2)

#             dx, dy = rc[0] - lc[0], rc[1] - lc[1]
#             raw_angle = math.degrees(math.atan2(-dy, dx))
#             raw_dist  = math.hypot(dx, dy)

#             # init smoothing states on first frame
#             if s_dog_angle is None:
#                 s_dog_angle, s_dog_dist = raw_angle, raw_dist
#                 s_gl_angle,  s_gl_dist  = raw_angle, raw_dist

#             s_dog_angle = DOG_SMOOTHING * s_dog_angle + (1 - DOG_SMOOTHING) * raw_angle
#             s_dog_dist  = DOG_SMOOTHING * s_dog_dist  + (1 - DOG_SMOOTHING) * raw_dist
#             s_gl_angle  = GLASSES_SMOOTHING * s_gl_angle + (1 - GLASSES_SMOOTHING) * raw_angle
#             s_gl_dist   = GLASSES_SMOOTHING * s_gl_dist  + (1 - GLASSES_SMOOTHING) * raw_dist

#             # Apply TILT_FOLLOW only to the *rotation* of the dog (not the glasses)
#             dog_angle = s_dog_angle * TILT_FOLLOW
#             gl_angle  = s_gl_angle

#             debug_angle = dog_angle

#             mid_x = (lc[0] + rc[0]) // 2
#             mid_y = (lc[1] + rc[1]) // 2

#             # Face-height (for dog anchor)
#             fh = px(FOREHEAD); ch = px(CHIN)
#             face_height = math.hypot(ch[0] - fh[0], ch[1] - fh[1])

#             # ---- SMILE ----
#             smiling_now, debug_ratio = is_smiling(lm, w, h)
#             dog = dog_smile if smiling_now else dog_neutral

#             # ---- DOG (tilt-aware position AND rotation) ----
#             dog_w = max(1, int(s_dog_dist * DOG_WIDTH_FACTOR))
#             dog_h = int(dog_w * dog.shape[0] / dog.shape[1])

#             # Rotate "up" vector by dog_angle so dog stays above head when tilted
#             dog_rad = math.radians(dog_angle)
#             up_dx =  math.sin(dog_rad)
#             up_dy = -math.cos(dog_rad)
#             lift = DOG_Y_OFFSET * face_height + dog_h * 0.35
#             dog_cx = mid_x + up_dx * lift
#             dog_cy = mid_y + up_dy * lift

#             frame = overlay_rotated(frame, dog, dog_cx, dog_cy, dog_w, dog_h, dog_angle)

#             # ---- SUNGLASSES (tilt-aware) ----
#             sg_w = max(1, int(s_gl_dist * SUNGLASSES_SCALE))
#             sg_h = int(sg_w * sunglasses.shape[0] / sunglasses.shape[1])
#             sg_rad = math.radians(gl_angle)
#             sg_off = s_gl_dist * SUNGLASSES_Y_OFF
#             sg_cx = mid_x + (-math.sin(sg_rad)) * sg_off
#             sg_cy = mid_y + ( math.cos(sg_rad)) * sg_off

#             frame = overlay_rotated(frame, sunglasses, sg_cx, sg_cy, sg_w, sg_h, gl_angle)

#         # HUD
#         color = (0, 255, 0) if smiling_now else (180, 180, 180)
#         cv2.putText(frame, "SMILING" if smiling_now else "NEUTRAL",
#                     (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
#         if SHOW_DEBUG:
#             cv2.putText(frame, f"tilt: {debug_angle:+6.1f}deg  smile: {debug_ratio:.2f}",
#                         (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)

#         cv2.imshow("Dog + Sunglasses (Tilt + Smile)", frame)
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

#     cap.release()
#     cv2.destroyAllWindows()


# if __name__ == "__main__":
#     main()

# import cv2
# import mediapipe as mp
# import numpy as np
# import math
# import os

# # --- CONFIGURATION ---
# DOG_IMAGE_PATH   = "pngtree-lovely-dog-ear-decoration-png-image_7380427.png"
# GOOGLE_IMAGE_PATH = "google.png"

# # Dog placement — the dog face is drawn OVER the whole face
# DOG_SCALE         = 4.2       # relative to eye distance
# DOG_Y_OFFSET      = 0.05      # positive pushes down along face "down" axis

# # Google logo on eyes
# GOOGLE_SCALE      = 3.0
# GOOGLE_Y_OFFSET   = 0.05

# # Smoothing (0 = frozen, 1 = no smoothing). Lower = snappier.
# DOG_SMOOTH        = 0.25
# GOOGLE_SMOOTH     = 0.25

# # Max webp output size so the per-frame resize doesn't tank FPS
# MAX_OVERLAY_W     = 900

# SHOW_DEBUG        = True

# # Landmarks
# L_OUTER, L_INNER, R_INNER, R_OUTER = 33, 133, 362, 263
# FOREHEAD, CHIN    = 10, 152


# # ---------------------------------------------------------------
# # Robust loader: works for PNG, WebP, GIF frame 1, etc.
# # Guarantees a 4-channel BGRA image with a valid alpha channel.
# # ---------------------------------------------------------------
# def load_overlay(path, max_w=MAX_OVERLAY_W):
#     if not os.path.exists(path):
#         raise FileNotFoundError(f"Missing: {path}")

#     img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
#     if img is None:
#         raise IOError(
#             f"cv2.imread could not decode {path}. "
#             f"If it's a WebP, your OpenCV build may lack WebP support. "
#             f"Try: pip install --upgrade opencv-python"
#         )

#     # Some webp/gif frames come back as 2D grayscale
#     if img.ndim == 2:
#         img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
#     elif img.shape[2] == 3:
#         # No alpha channel in file -> synthesize from a white-background check
#         # (assumes the artwork sits on a light background; common for sticker PNGs)
#         bgr = img
#         # Use luminance-distance-from-white as alpha
#         white_dist = 255 - np.min(bgr, axis=2)
#         alpha = np.clip(white_dist.astype(np.float32) * 1.3, 0, 255).astype(np.uint8)
#         img = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA)
#         img[:, :, 3] = alpha
#     # else: already 4-channel BGRA

#     # Downscale huge source assets once at load (huge win for FPS)
#     if img.shape[1] > max_w:
#         r = max_w / img.shape[1]
#         img = cv2.resize(img, (max_w, int(img.shape[0] * r)),
#                          interpolation=cv2.INTER_AREA)

#     return img


# # ---------------------------------------------------------------
# # Rotated alpha-blended overlay, centered at (cx, cy)
# # ---------------------------------------------------------------
# def overlay_rotated(background, overlay, cx, cy, w, h, angle):
#     w, h = max(1, int(w)), max(1, int(h))
#     ov = cv2.resize(overlay, (w, h), interpolation=cv2.INTER_AREA)

#     diag = int(math.ceil(math.hypot(w, h)))
#     canvas = np.zeros((diag, diag, 4), dtype=np.uint8)
#     ox, oy = (diag - w) // 2, (diag - h) // 2
#     canvas[oy:oy + h, ox:ox + w] = ov

#     M = cv2.getRotationMatrix2D((diag / 2, diag / 2), angle, 1.0)
#     rot = cv2.warpAffine(canvas, M, (diag, diag),
#                          flags=cv2.INTER_LINEAR,
#                          borderMode=cv2.BORDER_CONSTANT,
#                          borderValue=(0, 0, 0, 0))

#     x = int(cx - diag / 2)
#     y = int(cy - diag / 2)

#     bg_h, bg_w = background.shape[:2]
#     if x >= bg_w or y >= bg_h or x + diag <= 0 or y + diag <= 0:
#         return background

#     x1, y1 = max(0, x), max(0, y)
#     x2, y2 = min(bg_w, x + diag), min(bg_h, y + diag)
#     ox1, oy1 = max(0, -x), max(0, -y)
#     ox2, oy2 = ox1 + (x2 - x1), oy1 + (y2 - y1)

#     roi = background[y1:y2, x1:x2]
#     crop = rot[oy1:oy2, ox1:ox2]
#     rgb = crop[:, :, :3].astype(np.float32)
#     a = crop[:, :, 3:4].astype(np.float32) / 255.0
#     roi[:] = (a * rgb + (1.0 - a) * roi.astype(np.float32)).astype(np.uint8)
#     return background


# def main():
#     dog    = load_overlay(DOG_IMAGE_PATH)
#     google = load_overlay(GOOGLE_IMAGE_PATH)
#     print(f"Dog overlay   : {dog.shape}  alpha min={dog[...,3].min()} max={dog[...,3].max()}")
#     print(f"Google overlay: {google.shape} alpha min={google[...,3].min()} max={google[...,3].max()}")

#     mp_face_mesh = mp.solutions.face_mesh
#     face_mesh = mp_face_mesh.FaceMesh(
#         max_num_faces=1, refine_landmarks=True,
#         min_detection_confidence=0.5, min_tracking_confidence=0.5,
#     )

#     cap = cv2.VideoCapture(0)

#     dog_angle_s = dog_dist_s = None
#     ggl_angle_s = ggl_dist_s = None

#     while cap.isOpened():
#         ok, frame = cap.read()
#         if not ok:
#             break

#         frame = cv2.flip(frame, 1)
#         h, w, _ = frame.shape
#         rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = face_mesh.process(rgb)

#         dbg = ""

#         if results.multi_face_landmarks:
#             lm = results.multi_face_landmarks[0].landmark

#             def px(i):
#                 return int(lm[i].x * w), int(lm[i].y * h)

#             # Eye corners / centers
#             p_lo, p_li = px(L_OUTER), px(L_INNER)
#             p_ri, p_ro = px(R_INNER), px(R_OUTER)
#             lc = ((p_lo[0] + p_li[0]) // 2, (p_lo[1] + p_li[1]) // 2)
#             rc = ((p_ro[0] + p_ri[0]) // 2, (p_ro[1] + p_ri[1]) // 2)

#             dx, dy = rc[0] - lc[0], rc[1] - lc[1]
#             raw_angle = math.degrees(math.atan2(-dy, dx))
#             raw_dist  = math.hypot(dx, dy)
#             if raw_dist < 1:
#                 raw_dist = 1

#             # Smoothing
#             if dog_angle_s is None:
#                 dog_angle_s, dog_dist_s = raw_angle, raw_dist
#                 ggl_angle_s, ggl_dist_s = raw_angle, raw_dist
#             dog_angle_s = DOG_SMOOTH * dog_angle_s + (1 - DOG_SMOOTH) * raw_angle
#             dog_dist_s  = DOG_SMOOTH * dog_dist_s  + (1 - DOG_SMOOTH) * raw_dist
#             ggl_angle_s = GOOGLE_SMOOTH * ggl_angle_s + (1 - GOOGLE_SMOOTH) * raw_angle
#             ggl_dist_s  = GOOGLE_SMOOTH * ggl_dist_s  + (1 - GOOGLE_SMOOTH) * raw_dist

#             mid_x = (lc[0] + rc[0]) // 2
#             mid_y = (lc[1] + rc[1]) // 2

#             # ------------------ DOG ------------------
#             # Size: relative to eye distance but respect dog aspect ratio
#             dog_w = max(1, int(dog_dist_s * DOG_SCALE))
#             dog_h = int(dog_w * dog.shape[0] / dog.shape[1])

#             # Anchor: rotate the "down" offset with the face so the dog
#             # sits *slightly* below the eye line (like a face mask)
#             rad = math.radians(dog_angle_s)
#             down_x = -math.sin(rad)
#             down_y =  math.cos(rad)
#             off = dog_h * DOG_Y_OFFSET
#             dog_cx = mid_x + down_x * off
#             dog_cy = mid_y + down_y * off

#             frame = overlay_rotated(frame, dog, dog_cx, dog_cy,
#                                     dog_w, dog_h, dog_angle_s)

#             # ------------------ GOOGLE ------------------
#             # Place logo on top of the eyes (so it stays visible over the dog)
#             g_w = max(1, int(ggl_dist_s * GOOGLE_SCALE))
#             g_h = int(g_w * google.shape[0] / google.shape[1])

#             rad_g = math.radians(ggl_angle_s)
#             off_g = g_h * GOOGLE_Y_OFFSET
#             g_cx = mid_x + (-math.sin(rad_g)) * off_g
#             g_cy = mid_y + ( math.cos(rad_g)) * off_g

#             frame = overlay_rotated(frame, google, g_cx, g_cy,
#                                     g_w, g_h, ggl_angle_s)

#             if SHOW_DEBUG:
#                 dbg = f"angle={dog_angle_s:+.1f}  eye_dist={dog_dist_s:.0f}px"

#         cv2.putText(frame, "Q to quit", (20, 30),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 1)
#         if SHOW_DEBUG and dbg:
#             cv2.putText(frame, dbg, (20, 60),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)

#         cv2.imshow("Dog + Google Eyes Filter", frame)
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

#     cap.release()
#     cv2.destroyAllWindows()


# if __name__ == "__main__":
#     main()

import cv2
import mediapipe as mp
import numpy as np
import math
import os

# -------------------- PATHS --------------------
DOG_NEUTRAL_PATH     = "pngtree-lovely-dog-ear-decoration-png-image_7380427.png"
DOG_SMILE_PATH       = "dog_smile.png"
DOG_BLINK_PATH       = "dog_blink.png"
DOG_SMILE_BLINK_PATH = "dog_smile_blink.png"
GOOGLE_IMAGE_PATH    = "google.png"

# -------------------- PLACEMENT --------------------
DOG_SCALE         = 3.6
DOG_Y_OFFSET      = -0.25

GOOGLE_SCALE      = 3.0
GOOGLE_Y_OFFSET   = 0.05

# -------------------- SMOOTHING --------------------
DOG_SMOOTH        = 0.25
GOOGLE_SMOOTH     = 0.25
# Extra smoothing on yaw/pitch so head turns don't jitter
YAW_SMOOTH        = 0.35
PITCH_SMOOTH      = 0.35

# Yaw/pitch gains — how strongly the overlay responds to nose direction.
# 1.0 = match nose literally. >1 = exaggerated. <1 = subtle.
YAW_GAIN          = 0.85
PITCH_GAIN        = 0.65
# Cap so extreme turns don't flip the image
MAX_YAW_DEG       = 55.0
MAX_PITCH_DEG     = 35.0

# -------------------- THRESHOLDS --------------------
SMILE_THRESHOLD   = 0.30
LAUGH_OPEN_THRESH = 0.025
EAR_CLOSED        = 0.19
EAR_OPEN          = 0.24
STATE_DEBOUNCE    = 3

MAX_OVERLAY_W     = 900
SHOW_DEBUG        = True

# -------------------- LANDMARKS --------------------
L_OUTER, L_INNER, R_INNER, R_OUTER = 33, 133, 362, 263
L_EYE_UP,  L_EYE_DN = 159, 145
R_EYE_UP,  R_EYE_DN = 386, 374
MOUTH_L, MOUTH_R    = 61, 291
LIP_UP,  LIP_DN     = 13, 14
FOREHEAD, CHIN      = 10, 152

# Nose landmarks
NOSE_TIP     = 1
NOSE_BRIDGE  = 168
NOSE_BASE    = 2
NOSE_L_ALAR  = 129
NOSE_R_ALAR  = 358


# -----------------------------------------------------------
def load_overlay(path, max_w=MAX_OVERLAY_W, required=False):
    if not os.path.exists(path):
        if required:
            raise FileNotFoundError(f"Missing required file: {path}")
        return None
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise IOError(f"cv2.imread could not decode {path}")
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
    elif img.shape[2] == 3:
        bgr = img
        white_dist = 255 - np.min(bgr, axis=2)
        alpha = np.clip(white_dist.astype(np.float32) * 1.3, 0, 255).astype(np.uint8)
        img = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA)
        img[:, :, 3] = alpha
    if img.shape[1] > max_w:
        r = max_w / img.shape[1]
        img = cv2.resize(img, (max_w, int(img.shape[0] * r)),
                         interpolation=cv2.INTER_AREA)
    return img


def overlay_perspective(background, overlay, cx, cy, w, h,
                        roll_deg, yaw_deg, pitch_deg):
    """
    Draw overlay rotated by roll (in-plane), and foreshortened by yaw/pitch
    (out-of-plane) using a perspective warp centered at (cx, cy).
    """
    w, h = max(1, int(w)), max(1, int(h))
    ov = cv2.resize(overlay, (w, h), interpolation=cv2.INTER_AREA)

    # Pad to a square so a full 3D warp never clips corners
    diag = int(math.ceil(math.hypot(w, h)))
    canvas = np.zeros((diag, diag, 4), dtype=np.uint8)
    ox, oy = (diag - w) // 2, (diag - h) // 2
    canvas[oy:oy + h, ox:ox + w] = ov

    # ---- Build a 3D rotation and project back to 2D ----
    # We rotate around X (pitch), Y (yaw), Z (roll) in that order.
    rx = math.radians(pitch_deg)
    ry = math.radians(yaw_deg)
    rz = math.radians(roll_deg)

    Rx = np.array([[1, 0, 0],
                   [0, math.cos(rx), -math.sin(rx)],
                   [0, math.sin(rx),  math.cos(rx)]], dtype=np.float64)
    Ry = np.array([[ math.cos(ry), 0, math.sin(ry)],
                   [0,            1, 0           ],
                   [-math.sin(ry), 0, math.cos(ry)]], dtype=np.float64)
    Rz = np.array([[math.cos(rz), -math.sin(rz), 0],
                   [math.sin(rz),  math.cos(rz), 0],
                   [0,            0,            1]], dtype=np.float64)
    R = Rz @ Ry @ Rx  # apply pitch, then yaw, then roll

    # Corners of the padded canvas, centered at origin
    half = diag / 2.0
    corners = np.array([
        [-half, -half, 0],
        [ half, -half, 0],
        [ half,  half, 0],
        [-half,  half, 0],
    ], dtype=np.float64)

    # Simple perspective: after rotation, apply foreshortening based on Z
    # (points "closer" in Z project as larger). Camera distance = 3*diag.
    cam_z = 3.0 * diag
    rot_corners = (R @ corners.T).T
    proj = []
    for p in rot_corners:
        denom = cam_z - p[2]
        if denom < cam_z * 0.3:
            denom = cam_z * 0.3
        scale = cam_z / denom
        proj.append([p[0] * scale, p[1] * scale])
    proj = np.array(proj, dtype=np.float32) + np.array([half, half], dtype=np.float32)

    src = np.array([
        [0,     0    ],
        [diag,  0    ],
        [diag,  diag ],
        [0,     diag ],
    ], dtype=np.float32)

    M = cv2.getPerspectiveTransform(src, proj)
    warped = cv2.warpPerspective(
        canvas, M, (diag, diag),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )

    x = int(cx - diag / 2)
    y = int(cy - diag / 2)
    bg_h, bg_w = background.shape[:2]
    if x >= bg_w or y >= bg_h or x + diag <= 0 or y + diag <= 0:
        return background

    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(bg_w, x + diag), min(bg_h, y + diag)
    ox1, oy1 = max(0, -x), max(0, -y)
    ox2, oy2 = ox1 + (x2 - x1), oy1 + (y2 - y1)

    roi = background[y1:y2, x1:x2]
    crop = warped[oy1:oy2, ox1:ox2]
    rgb = crop[:, :, :3].astype(np.float32)
    a = crop[:, :, 3:4].astype(np.float32) / 255.0
    roi[:] = (a * rgb + (1.0 - a) * roi.astype(np.float32)).astype(np.uint8)
    return background


def eye_aspect_ratio(upper, lower, left_c, right_c):
    horiz = math.hypot(right_c[0] - left_c[0], right_c[1] - left_c[1])
    if horiz < 1:
        return 0.0
    vert = math.hypot(upper[0] - lower[0], upper[1] - lower[1])
    return vert / horiz


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# -----------------------------------------------------------
def main():
    dog_neutral = load_overlay(DOG_NEUTRAL_PATH, required=True)
    dog_smile   = load_overlay(DOG_SMILE_PATH)
    dog_blink   = load_overlay(DOG_BLINK_PATH)
    dog_both    = load_overlay(DOG_SMILE_BLINK_PATH)
    google      = load_overlay(GOOGLE_IMAGE_PATH, required=True)

    have = {
        "smile": dog_smile is not None,
        "blink": dog_blink is not None,
        "both":  dog_both  is not None,
    }
    print("Dog overlay   :", dog_neutral.shape,
          f"alpha[{dog_neutral[...,3].min()}-{dog_neutral[...,3].max()}]")
    print("Google overlay:", google.shape,
          f"alpha[{google[...,3].min()}-{google[...,3].max()}]")
    print("Optional dog states loaded:", have)

    def pick_dog(smiling, blinking):
        if smiling and blinking and have["both"]:
            return dog_both
        if smiling and have["smile"]:
            return dog_smile
        if blinking and have["blink"]:
            return dog_blink
        return dog_neutral

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1, refine_landmarks=True,
        min_detection_confidence=0.5, min_tracking_confidence=0.5,
    )

    cap = cv2.VideoCapture(0)

    # Smoothed state
    dog_angle_s = dog_dist_s = None
    ggl_angle_s = ggl_dist_s = None
    dog_yaw_s = dog_pitch_s = 0.0
    ggl_yaw_s = ggl_pitch_s = 0.0

    smiling_state = False
    blink_l_state = False
    blink_r_state = False
    smile_counter = 0
    blink_l_counter = 0
    blink_r_counter = 0

    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        dbg = ""
        smiling_now = False

        if results.multi_face_landmarks:
            lm = results.multi_face_landmarks[0].landmark

            def px(i):
                return int(lm[i].x * w), int(lm[i].y * h)

            # ---- ROLL (eye line) ----
            p_lo, p_li = px(L_OUTER), px(L_INNER)
            p_ri, p_ro = px(R_INNER), px(R_OUTER)
            lc = ((p_lo[0] + p_li[0]) // 2, (p_lo[1] + p_li[1]) // 2)
            rc = ((p_ro[0] + p_ri[0]) // 2, (p_ro[1] + p_ri[1]) // 2)
            dx, dy = rc[0] - lc[0], rc[1] - lc[1]
            raw_angle = math.degrees(math.atan2(-dy, dx))
            raw_dist  = math.hypot(dx, dy)
            if raw_dist < 1:
                raw_dist = 1

            # ---- YAW & PITCH (nose vector) ----
            # Nose bridge -> nose tip is the 2D projection of the nose axis.
            # When looking straight ahead it's ~vertical (dy only).
            # When turning right, the tip shifts right (dx grows).
            n_tip    = px(NOSE_TIP)
            n_bridge = px(NOSE_BRIDGE)
            n_base   = px(NOSE_BASE)
            n_lal    = px(NOSE_L_ALAR)
            n_ral    = px(NOSE_R_ALAR)

            # Horizontal nose offset vs face width -> yaw
            face_w = max(1, math.hypot(p_ro[0] - p_lo[0], p_ro[1] - p_lo[1]))
            nose_dx = n_tip[0] - n_bridge[0]
            yaw_raw = math.degrees(math.atan2(nose_dx, raw_dist * 0.9))
            yaw_raw *= YAW_GAIN
            yaw_raw = clamp(yaw_raw, -MAX_YAW_DEG, MAX_YAW_DEG)

            # Vertical nose offset (tip vs bridge vs base) -> pitch
            # Look down  => tip drops relative to bridge  (dy > 0)
            # Look up    => tip rises                        (dy < 0)
            face_h_eye = max(1, math.hypot(px(CHIN)[0] - px(FOREHEAD)[0],
                                           px(CHIN)[1] - px(FOREHEAD)[1]))
            nose_dy = n_tip[1] - n_bridge[1]
            # Baseline ratio when looking straight (nose is ~1/3 of face)
            baseline = 0.32
            pitch_dev = (nose_dy / face_h_eye) - baseline
            pitch_raw = math.degrees(math.atan2(pitch_dev * 2.0, 1.0))
            pitch_raw *= PITCH_GAIN
            pitch_raw = clamp(pitch_raw, -MAX_PITCH_DEG, MAX_PITCH_DEG)

            # ---- Smoothing ----
            if dog_angle_s is None:
                dog_angle_s, dog_dist_s = raw_angle, raw_dist
                ggl_angle_s, ggl_dist_s = raw_angle, raw_dist
                dog_yaw_s, dog_pitch_s = yaw_raw, pitch_raw
                ggl_yaw_s, ggl_pitch_s = yaw_raw, pitch_raw

            dog_angle_s = DOG_SMOOTH * dog_angle_s + (1 - DOG_SMOOTH) * raw_angle
            dog_dist_s  = DOG_SMOOTH * dog_dist_s  + (1 - DOG_SMOOTH) * raw_dist
            ggl_angle_s = GOOGLE_SMOOTH * ggl_angle_s + (1 - GOOGLE_SMOOTH) * raw_angle
            ggl_dist_s  = GOOGLE_SMOOTH * ggl_dist_s  + (1 - GOOGLE_SMOOTH) * raw_dist

            dog_yaw_s   = YAW_SMOOTH * dog_yaw_s   + (1 - YAW_SMOOTH) * yaw_raw
            dog_pitch_s = PITCH_SMOOTH * dog_pitch_s + (1 - PITCH_SMOOTH) * pitch_raw
            ggl_yaw_s   = YAW_SMOOTH * ggl_yaw_s   + (1 - YAW_SMOOTH) * yaw_raw
            ggl_pitch_s = PITCH_SMOOTH * ggl_pitch_s + (1 - PITCH_SMOOTH) * pitch_raw

            mid_x = (lc[0] + rc[0]) // 2
            mid_y = (lc[1] + rc[1]) // 2

            # ---- SMILE / LAUGH ----
            ml, mr = px(MOUTH_L), px(MOUTH_R)
            mouth_w = math.hypot(mr[0] - ml[0], mr[1] - ml[1])
            lu, ld = px(LIP_UP), px(LIP_DN)
            mouth_open = math.hypot(ld[0] - lu[0], ld[1] - lu[1])
            face_h = math.hypot(px(CHIN)[0] - px(FOREHEAD)[0],
                                px(CHIN)[1] - px(FOREHEAD)[1]) + 1e-6
            smile_ratio = mouth_w / face_h
            open_ratio  = mouth_open / face_h
            is_smile = smile_ratio > SMILE_THRESHOLD
            is_laugh = (smile_ratio > SMILE_THRESHOLD) and (open_ratio > LAUGH_OPEN_THRESH)
            smiling_now = is_smile or is_laugh

            # ---- BLINK ----
            le_up, le_dn = px(L_EYE_UP), px(L_EYE_DN)
            re_up, re_dn = px(R_EYE_UP), px(R_EYE_DN)
            ear_l = eye_aspect_ratio(le_up, le_dn, p_lo, p_li)
            ear_r = eye_aspect_ratio(re_up, re_dn, p_ri, p_ro)

            blink_l_now = ear_l < (EAR_OPEN if blink_l_state else EAR_CLOSED)
            blink_r_now = ear_r < (EAR_OPEN if blink_r_state else EAR_CLOSED)

            if blink_l_now != blink_l_state:
                blink_l_counter += 1
                if blink_l_counter >= STATE_DEBOUNCE:
                    blink_l_state = blink_l_now
                    blink_l_counter = 0
            else:
                blink_l_counter = 0
            if blink_r_now != blink_r_state:
                blink_r_counter += 1
                if blink_r_counter >= STATE_DEBOUNCE:
                    blink_r_state = blink_r_now
                    blink_r_counter = 0
            else:
                blink_r_counter = 0
            if smiling_now != smiling_state:
                smile_counter += 1
                if smile_counter >= STATE_DEBOUNCE:
                    smiling_state = smiling_now
                    smile_counter = 0
            else:
                smile_counter = 0

            # ---------- DOG ----------
            any_blink = blink_l_state and blink_r_state
            dog = pick_dog(smiling_state, any_blink)

            dog_w = max(1, int(dog_dist_s * DOG_SCALE))
            dog_h = int(dog_w * dog.shape[0] / dog.shape[1])

            # Anchor offset rotated in the SAME 3D space as the overlay
            rad_roll = math.radians(dog_angle_s)
            # Vertical offset along face's "up" direction (roll + pitch)
            off = dog_h * DOG_Y_OFFSET
            down_x = -math.sin(rad_roll) * math.cos(math.radians(dog_pitch_s))
            down_y =  math.cos(rad_roll) * math.cos(math.radians(dog_pitch_s))
            dog_cx = mid_x + down_x * off
            dog_cy = mid_y + down_y * off

            frame = overlay_perspective(frame, dog, dog_cx, dog_cy,
                                        dog_w, dog_h,
                                        dog_angle_s, dog_yaw_s, dog_pitch_s)

            # ---------- GOOGLE ----------
            g_w = max(1, int(ggl_dist_s * GOOGLE_SCALE))
            g_h = int(g_w * google.shape[0] / google.shape[1])
            rad_g = math.radians(ggl_angle_s)
            off_g = g_h * GOOGLE_Y_OFFSET
            g_cx = mid_x + (-math.sin(rad_g)) * off_g
            g_cy = mid_y + ( math.cos(rad_g)) * off_g
            frame = overlay_perspective(frame, google, g_cx, g_cy,
                                        g_w, g_h,
                                        ggl_angle_s, ggl_yaw_s, ggl_pitch_s)

            if SHOW_DEBUG:
                dbg = (f"roll={dog_angle_s:+.0f} yaw={dog_yaw_s:+.0f} "
                       f"pitch={dog_pitch_s:+.0f} | "
                       f"smile={smile_ratio:.2f} "
                       f"{'LAUGH ' if smiling_state else ''}"
                       f"{'BLINK' if any_blink else ''}")

        cv2.putText(frame, "Q to quit", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 1)
        if SHOW_DEBUG and dbg:
            cv2.putText(frame, dbg, (20, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        cv2.imshow("Dog Ears + Google (nose-aligned)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()