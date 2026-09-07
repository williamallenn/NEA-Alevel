import pygame
import sys
import random
from settings import *

class SpriteSheet:
	def __init__(self, file, alpha=False):
		self.alpha = alpha
		if alpha:
			self.sheet = pygame.image.load(file).convert_alpha()
		else:
			self.sheet = pygame.image.load(file).convert()

	def get_sprite(self, x, y, width, height):
		if self.alpha:
			sprite = pygame.Surface([width, height], pygame.SRCALPHA)
		else:
			sprite = pygame.Surface([width, height])
		sprite.blit(self.sheet, (0, 0), (x, y, width, height))
		return sprite


class CameraGroup(pygame.sprite.Group):
	def __init__(self, game):
		super().__init__()
		self.game = game
		self.display_surface = game.screen
		self.offset = pygame.math.Vector2()
		self.half_w = self.display_surface.get_size()[0] // 2
		self.half_h = self.display_surface.get_size()[1] // 2

	def center_target_camera(self, target):
		self.offset.x = target.rect.centerx - self.half_w
		self.offset.y = target.rect.centery - self.half_h

	def custom_draw(self, player):
		self.center_target_camera(player)
		self.display_surface.fill("#73D8E7")

		for sprite in self.game.ground_sprites:
			offset_pos = sprite.rect.topleft - self.offset
			self.display_surface.blit(sprite.image, offset_pos)

		for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
			image_rect = sprite.image.get_rect(center=sprite.rect.center)
			offset_pos = image_rect.topleft - self.offset
			self.display_surface.blit(sprite.image, offset_pos)


class Player(pygame.sprite.Sprite):
	def __init__(self, game, x, y):

		self.game = game
		self.groups = game.all_sprites
		pygame.sprite.Sprite.__init__(self, game.all_sprites)
		self.x = x * TILE_SIZE
		self.y = y * TILE_SIZE
		self.direction = pygame.math.Vector2()
		self.width = TILE_SIZE
		self.height = TILE_SIZE
		self.looking = "down"
		sprite_scale = 2
		self.image = pygame.Surface([int(TILE_SIZE * sprite_scale)] * 2, pygame.SRCALPHA)
		player_img = pygame.image.load("images/Player1.png").convert_alpha()
		player_img = pygame.transform.scale(player_img, self.image.get_size())
		self.image.blit(player_img, (0, 0))
		self.rect = pygame.Rect(0, 0, self.width, self.height)
		self.rect.x = self.x
		self.rect.y = self.y
		self.health = PLAYER_BASE_HEALTH
		self.max_health = PLAYER_BASE_HEALTH
		self.speed = 350
		self.damage = PLAYER_BASE_DAMAGE
		self.money = STARTING_MONEY
		self.extra_bullets = 0
		self.bullet_pierce = 0
		self.explosive_rounds = False
		self.lifesteal_amount = 0
		self.shield_charges = 0
		self.hit_invulnerability_ms = DEFAULT_HIT_INVULNERABILITY_MS
		self.chosen_upgrades = []
		self.last_attack_time = 0
		self.attack_cooldown_multiplier = 1.0
		self.weapon_keys = list(WEAPON_DATA.keys())
		self.weapon_index = 0
		self.last_weapon_switch_time = 0

	def move(self):
		key = pygame.key.get_pressed()
		self.direction.x = 0
		self.direction.y = 0
		if key[pygame.K_w]:
			self.direction.y = -1
			self.looking = "up"
		if key[pygame.K_s]:
			self.direction.y = 1
			self.looking = "down"
		if key[pygame.K_a]:
			self.direction.x = -1
			self.looking = "left"
		if key[pygame.K_d]:
			self.direction.x = 1
			self.looking = "right"
		if self.direction.magnitude() != 0:
			self.direction = self.direction.normalize()

	def current_weapon(self):
		return WEAPON_DATA[self.weapon_keys[self.weapon_index]]

	def switch_weapon(self):
		now = pygame.time.get_ticks()
		if now - self.last_weapon_switch_time < WEAPON_SWITCH_COOLDOWN_MS:
			return
		self.weapon_index = (self.weapon_index + 1) % len(self.weapon_keys)
		self.last_weapon_switch_time = now

	def shoot(self):
		now = pygame.time.get_ticks()
		weapon = self.current_weapon()
		cooldown = weapon["cooldown"] * self.attack_cooldown_multiplier
		if now - self.last_attack_time < cooldown:
			return
		mouse_screen_pos = pygame.mouse.get_pos()
		world_mouse_pos = pygame.math.Vector2(mouse_screen_pos) + self.game.all_sprites.offset
		base_direction = world_mouse_pos - pygame.math.Vector2(self.rect.center)
		if base_direction.magnitude() != 0:
			base_direction = base_direction.normalize()
		total_bullets = weapon["bullet_count"] + self.extra_bullets
		spread_angle = weapon["spread_degrees"] if weapon["spread_degrees"] > 0 else TWIN_SHOT_ANGLE_OFFSET_DEGREES
		spread_start = -(total_bullets - 1) * spread_angle / 2
		bullet_damage = self.damage * weapon["damage_multiplier"]
		for i in range(total_bullets):
			angle = spread_start + i * spread_angle
			Bullet(self.game, self, base_direction.rotate(angle), bullet_damage, weapon["bullet_speed"], self.bullet_pierce, self.explosive_rounds)
		self.last_attack_time = now

	def collide_w_blocks(self, direction):
		if direction == 'x':
			hit = pygame.sprite.spritecollide(self, self.game.blocks, False)
			if hit:
				if self.direction.x > 0:
					self.rect.x = hit[0].rect.left - self.rect.width
				if self.direction.x < 0:
					self.rect.x = hit[0].rect.right
		if direction == 'y':
			hit = pygame.sprite.spritecollide(self, self.game.blocks, False)
			if hit:
				if self.direction.y > 0:
					self.rect.y = hit[0].rect.top - self.rect.height
				if self.direction.y < 0:
					self.rect.y = hit[0].rect.bottom

	def collide_w_enemies(self):
		hit = [s for s in pygame.sprite.spritecollide(self, self.game.enemies, False) if s is not self]
		if hit:
			self.take_damage()

	def collide_w_bullets(self):
			hit = pygame.sprite.spritecollide(self, self.game.bullets, True)
			if hit:
				self.take_damage()

	def take_damage(self):
		now = pygame.time.get_ticks()
		if not hasattr(self, "last_hit_time"):
			self.last_hit_time = 0
		if now - self.last_hit_time < self.hit_invulnerability_ms:
			return
		self.last_hit_time = now
		if self.shield_charges > 0:
			self.shield_charges -= 1
			return
		self.health -= 1

	def update(self, dt):
		self.move()
		self.rect.x += self.direction.x * self.speed * dt
		self.collide_w_blocks('x')
		self.rect.y += self.direction.y * self.speed * dt
		self.collide_w_blocks('y')
		self.collide_w_enemies()

class Enemy(Player):
	def __init__(self, game, x, y):
		super().__init__(game, x, y)
		self.groups = game.all_sprites, game.enemies
		game.enemies.add(self)
		self.speed = 90
		self.health = 3
		self.rect = pygame.Rect(0, 0, self.width, self.height)
		self.rect.x = self.x
		self.rect.y = self.y
		sheet = game.zombie_sprite_sheet.sheet
		frame_count = 4
		frame_width = sheet.get_width() // frame_count
		frame_height = sheet.get_height()
		sprite_scale = 1.5
		img_size = int(TILE_SIZE * sprite_scale)

		self.frames = []
		for i in range(frame_count):
			frame = game.zombie_sprite_sheet.get_sprite(i * frame_width, 0, frame_width, frame_height)
			frame = pygame.transform.scale(frame, (img_size, img_size))
			self.frames.append(frame)

		self.frame_index = 0
		self.animation_speed = 8
		self.image = self.frames[0]

	def animate(self, dt):
		self.frame_index += self.animation_speed * dt
		if self.frame_index >= len(self.frames):
			self.frame_index = 0
		self.image = self.frames[int(self.frame_index)]

	def move(self):
		self.direction.x = 0
		self.direction.y = 0

		if self.rect.x < self.game.player.rect.x:
			self.direction.x = 1
			self.looking = "right"
		elif self.rect.x > self.game.player.rect.x:
			self.direction.x = -1
			self.looking = "left"

		if self.rect.y < self.game.player.rect.y:
			self.direction.y = 1
			self.looking = "down"
		elif self.rect.y > self.game.player.rect.y:
			self.direction.y = -1
			self.looking = "up"

		if self.direction.magnitude() != 0:
			self.direction = self.direction.normalize()

	def collide_w_enemies(self):
		pass

	def soft_collide_w_enemies(self, overlap_tolerance=8):
		hit = [s for s in pygame.sprite.spritecollide(self, self.game.enemies, False) if s is not self]
		if not hit:
			return
		push_x_total = 0
		push_y_total = 0

		for other in hit:
			dx = self.rect.centerx - other.rect.centerx
			dy = self.rect.centery - other.rect.centery
			dist = (dx ** 2 + dy ** 2) ** 0.5
			min_dist = (self.rect.width / 2 + other.rect.width / 2) - overlap_tolerance
			if dist < min_dist and dist > 0:
				overlap = min_dist - dist
				push_x_total += (dx / dist) * overlap * 0.5
				push_y_total += (dy / dist) * overlap * 0.5
			elif dist == 0:
				push_x_total += random.uniform(-1, 1)
				push_y_total += random.uniform(-1, 1)

		self.rect.x += push_x_total
		self.rect.y += push_y_total

	def collide_w_blocks(self, direction):
		return super().collide_w_blocks(direction)
	def collide_w_bullets(self):
		return super().collide_w_bullets()
	def update(self, dt):
		super().update(dt)
		self.soft_collide_w_enemies()
		if self.direction.magnitude() != 0:
			self.animate(dt)

class WeaponSprite(pygame.sprite.Sprite):
	def __init__(self, game, player):
		self.game = game
		self.player = player
		self.groups = game.all_sprites
		pygame.sprite.Sprite.__init__(self, self.groups)
		self.image = pygame.Surface((WEAPON_ICON_SIZE, WEAPON_ICON_SIZE), pygame.SRCALPHA)
		self.rect = self.image.get_rect(center=player.rect.center)

	def current_icon(self):
		key = self.player.weapon_keys[self.player.weapon_index]
		icon = self.game.weapon_icons.get(key)
		if icon is not None:
			return icon
		fallback = pygame.Surface((WEAPON_ICON_SIZE, WEAPON_ICON_SIZE), pygame.SRCALPHA)
		pygame.draw.rect(fallback, WEAPON_DATA[key]["colour"], fallback.get_rect(), border_radius=WEAPON_ICON_CORNER_RADIUS)
		return fallback

	def update(self, dt):
		mouse_screen_pos = pygame.mouse.get_pos()
		world_mouse_pos = pygame.math.Vector2(mouse_screen_pos) + self.game.all_sprites.offset
		player_center = pygame.math.Vector2(self.player.rect.center)
		direction = world_mouse_pos - player_center
		if direction.magnitude() != 0:
			direction = direction.normalize()

		angle = direction.angle_to(pygame.math.Vector2(1, 0))
		self.image = pygame.transform.rotate(self.current_icon(), angle)
		self.rect = self.image.get_rect(center=player_center + direction * WEAPON_ORBIT_RADIUS)

class Block(pygame.sprite.Sprite):
	def __init__(self, game, x, y):
		self.game = game
		self.groups = game.ground_sprites, game.blocks
		pygame.sprite.Sprite.__init__(self, self.groups)
		self.x = x * TILE_SIZE
		self.y = y * TILE_SIZE
		self.width = TILE_SIZE
		self.height = TILE_SIZE
		self.image = pygame.Surface([self.width, self.height])
		self.image.fill("black")
		self.rect = self.image.get_rect()
		self.rect.x = self.x
		self.rect.y = self.y

class Ground(pygame.sprite.Sprite):
	def __init__(self, game, x, y, tile_key):
		self.game = game
		self.groups = game.ground_sprites
		pygame.sprite.Sprite.__init__(self, self.groups)
		self.x = x * TILE_SIZE
		self.y = y * TILE_SIZE
		self.width = TILE_SIZE
		self.height = TILE_SIZE
		sprite_x, sprite_y = GROUND_SPRITE_COORDS[tile_key]
		self.image = self.game.ground_sprite_sheet.get_sprite(sprite_x, sprite_y, self.width, self.height)
		self.rect = self.image.get_rect()
		self.rect.x = self.x
		self.rect.y = self.y

class Bullet(pygame.sprite.Sprite):
	def __init__(self, game, player, direction, damage, speed, pierce=0, explosive=False):
		self.game = game
		self.groups = game.all_sprites, game.bullets
		pygame.sprite.Sprite.__init__(self, self.groups)
		self.image = pygame.Surface((16, 16))
		self.image.fill("yellow")
		self.direction = direction
		self.damage = damage
		self.pierce_remaining = pierce
		self.explosive = explosive
		spawn = pygame.math.Vector2(player.rect.center) + self.direction * 20
		self.rect = self.image.get_rect(center=spawn)
		self.speed = speed
		self.spawn_time = pygame.time.get_ticks()
		self.lifetime = 1000

	def reward_kill(self):
		self.game.player.money += ENEMY_KILL_REWARD
		self.game.kill_count += 1
		if self.game.player.lifesteal_amount > 0:
			self.game.player.health = min(self.game.player.max_health, self.game.player.health + self.game.player.lifesteal_amount)

	def apply_explosion_damage(self, origin_enemy):
		for enemy in self.game.enemies:
			if enemy is origin_enemy:
				continue
			distance = pygame.math.Vector2(enemy.rect.center).distance_to(origin_enemy.rect.center)
			if distance <= EXPLOSIVE_ROUNDS_RADIUS:
				enemy.health -= EXPLOSIVE_ROUNDS_DAMAGE
				if enemy.health <= 0:
					enemy.kill()
					self.reward_kill()

	def check_hit(self):
		hit_enemies = pygame.sprite.spritecollide(self, self.game.enemies, False)
		for enemy in hit_enemies:
			enemy.health -= self.damage
			if self.explosive:
				self.apply_explosion_damage(enemy)
			if enemy.health <= 0:
				enemy.kill()
				self.reward_kill()
			if self.pierce_remaining > 0:
				self.pierce_remaining -= 1
			else:
				self.kill()
			break

	def collide_w_blocks(self, direction):
		if direction == 'x':
			hit = pygame.sprite.spritecollide(self, self.game.blocks, False)
			if hit:
				if self.direction.x > 0:
					self.rect.x = hit[0].rect.left - self.rect.width
				if self.direction.x < 0:
					self.rect.x = hit[0].rect.right
		if direction == 'y':
			hit = pygame.sprite.spritecollide(self, self.game.blocks, False)
			if hit:
				if self.direction.y > 0:
					self.rect.y = hit[0].rect.top - self.rect.height
				if self.direction.y < 0:
					self.rect.y = hit[0].rect.bottom

	def update(self, dt):
		self.rect.x += self.direction.x * self.speed * dt
		self.rect.y += self.direction.y * self.speed * dt
		self.check_hit()
		if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
			self.kill()

class Button:
	def __init__(self, image_path, x, y, scale=1.0):
		image = pygame.image.load(image_path).convert_alpha()
		width = int(image.get_width() * scale)
		height = int(image.get_height() * scale)
		self.image = pygame.transform.scale(image, (width, height))
		self.hover_image = pygame.transform.scale(self.image, (int(width * 1.08), int(height * 1.08)))
		self.rect = self.image.get_rect(center=(x, y))
		self.hovered = False

	def update(self, mouse_pos):
		self.hovered = self.rect.collidepoint(mouse_pos)

	def draw(self, surface):
		if self.hovered:
			img = self.hover_image
			rect = img.get_rect(center=self.rect.center)
		else:
			img = self.image
			rect = self.rect
		surface.blit(img, rect)

	def clicked(self, event):
		return (
			event.type == pygame.MOUSEBUTTONDOWN
			and event.button == 1
			and self.rect.collidepoint(event.pos)
		)


class TextButton:
	def __init__(self, text, x, y, width, height, font, base_colour="#2B2B3A", hover_colour="#63A375"):
		self.text = text
		self.rect = pygame.Rect(0, 0, width, height)
		self.rect.center = (x, y)
		self.font = font
		self.base_colour = base_colour
		self.hover_colour = hover_colour
		self.hovered = False

	def update(self, mouse_pos):
		self.hovered = self.rect.collidepoint(mouse_pos)

	def draw(self, surface):
		colour = self.hover_colour if self.hovered else self.base_colour
		pygame.draw.rect(surface, colour, self.rect, border_radius=8)
		pygame.draw.rect(surface, "white", self.rect, width=2, border_radius=8)
		text_surf = self.font.render(self.text, True, "white")
		surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

	def clicked(self, event):
		return (
			event.type == pygame.MOUSEBUTTONDOWN
			and event.button == 1
			and self.rect.collidepoint(event.pos)
		)


class InputBox:
	def __init__(self, x, y, width, height, font, placeholder="", is_password=False, max_length=24):
		self.rect = pygame.Rect(0, 0, width, height)
		self.rect.center = (x, y)
		self.font = font
		self.text = ""
		self.placeholder = placeholder
		self.is_password = is_password
		self.max_length = max_length
		self.active = False

	def handle_event(self, event):
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			self.active = self.rect.collidepoint(event.pos)
		elif event.type == pygame.KEYDOWN and self.active:
			if event.key == pygame.K_BACKSPACE:
				self.text = self.text[:-1]
			elif event.key in (pygame.K_RETURN, pygame.K_TAB):
				pass
			elif len(self.text) < self.max_length and event.unicode.isprintable():
				self.text += event.unicode

	def draw(self, surface):
		background_colour = "white" if self.active else "#D8D8D8"
		pygame.draw.rect(surface, background_colour, self.rect, border_radius=6)
		pygame.draw.rect(surface, "black", self.rect, width=2, border_radius=6)
		display_text = ("*" * len(self.text)) if self.is_password else self.text
		if display_text:
			text_surf = self.font.render(display_text, True, "black")
		else:
			text_surf = self.font.render(self.placeholder, True, "#777777")
		surface.blit(text_surf, (self.rect.x + 12, self.rect.centery - text_surf.get_height() // 2))
