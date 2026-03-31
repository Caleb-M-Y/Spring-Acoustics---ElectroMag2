from machine import Pin
import random
import time
from neopixel import Neopixel


# Buttons
button_mode = Pin(7, Pin.IN, Pin.PULL_UP)
button_brightness = Pin(6, Pin.IN, Pin.PULL_UP)

# LED strip hardware (same map as OG_LED_YUH.py)
LEDS_PER_STRIP = [10, 10, 10, 10, 10, 10]
GPIO_PINS = [20, 21, 2, 3, 4, 5]
STATE_MACHINES = [0, 1, 2, 3, 4, 5]

strips = [
	Neopixel(count, sm, pin, "GRB")
	for count, sm, pin in zip(LEDS_PER_STRIP, STATE_MACHINES, GPIO_PINS)
]

TOTAL_LEDS = sum(LEDS_PER_STRIP)


# Persistent state for advanced effects
fire_heat = [[0 for _ in range(count)] for count in LEDS_PER_STRIP]
fireworks_rockets = []
fireworks_sparks = []


def set_brightness(level):
	for strip in strips:
		strip.brightness(level)


def show_all():
	for strip in strips:
		strip.show()


def clear_all():
	for strip in strips:
		strip.fill((0, 0, 0))
	show_all()


def fill_all(color):
	for strip in strips:
		strip.fill(color)
	show_all()


def wheel(pos):
	# Classic color wheel (0-255 -> RGB)
	pos = pos % 256
	if pos < 85:
		return (255 - pos * 3, pos * 3, 0)
	if pos < 170:
		pos -= 85
		return (0, 255 - pos * 3, pos * 3)
	pos -= 170
	return (pos * 3, 0, 255 - pos * 3)


def heat_to_rgb(heat):
	# heat: 0-255 mapped to black -> red -> orange -> yellow -> white
	heat = max(0, min(255, heat))
	if heat < 85:
		return (heat * 3, 0, 0)
	if heat < 170:
		heat -= 85
		return (255, heat * 3, 0)
	heat -= 170
	return (255, 255, min(255, heat * 3))


def boot_sequence(frame):
	# Strips "boot" one by one in cyan, then settle to dim blue.
	active_strip = (frame // 4) % len(strips)
	step = frame % 4

	for strip_idx, strip in enumerate(strips):
		for led in range(LEDS_PER_STRIP[strip_idx]):
			if strip_idx < active_strip:
				strip.set_pixel(led, (0, 30, 120))
			elif strip_idx == active_strip and led <= step * 2:
				strip.set_pixel(led, (0, 180, 255))
			else:
				strip.set_pixel(led, (0, 0, 0))
	show_all()


def eye_scanner(frame):
	# A red "eye" sweeps left/right with a soft tail.
	width = LEDS_PER_STRIP[0]
	span = (width - 1) * 2
	p = frame % span
	head = p if p < width else span - p

	for strip_idx, strip in enumerate(strips):
		strip.fill((0, 0, 0))
		color_boost = 45 * (strip_idx % 2)
		for t in range(4):
			pos = head - t
			if 0 <= pos < LEDS_PER_STRIP[strip_idx]:
				power = 255 // (t + 1)
				strip.set_pixel(pos, (power, color_boost, 0))
		for t in range(1, 3):
			pos = head + t
			if 0 <= pos < LEDS_PER_STRIP[strip_idx]:
				power = 120 // (t + 1)
				strip.set_pixel(pos, (power, color_boost // 2, 0))
	show_all()


def servo_pulse(frame):
	# Mechanical pulse in cool tones, alternating strip phase.
	phase = frame % 40
	if phase < 20:
		amp = phase
	else:
		amp = 40 - phase

	for strip_idx, strip in enumerate(strips):
		strip_amp = amp if strip_idx % 2 == 0 else 20 - abs(10 - amp)
		strip_amp = max(0, strip_amp)
		for led in range(LEDS_PER_STRIP[strip_idx]):
			led_wave = (strip_amp * (led + 2)) // LEDS_PER_STRIP[strip_idx]
			strip.set_pixel(led, (0, led_wave * 4, 40 + led_wave * 8))
	show_all()


def glitch_storm(frame):
	# Randomized short bursts with occasional white glitch flashes.
	for strip_idx, strip in enumerate(strips):
		for led in range(LEDS_PER_STRIP[strip_idx]):
			noise = random.randint(0, 100)
			if noise < 8:
				strip.set_pixel(led, (255, 255, 255))
			elif noise < 40:
				strip.set_pixel(led, (0, random.randint(100, 255), random.randint(80, 200)))
			elif noise < 65:
				strip.set_pixel(led, (random.randint(120, 255), 0, 0))
			else:
				strip.set_pixel(led, (0, 0, 0))

		if frame % 13 == 0:
			strip.fill((255, 255, 255))
	show_all()


def plasma_storm(frame):
	# Loud, high-energy plasma ribbons with occasional all-strip flashes.
	for strip_idx, strip in enumerate(strips):
		for led in range(LEDS_PER_STRIP[strip_idx]):
			virtual_pos = strip_idx * LEDS_PER_STRIP[strip_idx] + led
			hue = (virtual_pos * 5 + frame * 13 + strip_idx * 27) % 256
			color = wheel(hue)
			boost = (frame + led * 3 + strip_idx * 7) % 18
			if boost > 14:
				r, g, b = color
				color = (min(255, r + 80), min(255, g + 80), min(255, b + 80))
			strip.set_pixel(led, color)

	if frame % 37 == 0:
		for strip_idx, strip in enumerate(strips):
			for led in range(LEDS_PER_STRIP[strip_idx]):
				if random.randint(0, 100) < 30:
					strip.set_pixel(led, (255, 255, 255))

	show_all()


def show_fire_effect(frame):
	# Rebuilt inferno effect with heat diffusion, sparks, embers, and rare blue-white blowtorches.
	for strip_idx, strip in enumerate(strips):
		heat = fire_heat[strip_idx]
		count = LEDS_PER_STRIP[strip_idx]

		# 1) Cool each cell randomly.
		for i in range(count):
			cooling = random.randint(0, 28 + strip_idx * 2)
			heat[i] = max(0, heat[i] - cooling)

		# 2) Diffuse heat upward.
		for k in range(count - 1, 1, -1):
			heat[k] = (heat[k - 1] + heat[k - 2] + heat[k - 2]) // 3

		# 3) Spawn new sparks at the base.
		if random.randint(0, 255) < 170:
			spark_y = random.randint(0, 1)
			heat[spark_y] = min(255, heat[spark_y] + random.randint(160, 255))

		# Occasional violent jet for extra drama.
		if random.randint(0, 1000) < 25:
			heat[0] = 255
			if count > 1:
				heat[1] = min(255, heat[1] + 120)

		# 4) Render with ember shimmer and occasional torch-blue tip.
		for i in range(count):
			base = heat_to_rgb(heat[i])
			r, g, b = base

			# Ember flicker in lower half.
			if i < count // 2 and random.randint(0, 100) < 25:
				r = min(255, r + random.randint(10, 50))
				g = min(255, g + random.randint(0, 25))

			# Hot tip occasionally shifts to blowtorch white-blue.
			if i >= count - 2 and heat[i] > 220 and random.randint(0, 100) < 35:
				r = 220
				g = 230
				b = 255

			strip.set_pixel(i, (r, g, b))

	show_all()


def spawn_firework_rocket():
	# Launch rocket from a random strip, near the bottom.
	strip_idx = random.randint(0, len(strips) - 1)
	color = random.choice([
		(255, 80, 30),
		(255, 255, 120),
		(140, 255, 255),
		(255, 120, 255),
		(120, 255, 140),
	])
	start_pos = LEDS_PER_STRIP[strip_idx] - 1
	peak = random.randint(1, 4)
	# (strip, pos_float, velocity, color, peak)
	fireworks_rockets.append([strip_idx, float(start_pos), -0.85, color, peak])


def explode_firework(strip_idx, center_pos, base_color, mega=False):
	# Create a spherical-looking blast with particles on this and adjacent strips.
	spread = 2 if mega else 1
	particle_count = 26 if mega else 16

	for _ in range(particle_count):
		target_strip = strip_idx + random.randint(-spread, spread)
		if target_strip < 0 or target_strip >= len(strips):
			continue

		start = float(max(0, min(LEDS_PER_STRIP[target_strip] - 1, int(center_pos))))
		velocity = random.uniform(-0.8, 0.9)
		age_max = random.randint(12, 22 if mega else 18)
		drift = random.uniform(-0.25, 0.25)

		if random.randint(0, 100) < 35:
			color = wheel(random.randint(0, 255))
		else:
			color = base_color

		# (strip, pos_float, velocity, drift, color, age, age_max)
		fireworks_sparks.append([target_strip, start, velocity, drift, color, 0, age_max])


def ultimate_firework_show(frame):
	# Big rockets, bloom explosions, glitter embers, and occasional full-sky finales.
	for strip_idx, strip in enumerate(strips):
		for led in range(LEDS_PER_STRIP[strip_idx]):
			strip.set_pixel(led, (0, 0, 0))

	# Random launches keep action continuous.
	if len(fireworks_rockets) < 4 and random.randint(0, 100) < 35:
		spawn_firework_rocket()

	# Periodic mega finale.
	if frame % 140 == 0:
		mid = random.randint(1, len(strips) - 2)
		explode_firework(mid, random.randint(2, 4), wheel(random.randint(0, 255)), mega=True)

	# Update rockets.
	new_rockets = []
	for rocket in fireworks_rockets:
		strip_idx, pos, vel, color, peak = rocket

		# Draw bright head + short tail.
		head = int(pos)
		if 0 <= head < LEDS_PER_STRIP[strip_idx]:
			strips[strip_idx].set_pixel(head, color)
			if head + 1 < LEDS_PER_STRIP[strip_idx]:
				r, g, b = color
				strips[strip_idx].set_pixel(head + 1, (r // 4, g // 4, b // 4))
			if head + 2 < LEDS_PER_STRIP[strip_idx]:
				r, g, b = color
				strips[strip_idx].set_pixel(head + 2, (r // 10, g // 10, b // 10))

		pos += vel
		vel += 0.025  # gravity slows upward motion

		if pos <= peak:
			explode_firework(strip_idx, pos, color, mega=False)
		else:
			new_rockets.append([strip_idx, pos, vel, color, peak])

	fireworks_rockets[:] = new_rockets

	# Update sparks.
	new_sparks = []
	for spark in fireworks_sparks:
		strip_idx, pos, vel, drift, color, age, age_max = spark
		age += 1
		pos += vel
		vel += 0.07  # falling

		# Drift to nearby strips during life.
		if random.randint(0, 100) < 20:
			strip_idx += -1 if drift < 0 else 1
			strip_idx = max(0, min(len(strips) - 1, strip_idx))

		if age < age_max:
			p = int(pos)
			if 0 <= p < LEDS_PER_STRIP[strip_idx]:
				fade = (age_max - age) / age_max
				r, g, b = color
				r = int(r * fade)
				g = int(g * fade)
				b = int(b * fade)

				# Glitter points near end of life.
				if age > age_max - 5 and random.randint(0, 100) < 30:
					r = 255
					g = 255
					b = 255

				strips[strip_idx].set_pixel(p, (r, g, b))
				new_sparks.append([strip_idx, pos, vel, drift, color, age, age_max])

	fireworks_sparks[:] = new_sparks
	show_all()


def rainbow_tread(frame):
	# Rainbow appears like moving tank treads across the 6 strips.
	for strip_idx, strip in enumerate(strips):
		for led in range(LEDS_PER_STRIP[strip_idx]):
			virtual_pos = strip_idx * LEDS_PER_STRIP[strip_idx] + led
			hue = (virtual_pos * 256 // TOTAL_LEDS + frame * 5) % 256
			strip.set_pixel(led, wheel(hue))
	show_all()


def alarm_bars(frame):
	# Red/blue emergency bars sweeping in opposite directions.
	width = LEDS_PER_STRIP[0]
	left = frame % width
	right = (width - 1) - (frame % width)

	for strip_idx, strip in enumerate(strips):
		strip.fill((0, 0, 0))
		if strip_idx < len(strips) // 2:
			strip.set_pixel(left, (255, 0, 0))
			if left > 0:
				strip.set_pixel(left - 1, (70, 0, 0))
		else:
			strip.set_pixel(right, (0, 0, 255))
			if right < width - 1:
				strip.set_pixel(right + 1, (0, 0, 70))
	show_all()


def idle_breath(frame):
	# Robot idle glow in blue-violet.
	phase = frame % 80
	if phase < 40:
		level = phase
	else:
		level = 80 - phase

	r = 10 + level * 2
	g = 0
	b = 20 + level * 5
	fill_all((r, g, b))


def mode_indicator_flash(mode_idx):
	# Quick visual cue after mode change.
	base = wheel((mode_idx * 31) % 256)
	for _ in range(2):
		fill_all(base)
		time.sleep(0.06)
		clear_all()
		time.sleep(0.05)


MODES = [
	("IDLE", idle_breath, 0.035),
	("BOOT", boot_sequence, 0.055),
	("EYE", eye_scanner, 0.03),
	("SERVO", servo_pulse, 0.03),
	("GLITCH", glitch_storm, 0.065),
	("PLASMA", plasma_storm, 0.028),
	("INFERNO", show_fire_effect, 0.05),
	("RAINBOW", rainbow_tread, 0.03),
	("ALARM", alarm_bars, 0.055),
	("ULTIMATE FIREWORK SHOW", ultimate_firework_show, 0.04),
]


# Startup state
mode_index = 0
frame = 0
brightness = 90
brightness_dir = 1
last_mode_state = 1
last_brightness_state = 1

set_brightness(brightness)
clear_all()


while True:
	mode_state = button_mode.value()
	if mode_state == 0 and last_mode_state == 1:
		mode_index = (mode_index + 1) % len(MODES)
		frame = 0
		fireworks_rockets[:] = []
		fireworks_sparks[:] = []
		clear_all()
		mode_indicator_flash(mode_index)
		time.sleep(0.2)
	last_mode_state = mode_state

	bright_state = button_brightness.value()
	if bright_state == 0 and last_brightness_state == 1:
		brightness += 30 * brightness_dir
		if brightness >= 255:
			brightness = 255
			brightness_dir = -1
		elif brightness <= 10:
			brightness = 10
			brightness_dir = 1
		set_brightness(brightness)
		time.sleep(0.2)
	last_brightness_state = bright_state

	_, effect_fn, delay = MODES[mode_index]
	effect_fn(frame)
	frame = (frame + 1) % 10000
	time.sleep(delay)
