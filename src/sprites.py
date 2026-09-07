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

	def getSprite(self, x, y, width, height):
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

	def customDraw(self, player):
		self.center_target_camera(player)
		self.display_surface.fill("#73D8E7")

		for sprite in self.game.groundSprites:
			offset_pos = sprite.rect.topleft - self.offset
			self.display_surface.blit(sprite.image, offset_pos)

		for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
			image_rect = sprite.image.get_rect(center=sprite.rect.center)
			offset_pos = image_rect.topleft - self.offset
			self.display_surface.blit(sprite.image, offset_pos)


class Player(pygame.sprite.Sprite):
	def __init__(self, game, x, y):

		self.game = game
		self.groups = game.allSprites
		pygame.sprite.Sprite.__init__(self, game.allSprites)
		self.x = x * TileSize
		self.y = y * TileSize
		self.direction = pygame.math.Vector2()
		self.width = TileSize
		self.height = TileSize
		self.looking = "down"
		sprite_scale = 2
		self.image = pygame.Surface([int(TileSize * sprite_scale)] * 2, pygame.SRCALPHA)
		playerImg = pygame.image.load("images/Player1.png").convert_alpha()
		playerImg = pygame.transform.scale(playerImg, self.image.get_size())
		self.image.blit(playerImg, (0, 0))
		self.rect = pygame.Rect(0, 0, self.width, self.height) 
		self.rect.x = self.x
		self.rect.y = self.y
		self.health = PlayerBaseHealth
		self.max_health = PlayerBaseHealth
		self.speed = 350
		self.damage = PlayerBaseDamage
		self.money = StartingMoney
		self.extra_bullets = 0
		self.bullet_pierce = 0
		self.explosive_rounds = False
		self.lifesteal_amount = 0
		self.shield_charges = 0
		self.hit_invulnerability_ms = DefaultHitInvulnerabilityMs
		self.chosen_upgrades = []
		self.last_attack_time = 0
		self.attack_cooldown_multiplier = 1.0
		self.weapon_keys = list(WeaponData.keys())
		self.weapon_index = 0
		self.last_weapon_switch_time = 0

	def move(self):
		Key = pygame.key.get_pressed()
		self.direction.x = 0
		self.direction.y = 0
		if Key[pygame.K_w]:
			self.direction.y = -1
			self.looking = "up"
		if Key[pygame.K_s]:
			self.direction.y = 1
			self.looking = "down"
		if Key[pygame.K_a]:
			self.direction.x = -1
			self.looking = "left"
		if Key[pygame.K_d]:
			self.direction.x = 1
			self.looking = "right"
		if Key[pygame.K_ESCAPE]:
			self.game.playing = False
		if self.direction.magnitude() != 0:
			self.direction = self.direction.normalize()

	def currentWeapon(self):
		return WeaponData[self.weapon_keys[self.weapon_index]]

	def switchWeapon(self):
		now = pygame.time.get_ticks()
		if now - self.last_weapon_switch_time < WeaponSwitchCooldownMs:
			return
		self.weapon_index = (self.weapon_index + 1) % len(self.weapon_keys)
		self.last_weapon_switch_time = now

	def shoot(self):
		now = pygame.time.get_ticks()
		weapon = self.currentWeapon()
		cooldown = weapon["cooldown"] * self.attack_cooldown_multiplier
		if now - self.last_attack_time < cooldown:
			return
		mouse_screen_pos = pygame.mouse.get_pos()
		world_mouse_pos = pygame.math.Vector2(mouse_screen_pos) + self.game.allSprites.offset
		base_direction = world_mouse_pos - pygame.math.Vector2(self.rect.center)
		if base_direction.magnitude() != 0:
			base_direction = base_direction.normalize()
		total_bullets = weapon["bullet_count"] + self.extra_bullets
		spread_angle = weapon["spread_degrees"] if weapon["spread_degrees"] > 0 else TwinShotAngleOffsetDegrees
		spread_start = -(total_bullets - 1) * spread_angle / 2
		bullet_damage = self.damage * weapon["damage_multiplier"]
		for i in range(total_bullets):
			angle = spread_start + i * spread_angle
			Bullet(self.game, self, base_direction.rotate(angle), bullet_damage, weapon["bullet_speed"], self.bullet_pierce, self.explosive_rounds)
		self.last_attack_time = now

	def collideWBlocks(self, direction):
		if direction == 'x':
			Hit = pygame.sprite.spritecollide(self, self.game.blocks, False)
			if Hit:
				if self.direction.x > 0:
					self.rect.x = Hit[0].rect.left - self.rect.width
				if self.direction.x < 0:
					self.rect.x = Hit[0].rect.right
		if direction == 'y':
			Hit = pygame.sprite.spritecollide(self, self.game.blocks, False)
			if Hit:
				if self.direction.y > 0:
					self.rect.y = Hit[0].rect.top - self.rect.height
				if self.direction.y < 0:
					self.rect.y = Hit[0].rect.bottom

	def collideWEnemies(self):
		Hit = [s for s in pygame.sprite.spritecollide(self, self.game.enemies, False) if s is not self]
		if Hit:
			self.takeDamage()

	def collideWBullets(self):
			Hit = pygame.sprite.spritecollide(self, self.game.bullets, True)
			if Hit:
				self.takeDamage()

	def takeDamage(self):
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
		self.collideWBlocks('x')
		self.rect.y += self.direction.y * self.speed * dt
		self.collideWBlocks('y')
		self.collideWEnemies()

class Enemy(Player):
	def __init__(self, game, x, y):
		super().__init__(game, x, y)
		self.groups = game.allSprites, game.enemies
		game.enemies.add(self)
		self.speed = 90
		self.health = 3
		self.rect = pygame.Rect(0, 0, self.width, self.height)
		self.rect.x = self.x
		self.rect.y = self.y
		sheet = game.ZombieSpriteSheet.sheet
		frame_count = 4
		frame_width = sheet.get_width() // frame_count
		frame_height = sheet.get_height()
		sprite_scale = 1.5
		img_size = int(TileSize * sprite_scale)

		self.frames = []
		for i in range(frame_count):
			frame = game.ZombieSpriteSheet.getSprite(i * frame_width, 0, frame_width, frame_height)
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

	def collideWEnemies(self):
		pass

	def softCollideWEnemies(self, overlap_tolerance=8):
		Hit = [s for s in pygame.sprite.spritecollide(self, self.game.enemies, False) if s is not self]
		if not Hit:
			return
		push_x_total = 0
		push_y_total = 0

		for other in Hit:
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

	def collideWBlocks(self, direction):
		return super().collideWBlocks(direction)
	def collideWBullets(self):
		return super().collideWBullets()
	def update(self, dt):
		super().update(dt)
		self.softCollideWEnemies()
		if self.direction.magnitude() != 0:
			self.animate(dt)

class WeaponSprite(pygame.sprite.Sprite):
	def __init__(self, game, player):
		self.game = game
		self.player = player
		self.groups = game.allSprites
		pygame.sprite.Sprite.__init__(self, self.groups)
		self.image = pygame.Surface((WeaponIconSize, WeaponIconSize), pygame.SRCALPHA)
		self.rect = self.image.get_rect(center=player.rect.center)

	def currentIcon(self):
		key = self.player.weapon_keys[self.player.weapon_index]
		icon = self.game.weaponIcons.get(key)
		if icon is not None:
			return icon
		fallback = pygame.Surface((WeaponIconSize, WeaponIconSize), pygame.SRCALPHA)
		pygame.draw.rect(fallback, WeaponData[key]["colour"], fallback.get_rect(), border_radius=WeaponIconCornerRadius)
		return fallback

	def update(self, dt):
		mouse_screen_pos = pygame.mouse.get_pos()
		world_mouse_pos = pygame.math.Vector2(mouse_screen_pos) + self.game.allSprites.offset
		player_center = pygame.math.Vector2(self.player.rect.center)
		direction = world_mouse_pos - player_center
		if direction.magnitude() != 0:
			direction = direction.normalize()

		angle = direction.angle_to(pygame.math.Vector2(1, 0))
		self.image = pygame.transform.rotate(self.currentIcon(), angle)
		self.rect = self.image.get_rect(center=player_center + direction * WeaponOrbitRadius)

class Block(pygame.sprite.Sprite):
	def __init__(self, game, x, y):
		self.game = game
		self.groups = game.groundSprites, game.blocks
		pygame.sprite.Sprite.__init__(self, self.groups)
		self.x = x * TileSize
		self.y = y * TileSize
		self.width = TileSize
		self.height = TileSize
		self.image = pygame.Surface([self.width, self.height])
		self.image.fill("black")
		self.rect = self.image.get_rect()
		self.rect.x = self.x
		self.rect.y = self.y

class Ground(pygame.sprite.Sprite):
	def __init__(self, game, x, y, tile_key):
		self.game = game
		self.groups = game.groundSprites
		pygame.sprite.Sprite.__init__(self, self.groups)
		self.x = x * TileSize
		self.y = y * TileSize
		self.width = TileSize
		self.height = TileSize
		sprite_x, sprite_y = GroundSpriteCoords[tile_key]
		self.image = self.game.GroundSpriteSheet.getSprite(sprite_x, sprite_y, self.width, self.height)
		self.rect = self.image.get_rect()
		self.rect.x = self.x
		self.rect.y = self.y

class Bullet(pygame.sprite.Sprite):
	def __init__(self, game, player, direction, damage, speed, pierce=0, explosive=False):
		self.game = game
		self.groups = game.allSprites, game.bullets
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
		self.spawnTime = pygame.time.get_ticks()
		self.lifetime = 1000

	def rewardKill(self):
		self.game.player.money += EnemyKillReward
		self.game.killCount += 1
		if self.game.player.lifesteal_amount > 0:
			self.game.player.health = min(self.game.player.max_health, self.game.player.health + self.game.player.lifesteal_amount)

	def applyExplosionDamage(self, origin_enemy):
		for enemy in self.game.enemies:
			if enemy is origin_enemy:
				continue
			distance = pygame.math.Vector2(enemy.rect.center).distance_to(origin_enemy.rect.center)
			if distance <= ExplosiveRoundsRadius:
				enemy.health -= ExplosiveRoundsDamage
				if enemy.health <= 0:
					enemy.kill()
					self.rewardKill()

	def checkHit(self):
		hitEnemies = pygame.sprite.spritecollide(self, self.game.enemies, False)
		for enemy in hitEnemies:
			enemy.health -= self.damage
			if self.explosive:
				self.applyExplosionDamage(enemy)
			if enemy.health <= 0:
				enemy.kill()
				self.rewardKill()
			if self.pierce_remaining > 0:
				self.pierce_remaining -= 1
			else:
				self.kill()
			break

	def collideWBlocks(self, direction):
		if direction == 'x':
			Hit = pygame.sprite.spritecollide(self, self.game.blocks, False)
			if Hit:
				if self.direction.x > 0:
					self.rect.x = Hit[0].rect.left - self.rect.width
				if self.direction.x < 0:
					self.rect.x = Hit[0].rect.right
		if direction == 'y':
			Hit = pygame.sprite.spritecollide(self, self.game.blocks, False)
			if Hit:
				if self.direction.y > 0:
					self.rect.y = Hit[0].rect.top - self.rect.height
				if self.direction.y < 0:
					self.rect.y = Hit[0].rect.bottom

	def update(self, dt):
		self.rect.x += self.direction.x * self.speed * dt
		self.rect.y += self.direction.y * self.speed * dt
		self.checkHit()
		if pygame.time.get_ticks() - self.spawnTime > self.lifetime:
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

	def handleEvent(self, event):
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