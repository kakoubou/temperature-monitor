from PIL import Image, ImageDraw, ImageFont

SIZE = 640
FONT_PATH       = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_PATH_LINUX = "/usr/share/fonts/opentype/urw-base35/C059-BdIta.otf"

# 分隔线
DIVX        = 350
DIVY        = 320
LINE_Y_TOP  = 165
LINE_Y_BOT  = 530
LINE_X_END  = 575

# 颜色
BG_FILL        = (10, 10, 15)
CIRCLE_FILL    = (20, 20, 30)
CIRCLE_OUTLINE = (50, 50, 70)
LINE_COLOR     = (70, 70, 90)
LABEL_COLOR    = (150, 150, 170)
ARC_BG_COLOR   = (40, 40, 50)

# 圆形背景
BG_MARGIN = 20

# 弧形进度条
ARC_MARGIN = 40
ARC_START  = 135
ARC_SWEEP  = 270
ARC_WIDTH  = 18

# Linux 标签
LINUX_LBL_CX = 320
LINUX_LBL_CY = 105
FONT_LINUX   = 60

# 字体大小
FONT_CPU     = 80
FONT_CPU_DEG = 34
FONT_CPU_LBL = 32
FONT_SM      = 60
FONT_SM_DEG  = 26
FONT_SM_LBL  = 32

# 模块级字体缓存
try:
    _font_cpu     = ImageFont.truetype(FONT_PATH, FONT_CPU)
    _font_cpu_deg = ImageFont.truetype(FONT_PATH, FONT_CPU_DEG)
    _font_cpu_lb  = ImageFont.truetype(FONT_PATH, FONT_CPU_LBL)
    _font_sm      = ImageFont.truetype(FONT_PATH, FONT_SM)
    _font_sm_deg  = ImageFont.truetype(FONT_PATH, FONT_SM_DEG)
    _font_sm_lb   = ImageFont.truetype(FONT_PATH, FONT_SM_LBL)
    _font_linux   = ImageFont.truetype(FONT_PATH_LINUX, FONT_LINUX)
except Exception:
    _font_cpu = _font_cpu_deg = _font_cpu_lb = ImageFont.load_default()
    _font_sm  = _font_sm_deg  = _font_sm_lb  = ImageFont.load_default()
    _font_linux = ImageFont.load_default()

# 数字中心坐标
CPU_NUM_CX = 200
CPU_NUM_CY = 300
LIQ_NUM_CX = 458
LIQ_NUM_CY = 235
GPU_NUM_CX = 458
GPU_NUM_CY = 383

# 标签坐标（左上角 x 轴居中基准，y 为顶部）
CPU_LBL_CX = 200
CPU_LBL_CY = 340
LIQ_LBL_CX = 458
LIQ_LBL_CY = 264
GPU_LBL_CX = 458
GPU_LBL_CY = 412


def temp_color(temp):
    if temp < 50:
        return (0, 220, 255)
    elif temp < 70:
        return (255, 200, 0)
    else:
        return (255, 60, 60)

def label_color(temp):
    if temp < 50:
        return LABEL_COLOR
    elif temp < 70:
        return (255, 200, 0)
    else:
        return (255, 60, 60)

def _draw_block(d, value_str, label, font_num, font_deg, font_lbl,
                num_cx, num_cy, lbl_cx, lbl_cy, color, lbl_color=LABEL_COLOR):
    bb = d.textbbox((0, 0), value_str, font=font_num)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    tx = num_cx - tw // 2 - bb[0]
    ty = num_cy - th // 2 - bb[1]
    d.text((tx, ty), value_str, font=font_num, fill=color)
    d.text((tx + tw + 2, ty), "°", font=font_deg, fill=color)

    lb = d.textbbox((0, 0), label, font=font_lbl)
    lw = lb[2] - lb[0]
    d.text((lbl_cx - lw // 2 - lb[0], lbl_cy), label, font=font_lbl, fill=lbl_color)

def make_image(cpu_temp, liquid_temp=None, gpu_temp=None):
    img = Image.new("RGB", (SIZE, SIZE), BG_FILL)
    d = ImageDraw.Draw(img)

    # 圆形背景
    d.ellipse([BG_MARGIN, BG_MARGIN, SIZE - BG_MARGIN, SIZE - BG_MARGIN],
              fill=CIRCLE_FILL, outline=CIRCLE_OUTLINE, width=4)

    # 弧形进度条（跟随 CPU 温度）
    cpu_color = temp_color(cpu_temp)
    sweep = int(ARC_SWEEP * min(cpu_temp / 100.0, 1.0))
    arc_box = [ARC_MARGIN, ARC_MARGIN, SIZE - ARC_MARGIN, SIZE - ARC_MARGIN]
    d.arc(arc_box, start=ARC_START, end=ARC_START + ARC_SWEEP,
          fill=ARC_BG_COLOR, width=ARC_WIDTH)
    if sweep > 0:
        d.arc(arc_box, start=ARC_START, end=ARC_START + sweep,
              fill=cpu_color, width=ARC_WIDTH)

    # "Linux" 标签
    lb = d.textbbox((0, 0), "Linux", font=_font_linux)
    lw = lb[2] - lb[0]
    d.text((LINUX_LBL_CX - lw // 2 - lb[0], LINUX_LBL_CY), "Linux", font=_font_linux, fill=(255, 255, 255))

    # 分隔线
    d.line([(DIVX, LINE_Y_TOP), (DIVX, LINE_Y_BOT)], fill=LINE_COLOR, width=2)
    d.line([(DIVX + 10, DIVY), (LINE_X_END, DIVY)], fill=LINE_COLOR, width=2)

    # 左侧：CPU
    _draw_block(d, f"{cpu_temp:.1f}", "CPU",
                _font_cpu, _font_cpu_deg, _font_cpu_lb,
                num_cx=CPU_NUM_CX, num_cy=CPU_NUM_CY,
                lbl_cx=CPU_LBL_CX, lbl_cy=CPU_LBL_CY,
                color=cpu_color, lbl_color=label_color(cpu_temp))

    # 右上：液温
    if liquid_temp is not None:
        _draw_block(d, f"{liquid_temp:.1f}", "LIQUID",
                    _font_sm, _font_sm_deg, _font_sm_lb,
                    num_cx=LIQ_NUM_CX, num_cy=LIQ_NUM_CY,
                    lbl_cx=LIQ_LBL_CX, lbl_cy=LIQ_LBL_CY,
                    color=temp_color(liquid_temp), lbl_color=label_color(liquid_temp))

    # 右下：GPU
    if gpu_temp is not None:
        _draw_block(d, f"{gpu_temp:.1f}", "GPU",
                    _font_sm, _font_sm_deg, _font_sm_lb,
                    num_cx=GPU_NUM_CX, num_cy=GPU_NUM_CY,
                    lbl_cx=GPU_LBL_CX, lbl_cy=GPU_LBL_CY,
                    color=temp_color(gpu_temp), lbl_color=label_color(gpu_temp))

    return img
