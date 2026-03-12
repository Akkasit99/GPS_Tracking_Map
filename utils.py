import pandas as pd
from PIL import Image, ImageTk, ImageDraw
import os
import sys
import math
from config import COLORS

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_car_icons():
    icons = {}
    try:
        car_path = resource_path("car.png")
        if os.path.exists(car_path):
            img = Image.open(car_path).resize((45, 45), Image.Resampling.LANCZOS)
            icons['run'] = ImageTk.PhotoImage(img)
        elif os.path.exists("car.png"):
            img = Image.open("car.png").resize((45, 45), Image.Resampling.LANCZOS)
            icons['run'] = ImageTk.PhotoImage(img)
        else:
            raise FileNotFoundError
    except:
        w, h = 44, 44 
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([8, 5, 36, 39], radius=6, fill=COLORS.get("success", "#28a745"), outline="white", width=2)
        icons['run'] = ImageTk.PhotoImage(img)

    img_idle = Image.new("RGBA", (30, 30), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img_idle)
    draw.ellipse([2, 2, 28, 28], fill=COLORS.get("warning", "#ffcc00"), outline="white", width=2)
    icons['idle'] = ImageTk.PhotoImage(img_idle)

    img_stop = Image.new("RGBA", (30, 30), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img_stop)
    draw.ellipse([2, 2, 28, 28], fill=COLORS.get("danger", "#dc3545"), outline="white", width=2)
    icons['stop'] = ImageTk.PhotoImage(img_stop)
    
    return icons

def process_gps_data(file_path):
    try:
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='cp874')

        cols = {c.lower().strip(): c for c in df.columns}
        
        col_lat = cols.get('lat') or cols.get('latitude') or cols.get('纬度')
        col_lon = cols.get('long') or cols.get('lon') or cols.get('lng') or cols.get('longitude') or cols.get('经度')
        col_time = cols.get('r-time') or cols.get('time') or cols.get('timestamp') or cols.get('设备时间')

        if not col_lat or not col_lon or not col_time:
            return None, "Missing Columns", None

        # [UPDATE] ให้ Pandas อ่านเวลาแบบยืดหยุ่น ป้องกันปัญหาวันและเดือนสลับกัน
        df[col_time] = pd.to_datetime(df[col_time].astype(str), format='mixed', errors='coerce')
        
        if df[col_time].isna().any():
            mask = df[col_time].isna()
            df.loc[mask, col_time] = pd.to_datetime(df.loc[mask, col_time], errors='coerce')

        df = df.dropna(subset=[col_time])
        
        # [NEW] กรองข้อมูลเวลาในอนาคตออก
        current_time = pd.Timestamp.now()
        future_mask = df[col_time] > current_time
        future_count = future_mask.sum()
        
        warning_msg = None
        if future_count > 0:
            df = df[~future_mask] 
            warning_msg = f"⚠️ ตรวจพบข้อมูลเวลาใน 'อนาคต' จำนวน {future_count} จุด\nระบบได้ทำการตัดข้อมูลส่วนนี้ออกเพื่อป้องกันการแสดงผลผิดพลาดแล้วครับ"

        df = df.sort_values(col_time)
        
        if df.empty: return None, "Empty Data", warning_msg
        
        df['date_str'] = df[col_time].dt.strftime('%Y-%m-%d')
        
        return df, None, warning_msg

    except Exception as e:
        return None, str(e), None

def create_circle_icon_marker():
    size = 12 
    img = Image.new("RGBA", (size+4, size+4), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([0, 0, size+3, size+3], fill="black")
    draw.ellipse([2, 2, size+1, size+1], fill="white")
    return ImageTk.PhotoImage(img)

def create_transparent_icon():
    img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    return ImageTk.PhotoImage(img)

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_total_distance(coords):
    total_dist = 0
    if len(coords) < 2: return 0
    for i in range(len(coords) - 1):
        total_dist += haversine_distance(coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1])
    return total_dist