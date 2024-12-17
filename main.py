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

    def start_jump(self):
        """Начало прыжка"""
        if not self.is_jumping and self.rect.bottom >= SCREEN_HEIGHT:
            self.jump_sound.play()  # Воспроизводим звук прыжка
            self.is_jumping = True
            self.is_jump_pressed = True
            self.jump_time = 0
            self.velocity = self.min_jump_velocity  # Начальная скорость прыжка

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

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_SPACE, pygame.K_UP] and not self.is_game_over:
                    self.dino.start_jump()
                elif event.key == pygame.K_t:
                    self.is_night = not self.is_night
                elif event.key == pygame.K_F3:  # Добавляем клавишу для переключения debug информации
                    self.show_debug = not self.show_debug
            elif event.type == pygame.KEYUP:
                if event.key in [pygame.K_SPACE, pygame.K_UP]:
                    self.dino.stop_jump()
            elif event.type == pygame.MOUSEBUTTONDOWN and self.is_game_over:
                # Проверяем клик по кнопке перезапуска
                if self.reset_button_rect.collidepoint(event.pos):
                    self.reset_game_state()

    def draw_debug_info(self):
        """Отрисовка debug информации"""
        if not self.show_debug:
            return
            
        debug_info = [
            f"FPS: {int(self.clock.get_fps())}",
            f"Jump Velocity: {self.dino.velocity:.2f}",
            f"Is Night: {self.is_night}",
            f"Game Speed: {self.game_speed:.2f}"
        ]
        
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

        # Отображение счета с учетом подмигивания
        score_color = self.sprite_day_color if self.transition_progress < 0.5 else self.sprite_night_color
        if not self.score_blinking or self.blink_visible:
            score_text = self.font.render(f'Score: {self.score}', True, score_color)
            self.screen.blit(score_text, (10, 10))

        # Добавляем отрисовку debug информации
        self.draw_debug_info()

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
