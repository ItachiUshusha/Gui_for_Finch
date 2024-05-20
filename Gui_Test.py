# добавить кнопку отчистки графика а вместе с ним и отчистку текста в файле
# добавить более красивую запись в файл

import sys
import math
import time
import threading

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QPushButton, QLineEdit, QFileDialog
from PyQt6.QtGui import QFont
import pyqtgraph as pg
from BirdBrain import Finch
from time import sleep
import csv


# Подкласс QMainWindow для настройки главного окна приложения
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(50, 50, 1200, 600)
        self.setFixedSize(1200, 600)

        # надпись о пделючении/не подключении робота
        self.label6 = QLabel('', self)
        self.label6.setGeometry(800, 0, 200, 30)

        # обработчик ошибок если робот не подключен.
        try:
            self.bird = Finch()
            self.label6.setText('Успешное подключение finchrobot.')
        except:
            self.label6.setText('Finchrobot не подключен.')

        self.setStyleSheet("background-color: lightgrey;")

        # график
        self.x = 0
        self.y = 0
        self.k = 0
        self.result = []

        # скорость робота
        self.V_l = 1
        self.V_r = 1
        self.dV = 1
        self.V = 1
        self.t = 20
        # self.degree = 0

        # состояние кнопки
        self.is_button_pressed = False

        # проверка на то должен ли обновляться график
        self.upd = True

        # название окна приложения
        self.setWindowTitle("Finch speed")

        # верхняя надпись
        self.label2 = QLabel("Скорость робота", self)
        self.label2.setGeometry(200, 10, 200, 50)

        # нижняя надпись отображающая скорость робота в усл. единицах
        self.label = QLabel("Нажмите клавишу (W, A, S, D)", self)
        self.label.setGeometry(60, 100, 400, 50)
        self.label.setAlignment(Qt.AlignmentFlag.AlignHCenter)  # Установка выравнивания по центру

        # настройка шрифта
        self.font = QFont()
        self.font.setPointSize(12)  # Установим желаемый размер шрифта
        self.label.setFont(self.font)
        self.label2.setFont(self.font)

        # кнопка остановки графика
        self.button = QPushButton("Запустить график", self)
        self.button.setGeometry(350, 190, 120, 40)
        self.button.clicked.connect(self.keyIsPressed)
        self.buttton_is_pressed = True

        # параметры кнопки записи в файл
        self.button2 = QPushButton("Записать в файл", self)
        self.button2.setGeometry(350, 140, 120, 40)
        self.button2.clicked.connect(self.write_file)

        # внешний вид графика (линии, надписи осей и т.д.)
        self.plot_graph = pg.PlotWidget(self)
        pen = pg.mkPen(color=(46, 188, 100), width=2)
        styles = {"color": "black", "font-size": "18px"}
        self.plot_graph.setLabel("left", "", **styles)
        self.plot_graph.setLabel("bottom", "", **styles)
        self.plot_graph.setTitle("Finch robot", color=(0, 0, 0))
        self.plot_graph.setBackground("w")

        # список значений x и y координат
        self.xt = []
        self.yt = []

        # расположение гравика на интерфейсе
        self.plot_graph.setGeometry(530, 25, 650, 550)

        # отрисовка графика
        self.line = self.plot_graph.plot(self.xt, self.yt, pen=pen)

        # установка таймера для графика
        self.label3 = QLabel("Введите с каким шагом будет отрисовываться график", self)
        self.label3.setGeometry(20, 150, 300, 80)

        # строка ввода пользователем шага
        self.input = QLineEdit(self)
        self.input.setReadOnly(True)
        self.input.setGeometry(20, 200, 300, 30)
        self.input.mousePressEvent = self.MousePressEvent
        self.input.textChanged.connect(self.printInp)
        self.count = 0

        self.label4 = QLabel("Введите значение времени для графика", self)
        self.label4.setGeometry(20, 234, 300, 30)

        # строка для ввода времени пользователем
        self.input_t = QLineEdit(self)
        self.input_t.setReadOnly(True)
        self.input_t.setGeometry(20, 260, 300, 30)
        self.input_t.mousePressEvent = self.Press_t
        self.input_t.textChanged.connect(self.timeInp)
        self.count_t = 0

        self.input_v = QLineEdit(self)
        self.input_v.setReadOnly(True)
        self.input_v.setGeometry(20, 380, 300, 30)
        self.input_v.mousePressEvent = self.Press_v
        self.input_v.textChanged.connect(self.speedInp)
        self.count_v = 0
        self.v = []

        # установка таймера с каким шагом будет отрисовываться график
        self.timer = QTimer()
        self.timer.setInterval(65)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

        self.label5 = QLabel("Счетчик цикла: ", self)
        self.label5.setGeometry(20, 290, 200, 30)
        self.count_s = 0

        self.button_v = QPushButton("Отрисовать данные", self)
        self.button_v.setGeometry(350, 375, 120, 40)
        self.button_v.clicked.connect(self.but_v)
        self.uk = True

        self.button_reset = QPushButton("Отчистить значения скорости", self)
        self.button_reset.setGeometry(350, 240, 170, 40)
        self.button_reset.clicked.connect(self.but_res)

        self.but_file = QPushButton("Выбрать файл", self)
        self.but_file.setGeometry(350, 420, 170, 40)
        self.but_file.clicked.connect(self.open_file)

    # функция обновляющая значения графика
    def update_plot(self):
        if self.upd and not self.uk:
            self.xt.append(self.coord_x()[0])
            self.yt.append(self.coord_x()[1])
            self.result.append(self.coord_x())
            self.count_s += 1
            self.label5.setText(f"Счетчик цикла: {self.count_s}")
            self.line.setData(self.xt, self.yt)
            x_max = max(self.xt)
            y_max = max(self.yt)
            x_min = min(self.xt)
            y_min = min(self.yt)
            if (x_max > y_max) and (x_min < y_min):
                self.plot_graph.setXRange(x_min, x_max)
                self.plot_graph.setYRange(x_min, x_max)
            elif (x_max < y_max) and (x_min > y_min):
                self.plot_graph.setXRange(y_min, y_max)
                self.plot_graph.setYRange(y_min, y_max)
            elif (x_max < y_max) and (x_min < y_min):
                self.plot_graph.setXRange(x_min, y_max)
                self.plot_graph.setYRange(x_min, y_max)
            elif (x_max > y_max) and (x_min > y_min):
                self.plot_graph.setXRange(y_min, x_max)
                self.plot_graph.setYRange(y_min, x_max)
            return self.result
        else:
            self.upd = True
            return self.result

    def but_v(self):
        self.uk = True
        self.button.setText('Продолжить')
        self.buttton_is_pressed = True
        self.tI = 0
        if len(self.v) == 3 and self.uk:
            self.V_l = int(self.v[0])
            self.V_r = int(self.v[1])
            tI = int(self.v[2])
            timeout = time.time() + tI
            while True:
                print(1)
                self.xt.append(self.coord_x()[0])
                self.yt.append(self.coord_x()[1])
                self.result.append(self.coord_x())
                self.count_s += 1
                self.label5.setText(f"Счетчик цикла: {self.count_s}")
                self.line.setData(self.xt, self.yt)
                x_max = max(self.xt)
                y_max = max(self.yt)
                x_min = min(self.xt)
                y_min = min(self.yt)
                if (x_max > y_max) and (x_min < y_min):
                    self.plot_graph.setXRange(x_min, x_max)
                    self.plot_graph.setYRange(x_min, x_max)
                elif (x_max < y_max) and (x_min > y_min):
                    self.plot_graph.setXRange(y_min, y_max)
                    self.plot_graph.setYRange(y_min, y_max)
                elif (x_max < y_max) and (x_min < y_min):
                    self.plot_graph.setXRange(x_min, y_max)
                    self.plot_graph.setYRange(x_min, y_max)
                elif (x_max > y_max) and (x_min > y_min):
                    self.plot_graph.setXRange(y_min, x_max)
                    self.plot_graph.setYRange(y_min, x_max)
                try:
                    self.bird.setMotors(self.V_l, self.V_r)
                except:
                    pass
                if time.time() > timeout:
                    self.bird.stopAll()
                    break
                sleep(0.065)

    def but_res(self):
        self.V_l = 0
        self.V_r = 0
        self.label.setText(f"[{self.V_l}]====================[{self.V_r}]")
        try:
            self.bird.setMotors(self.V_l, self.V_r)
        except:
            pass

    # функция записи в файл данных при нажатии кнопки
    def write_file(self):
        self.upd = False
        with open("data.csv", mode="w", encoding='utf-8') as w_file:
            file_writer = csv.writer(w_file, delimiter=",", lineterminator="\r")
            file_writer.writerow(["x", "y", "V_l", "V_r", "k"])
            for i in range(len(self.result)):
                file_writer.writerow([self.result[i][0], self.result[i][1], self.result[i][2],
                                      self.result[i][3], self.result[i][4]])

    # функция устанавливающая пользовательское значение шага
    def printInp(self, d):
        self.timer.setInterval(int(d))
        if self.count != 1:
            self.count_s += 1
        self.label5.setText(f"Счетчик цикла: {self.count_s}")
        return (int(d))

    def timeInp(self, t):
        self.t = float(t)

    def speedInp(self, v):
        self.v = v.split(", ")

    # функция включения и отключения строки ввода
    def MousePressEvent(self, event):
        self.count += 1
        if event.button() == Qt.MouseButton.LeftButton and self.count == 1:
            self.input.setReadOnly(False)
            super().mousePressEvent(event)
        elif event.button() == Qt.MouseButton.LeftButton and self.count == 2:
            self.input.setReadOnly(True)
            super().mousePressEvent(event)
            self.count = 0

    def Press_t(self, event):
        self.count_t += 1
        if event.button() == Qt.MouseButton.LeftButton and self.count_t == 1:
            self.input_t.setReadOnly(False)
            super().mousePressEvent(event)
        elif event.button() == Qt.MouseButton.LeftButton and self.count_t == 2:
            self.input_t.setReadOnly(True)
            super().mousePressEvent(event)
            self.count_t = 0

    def Press_v(self, event):
        self.count_v += 1
        if event.button() == Qt.MouseButton.LeftButton and self.count_v == 1:
            self.input_v.setReadOnly(False)
            super().mousePressEvent(event)
        elif event.button() == Qt.MouseButton.LeftButton and self.count_v == 2:
            self.input_v.setReadOnly(True)
            super().mousePressEvent(event)
            self.count_v = 0

    # функция считывания нажатой клавиши и установки в соответствии с ней скорости
    def keyPressEvent(self, event):
        # Обработка нажатия клавиши
        key = event.key()
        if key == Qt.Key.Key_W:
            result = self.set_move_up()
            if not self.buttton_is_pressed:
                try:
                    self.bird.setMotors(result[0], result[1])
                except:
                    pass
            self.label.setText(f"[{result[0]}]====================[{result[1]}]")
        elif key == Qt.Key.Key_S:
            result = self.set_move_down()
            if not self.buttton_is_pressed:
                try:
                    self.bird.setMotors(result[0], result[1])
                except:
                    pass
            self.label.setText(f"[{result[0]}]====================[{result[1]}]")
        elif key == Qt.Key.Key_D:
            result = self.set_move_right()
            if not self.buttton_is_pressed:
                try:
                    self.bird.setMotors(result[0], result[1])
                except:
                    pass
            self.label.setText(f"[{result[0]}]====================[{result[1]}]")
        elif key == Qt.Key.Key_A:
            result = self.set_move_left()
            if not self.buttton_is_pressed:
                try:
                    self.bird.setMotors(result[0], result[1])
                except:
                    pass
            self.label.setText(f"[{result[0]}]====================[{result[1]}]")

    # функция которая связана с кнопкой остановки графика
    def keyIsPressed(self):
        if not (self.buttton_is_pressed) and self.uk:
            self.timer.stop()
            try:
                self.bird.stop()
            except:
                pass
            self.button.setText('Продолжить')
            self.buttton_is_pressed = True
        elif not (self.buttton_is_pressed):
            self.timer.stop()
            try:
                self.bird.stop()
            except:
                pass
            self.button.setText('Продолжить')
            self.buttton_is_pressed = True
        else:
            self.timer.start()
            try:
                self.bird.setMotors(self.V_l, self.V_r)
            except:
                pass
            self.button.setText('Остановить график')
            self.buttton_is_pressed = False
            self.uk = False

    # функции вычисляющие скорость робота
    def set_move_down(self):
        self.V = (self.V_l + self.V_r) / 2
        Vn = self.V - self.dV

        if self.V_r == 0 and self.V_l == 0:
            V_rn = (2 * Vn) / (1 + 1)
            V_ln = V_rn * 1
            self.V_r = round(V_rn)
            self.V_l = round(V_ln)
            return (self.V_l, self.V_r)
        elif self.V_r + self.V_l == 0:
            return (self.V_l, self.V_r)
        else:
            if self.V_r > 0.0001:
                V_rn = (2 * Vn) / (1 + (self.V_l / self.V_r))
                V_ln = V_rn * (self.V_l / self.V_r)
                self.V_r = round(V_rn)
                self.V_l = round(V_ln)
                return (self.V_l, self.V_r, 0)
            elif self.V_r <= 0.0001 and self.V_r >= 0:
                self.V_r = 0.0001
                V_rn = (2 * Vn) / (1 + (self.V_l / self.V_r))
                V_ln = V_rn * (self.V_l / self.V_r)
                self.V_r = round(V_rn)
                self.V_l = round(V_ln)
                return (self.V_l, self.V_r, 0)
            else:
                V_rn = (2 * Vn) / (1 + (self.V_l / self.V_r))
                V_ln = V_rn * (self.V_l / self.V_r)
                self.V_r = V_rn
                self.V_l = V_ln
                return (round(self.V_l, 0), round(self.V_r, 0))

    def set_move_up(self):
        self.V = (self.V_l + self.V_r) / 2
        Vn = self.V + self.dV

        if self.V_r == 0 and self.V_l == 0:
            V_rn = (2 * Vn) / (1 + 1)
            V_ln = V_rn * 1
            self.V_r = round(V_rn)
            self.V_l = round(V_ln)
            return (self.V_l, self.V_r)
        elif self.V_r + self.V_l == 0:
            return (self.V_l, self.V_r)
        else:
            if self.V_r >= 0.0001:
                V_rn = (2 * Vn) / (1 + (self.V_l / self.V_r))
                V_ln = V_rn * (self.V_l / self.V_r)
                self.V_r = round(V_rn)
                self.V_l = round(V_ln)
                return (self.V_l, self.V_r)
            else:
                self.V_r = 0.0001
                V_rn = (2 * Vn) / (1 + (self.V_l / self.V_r))
                V_ln = V_rn * (self.V_l / self.V_r)
                self.V_r = round(V_rn)
                self.V_l = round(V_ln)
                return (self.V_l, self.V_r)

    def set_move_right(self):
        if self.V_r != 0 and self.V_l != 0:
            V_rn = self.V_r - self.dV
            V_ln = self.V_l + self.dV
            self.V_r = round(V_rn)
            self.V_l = round(V_ln)
            return (self.V_l, self.V_r)
        else:
            return (self.V_l, self.V_r)

    def set_move_left(self):
        if self.V_r != 0 and self.V_l != 0:
            V_rn = self.V_r + self.dV
            V_ln = self.V_l - self.dV
            self.V_r = round(V_rn)
            self.V_l = round(V_ln)
            return (self.V_l, self.V_r)
        else:
            return (self.V_l, self.V_r)

    # функция вычисляющая координаты x, y, а также среднюю скорость и угловую скорость робота
    def coord_x(self):
        d = 10.2  # в сантиметрах
        V = (self.V_r * 0.385 + self.V_l * 0.385) / 2
        if self.V_l == self.V_r:
            l = 9999999999999999999
        else:
            l = (self.V_l * 0.385 * d) / (self.V_l * 0.385 - self.V_r * 0.385)
        w = V / (l - (d / 2))
        self.k = self.k + (w * (1/self.t))
        self.x = (self.x + V * math.sin(self.k))
        self.y = (self.y + V * math.cos(self.k))
        return (round(self.x / self.t, 2) , round(self.y / self.t, 2) , round(self.V_r * 0.385, 2), round(self.V_l * 0.385, 2), self.k)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Text Files (*.txt)")
        if file_path:
            self.read_coordinates(file_path)
            try:
                self.degree = self.bird.getCompass()
            except:
                pass

    def getdist(self, x, y, x_prev, y_prev):
        return (math.sqrt((x - x_prev) * (x - x_prev) + (y - y_prev) * (y - y_prev)))

    def getscal(self, x_next, y_next, x, y, x_prev, y_prev):
        return ((x - x_prev) * (x_next - x) + (y - y_prev) * (y_next - y))

    def getAngle(self, x_next, y_next, x, y, x_prev, y_prev):
        return (math.asin(((x - x_prev) * (y_next - y) - (y - y_prev) * (x_next - x)) / (
                    self.getdist(x, y, x_prev, y_prev) * self.getdist(x_next, y_next, x, y))) * 180) / math.pi

    def read_coordinates(self, file_path):
        with open(file_path, "r", encoding='utf-8') as file:
            mass = []
            for line in file:
                mass.append((line.strip()).split(','))
            x = 0
            y = 0
            x_next = 0
            y_next = 0
            file.close()
            if (mass[0][0] == "С остановками"):
                for i in range(1, len(mass)):
                    x_prev = x
                    y_prev = y
                    x = x_next
                    y = y_next
                    x_next = float(mass[i][0])
                    y_next = float(mass[i][1])
                    if (i <= 2):
                        try:
                            self.bird.setMove("F", self.getdist(x_next, y_next, x, y), 20)
                            print(x, y)
                        except:
                            pass
                    elif self.getscal(x_next, y_next, x, y, x_prev, y_prev) >= 0:
                        deg = self.getAngle(x_next, y_next, x, y, x_prev, y_prev)
                        print(self.getscal(x_next, y_next, x, y, x_prev, y_prev))
                    else:
                        deg = 180 - self.getAngle(x_next, y_next, x, y, x_prev, y_prev)
                        print(self.getscal(x_next, y_next, x, y, x_prev, y_prev))
                    try:
                        self.bird.setTurn("L", round(deg), 20)
                        self.bird.setMove("F", self.getdist(x_next, y_next, x, y), 20)
                        sleep(0.5)
                    except:
                        pass

                    self.xt.append(x_next)
                    self.yt.append(y_next)
                    # self.result.append([x, y, 7.7, 7.7, ])
                    self.count_s += 1
                    self.label5.setText(f"Счетчик цикла: {self.count_s}")
                    self.line.setData(self.xt, self.yt)
                    x_max = max(self.xt)
                    y_max = max(self.yt)
                    x_min = min(self.xt)
                    y_min = min(self.yt)
                    if (x_max > y_max) and (x_min < y_min):
                        self.plot_graph.setXRange(x_min, x_max)
                        self.plot_graph.setYRange(x_min, x_max)
                    elif (x_max < y_max) and (x_min > y_min):
                        self.plot_graph.setXRange(y_min, y_max)
                        self.plot_graph.setYRange(y_min, y_max)
                    elif (x_max < y_max) and (x_min < y_min):
                        self.plot_graph.setXRange(x_min, y_max)
                        self.plot_graph.setYRange(x_min, y_max)
                    elif (x_max > y_max) and (x_min > y_min):
                        self.plot_graph.setXRange(y_min, x_max)
                        self.plot_graph.setYRange(y_min, x_max)
                # return self.result
            elif (mass[0][0] == "Без остановок с фикс. скоростью"):
                print("ОК")
                del_x, del_y = 0, 0
                for i in range(2, len(mass)):
                    x_r = self.coord_x()[0]
                    y_r = self.coord_x()[1]
                    x_prev = x
                    y_prev = y
                    x = y_r
                    y = x_r
                    x_next = float(mass[i][0])
                    y_next = float(mass[i][1])
                    self.V_l = 20
                    self.V_r = 20
                    while (self.getdist(x_next + del_x, y_next + del_y, x_r, y_r) >= 1):
                        sleep(1/self.t)
                        x_r = self.coord_x()[0]
                        y_r = self.coord_x()[1]
                        print("x_r:", x_r, "| y_r:", y_r)
                        print("dist", self.getdist(x_next + del_x, y_next + del_y, x_r, y_r))
                        try:
                            self.bird.setMotors(self.V_l, self.V_r)
                        except:
                            pass
                    if self.getscal(x_next, y_next, x, y, x_prev, y_prev) >= 0:
                        deg = self.getAngle(x_next, y_next, x, y, x_prev, y_prev)
                    else:
                        deg = (180 - self.getAngle(x_next, y_next, x, y, x_prev, y_prev))
                    deg_r = 0
                    print("deg", deg)
                    while abs(abs(deg_r) - abs(deg)) >= 3:
                        sleep(1/self.t)
                        x_r = self.coord_x()[0]
                        y_r = self.coord_x()[1]
                        if self.getscal(x_next, y_next, x, y, x_prev, y_prev) >= 0:
                            deg_r = self.getAngle(x_next, y_next, x_r, y_r, x_prev, y_prev)
                            if deg_r >= 1:
                                self.V_l = 40
                                self.V_r = 20
                                try:
                                    self.bird.setMotors(self.V_l, self.V_r)
                                    deg_r = (self.getAngle(x_next, y_next, x_r, y_r, x_prev, y_prev))
                                except:
                                    pass
                            elif deg_r <= -1:
                                self.V_l = 20
                                self.V_r = 40
                                try:
                                    self.bird.setMotors(self.V_l, self.V_r)
                                    deg_r = self.getAngle(x_next, y_next, x_r, y_r, x_prev, y_prev)
                                except:
                                    pass
                        else:
                            deg_r = (180 - self.getAngle(x_next, y_next, x_r, y_r, x_prev, y_prev))
                            if deg_r >= 1:
                                self.V_l = 40
                                self.V_r = 20
                                try:
                                    self.bird.setMotors(self.V_l, self.V_r)
                                    deg_r = (180 - self.getAngle(x_next, y_next, x_r, y_r, x_prev, y_prev))
                                except:
                                    pass
                            elif deg_r <= -1:
                                self.V_l = 20
                                self.V_r = 40
                                try:
                                    self.bird.setMotors(self.V_l, self.V_r)
                                    deg_r = 180 - self.getAngle(x_next, y_next, x_r, y_r, x_prev, y_prev)
                                except:
                                    pass
                        print(deg_r)
                        print("x_r", x_r, "| y_r", y_r)
                    del_x = x_r-x_next
                    del_y = y_r-y_next
                    print('del_x', del_x, "| del_y", del_y)

                    try:
                        self.bird.stop()
                    except:
                        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    # try:
    #     bird = Finch()
    #     bird.stopall()
    # except:
    #     pass

    sys.exit(app.exec())
