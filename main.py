import sys
import csv
import random
import sqlite3

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QSpinBox,
    QPushButton,
    QHBoxLayout,
    QCheckBox,
)
from PyQt5.QtCore import Qt, QRectF, QUrl
from PyQt5.QtGui import QPainter, QBrush, QPen, QFont, QColor, QIcon
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer, QMediaPlaylist
from datetime import datetime


class Tile:
    def __init__(self, value):
        self.value = value


# Программа
class Game(QWidget):
    def __init__(self):
        super().__init__()

        self.setFixedSize(345, 450)  # Размер окна
        self.game_view = GameView(
            self, self.history_game, self.data_history
        )  # Экземпляр GameView
        self.connection = sqlite3.connect("files/game_history.db")  # История игр

        self.tab = QTabWidget()  # Создание вкладок
        self.tab.setFocusPolicy(Qt.NoFocus)  # Игнорирование горячих клавиш вкладок

        # Вкладки
        self.tab.addTab(self.game_view, "Игра")
        self.tab.addTab(self.project_info(), "О проекте")
        self.tab.addTab(self.history_game(), "История игр")
        self.tab.addTab(self.game_view.settings(), "Настройки")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Удаление отступов
        layout.addWidget(self.tab)
        self.setLayout(layout)

    # Вкладка "О проекте"
    def project_info(self):
        info_widget = QWidget()
        layout = QVBoxLayout()
        info_label = QLabel()
        info_label.setFont(QFont("Arial", 14))
        info_label.setText(
        """
            <p>
                В приложении:<br>
                • Сохранение лучшего результата<br>
                • История игр, импорт и экспорт<br>
                • Изменение размера игрового поля<br>
                • Фоновая музыка<br>
            </p>
            <p>
                Правила игры:<br>
                Цель: получить в сумме 2048<br>
                Игра заканчивается поражением,<br>если после очередного хода<br>невозможно совершить действие.
            </p>
            <p>
                <br>Горячие клавиши:<br>
                • Up, Down, Left и Right - <br> перемещение плиток<br>
                • Esc - начать заново
            </p>
        """
        )
        layout.addWidget(info_label)
        info_widget.setLayout(layout)

        return info_widget

    # Данные об истории игр
    def data_history(self):
        history_data = []

        with sqlite3.connect("files/game_history.db") as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT result, score, best_score, timestamp FROM game_history"
            )

            for result, score, best_score, timestamp in cursor.fetchall():
                history_data.append((result, score, best_score, timestamp))

        return history_data

    # Вкладка "История игр"
    def history_game(self):
        history_widget = QWidget()
        layout = QVBoxLayout()
        history_label = QLabel()
        history_label.setFont(QFont("Arial", 14))

        history_data = self.data_history()  # Получить данные об истории игр

        if not history_data:
            history_label.setText("История игр пуста")
            history_label.setAlignment(Qt.AlignCenter)
        else:
            history_table = QTableWidget()  # Создание таблицы

            # Кол-во строк и столбцов в таблице
            history_table.setRowCount(len(history_data))
            history_table.setColumnCount(4)

            history_table.setHorizontalHeaderLabels(
                ["Результат", "Очки", "Рекорд", "Дата и время"]
            )  # Заголовки таблицы

            # Заполнение таблицы данными
            for row,(result, score, best_score, timestamp) \
                in enumerate(history_data):
                history_table.setItem(row, 0, QTableWidgetItem(result))
                history_table.setItem(row, 1, QTableWidgetItem(str(score)))
                history_table.setItem(
                    row, 2, QTableWidgetItem(
                        str(best_score if best_score > 0 else "-")
                    )
                )
                history_table.setItem(row, 3, QTableWidgetItem(timestamp))

                # Ширина столбцов
                history_table.setColumnWidth(0, 74)
                history_table.setColumnWidth(1, 54)
                history_table.setColumnWidth(2, 54)
                history_table.setColumnWidth(3, 115)

            layout.addWidget(history_table)  # Добавление таблицы

        layout.addWidget(history_label)

        history_widget.setLayout(layout)
        return history_widget

    # Перенаправление горячих клавиш
    def keyPressEvent(self, event):
        self.tab.currentWidget().keyPressEvent(event) 

    # Закрыть соединение с базой данных
    def close_connection(self):
        self.connection.close()


# 2048
class GameView(QWidget):
    def __init__(self, game, history_game, data_history):
        super().__init__()

        self.game = game
        self.history_game = history_game
        self.data_history = data_history

        self.connection = sqlite3.connect("files/game_history.db")  # История игр

        # Размер сетки
        try:
            with open("files/grid.txt", "r") as file:
                self.grid_size = int(file.read())
        except FileNotFoundError:
            self.grid_size = 4

        self.tile_margin = 10  # Расстояние между плитками
        self.tile_size = (
            340 - self.tile_margin * (self.grid_size + 1)
        ) / self.grid_size  # Размер плитки

        # Цвета плиток
        self.colors_tile = {
            0: QBrush(QColor(0xE0D1BF)),
            2: QBrush(QColor(0xEEE4DA)),
            4: QBrush(QColor(0xEDE0C8)),
            8: QBrush(QColor(0xF2B179)),
            16: QBrush(QColor(0xF59563)),
            32: QBrush(QColor(0xF67C5F)),
            64: QBrush(QColor(0xF65E3B)),
            128: QBrush(QColor(0xEDCF72)),
            256: QBrush(QColor(0xEDCC61)),
            512: QBrush(QColor(0xEDC850)),
            1024: QBrush(QColor(0xEDC53F)),
            2048: QBrush(QColor(0xEDC22E)),
        }

        self.background = QBrush(QColor(0xF3EEE3))  # Цвет фона
        self.colors_element = QBrush(QColor(0x776E65))  # Цвет кнопок

        # Цвета текста
        self.color_text = QPen(QColor(0xFFF4EA))
        self.color_white = QPen(QColor(0xF9F6F2))
        self.color_dark = QPen(QColor(0x776E65))

        # Музыка
        self.media_playlist = QMediaPlaylist()
        self.media_playlist.addMedia(
            QMediaContent(QUrl.fromLocalFile("music/1.mp3"))
        )
        self.media_playlist.setPlaybackMode(QMediaPlaylist.CurrentItemInLoop)

        self.media_player = QMediaPlayer(self)
        self.media_player.setPlaylist(self.media_playlist)
        self.media_player.setVolume(50)  # Громкость

        self.record()
        self.game_history()
        self.reset_game()

    # Чтение рекорда
    def record(self):
        try:
            with open("files/record.txt", "r") as file:
                self.high_score = int(file.read())
        except FileNotFoundError:
            self.high_score = 0

    # Создание таблицы для хранения истории игр
    def game_history(self):
        with self.connection:
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS game_history (
                    id INTEGER PRIMARY KEY,
                    result TEXT,
                    score INTEGER,
                    best_score INTEGER,
                    timestamp DATETIME
                )
                """
            )

    # Обновление вкладки об истории игр
    def update_history_tab(self):
        self.game.tab.removeTab(2)
        self.game.tab.insertTab(2, self.history_game(), "История игр")

    # Обновление истории после каждой игры
    def update_history(self, result, score):
        best_score = self.high_score if self.score >= self.high_score else -1
        timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        with self.connection:
            self.connection.execute(
                f"""
                INSERT INTO game_history (score, result, best_score, timestamp)
                VALUES (?, ?, ?, ?)
            """,
                (result, score, best_score, timestamp),
            )

        self.update_history_tab()

    # Начать заново
    def reset_game(self):
        self.tiles = [
            [None for _ in range(self.grid_size)] for _ in range(self.grid_size)
        ]
        self.tiles_empty = list(
            range(0, self.grid_size * self.grid_size)
        )  # Пустые ячейки
        self.score = 0  # Счёт
        self.add_tile()
        self.add_tile()
        self.update()  # Перерисовка плиток

    # Создание плитки
    def add_tile(self):
        if len(self.tiles_empty) > 0:
            tile_new = (
                2 if random.random() < 0.9 else 4
            )  # Создание плитки 2 с вероятностью 90%, 4 => 10%
            index = self.tiles_empty.pop(
                int(random.random() * len(self.tiles_empty))
            )  # Размещение плитки в любой пустой ячейке
            grid_X = index % self.grid_size
            grid_Y = index // self.grid_size
            self.tiles[grid_X][grid_Y] = Tile(tile_new)

    # Клавиша "Вперёд"
    def up(self):
        tile_moved = False

        for grid_X in range(self.grid_size):
            for grid_Y in range(1, self.grid_size):
                if self.tiles[grid_X][grid_Y] is not None:
                    index = grid_Y

                    while index - 1 >= 0 and self.tiles[grid_X][index - 1] is None:
                        index -= 1
                    if (
                        index - 1 >= 0
                        and self.tiles[grid_X][index - 1].value
                        == self.tiles[grid_X][grid_Y].value
                    ):
                        self.score += self.tiles[grid_X][grid_Y].value * 2
                        self.tiles[grid_X][index - 1].value *= 2
                        self.tiles[grid_X][grid_Y] = None
                        tile_moved = True
                    elif index < grid_Y:
                        self.tiles[grid_X][index] = self.tiles[grid_X][grid_Y]
                        self.tiles[grid_X][grid_Y] = None
                        tile_moved = True

        if tile_moved:
            self.update_tiles()

    # Клавиша "Назад"
    def down(self):
        tile_moved = False

        for grid_X in range(self.grid_size):
            for grid_Y in range(self.grid_size - 2, -1, -1):
                if self.tiles[grid_X][grid_Y] is not None:
                    index = grid_Y

                    while (
                        index + 1 < self.grid_size
                        and self.tiles[grid_X][index + 1] is None
                    ):
                        index += 1
                    if (
                        index + 1 < self.grid_size
                        and self.tiles[grid_X][index + 1].value
                        == self.tiles[grid_X][grid_Y].value
                    ):
                        self.score += self.tiles[grid_X][grid_Y].value * 2
                        self.tiles[grid_X][index + 1].value *= 2
                        self.tiles[grid_X][grid_Y] = None
                        tile_moved = True
                    elif index > grid_Y:
                        self.tiles[grid_X][index] = self.tiles[grid_X][grid_Y]
                        self.tiles[grid_X][grid_Y] = None
                        tile_moved = True

        if tile_moved:
            self.update_tiles()

    # Клавиша "Влево"
    def left(self):
        tile_moved = False

        for grid_X in range(1, self.grid_size):
            for grid_Y in range(self.grid_size):
                if self.tiles[grid_X][grid_Y] is not None:
                    index = grid_X

                    while index - 1 >= 0 and self.tiles[index - 1][grid_Y] is None:
                        index -= 1
                    if (
                        index - 1 >= 0
                        and self.tiles[index - 1][grid_Y].value
                        == self.tiles[grid_X][grid_Y].value
                    ):
                        self.score += self.tiles[grid_X][grid_Y].value * 2
                        self.tiles[index - 1][grid_Y].value *= 2
                        self.tiles[grid_X][grid_Y] = None
                        tile_moved = True
                    elif index < grid_X:
                        self.tiles[index][grid_Y] = self.tiles[grid_X][grid_Y]
                        self.tiles[grid_X][grid_Y] = None
                        tile_moved = True

        if tile_moved:
            self.update_tiles()

    # Клавиша "Вправо"
    def right(self):
        tile_moved = False

        for grid_X in range(self.grid_size - 2, -1, -1):
            for grid_Y in range(self.grid_size):
                if self.tiles[grid_X][grid_Y] is not None:
                    index = grid_X

                    while (
                        index + 1 < self.grid_size
                        and self.tiles[index + 1][grid_Y] is None
                    ):
                        index += 1
                    if (
                        index + 1 < self.grid_size
                        and self.tiles[index + 1][grid_Y].value
                        == self.tiles[grid_X][grid_Y].value
                    ):
                        self.score += self.tiles[grid_X][grid_Y].value * 2
                        self.tiles[index + 1][grid_Y].value *= 2
                        self.tiles[grid_X][grid_Y] = None
                        tile_moved = True
                    elif index > grid_X:
                        self.tiles[index][grid_Y] = self.tiles[grid_X][grid_Y]
                        self.tiles[grid_X][grid_Y] = None
                        tile_moved = True

        if tile_moved:
            self.update_tiles()

    # Обновление плиток
    def update_tiles(self):
        self.tiles_empty = []

        for x in range(self.grid_size):
            for y in range(self.grid_size):
                tile = self.tiles[x][y]

                if tile is not None and tile.value == 2048:
                    if self.score > self.high_score:
                        self.high_score = self.score

                    QMessageBox.information(self, "2048", "Вы выиграли!")
                    self.update_history(self.score, "Выигрыш")
                    self.reset_game()

                if self.tiles[x][y] is None:
                    self.tiles_empty.append(x + y * self.grid_size)

        self.add_tile()
        self.high_score = max(self.score, self.high_score)
        self.update()

        # Сохранение рекорда
        try:
            with open("files/record.txt", "w") as file:
                file.write(str(self.high_score))
        except FileNotFoundError:
            self.high_score = 0

        if not self.tiles_available():
            QMessageBox.information(self, "2048", "Игра окончена")
            self.update_history(self.score, "Проигрыш")
            self.reset_game()

    # Проверка доступных ходов
    def tiles_available(self):
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                if (
                    self.tiles_empty
                    or (
                        x < self.grid_size - 1
                        and self.tiles[x][y].value == self.tiles[x + 1][y].value
                    )
                    or (
                        y < self.grid_size - 1
                        and self.tiles[x][y].value == self.tiles[x][y + 1].value
                    )
                ):
                    return True

        return False

    # События клавиш
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reset_game()
        elif event.key() == Qt.Key_Up:
            self.up()
        elif event.key() == Qt.Key_Down:
            self.down()
        elif event.key() == Qt.Key_Left:
            self.left()
        elif event.key() == Qt.Key_Right:
            self.right()

    # Блок "Счёт"
    def block_score(self, painter):
        painter.setBrush(self.colors_element)
        painter.drawRoundedRect(QRectF(10, 10, 80, 60), 10.0, 10.0)
        painter.setFont(QFont("Arial", 14))
        painter.setPen(self.color_text)
        painter.drawText(QRectF(20, 15, 80, 20), "Счёт")

    # Блок "Рекорд"
    def block_best(self, painter):
        painter.setBrush(self.colors_element)
        painter.drawRoundedRect(QRectF(100, 10, 80, 60), 10.0, 10.0)
        painter.setFont(QFont("Arial", 14))
        painter.setPen(self.color_text)
        painter.drawText(QRectF(110, 15, 80, 20), "Рекорд")

    # Отрисовка элементов
    def paintEvent(self, painter):
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.background)
        painter.drawRect(self.rect())

        self.block_score(painter)
        self.block_best(painter)

        painter.drawText(QRectF(20, 40, 80, 50), str(self.score))
        painter.drawText(QRectF(110, 40, 80, 50), str(self.high_score))
        painter.setFont(QFont("Arial", int(self.tile_size / 4)))

        for grid_X in range(self.grid_size):
            for grid_Y in range(self.grid_size):
                tile = self.tiles[grid_X][grid_Y]

                if tile is None:
                    painter.setBrush(self.colors_tile[0])
                else:
                    painter.setBrush(self.colors_tile[tile.value])

                # Положение плиток
                position = QRectF(
                    self.tile_margin
                    + grid_X * (self.tile_size + self.tile_margin),
                    80 + self.tile_margin
                    + grid_Y * (self.tile_size + self.tile_margin),
                    self.tile_size,
                    self.tile_size,
                )
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(position, 5.0, 5.0)  # Скругление плиток

                if tile is not None:
                    # Размер шрифта
                    if self.grid_size == 2:
                        font_size = 22
                    if self.grid_size == 3:
                        font_size = 20
                    elif self.grid_size == 4:
                        font_size = 18
                    elif self.grid_size == 5:
                        font_size = 16
                    elif self.grid_size == 6:
                        font_size = 14

                    painter.setPen(
                        self.color_dark if tile.value < 8 else self.color_white
                    )
                    painter.setFont(QFont("Arial", font_size))
                    painter.drawText(
                        position, Qt.AlignCenter | Qt.AlignVCenter,
                        str(tile.value)
                    )

    # Вкладка "Настройки"
    def settings(self):
        settings_widget = QWidget(self)
        settings_layout = QVBoxLayout()

        # Поле
        spinbox = QSpinBox()
        spinbox.setMinimum(2)
        spinbox.setMaximum(6)
        spinbox.setValue(self.grid_size)

        # Кнопка "Сохранить"
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(
            lambda: self.settings_apply(spinbox.value())
        )

        settings_row = QHBoxLayout()
        settings_row.addWidget(QLabel("Размер сетки:"))
        settings_row.addWidget(spinbox)
        settings_row.addWidget(save_button)

        music_layout = QHBoxLayout()
        music_checkbox = QCheckBox("Музыка")
        music_checkbox.setChecked(False)
        music_checkbox.stateChanged.connect(self.toggle_music)
        music_layout.addWidget(music_checkbox)

        # Кнопки импорта/экспорта
        import_data = QPushButton("Импорт истории")
        import_data.clicked.connect(self.import_csv)
        export_data = QPushButton("Экспорт истории")
        export_data.clicked.connect(self.export_csv)
        history_clear = QPushButton("Очистка истории")
        history_clear.clicked.connect(self.history_clear)

        history_import = QHBoxLayout()
        history_import.addWidget(import_data)
        history_import.addWidget(export_data)
        history_import.addWidget(history_clear)

        # Размещение элементов
        settings_layout.addLayout(history_import)
        settings_layout.addLayout(settings_row)
        settings_layout.addLayout(music_layout)
        settings_layout.addStretch()

        settings_widget.setLayout(settings_layout)
        return settings_widget

    # Очистить историю игр
    def history_clear(self):
        connection = sqlite3.connect("files/game_history.db")
        cursor = connection.cursor()
        cursor.execute("DELETE FROM game_history")

        connection.commit()
        connection.close()

        self.clear_message = QMessageBox(
            QMessageBox.Information, "2048", "История игр очищена"
        )
        self.clear_message.exec_()

        self.update_history_tab()

    # Импорт данных в CSV-файл
    def import_csv(self):
        try:
            connection = sqlite3.connect("files/game_history.db")
            cursor = connection.cursor()
            cursor.execute("DELETE FROM game_history")  # Удаление существующих данных

            with open("files/game_history.csv", "r", newline="") as csvfile:
                csv_reader = csv.reader(csvfile)
                next(csv_reader)  # Пропуск первой строки с заголовками

                for row in csv_reader:
                    result, score, best_score, timestamp = row
                    cursor.execute(
                        "INSERT INTO game_history (result, score, best_score, timestamp) VALUES (?, ?, ?, ?)",
                        (result, int(score), int(best_score), timestamp),
                    )

            connection.commit()
            connection.close()

            self.import_message = QMessageBox(
                QMessageBox.Information, "2048",
                "Данные импортированы из файла Excel"
            )
            self.import_message.exec_()

            self.update_history_tab()
        except Exception as e:
            self.import_message = QMessageBox(
                QMessageBox.Critical,
                "2048",
                f"Произошла ошибка при импорте данных из файла Excel: {str(e)}",
            )
            self.import_message.exec()

    # Экспорт данных в CSV-файл
    def export_csv(self):
        try:
            data = [("Результат", "Очки", "Рекорд", "Дата и время")]
            data.extend(self.data_history())

            with open("files/game_history.csv", "w", newline="") as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerows(data)

            self.export_message = QMessageBox(
                QMessageBox.Information, "2048",
                "Данные экспортированы в файл Excel"
            )
            self.export_message.exec_()
        except Exception as e:
            self.export_message = QMessageBox(
                QMessageBox.Critical,
                "2048",
                f"Произошла ошибка при экспорте данных в файл Excel: {str(e)}",
            )
            self.export_message.exec()

    # Применение настройки
    def settings_apply(self, new_grid_size):
        if new_grid_size != self.grid_size:
            self.grid_size = new_grid_size
            self.tile_size = (
                340 - self.tile_margin * (self.grid_size + 1)
            ) / self.grid_size
            self.reset_game()

            # Сохранение размера сетки
            with open("files/grid.txt", "w") as file:
                file.write(str(new_grid_size))

    # Переключатель музыки
    def toggle_music(self, state):
        if state == Qt.Checked:
            self.media_player.play()
        else:
            self.media_player.stop()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Game()
    ex.setWindowTitle("2048")
    ex.setWindowIcon(QIcon("images/logo.png"))
    ex.show()
    app.aboutToQuit.connect(ex.close_connection)
    sys.exit(app.exec_())
