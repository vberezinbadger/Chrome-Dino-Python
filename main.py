import pygame
import random
import os
from PIL import Image
import io
import cairosvg

# Инициализация pygame
pygame.init()
pygame.font.init()
pygame.mixer.init()  # Инициализация звуковой подсистемы

# Константы
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 200
FPS = 60

def convert_svg_to_png(svg_path, png_path, width, height):
    """Конвертирует SVG в PNG"""
    if not os.path.exists(png_path):
        cairosvg.svg2png(
            url=svg_path,
            write_to=png_path,
            output_width=width,
            output_height=height
        )

def initialize_images():
    """Конвертирует все необходимые SVG в PNG с правильными размерами из main.js"""
    image_conversions = [
        ("images/dino_walk_1.svg", "images/dino_walk_1.png", 40, 43),  # Обновленная высота
        ("images/dino_walk_2.svg", "images/dino_walk_2.png", 40, 43),  # Обновленная высота
        ("images/dino_crash.svg", "images/dino_crash.png", 40, 43),    # Обновленная высота
        # Размеры кактуса теперь будут определяться динамически
        ("images/obstical_cactus.svg", "images/obstical_cactus.png", 20, 40),  # Обновленные размеры
        ("images/cloud.svg", "images/cloud.png", 60, 25),
        ("images/land_normal.svg", "images/land_normal.png", 100, 5),
        ("images/land_bump.svg", "images/land_bump.png", 60, 12),
        ("images/game_over.svg", "images/game_over.png", 250, 15),  # Исправленные размеры
        ("images/reset.svg", "images/reset.png", 40, 40),
        ("images/ptero_fly1.svg", "images/ptero_fly1.png", 40, 35),  # Обновленные размеры
        ("images/ptero_fly2.svg", "images/ptero_fly2.png", 40, 35),  # Обновленные размеры
    ]
    
    # Создаем папку images если её нет
    if not os.path.exists("images"):
        os.makedirs("images")
    
    for svg_path, png_path, width, height in image_conversions:
        if os.path.exists(svg_path):
            convert_svg_to_png(svg_path, png_path, width, height)

def load_image(path, width, height):
    """Загружает изображение и масштабирует его"""
    try:
        # Проверяем, существует ли PNG версия
        png_path = os.path.splitext(path)[0] + ".png"
        if (os.path.exists(png_path)):
            path = png_path
        
        image = pygame.image.load(path)
        return pygame.transform.scale(image, (width, height))
    except pygame.error as e:
        print(f"Ошибка загрузки изображения {path}: {e}")
        # Создаем пустое изображение если файл не найден
        surface = pygame.Surface((width, height))
        surface.fill((255, 0, 0))  # Заполняем красным для отладки
        return surface

# Конвертируем все изображения при запуске
initialize_images()

class GameObject:
    def __init__(self, x, y, width, height, image_path):
        self.rect = pygame.Rect(x, y, width, height)
        self.image = load_image(image_path, width, height)
        self.velocity = 0
        
    def update(self, dt):
        """Обновление состояния объекта"""
        pass  # Базовый класс не требует обновления
        
    def draw(self, screen):
        screen.blit(self.image, self.rect)

class Dino(GameObject):
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, "images", "dino_walk_1.png")
        super().__init__(10, SCREEN_HEIGHT - 43, 40, 43, image_path)  # Обновили позицию Y и высоту
        
        self.walk_images = [
            load_image(os.path.join(current_dir, "images", "dino_walk_1.png"), 40, 43),
            load_image(os.path.join(current_dir, "images", "dino_walk_2.png"), 40, 43)
        ]
        self.crash_image = load_image(os.path.join(current_dir, "images", "dino_crash.png"), 40, 43)
        
        self.gravity = 0.6
        self.velocity = 0
        self.is_jumping = False
        self.animation_count = 0
        self.is_crashed = False
        self.min_jump_velocity = -6  # Уменьшили начальную скорость прыжка с -6 до -5
        self.max_jump_velocity = -8  # Уменьшили максимальную скорость прыжка с -9 до -7
        self.jump_time = 0
        self.max_jump_time = 150  # Уменьшили время удержания с 200 до 150
        self.is_jump_pressed = False
        self.jump_sound = pygame.mixer.Sound(os.path.join(current_dir, "sounds", "jump.wav"))
        self.auto_mode = False  # Добавляем флаг автоматического режима
        self.vision_distance = 250  # Увеличиваем дистанцию видимости
        self.next_obstacle = None  # Ближайшее препятствие
        self.auto_jump_power = -6  # Базовая сила прыжка для авто-режима
        self.auto_jump_duration = 0  # Длительность удержания прыжка
        self.current_game_speed = 4  # Текущая скорость игры
        self.jump_adjustment = 1.0  # Коэффициент корректировки прыжка
        self.jump_distances = {
            'near': 60,    # Близкое расстояние
            'medium': 120,  # Среднее расстояние
            'far': 180     # Дальнее расстояние
        }

    def start_jump(self):
        """Начало прыжка"""
        if not self.is_jumping and self.rect.bottom >= SCREEN_HEIGHT:
            self.jump_sound.play()  # Воспроизводим звук прыжка
            self.is_jumping = True
            self.is_jump_pressed = True
            self.jump_time = 0
            self.velocity = self.auto_jump_power if self.auto_mode else self.min_jump_velocity  # Используем рассчитанную силу прыжка в авто-режиме

    def update(self, dt):
        if not self.is_crashed:
            # Обновление прыжка
            if self.is_jumping and self.is_jump_pressed:
                self.jump_time += dt * 1000  # Переводим в миллисекунды
                if self.jump_time <= self.max_jump_time and self.velocity > self.max_jump_velocity:
                    # Уменьшили коэффициент усиления с 3 до 2
                    self.velocity = max(
                        self.max_jump_velocity,
                        self.min_jump_velocity - (self.jump_time / self.max_jump_time) * 2
                    )

            # Гравитация
            self.velocity += self.gravity
            self.rect.y += self.velocity
            
            # Ограничение по земле
            if self.rect.bottom > SCREEN_HEIGHT:
                self.rect.bottom = SCREEN_HEIGHT
                self.velocity = 0
                self.is_jumping = False
                self.is_jump_pressed = False
                self.jump_time = 0
            
            # Анимация
            self.animation_count += 1
            if self.animation_count >= len(self.walk_images) * 10:
                self.animation_count = 0
            self.image = self.walk_images[self.animation_count // 10]

    def stop_jump(self):
        """Окончание прыжка при отпускании кнопки"""
        self.is_jump_pressed = False

    def crash(self):
        self.is_crashed = True
        self.image = self.crash_image

    def should_jump(self, obstacles, pterodactyls):
        """Определяет, нужно ли прыгать"""
        if not obstacles and not pterodactyls:
            return False

        # Объединяем все препятствия
        all_obstacles = []
        all_obstacles.extend(obstacles)
        all_obstacles.extend(pterodactyls)

        # Ищем ближайшее препятствие впереди динозавра
        nearest = None
        min_distance = float('inf')
        
        for obstacle in all_obstacles:
            if obstacle.rect.left > self.rect.right:  # Только препятствия впереди
                distance = obstacle.rect.left - self.rect.right
                if distance < min_distance:
                    min_distance = distance
                    nearest = obstacle
        
        self.next_obstacle = nearest

        # Определяем оптимальную дистанцию для начала прыжка
        if nearest:
            jump_distance = self.vision_distance * 0.4  # 40% от дистанции видимости

            # Корректируем расстояние в зависимости от типа и высоты препятствия
            if isinstance(nearest, Pterodactyl):
                if nearest.rect.bottom < SCREEN_HEIGHT - 60:
                    jump_distance *= 1.4  # Увеличиваем дистанцию для высоких птеродактилей
                else:
                    jump_distance *= 1.2  # Для низких птеродактилей
            else:
                # Для кактусов учитываем их высоту
                height_factor = nearest.rect.height / 40.0  # Нормализуем относительно стандартной высоты
                jump_distance *= (1 + height_factor * 0.2)  # Увеличиваем дистанцию для высоких кактусов

            # Корректируем расстояние с учетом текущей скорости
            jump_distance *= (self.current_game_speed / 4.0)

            # Проверяем, нужно ли прыгать
            if min_distance <= jump_distance:
                self.auto_jump_power, self.auto_jump_duration = self.calculate_jump_power(nearest)
                return self.rect.bottom >= SCREEN_HEIGHT - 1

        return False

    def calculate_jump_power(self, obstacle):
        """Рассчитывает необходимую силу прыжка для преодоления препятствия"""
        if not obstacle:
            return self.min_jump_velocity, 0
        
        distance = obstacle.rect.left - self.rect.right
        height_diff = self.rect.bottom - obstacle.rect.top
        
        # Базовая сила прыжка зависит от расстояния до препятствия
        if distance < self.jump_distances['near']:
            base_power = self.max_jump_velocity * 1.2  # Сильный прыжок для близких препятствий
            duration = self.max_jump_time * 0.9
        elif distance < self.jump_distances['medium']:
            base_power = self.max_jump_velocity * 1.1
            duration = self.max_jump_time * 0.8
        else:
            base_power = self.max_jump_velocity
            duration = self.max_jump_time * 0.7

        # Дополнительная корректировка для птеродактилей
        if isinstance(obstacle, Pterodactyl):
            if obstacle.rect.bottom < SCREEN_HEIGHT - 60:
                base_power *= 1.2  # Усиливаем прыжок для высоко летящих птеродактилей
                duration *= 0.9
            else:
                base_power *= 0.9  # Ослабляем для низко летящих
                duration *= 0.7
        else:
            # Корректировка для кактусов разной высоты
            if height_diff > 35:
                base_power *= 1.15
                duration *= 0.95
            elif height_diff > 25:
                base_power *= 1.1
                duration *= 0.85

        # Корректировка с учетом скорости игры
        speed_factor = 1 + (self.current_game_speed - 4) * 0.15
        
        # Применяем корректировки
        power = base_power * speed_factor * self.jump_adjustment
        
        # Ограничиваем значения
        power = max(min(power, -5), -10)
        duration = max(min(duration, self.max_jump_time), self.max_jump_time * 0.4)
        
        return power, duration

class Cloud(GameObject):
    def __init__(self, x, y):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Используем оригинальные размеры из main.js
        width = random.randint(60, 65)   # Оригинальная ширина
        height = random.randint(20, 25)   # Оригинальная высота
        super().__init__(x, y, width, height, os.path.join(current_dir, "images", "cloud.png"))
        self.speed = 2  # Облака двигаются медленнее чем препятствия

class Land(GameObject):
    def __init__(self, x, is_bump=False):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.is_bump = is_bump
        if is_bump:
            # Используем оригинальные размеры из main.js
            super().__init__(x, SCREEN_HEIGHT - 15, 60, 12, 
                           os.path.join(current_dir, "images", "land_bump.png"))
        else:
            # Используем оригинальные размеры из main.js
            super().__init__(x, SCREEN_HEIGHT - 10, 100, 5, 
                           os.path.join(current_dir, "images", "land_normal.png"))

class Pterodactyl(GameObject):
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(SCREEN_WIDTH, 0, 40, 35,  # Обновленные размеры
                        os.path.join(current_dir, "images", "ptero_fly1.png"))
        
        # Загружаем кадры анимации с новыми размерами
        self.fly_images = [
            load_image(os.path.join(current_dir, "images", "ptero_fly1.png"), 40, 35),
            load_image(os.path.join(current_dir, "images", "ptero_fly2.png"), 40, 35)
        ]
        
        # Устанавливаем случайную высоту полета
        self.heights = [SCREEN_HEIGHT - 40 - 40, SCREEN_HEIGHT - 80 - 40]  # Две возможные высоты
        self.rect.y = random.choice(self.heights)
        
        self.animation_count = 0
        self.speed = 4  # Уменьшаем скорость с 6 до 4

    def update(self, game_speed):
        # Движение влево
        self.rect.x -= game_speed + self.speed
        
        # Анимация
        self.animation_count += 1
        if self.animation_count >= len(self.fly_images) * 10:
            self.animation_count = 0
        self.image = self.fly_images[self.animation_count // 10]

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Chrome Dino Game")
        
        # Устанавливаем иконку игры
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, "images", "game-icon.png")
        if os.path.exists(icon_path):
            icon = pygame.image.load(icon_path)
            pygame.display.set_icon(icon)
        
        self.clock = pygame.time.Clock()
        
        # Загружаем пользовательский шрифт
        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(current_dir, "fonts", "arcade_font.TTF")
        if os.path.exists(font_path):
            self.font = pygame.font.Font(font_path, 8)  # для счета
            self.debug_font = pygame.font.Font(font_path, 8)  # для debug информации
        else:
            print("Шрифт не найден, использую стандартный")
            self.font = pygame.font.Font(None, 36)
            self.debug_font = pygame.font.Font(None, 36)
        
        self.dino = Dino()
        self.obstacles = []
        self.clouds = []
        self.lands = []
        self.pterodactyls = []  # Добавляем список для птеродактилей
        self.score = 0
        self.running = True
        self.initial_game_speed = 4  # Начальная скорость
        self.game_speed = self.initial_game_speed
        self.speed_increment = 0.001  # Увеличение скорости за каждое очко
        self.max_game_speed = 8  # Максимальная скорость
        self.last_time = pygame.time.get_ticks()
        self.land_width = 20  # Фиксированная ширина для всех элементов земли
        self.initialize_land()
        
        # Добавляем параметры дня и ночи
        self.day_night_cycle = 120 * FPS  # 2 минуты в кадрах
        self.current_cycle = 0
        self.is_night = False
        self.transition_progress = 0  # 0 = день, 1 = ночь
        self.transition_speed = 0.02  # Скорость перехода
        self.day_color = (255, 255, 255)  # Белый для дня
        self.night_color = (32, 33, 36)   # #202124 для ночи
        self.sprite_day_color = (0, 0, 0)      # Черный для спрайтов днем
        self.sprite_night_color = (255, 255, 255)  # Белый для спрайтов ночью

        # Добавляем спрайты для Game Over экрана с поддержкой прозрачности
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.game_over_sprite = pygame.image.load(
            os.path.join(current_dir, "images", "game_over.png")
        ).convert_alpha()
        self.game_over_sprite = pygame.transform.scale(self.game_over_sprite, (250, 15))  # Исправленные размеры
        
        self.reset_button = pygame.image.load(
            os.path.join(current_dir, "images", "replay_button.png")  # Изменен путь к файлу
        ).convert_alpha()
        self.reset_button = pygame.transform.scale(self.reset_button, (34, 30))  # Новые размеры 34x30
        
        # Создаем прямоугольники для позиционирования
        self.game_over_rect = self.game_over_sprite.get_rect()
        self.reset_button_rect = self.reset_button.get_rect()
        
        self.reset_game_state()
        self.show_debug = True  # Флаг для отображения debug информации
        self.show_advanced_debug = False  # Расширенный debug (M)
        self.show_vision = False  # Флаг для отображения линии зрения

        # Загружаем звуки
        self.jump_sound = pygame.mixer.Sound(os.path.join(current_dir, "sounds", "jump.wav"))
        self.point_sound = pygame.mixer.Sound(os.path.join(current_dir, "sounds", "point.wav"))
        self.die_sound = pygame.mixer.Sound(os.path.join(current_dir, "sounds", "die.wav"))
        
        # Добавляем переменную для отслеживания последней тысячи очков
        self.last_point_score = 0  # Для отслеживания последней тысячи очков

        # Добавляем параметры для подмигивания счета
        self.score_blinking = False  # Флаг активного подмигивания
        self.blink_count = 0        # Счетчик подмигиваний
        self.blink_timer = 0        # Таймер для контроля времени
        self.blink_visible = True   # Текущее состояние видимости
        self.max_blinks = 4         # Количество подмигиваний
        self.blink_interval = 100   # Интервал между сменой состояния (в мс)

    def reset_game_state(self):
        """Сбрасывает состояние игры"""
        self.dino = Dino()
        self.obstacles = []
        self.clouds = []
        self.lands = []
        self.pterodactyls = []
        self.score = 0
        self.initialize_land()
        self.is_game_over = False
        self.game_speed = self.initial_game_speed  # Сброс скорости при перезапуске

    def invert_surface_keeping_alpha(self, surface):
        """Инвертирует цвета спрайта, сохраняя прозрачность"""
        # Создаем новую поверхность с поддержкой альфа-канала
        inv = pygame.Surface(surface.get_rect().size, pygame.SRCALPHA)
        
        # Получаем доступ к пиксельным данным
        for x in range(surface.get_width()):
            for y in range(surface.get_height()):
                color = surface.get_at((x, y))
                # Инвертируем только если пиксель не прозрачный
                if color.a > 0:
                    inv.set_at((x, y), (255, 255, 255, color.a))
                else:
                    inv.set_at((x, y), (0, 0, 0, 0))
        return inv

    def apply_night_effect(self, surface):
        """Применяет эффект ночи к поверхности"""
        if self.transition_progress > 0:
            # Создаем копию с сохранением альфа-канала
            result = surface.copy()
            # Создаем инвертированную версию с сохранением прозрачности
            night_surface = self.invert_surface_keeping_alpha(surface)
            # Устанавливаем прозрачность для плавного перехода
            night_surface.set_alpha(int(255 * self.transition_progress))
            # Накладываем ночной эффект
            result.blit(night_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            return result
        return surface

    def get_current_background_color(self):
        """Возвращает текущий цвет фона с учетом перехода"""
        return tuple(
            int(day + (night - day) * self.transition_progress)
            for day, night in zip(self.day_color, self.night_color)
        )

    def initialize_land(self):
        """Создаем начальную землю с правильными размерами"""
        self.lands.clear()
        x = 0
        
        # Заполняем экран элементами земли
        while x < SCREEN_WIDTH + 200:  # Добавляем запас справа
            is_bump = random.random() < 0.1  # 10% шанс появления бугорка
            land = Land(x, is_bump)
            self.lands.append(land)
            # Следующий элемент начинается там, где заканчивается текущий
            x = land.rect.right

    def spawn_obstacle(self):
        if len(self.obstacles) == 0 or self.obstacles[-1].rect.right < SCREEN_WIDTH - 300:
            height = 40  # Фиксированная высота
            width = 20   # Фиксированная ширина
            current_dir = os.path.dirname(os.path.abspath(__file__))
            image_path = os.path.join(current_dir, "images", "obstical_cactus.png")
            obstacle = GameObject(
                SCREEN_WIDTH, 
                SCREEN_HEIGHT - height,
                width, 
                height, 
                image_path
            )
            self.obstacles.append(obstacle)

    def spawn_cloud(self):
        if len(self.clouds) == 0 or self.clouds[-1].rect.right < SCREEN_WIDTH - 300:
            y = random.randint(20, 80)
            self.clouds.append(Cloud(SCREEN_WIDTH, y))

    def spawn_land(self):
        """Добавляем новые элементы земли, сохраняя непрерывность"""
        if not self.lands:
            self.initialize_land()
            return

        # Находим самый правый элемент
        rightmost = max(self.lands, key=lambda x: x.rect.right)
        
        # Добавляем новые элементы до тех пор, пока не будет достаточного запаса справа
        while rightmost.rect.right < SCREEN_WIDTH + 200:
            is_bump = random.random() < 0.1
            new_land = Land(rightmost.rect.right, is_bump)
            self.lands.append(new_land)
            rightmost = new_land

    def spawn_pterodactyl(self):
        """Создает нового птеродактиля"""
        # Создаем птеродактиля только если прошли 500 очков и с вероятностью 1%
        if (self.score > 500 and 
            (len(self.pterodactyls) == 0 or self.pterodactyls[-1].rect.right < SCREEN_WIDTH - 400) and
            random.random() < 0.01):
            self.pterodactyls.append(Pterodactyl())

    def update(self):
        if self.dino.is_crashed and not self.is_game_over:
            self.is_game_over = True
            self.die_sound.play()  # Воспроизводим звук при проигрыше
            # Центрируем спрайты Game Over экрана
            self.game_over_rect.centerx = SCREEN_WIDTH // 2
            self.game_over_rect.centery = SCREEN_HEIGHT // 2 - 32
            
            self.reset_button_rect.centerx = SCREEN_WIDTH // 2
            self.reset_button_rect.centery = SCREEN_HEIGHT // 2 + 32
        
        if not self.is_game_over:
            current_time = pygame.time.get_ticks()
            dt = (current_time - self.last_time) / 1000.0
            self.last_time = current_time
            
            self.dino.update(dt)
            
            # Обновление облаков
            for cloud in self.clouds[:]:
                cloud.rect.x -= 2  # Облака двигаются медленнее
                if cloud.rect.right < 0:
                    self.clouds.remove(cloud)
            
            # Обновление земли
            for land in self.lands[:]:
                land.rect.x -= self.game_speed
                # Удаляем только те сегменты, которые полностью ушли за экран
                if land.rect.right < -self.land_width:
                    self.lands.remove(land)
            
            # Проверяем необходимость добавления новых сегментов
            self.spawn_land()
            
            # Обновление препятствий
            for obstacle in self.obstacles[:]:
                obstacle.rect.x -= self.game_speed
                if obstacle.rect.right < 0:
                    self.obstacles.remove(obstacle)
                if self.dino.rect.colliderect(obstacle.rect):
                    self.dino.crash()

            self.spawn_obstacle()
            self.spawn_cloud()
            self.spawn_pterodactyl()
            self.score += 1

            # Увеличиваем скорость игры
            if self.game_speed < self.max_game_speed:
                self.game_speed = min(
                    self.max_game_speed,
                    self.initial_game_speed + (self.score * self.speed_increment)
                )

            # Проверяем достижение тысячи очков (более точная проверка)
            current_thousand = self.score // 1000
            last_thousand = self.last_point_score // 1000
            if current_thousand > last_thousand:
                self.point_sound.play()
                self.last_point_score = current_thousand * 1000
                # Запускаем подмигивание
                self.score_blinking = True
                self.blink_count = 0
                self.blink_timer = current_time
                self.blink_visible = True

            # Обновление подмигивания
            if self.score_blinking:
                if current_time - self.blink_timer >= self.blink_interval:
                    self.blink_visible = not self.blink_visible
                    self.blink_timer = current_time
                    if not self.blink_visible:  # Считаем только полные циклы
                        self.blink_count += 1
                    if self.blink_count >= self.max_blinks:
                        self.score_blinking = False
                        self.blink_visible = True

            # Обновление цикла дня и ночи
            self.current_cycle = (self.current_cycle + 1) % self.day_night_cycle
            if self.current_cycle == 0:
                self.is_night = not self.is_night

            # Обновление перехода
            target = 1.0 if self.is_night else 0.0
            if self.transition_progress < target:
                self.transition_progress = min(1.0, self.transition_progress + self.transition_speed)
            elif self.transition_progress > target:
                self.transition_progress = max(0.0, self.transition_progress - self.transition_speed)

            # Обновление птеродактилей
            for ptero in self.pterodactyls[:]:
                ptero.update(self.game_speed)
                if ptero.rect.right < 0:
                    self.pterodactyls.remove(ptero)
                if self.dino.rect.colliderect(ptero.rect):
                    self.dino.crash()

            # Обновляем текущую скорость игры для динозавра
            self.dino.current_game_speed = self.game_speed

            # Автоматическое управление
            if self.dino.auto_mode and not self.dino.is_crashed:
                if self.dino.should_jump(self.obstacles, self.pterodactyls):
                    self.dino.start_jump()
                elif (self.dino.is_jumping and
                      self.dino.jump_time >= self.dino.auto_jump_duration):
                    self.dino.stop_jump()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.is_game_over:
                    # Перезапускаем игру при нажатии любой клавиши в состоянии Game Over
                    self.reset_game_state()
                elif event.key in [pygame.K_SPACE, pygame.K_UP]:
                    self.dino.start_jump()
                elif event.key == pygame.K_t:
                    self.is_night = not self.is_night
                elif event.key == pygame.K_F3:
                    self.show_debug = not self.show_debug
                elif event.key == pygame.K_m:
                    self.show_advanced_debug = not self.show_advanced_debug
                elif event.key == pygame.K_n:
                    self.dino.auto_mode = not self.dino.auto_mode
                    self.show_vision = self.dino.auto_mode
            elif event.type == pygame.KEYUP:
                if event.key in [pygame.K_SPACE, pygame.K_UP]:
                    self.dino.stop_jump()
            elif event.type == pygame.MOUSEBUTTONDOWN and self.is_game_over:
                # Оставляем возможность перезапуска по клику на кнопку
                if self.reset_button_rect.collidepoint(event.pos):
                    self.reset_game_state()

    def draw_hitbox(self, surface, rect, color=(255, 0, 0)):
        """Отрисовка хитбокса объекта"""
        pygame.draw.rect(surface, color, rect, 1)

    def draw_object_info(self, obj, info_list):
        """Отрисовка информации об объекте"""
        if not self.show_advanced_debug:
            return

        text_color = self.sprite_night_color if self.transition_progress > 0.5 else self.sprite_day_color
        y_offset = 0
        
        for info in info_list:
            text_surface = self.debug_font.render(info, True, text_color)
            self.screen.blit(text_surface, (obj.rect.right + 5, obj.rect.top + y_offset))
            y_offset += 10

    def draw_debug_info(self):
        """Отрисовка debug информации"""
        if not self.show_debug:
            return
            
        debug_info = [
            f"FPS: {int(self.clock.get_fps())}",
            f"Jump Velocity: {self.dino.velocity:.2f}",
            f"Is Night: {self.is_night}",
            f"Game Speed: {self.game_speed:.2f}",
            f"Score: {self.score}",
            f"Objects: {len(self.obstacles) + len(self.pterodactyls)}",
        ]
        
        if self.show_advanced_debug:
            debug_info.extend([
                "Advanced Debug: ON",
                f"Pterodactyls: {len(self.pterodactyls)}",
                f"Obstacles: {len(self.obstacles)}",
                f"Clouds: {len(self.clouds)}",
                f"Auto Jump Power: {self.dino.auto_jump_power:.1f}",
                f"Auto Jump Duration: {self.dino.auto_jump_duration}"
            ])
        
        # Объединяем все строки в одну с переносами
        debug_text = "\n".join(debug_info)
        
        # Определяем цвет текста в зависимости от времени суток
        text_color = self.sprite_night_color if self.transition_progress > 0.5 else self.sprite_day_color
        
        # Разбиваем текст на строки для отрисовки
        y = 10  # Отступ сверху
        for line in debug_text.split('\n'):
            debug_surface = self.debug_font.render(line, True, text_color)
            # Позиционируем текст справа с отступом 10 пикселей
            x = SCREEN_WIDTH - debug_surface.get_width() - 10
            self.screen.blit(debug_surface, (x, y))
            y += debug_surface.get_height()

    def draw_vision_line(self):
        """Отрисовка линии зрения"""
        if self.show_vision and self.dino.next_obstacle:
            start_pos = (self.dino.rect.right, self.dino.rect.centery)
            end_pos = (self.dino.next_obstacle.rect.left, self.dino.next_obstacle.rect.centery)
            pygame.draw.line(self.screen, (0, 255, 0), start_pos, end_pos, 2)

    def draw(self):
        # Заливаем фон текущим цветом
        self.screen.fill(self.get_current_background_color())
        
        # Рисуем облака
        for cloud in self.clouds:
            cloud_surface = cloud.image.copy()
            if self.transition_progress > 0:
                cloud_surface = self.apply_night_effect(cloud_surface)
            self.screen.blit(cloud_surface, cloud.rect)
        
        # Рисуем землю
        for land in self.lands:
            land_surface = land.image.copy()
            if self.transition_progress > 0:
                land_surface = self.apply_night_effect(land_surface)
            self.screen.blit(land_surface, land.rect)
        
        # Рисуем динозавра
        dino_surface = self.dino.image.copy()
        if self.transition_progress > 0:
            dino_surface = self.apply_night_effect(dino_surface)
        self.screen.blit(dino_surface, self.dino.rect)
        
        # Рисуем препятствия
        for obstacle in self.obstacles:
            obstacle_surface = obstacle.image.copy()
            if self.transition_progress > 0:
                obstacle_surface = self.apply_night_effect(obstacle_surface)
            self.screen.blit(obstacle_surface, obstacle.rect)

        # Рисуем птеродактилей
        for ptero in self.pterodactyls:
            ptero_surface = ptero.image.copy()
            if self.transition_progress > 0:
                ptero_surface = self.apply_night_effect(ptero_surface)
            self.screen.blit(ptero_surface, ptero.rect)

        # Отображение счета с учетом подмигивания
        score_color = self.sprite_day_color if self.transition_progress < 0.5 else self.sprite_night_color
        if not self.score_blinking or self.blink_visible:
            score_text = self.font.render(f'Score: {self.score}', True, score_color)
            self.screen.blit(score_text, (10, 10))

        # Добавляем отрисовку debug информации
        self.draw_debug_info()

        # Отрисовка расширенного debug
        if self.show_advanced_debug:
            # Хитбокс и информация о динозавре
            self.draw_hitbox(self.screen, self.dino.rect, (0, 255, 0))
            self.draw_object_info(self.dino, [
                f"pos: ({self.dino.rect.x}, {self.dino.rect.y})",
                f"vel: {self.dino.velocity:.1f}",
                f"jump: {self.dino.is_jumping}"
            ])

            # Хитбоксы и информация о птеродактилях
            for ptero in self.pterodactyls:  # Исправлена опечатка
                self.draw_hitbox(self.screen, ptero.rect, (255, 0, 0))
                self.draw_object_info(ptero, [
                    f"pos: ({ptero.rect.x}, {ptero.rect.y})",
                    f"speed: {ptero.speed + self.game_speed:.1f}"
                ])

            # Хитбоксы и информация о препятствиях
            for obstacle in self.obstacles:
                self.draw_hitbox(self.screen, obstacle.rect, (255, 165, 0))
                self.draw_object_info(obstacle, [
                    f"pos: ({obstacle.rect.x}, {obstacle.rect.y})",
                    f"size: {obstacle.rect.width}x{obstacle.rect.height}"
                ])

            # Хитбоксы облаков (необязательно)
            for cloud in self.clouds:
                self.draw_hitbox(self.screen, cloud.rect, (0, 191, 255))

        # Отрисовка линии зрения перед отрисовкой debug информации
        if self.show_vision:
            self.draw_vision_line()

        # Отрисовка Game Over экрана поверх всего остального
        if self.is_game_over:
            # Рисуем спрайт Game Over
            game_over_surface = self.game_over_sprite.copy()
            if self.transition_progress > 0:
                game_over_surface = self.apply_night_effect(game_over_surface)
            self.screen.blit(game_over_surface, self.game_over_rect)
            
            # Рисуем кнопку перезапуска
            reset_surface = self.reset_button.copy()
            if self.transition_progress > 0:
                reset_surface = self.apply_night_effect(reset_surface)
            self.screen.blit(reset_surface, self.reset_button_rect)

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
