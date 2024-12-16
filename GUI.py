from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import font as tkfont
from PIL import Image, ImageTk
from openpyxl import Workbook
from threading import Thread, Event
import cv2
import os
from roboflow import Roboflow
import pandas as pd
import datetime  # from datetime import datetime
import re
import numpy as np
import time

flag = False
flag_1 = 0
flag_2 = 0
directorio_global = ''
empty_array = np.zeros((100, 100), dtype=np.uint8)
img = Image.fromarray(empty_array)
cap = cv2.VideoCapture(0)
time_dur1, time_int1, time_dur2, time_int2, time_dur3, time_int3 = 0, 0, 0, 0, 0, 0


def sec_formatter(val, fact):
    '''Función para convertir el valor de tiempo a segundos
    val: int - Valor de tiempo
    fact: str - Unidad de tiempo
    return: int - Valor de tiempo en segundos'''
    new_val = 0
    if fact == 'segundos':
        new_val = val
    elif fact == 'minutos':
        new_val = val * 60
    elif fact == 'horas':
        new_val = val * 3600
    elif fact == 'dias':
        new_val = val * 86400
    return new_val


class ImageProcessor:
    def __init__(self, api_key, project_name, version_number, proximity_threshold):
        self.rf = Roboflow(api_key=api_key)
        self.project = self.rf.workspace().project(project_name)
        self.model = self.project.version(version_number).model
        self.proximity_threshold = proximity_threshold

    def is_near(self, pred1, pred2):
        return abs(pred1['x'] - pred2['x']) < self.proximity_threshold and abs(pred1['y'] - pred2['y']) < self.proximity_threshold

    def get_image_creation_datetime(self, image_path):
        creation_time = os.path.getctime(image_path)
        return datetime.datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')

    def filter_predictions(self, predictions):
        filtered_predictions = []
        for pred in predictions['predictions']:
            found = False
            for group in filtered_predictions:
                if self.is_near(pred, group[0]):
                    existing_classes = [p['class'] for p in group]
                    if pred['class'] == '2' and '7' in existing_classes:
                        group[0] = pred
                    elif pred['class'] == '7' and '2' in existing_classes:
                        group[0] = next(p for p in group if p['class'] == '2')
                    elif pred['confidence'] > group[0]['confidence']:
                        group[0] = pred
                    found = True
                    break
            if not found:
                filtered_predictions.append([pred])
        return [group[0] for group in filtered_predictions]

    def predict_image(self, image_path):
        predictions = self.model.predict(
            image_path, confidence=8, overlap=50).json()
        filtered_predictions = self.filter_predictions(predictions)
        sorted_predictions = sorted(filtered_predictions, key=lambda p: p['x'])
        classes = [pred['class'] for pred in sorted_predictions]
        if len(classes) > 2:
            result_string = ''.join(classes[:-2]) + '.' + ''.join(classes[-2:])
        else:
            result_string = '.'.join(classes)
        return result_string

    def process_images(self, image_folder):
        image_files = [f for f in os.listdir(
            image_folder) if f.endswith(('.png', '.jpg', '.jpeg'))]
        results = []

        for image_file in image_files:
            image_path = os.path.join(image_folder, image_file)
            creation_datetime = self.get_image_creation_datetime(image_path)
            result_string = self.predict_image(image_path)
            results.append((image_file, creation_datetime, result_string))

        # Ordenar los resultados por el nombre del archivo de imagen numéricamente
        results.sort(key=lambda x: int(re.findall(r'\d+', x[0])[0]))

        # Crear el archivo Excel y agregar los datos ordenados
        excel_filename = os.path.join(image_folder, "predictions.xlsx")
        wb = Workbook()
        ws = wb.active
        ws.title = "Predictions"

        for result in results:
            ws.append(result)

        wb.save(excel_filename)
        # print(f"Los resultados han sido guardados en {excel_filename}")


class ConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.config(bg="lightblue")
        self.root.title("Configuración")
        self.root.geometry("700x400")

        alts_plural = ["segundos", "minutos", "horas", "días"]

        global value_c1, value_c2, value_c3, value_c4, value_c5, value_c6
        global value_b1, value_b2, value_b3, value_b4, value_b5, value_b6

        value_c1.set("Opción")
        value_c2.set("Opción")
        value_c3.set("Opción")
        value_c4.set("Opción")
        value_c5.set("Opción")
        value_c6.set("Opción")

        '''Fila 1'''
        row_tracker = 0
        self.label_save = Label(
            self.root, text="Elija la carpeta donde se guardaran las imágenes", bg="lightblue", font=bold_font)
        self.label_save.grid(column=0, row=row_tracker, columnspan=3)

        '''Fila 2'''
        row_tracker += 1
        self.label_file = Label(
            self.root, text="Directorio:", bg="lightblue", font=bold_font)
        self.label_file.grid(column=0, row=row_tracker, pady=10)
        self.label_file_ch = Label(
            self.root, text="No seleccionado", bg="lightblue", font=italic_font)
        self.label_file_ch.grid(
            column=1, row=row_tracker, pady=10, columnspan=2)
        self.btn_explorar = Button(self.root, text="Explorar",
                                   command=self.seleccionar_directorio, font=normal_font)
        self.btn_explorar.grid(column=3, row=row_tracker, pady=10)

        '''Fila 3'''
        row_tracker += 1
        self.label_a1 = Label(
            self.root, text="Los primeros", bg="lightblue", font=bold_font)
        self.label_a1.grid(column=0, row=row_tracker, pady=10)
        self.entry_b1 = Entry(
            self.root, textvariable=value_b1, width=5, font=normal_font)
        self.entry_b1.grid(column=1, row=row_tracker, pady=10)
        self.menu_c1 = OptionMenu(self.root, value_c1, *alts_plural[:-1])
        self.menu_c1.grid(column=2, row=row_tracker, pady=10)
        self.label_a2 = Label(
            self.root, text="tomará fotos cada ", bg="lightblue", font=bold_font)
        self.label_a2.grid(column=3, row=row_tracker, pady=10)
        self.entry_b2 = Entry(
            self.root, textvariable=value_b2, width=5, font=normal_font)
        self.entry_b2.grid(column=4, row=row_tracker, pady=10)
        self.menu_c2 = OptionMenu(self.root, value_c2, *alts_plural[:-1])
        self.menu_c2.grid(column=5, row=row_tracker, pady=10)

        '''Fila 4'''
        row_tracker += 1
        self.label_a3 = Label(
            self.root, text="Después, hasta llegar a ", bg="lightblue", font=bold_font)
        self.label_a3.grid(column=0, row=row_tracker, pady=10)
        self.entry_b3 = Entry(
            self.root, textvariable=value_b3, width=5, font=normal_font)
        self.entry_b3.grid(column=1, row=row_tracker, pady=10)
        self.menu_c3 = OptionMenu(self.root, value_c3, *alts_plural)
        self.menu_c3.grid(column=2, row=row_tracker, pady=10)
        self.label_a4 = Label(
            self.root, text="de duración, tomará fotos cada ", bg="lightblue", font=bold_font)
        self.label_a4.grid(column=3, row=row_tracker, pady=10)
        self.entry_b4 = Entry(
            self.root, textvariable=value_b4, width=5, font=normal_font)
        self.entry_b4.grid(column=4, row=row_tracker, pady=10)
        self.menu_c4 = OptionMenu(self.root, value_c4, *alts_plural[:-1])
        self.menu_c4.grid(column=5, row=row_tracker, pady=10)

        '''Fila 5'''
        row_tracker += 1
        self.label_a5 = Label(
            self.root, text="Finalmente, tomará fotos cada ", bg="lightblue", font=bold_font)
        self.label_a5.grid(column=0, row=row_tracker, pady=10)
        self.entry_b5 = Entry(
            self.root, textvariable=value_b5, width=5, font=normal_font)
        self.entry_b5.grid(column=1, row=row_tracker, pady=10)
        self.menu_c5 = OptionMenu(self.root, value_c5, *alts_plural[:-1])
        self.menu_c5.grid(column=2, row=row_tracker, pady=10)

        '''Fila 6'''
        row_tracker += 1
        self.label_a6 = Label(
            self.root, text="Total duración del experimento: ", bg="lightblue", font=bold_font)
        self.label_a6.grid(column=0, row=row_tracker, pady=10)
        self.entry_b6 = Entry(
            self.root, textvariable=value_b6, width=5, font=normal_font)
        self.entry_b6.grid(column=1, row=row_tracker, pady=10)
        self.menu_c6 = OptionMenu(self.root, value_c6, *alts_plural)
        self.menu_c6.grid(column=2, row=row_tracker, pady=10)

        '''Fila 7'''
        row_tracker += 1
        self.label_warn = Label(
            self.root, text="", bg="lightblue")
        self.label_warn.grid(column=0, row=row_tracker)

        btn_volver = Button(
            self.root, text="Volver a la Ventana Principal", command=self.b4_u_k1ll_me)
        btn_volver.grid(column=2, row=row_tracker, ipadx=10, columnspan=2)

        '''Fila 8'''
        row_tracker += 1
        self.label_value = Label(self.root, text="", bg="lightblue", height=4)
        self.label_value.grid(column=0, row=row_tracker, columnspan=3)

    def seleccionar_directorio(self):
        directorio = filedialog.askdirectory(title="Seleccionar carpeta")
        global directorio_global
        tmp_dir = ""
        if directorio:
            for char in directorio:
                if char == '/':
                    tmp_dir = tmp_dir + '//'
                else:
                    tmp_dir = tmp_dir + char
            self.root.geometry("")
            self.label_file_ch.config(text=f"Carpeta seleccionada: {tmp_dir}")
            # print(f"Directorio seleccionado: {tmp_dir}")
            directorio_global = tmp_dir
        elif directorio == "":
            self.label_file_ch.config(text="Seleccione una carpeta.")
            # print("Seleccione una carpeta.")

    def update_label(self, value):
        value = float(value)
        self.label_value.config(text=f"Slider Value: {value:.2f}")

    def go_back(self):
        self.root.destroy()

    def val_checker(self, value):
        self.root.geometry("")
        try:
            value = int(value)
        except ValueError:
            self.label_warn.config(
                text="Por favor, ingrese un valor válido en cada espacio. Porque uno no es un número", font=bold_font)
            return True
        if value < 1 or value > 59:
            self.label_warn.config(
                text="Por favor, ingrese un valor válido en cada espacio. Porque uno no está en el rango", font=bold_font)
            return True
        else:
            return False

    def b4_u_k1ll_me(self):
        val1 = sec_formatter(int(self.entry_b1.get()), value_c1.get())
        val2 = sec_formatter(int(self.entry_b2.get()), value_c2.get())
        val3 = sec_formatter(int(self.entry_b3.get()), value_c3.get())
        val4 = sec_formatter(int(self.entry_b4.get()), value_c4.get())
        val5 = sec_formatter(int(self.entry_b5.get()), value_c5.get())
        val6 = sec_formatter(int(self.entry_b6.get()), value_c6.get())
        # print('Value 1:', val1, 'Value 2:', val2, 'Value 3:', val3,
        # 'Value 4:', val4, 'Value 5:', val5, 'Value 6:', val6)
        if self.val_checker(self.entry_b1.get()) or self.val_checker(self.entry_b2.get()) or self.val_checker(self.entry_b3.get()) or self.val_checker(self.entry_b4.get()) or self.val_checker(self.entry_b5.get()) or self.val_checker(self.entry_b6.get()):
            return 0
        else:
            if val2 >= val1 or val4 >= val3 or val5 >= val6:
                self.label_warn.config(
                    text="Un valor de intervalo es mayor o igual al valor de duración", font=bold_font)
                return 0
            else:
                self.label_warn.config(text="", bg="lightblue", font=bold_font)
                self.root.destroy()


class InitApp:
    def __init__(self):
        global directorio_global, value_c1, value_c2, value_c3, value_c4, value_c5, value_c6
        global value_b1, value_b2, value_b3, value_b4, value_b5, value_b6
        api_key = "6iUlqDVylBlNgJyO6AaW"

        project_name = "dial-comparator-detection"
        version_number = 1
        proximity_threshold = 38

        processor = ImageProcessor(
            api_key, project_name, version_number, proximity_threshold)

        self.start_time = time.time()
        self.current_time = time.time()
        self.second = [0, int(self.current_time - self.start_time)]
        self.sec_counter = 0
        self.fotonombre = 0

        time_dur1 = sec_formatter(int(value_b1.get()), value_c1.get())
        time_int1 = sec_formatter(int(value_b2.get()), value_c2.get())
        time_dur2 = sec_formatter(int(value_b3.get()), value_c3.get())
        time_int2 = sec_formatter(int(value_b4.get()), value_c4.get())
        time_int3 = sec_formatter(int(value_b5.get()), value_c5.get())
        time_dur3 = sec_formatter(int(value_b6.get()), value_c6.get())

        self.astrolau(time_dur1, time_int1)
        self.astrolau(time_dur2, time_int2)
        self.astrolau(time_dur3, time_int3)

        if directorio_global == '':
            directorio_global = ".//"
        processor.process_images(directorio_global)

    def astrolau(self, the_time, the_interval):
        sec_counter = 0
        while self.second[1] != the_time:
            self.current_time = time.time()
            self.second = [self.second[1], int(
                self.current_time - self.start_time)]
            if self.second[1] != self.second[0]:
                sec_counter += 1
            if sec_counter == the_interval:
                self.fotonombre += 1
                if directorio_global:
                    img.save(str(directorio_global + "//foto_" +
                             str(self.fotonombre) + ".png"))
                else:
                    img.save("foto_" + str(self.fotonombre) + ".png")
                sec_counter = 0


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.config(bg="lightblue")
        self.root.title("Encender Cámara")
        self.root.geometry("800x600")

        self.pixel = PhotoImage(width=1, height=1)

        # Crear un botón para encender la cámara
        self.btn_cam = Button(
            self.root, text="Encender Cámara", command=self.toggle)
        self.btn_cam.grid(column=2, row=1, ipadx=20)
        # Crear un botón para configurar el entorno
        self.btn_config = Button(
            self.root, text="Configuración", command=lambda: (self.crear_ventana(1)))
        self.btn_config.grid(column=2, row=2, ipadx=20)
        # Crear un botón para iniciar la toma de datos
        self.btn1 = Button(
            self.root, text="INICIO", image=self.pixel, height=150, width=70, compound="c", command=lambda: (self.crear_ventana(2)))
        self.btn1.grid(column=2, row=3, ipadx=25)
        # Cerrar la ventana principal
        self.btn_kill = Button(root, text="Salir", command=root.destroy)
        self.btn_kill.grid(column=2, row=4, ipadx=20)
        # Crear un label para mostrar el video
        self.img_empty = PhotoImage()
        self.label = Label(root)
        self.label.config(bg="lightgreen", image=self.img_empty, compound=CENTER, width=int(
            cap.get(cv2.CAP_PROP_FRAME_WIDTH)), height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        self.label.grid(column=1, row=1, rowspan=3)
        cap.release()

        # Manejar el evento de cerrar la ventana
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        '''Función para cerrar la cámara y la ventana'''
        if flag:
            if cap.isOpened():
                cap.release()
        self.root.destroy()

    def toggle(self):
        global flag
        flag = not flag
        self.toggle_camera()

    def show_frame(self):
        '''Función para mostrar el video en el label'''
        _, self.frame = cap.read()
        global img
        if self.frame is not None:
            # self.frame = cv2.flip(self.frame, 1)
            self.cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
            img = Image.fromarray(self.cv2image)
            self.imgtk = ImageTk.PhotoImage(image=img)
            self.label.imgtk = self.imgtk
            self.label.configure(image=self.imgtk, bd=8, padx=30, pady=30)
            self.label.after(10, self.show_frame)

    def toggle_camera(self):
        '''Función para manipular la cámara'''
        global flag
        global flag_1

        if flag == True:
            self.btn_cam.config(text="Apagar Cámara")
            global cap
            cap = cv2.VideoCapture(0)
            self.show_frame()
            if flag_1 < 1:
                flag_1 = flag_1+1
        else:
            self.btn_cam.config(text="Encender Cámara")
            if flag_1 >= 1:
                if cap.isOpened():
                    cap.release()
                    self.label.config(image=self.img_empty)

    def crear_ventana(self, window_type):
        '''Create a new instance of Tkinter window'''
        if window_type == 1:
            config_app = Toplevel(self.root)
            ConfigApp(config_app)
        elif window_type == 2:
            self.loop_thread = Thread(target=lambda: InitApp())
            self.loop_thread.start()


# Crear la ventana principal
root = Tk()
'''Fuentes'''
font_size = 10
bold_font = tkfont.Font(family="Helvetica", size=font_size, weight="bold")
italic_font = tkfont.Font(family="Helvetica", size=font_size, slant="italic")
normal_font = tkfont.Font(family="Helvetica", size=font_size)
'''Variables para cada menú'''
value_c1, value_c2, value_c3, value_c4, value_c5, value_c6 = StringVar(
), StringVar(), StringVar(), StringVar(), StringVar(), StringVar()

value_b1, value_b2, value_b3, value_b4, value_b5, value_b6 = StringVar(
), StringVar(), StringVar(), StringVar(), StringVar(), StringVar()

# Create an instance of MainApp
main_app = MainApp(root)

# Ejecutar la aplicación
root.mainloop()
