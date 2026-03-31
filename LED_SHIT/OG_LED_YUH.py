#save this as the main.py file with button integration
#make to sure have neopixel.py downloaded to the pico 

from machine import Pin
import time
import random
from neopixel import Neopixel

# --- Defined colors ---
colors_rgb = {
    'red': (255, 0, 0),
    'orange': (255, 50, 0),
    'yellow': (255, 255, 0),
    'green': (0, 255, 0),
    'blue': (0, 0, 255),
    'violet': (200, 0, 100),
    'white': (255, 255, 255),
    'blank': (0, 0, 0)
}
color_names = ['red', 'orange', 'yellow', 'green', 'blue', 'violet', 'white']
num_modes = len(color_names) + 18  # +1 multi-color, +1 UCA, +14 effects, +4 new effects

# --- Button setup ---
button_color = Pin(7, Pin.IN, Pin.PULL_UP)      # GP7 - cycle colors
button_brightness = Pin(6, Pin.IN, Pin.PULL_UP) # GP6 - adjust brightness

# --- LED strip setup ---
num_leds_for_each_strip = [10, 10, 10, 10, 10, 10]
gpio_pins = [20, 21, 2, 3, 4, 5]  # GPIOs connected to LED data lines
state_machines = [0, 1, 2, 3, 4, 5]
brightness = 10

# Initialize each strip with its own pin and state machine
strips = [
    Neopixel(num_leds, sm, pin, "GRB")
    for num_leds, sm, pin in zip(num_leds_for_each_strip, state_machines, gpio_pins)
]

for strip in strips:
    strip.brightness(brightness)

# --- Control logic ---
mode_index = 0  # 0 = multi-color mode, 1-N = color from list, last = UCA mode
brightness_direction = -1  # Start by decreasing brightness
last_color_state = 1
last_brightness_state = 1

# Effect state variables
effect_frame = 0
sparkle_positions = []

def show_uca():
    for idx, strip in enumerate(strips):
        if idx % 2 == 0:
            rgb = colors_rgb['violet']
        else:
            rgb = colors_rgb['white']
        strip.fill(rgb)
        strip.show()

def show_rainbow_chase():
    """Rainbow pattern that chases across all strips"""
    global effect_frame
    for strip_idx, strip in enumerate(strips):
        for led in range(num_leds_for_each_strip[strip_idx]):
            # Create rainbow based on position and time
            hue = ((led + strip_idx * 10 + effect_frame) * 256 // 60) % 256
            rgb = hsv_to_rgb(hue, 255, 255)
            strip.set_pixel(led, rgb)
        strip.show()
    effect_frame = (effect_frame + 1) % 256

def show_pulse_wave():
    """Smooth breathing/pulsing effect with color shifting between violet, blue, and pink"""
    global effect_frame
    
    # Create smooth sine-wave pulse using effect_frame
    # This creates a value that smoothly goes from 0 -> 1 -> 0
    pulse_cycle = effect_frame % 100
    if pulse_cycle < 50:
        pulse_val = pulse_cycle / 50.0  # 0 to 1
    else:
        pulse_val = (100 - pulse_cycle) / 50.0  # 1 to 0
    
    # Apply easing for even smoother effect (quadratic ease in/out)
    if pulse_val < 0.5:
        smooth_pulse = 2 * pulse_val * pulse_val
    else:
        smooth_pulse = 1 - 2 * (1 - pulse_val) * (1 - pulse_val)
    
    # Cycle through colors: violet -> blue -> pink -> violet
    color_cycle = (effect_frame // 100) % 3
    
    if color_cycle == 0:  # Violet
        base_r, base_g, base_b = 200, 0, 255
    elif color_cycle == 1:  # Blue
        base_r, base_g, base_b = 0, 100, 255
    else:  # Pink
        base_r, base_g, base_b = 255, 0, 150
    
    # Apply pulse intensity
    r = int(base_r * smooth_pulse)
    g = int(base_g * smooth_pulse)
    b = int(base_b * smooth_pulse)
    
    for strip in strips:
        strip.fill((r, g, b))
        strip.show()
    
    effect_frame = (effect_frame + 1) % 300

def show_fire_effect():
    """Realistic flickering fire with red, orange, and yellow flames"""
    global effect_frame
    for strip_idx, strip in enumerate(strips):
        for led in range(num_leds_for_each_strip[strip_idx]):
            # Random fire color selection with weighted distribution
            fire_type = random.randint(0, 100)
            
            if fire_type < 40:  # 40% deep red/orange (base of flame)
                r = random.randint(180, 255)
                g = random.randint(20, 80)
                b = 0
            elif fire_type < 75:  # 35% bright orange (middle flame)
                r = random.randint(220, 255)
                g = random.randint(80, 140)
                b = 0
            else:  # 25% yellow-orange (tip of flame)
                r = random.randint(240, 255)
                g = random.randint(140, 200)
                b = random.randint(0, 30)
            
            # Add flickering intensity variation
            flicker = random.randint(70, 100) / 100.0
            r = int(r * flicker)
            g = int(g * flicker)
            b = int(b * flicker)
            
            strip.set_pixel(led, (r, g, b))
        strip.show()

def show_scanner():
    """Lightning storm with random strikes and chain lightning"""
    global effect_frame, sparkle_positions
    
    # Use sparkle_positions to track lightning strikes: [(strip_idx, led_idx, intensity, age), ...]
    if not isinstance(sparkle_positions, list) or effect_frame < 2:
        sparkle_positions = []
    
    # Fade all existing LEDs (afterglow effect)
    for strip_idx, strip in enumerate(strips):
        for led in range(num_leds_for_each_strip[strip_idx]):
            strip.set_pixel(led, (0, 0, 0))
    
    # Update existing lightning and fade them
    new_strikes = []
    for strike in sparkle_positions:
        if len(strike) != 4:
            continue
        strip_idx, led_idx, intensity, age = strike
        if age < 8:  # Lightning lasts for 8 frames
            # Draw the strike with blue-white color
            fade = 1.0 - (age / 8.0)
            r = int(255 * fade)
            g = int(255 * fade)
            b = int(255 * fade * 1.2)  # Slightly more blue
            
            if led_idx < num_leds_for_each_strip[strip_idx]:
                strips[strip_idx].set_pixel(led_idx, (r, g, b))
                
                # Lightning spreads to adjacent LEDs
                if led_idx > 0 and fade > 0.3:
                    strips[strip_idx].set_pixel(led_idx - 1, (r//2, g//2, b//2))
                if led_idx < num_leds_for_each_strip[strip_idx] - 1 and fade > 0.3:
                    strips[strip_idx].set_pixel(led_idx + 1, (r//2, g//2, b//2))
            
            new_strikes.append((strip_idx, led_idx, intensity, age + 1))
    
    sparkle_positions = new_strikes
    
    # Random chance to spawn new lightning strikes
    if random.randint(0, 100) < 35:  # 35% chance per frame
        strip_idx = random.randint(0, len(strips) - 1)
        led_idx = random.randint(0, num_leds_for_each_strip[strip_idx] - 1)
        intensity = random.randint(200, 255)
        sparkle_positions.append((strip_idx, led_idx, intensity, 0))
        
        # Chance for chain lightning (hits adjacent strip)
        if random.randint(0, 100) < 40:
            chain_strip = strip_idx + random.choice([-1, 1])
            if 0 <= chain_strip < len(strips):
                chain_led = led_idx + random.randint(-2, 2)
                chain_led = max(0, min(chain_led, num_leds_for_each_strip[chain_strip] - 1))
                sparkle_positions.append((chain_strip, chain_led, intensity, 1))
    
    # Occasional multi-strip flash (big strike)
    if effect_frame % 50 == 0 and random.randint(0, 100) < 30:
        flash_strip = random.randint(0, len(strips) - 1)
        # Full strip flash
        for led in range(num_leds_for_each_strip[flash_strip]):
            sparkle_positions.append((flash_strip, led, 255, 0))
    
    for strip in strips:
        strip.show()
    
    effect_frame = (effect_frame + 1) % 1000

def show_sparkle():
    """Random twinkling stars effect with fading"""
    global sparkle_positions, effect_frame
    
    # Track sparkles with fade: [(strip, led, color, age), ...]
    if not isinstance(sparkle_positions, list) or effect_frame == 0:
        sparkle_positions = []
    
    # Fade all LEDs
    for strip in strips:
        strip.fill((0, 0, 0))
    
    # Update existing sparkles with fade
    new_sparkles = []
    for sparkle in sparkle_positions:
        strip_idx, led_idx, color, age = sparkle
        if age < 6:  # Sparkle lasts 6 frames
            fade = 1.0 - (age / 6.0)
            r, g, b = color
            faded = (int(r * fade), int(g * fade), int(b * fade))
            strips[strip_idx].set_pixel(led_idx, faded)
            new_sparkles.append((strip_idx, led_idx, color, age + 1))
    
    sparkle_positions = new_sparkles
    
    # Add new sparkles randomly
    num_new = random.randint(2, 5)
    for _ in range(num_new):
        strip_idx = random.randint(0, len(strips) - 1)
        led_idx = random.randint(0, num_leds_for_each_strip[strip_idx] - 1)
        # Expanded color palette
        color = random.choice([
            (255, 255, 255),  # White
            (255, 200, 100),  # Warm white
            (100, 200, 255),  # Cool blue
            (255, 150, 200),  # Pink
            (200, 255, 150),  # Mint
            (255, 255, 100),  # Yellow
            (150, 100, 255)   # Purple
        ])
        sparkle_positions.append((strip_idx, led_idx, color, 0))
    
    for strip in strips:
        strip.show()
    
    effect_frame = (effect_frame + 1) % 1000

def show_christmas_fire():
    """Festive flickering Christmas colors - red, green, and white"""
    christmas_colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (255, 255, 255) # White
    ]
    
    for strip_idx, strip in enumerate(strips):
        for led in range(num_leds_for_each_strip[strip_idx]):
            # Pick a random Christmas color
            base_color = random.choice(christmas_colors)
            # Add flicker intensity
            flicker = random.randint(150, 255) / 255.0
            r = int(base_color[0] * flicker)
            g = int(base_color[1] * flicker)
            b = int(base_color[2] * flicker)
            strip.set_pixel(led, (r, g, b))
        strip.show()

def show_wave_effect():
    """Flowing wave with gradient blue shades moving across all strips"""
    global effect_frame
    
    for strip_idx, strip in enumerate(strips):
        for led in range(num_leds_for_each_strip[strip_idx]):
            # Create a smooth wave pattern across all LEDs
            # Calculate position in the wave (0-60 range covers all strips)
            position = (led + strip_idx * 10 - effect_frame) % 60
            
            # Create smooth wave using sine-like pattern
            # This creates peaks and valleys that move
            wave_val = abs(30 - position) / 30.0  # 0 at center, 1 at edges
            wave_val = 1 - wave_val  # Invert so center is bright
            
            # Create gradient from deep blue to cyan to light blue
            if wave_val > 0.7:  # Peak of wave - bright cyan
                r = int(wave_val * 50)
                g = int(wave_val * 255)
                b = 255
            elif wave_val > 0.3:  # Middle - medium blue
                r = 0
                g = int(wave_val * 180)
                b = int(wave_val * 255)
            else:  # Valley - deep blue/dark
                r = 0
                g = int(wave_val * 80)
                b = int(wave_val * 200)
            
            strip.set_pixel(led, (r, g, b))
        strip.show()
    
    effect_frame = (effect_frame + 1) % 60

def show_color_fade():
    """Smooth transition through rainbow colors"""
    global effect_frame
    
    # Cycle through hue spectrum
    hue = (effect_frame * 2) % 256
    rgb = hsv_to_rgb(hue, 255, 255)
    
    for strip in strips:
        strip.fill(rgb)
        strip.show()
    
    effect_frame = (effect_frame + 1) % 128

def show_strobe():
    """Intense strobe/flash effect"""
    global effect_frame
    
    # Alternate between white and off
    if effect_frame % 2 == 0:
        for strip in strips:
            strip.fill((255, 255, 255))
            strip.show()
    else:
        for strip in strips:
            strip.fill((0, 0, 0))
            strip.show()
    
    effect_frame = (effect_frame + 1) % 10

def show_meteor_shower():
    """Meteors shooting across strips with trailing tails"""
    global effect_frame, sparkle_positions
    
    # Initialize sparkle_positions as meteor tracking if needed
    if not isinstance(sparkle_positions, list) or effect_frame == 0:
        sparkle_positions = []
    
    # Fade all LEDs for trail effect
    for strip_idx, strip in enumerate(strips):
        for led in range(num_leds_for_each_strip[strip_idx]):
            # Dim existing LEDs to create trails
            strip.set_pixel(led, (0, 0, 0))  # Clear for fresh draw
    
    # Update meteor positions
    new_meteors = []
    for meteor in sparkle_positions:
        strip_idx, led_pos, color = meteor
        # Draw meteor with trail
        if led_pos < num_leds_for_each_strip[strip_idx]:
            strips[strip_idx].set_pixel(led_pos, color)  # Bright head
            # Trail behind it
            if led_pos > 0:
                r, g, b = color
                strips[strip_idx].set_pixel(led_pos - 1, (r//3, g//3, b//3))
            if led_pos > 1:
                r, g, b = color
                strips[strip_idx].set_pixel(led_pos - 2, (r//6, g//6, b//6))
            # Move meteor forward
            new_meteors.append((strip_idx, led_pos + 1, color))
    
    sparkle_positions = new_meteors
    
    # Randomly spawn new meteors (30% chance each frame)
    if random.randint(0, 100) < 30:
        strip_idx = random.randint(0, len(strips) - 1)
        # Random meteor colors: white, blue-white, yellow-white
        meteor_type = random.randint(0, 2)
        if meteor_type == 0:
            color = (255, 255, 255)  # White
        elif meteor_type == 1:
            color = (180, 220, 255)  # Blue-white
        else:
            color = (255, 240, 200)  # Yellow-white
        
        sparkle_positions.append((strip_idx, 0, color))
    
    for strip in strips:
        strip.show()
    
    effect_frame = (effect_frame + 1) % 1000

def show_police_lights():
    """Alternating red and blue police siren effect"""
    global effect_frame
    
    # Divide strips into left and right halves
    mid_point = len(strips) // 2
    
    # Alternate pattern every few frames
    pattern = (effect_frame // 3) % 4
    
    for strip_idx, strip in enumerate(strips):
        if pattern == 0 or pattern == 1:
            # Red on left, blue on right
            if strip_idx < mid_point:
                strip.fill((255, 0, 0) if pattern == 0 else (100, 0, 0))
            else:
                strip.fill((0, 0, 0))
        else:
            # Blue on right, red on left
            if strip_idx >= mid_point:
                strip.fill((0, 0, 255) if pattern == 2 else (0, 0, 100))
            else:
                strip.fill((0, 0, 0))
        strip.show()
    
    effect_frame = (effect_frame + 1) % 12

def show_matrix_rain():
    """Matrix-style digital rain cascading down"""
    global effect_frame, sparkle_positions
    
    # Use sparkle_positions to track rain drops: [(strip_idx, led_pos, brightness), ...]
    if not isinstance(sparkle_positions, list) or effect_frame % 50 == 0:
        if effect_frame % 50 == 0:
            sparkle_positions = []  # Reset periodically
    
    # Clear all LEDs first
    for strip_idx, strip in enumerate(strips):
        for led in range(num_leds_for_each_strip[strip_idx]):
            strip.set_pixel(led, (0, 0, 0))
    
    # Update existing rain drops
    new_drops = []
    for drop in sparkle_positions:
        strip_idx, led_pos, brightness = drop
        # Draw the drop and its trail
        if led_pos < num_leds_for_each_strip[strip_idx]:
            # Bright head
            if random.randint(0, 100) < 10:  # Occasional white flash
                strips[strip_idx].set_pixel(led_pos, (200, 255, 200))
            else:
                strips[strip_idx].set_pixel(led_pos, (0, brightness, 0))
            
            # Trail behind
            for trail in range(1, 4):
                if led_pos - trail >= 0:
                    trail_brightness = int(brightness * (0.6 ** trail))
                    if trail_brightness > 10:
                        strips[strip_idx].set_pixel(led_pos - trail, (0, trail_brightness, 0))
            
            # Move drop down and fade slightly
            new_brightness = int(brightness * 0.97)
            if new_brightness > 20:
                new_drops.append((strip_idx, led_pos + 1, new_brightness))
    
    sparkle_positions = new_drops
    
    # Spawn new rain drops randomly at the top
    for strip_idx in range(len(strips)):
        if random.randint(0, 100) < 20:  # 20% chance per strip per frame
            brightness = random.randint(180, 255)
            sparkle_positions.append((strip_idx, 0, brightness))
    
    for strip in strips:
        strip.show()
    
    effect_frame = (effect_frame + 1) % 1000

def show_aurora():
    """Aurora Borealis with flowing green, blue, and purple waves"""
    global effect_frame, sparkle_positions
    
    # Aurora doesn't use sparkle_positions, but reset it for next effect
    if effect_frame == 0:
        sparkle_positions = []
    
    for strip_idx, strip in enumerate(strips):
        for led in range(num_leds_for_each_strip[strip_idx]):
            # Create flowing wave pattern
            wave1 = (led + strip_idx * 5 + effect_frame) % 40
            wave2 = (led * 2 - strip_idx * 3 - effect_frame // 2) % 30
            
            # Combine waves for complex movement
            intensity1 = abs(20 - wave1) / 20.0
            intensity2 = abs(15 - wave2) / 15.0
            combined = (intensity1 + intensity2) / 2.0
            
            # Aurora colors: green and blue with hints of purple
            r = int(combined * 100)
            g = int(combined * 255 * 0.8)
            b = int(combined * 200)
            
            # Add some purple highlights
            if combined > 0.7:
                r = int(combined * 180)
                b = int(combined * 255)
            
            strip.set_pixel(led, (r, g, b))
        strip.show()
    
    effect_frame = (effect_frame + 1) % 80

def show_lava_lamp():
    """Rising colored blobs like a lava lamp"""
    global effect_frame, sparkle_positions
    
    # Track blobs: [(strip_idx, position, color, speed), ...]
    if not isinstance(sparkle_positions, list) or effect_frame < 2:
        sparkle_positions = []
    
    # Clear all LEDs
    for strip in strips:
        strip.fill((0, 0, 0))
    
    # Update blob positions
    new_blobs = []
    for blob in sparkle_positions:
        if len(blob) != 4:
            continue
        strip_idx, pos, color, speed = blob
        # Draw blob with gradient (3 LED blob)
        center_pos = int(pos)
        if 0 <= center_pos < num_leds_for_each_strip[strip_idx]:
            strips[strip_idx].set_pixel(center_pos, color)
        if 0 <= center_pos - 1 < num_leds_for_each_strip[strip_idx]:
            r, g, b = color
            strips[strip_idx].set_pixel(center_pos - 1, (r//2, g//2, b//2))
        if 0 <= center_pos + 1 < num_leds_for_each_strip[strip_idx]:
            r, g, b = color
            strips[strip_idx].set_pixel(center_pos + 1, (r//2, g//2, b//2))
        
        # Move blob up (reverse direction)
        new_pos = pos - speed
        if new_pos > -2:  # Keep if still visible
            new_blobs.append((strip_idx, new_pos, color, speed))
    
    sparkle_positions = new_blobs
    
    # Spawn new blobs at bottom
    if random.randint(0, 100) < 15:
        strip_idx = random.randint(0, len(strips) - 1)
        # Lava lamp colors: orange, red, pink, purple
        color = random.choice([
            (255, 100, 0),   # Orange
            (255, 0, 50),    # Red-pink
            (255, 0, 150),   # Pink
            (200, 0, 255),   # Purple
            (255, 50, 100)   # Hot pink
        ])
        speed = random.uniform(0.15, 0.35)
        sparkle_positions.append((strip_idx, num_leds_for_each_strip[strip_idx] - 1, color, speed))
    
    for strip in strips:
        strip.show()
    
    effect_frame = (effect_frame + 1) % 1000

def show_waterfall():
    """Cascading waterfall effect with blue-white rushing water"""
    global effect_frame, sparkle_positions
    
    # Track water drops: [(strip_idx, position, brightness), ...]
    if not isinstance(sparkle_positions, list) or effect_frame < 2:
        sparkle_positions = []
    
    # Fade existing pixels
    for strip_idx, strip in enumerate(strips):
        for led in range(num_leds_for_each_strip[strip_idx]):
            strip.set_pixel(led, (0, 0, 0))
    
    # Update water drops
    new_drops = []
    for drop in sparkle_positions:
        if len(drop) != 3:
            continue
        strip_idx, pos, brightness = drop
        # Draw the drop and splash effect
        drop_pos = int(pos)
        if drop_pos < num_leds_for_each_strip[strip_idx]:
            # White-blue water color
            r = int(brightness * 0.7)
            g = int(brightness * 0.9)
            b = brightness
            strips[strip_idx].set_pixel(drop_pos, (r, g, b))
            
            # Splash trail (2 LEDs behind)
            for trail in range(1, 3):
                if drop_pos - trail >= 0:
                    fade = 0.5 ** trail
                    strips[strip_idx].set_pixel(drop_pos - trail, 
                        (int(r * fade), int(g * fade), int(b * fade)))
            
            # Move drop down faster than rain
            new_pos = pos + 0.8
            if new_pos < num_leds_for_each_strip[strip_idx] + 2:
                new_drops.append((strip_idx, new_pos, brightness))
    
    sparkle_positions = new_drops
    
    # Spawn many drops (waterfall is dense)
    for strip_idx in range(len(strips)):
        if random.randint(0, 100) < 40:  # 40% chance - dense waterfall
            brightness = random.randint(200, 255)
            sparkle_positions.append((strip_idx, 0, brightness))
    
    for strip in strips:
        strip.show()
    
    effect_frame = (effect_frame + 1) % 1000

def show_fireworks():
    """Fireworks launching up and exploding"""
    global effect_frame, sparkle_positions
    
    # Track particles: [(strip_idx, position, color, state, age), ...]
    # state: 0=launching, 1=exploding
    if not isinstance(sparkle_positions, list) or effect_frame < 2:
        sparkle_positions = []
    
    # Clear all
    for strip in strips:
        strip.fill((0, 0, 0))
    
    # Update particles
    new_particles = []
    for particle in sparkle_positions:
        # Safety check for correct tuple length
        if len(particle) != 5:
            continue
        strip_idx, pos, color, state, age = particle
        
        if state == 0:  # Launching
            launch_pos = int(pos)
            if launch_pos >= 0 and launch_pos < num_leds_for_each_strip[strip_idx]:
                strips[strip_idx].set_pixel(launch_pos, color)
                # Trail
                if launch_pos + 1 < num_leds_for_each_strip[strip_idx]:
                    r, g, b = color
                    strips[strip_idx].set_pixel(launch_pos + 1, (r//3, g//3, b//3))
            
            # Move up and check for explosion
            new_pos = pos - 1.2
            if new_pos > 2:  # Still going up
                new_particles.append((strip_idx, new_pos, color, 0, age + 1))
            elif new_pos > 0:  # Explode!
                # Create explosion particles on same and adjacent strips
                for _ in range(8):
                    explode_strip = strip_idx + random.randint(-1, 1)
                    if 0 <= explode_strip < len(strips):
                        explode_pos = int(new_pos) + random.randint(-2, 2)
                        if 0 <= explode_pos < num_leds_for_each_strip[explode_strip]:
                            new_particles.append((explode_strip, explode_pos, color, 1, 0))
        
        else:  # Exploding (fade out)
            if age < 10:
                fade = 1.0 - (age / 10.0)
                r, g, b = color
                faded = (int(r * fade), int(g * fade), int(b * fade))
                if 0 <= int(pos) < num_leds_for_each_strip[strip_idx]:
                    strips[strip_idx].set_pixel(int(pos), faded)
                new_particles.append((strip_idx, pos, color, 1, age + 1))
    
    sparkle_positions = new_particles
    
    # Launch new fireworks randomly
    if random.randint(0, 100) < 8:  # 8% chance per frame
        strip_idx = random.randint(0, len(strips) - 1)
        # Firework colors
        color = random.choice([
            (255, 0, 0),     # Red
            (255, 100, 0),   # Orange
            (255, 255, 0),   # Yellow
            (0, 255, 0),     # Green
            (0, 150, 255),   # Blue
            (255, 0, 255),   # Magenta
            (255, 255, 255)  # White
        ])
        start_pos = num_leds_for_each_strip[strip_idx] - 1
        sparkle_positions.append((strip_idx, start_pos, color, 0, 0))
    
    for strip in strips:
        strip.show()
    
    effect_frame = (effect_frame + 1) % 1000

def hsv_to_rgb(h, s, v):
    """Convert HSV to RGB (h: 0-255, s: 0-255, v: 0-255)"""
    if s == 0:
        return (v, v, v)
    
    h = h * 6
    i = h >> 8
    f = h & 0xFF
    
    p = (v * (255 - s)) >> 8
    q = (v * (255 - ((s * f) >> 8))) >> 8
    t = (v * (255 - ((s * (255 - f)) >> 8))) >> 8
    
    i = i % 6
    if i == 0:
        return (v, t, p)
    if i == 1:
        return (q, v, p)
    if i == 2:
        return (p, v, t)
    if i == 3:
        return (p, q, v)
    if i == 4:
        return (t, p, v)
    return (v, p, q)

def show_multi_color():
    for idx, strip in enumerate(strips):
        color_name = color_names[idx % len(color_names)]
        rgb = colors_rgb[color_name]
        strip.fill(rgb)
        strip.show()

def apply_color_to_all_strips(color_name):
    rgb = colors_rgb[color_name]
    for strip in strips:
        strip.fill(rgb)
        strip.show()

def update_brightness_on_all_strips(new_brightness):
    for strip in strips:
        strip.brightness(new_brightness)
        strip.show()

# --- Show multi-color at startup ---
show_multi_color()

# --- Main loop ---
while True:
    # --- Color cycling button (GP7) ---
    current_color_state = button_color.value()
    if current_color_state == 0 and last_color_state == 1:
        mode_index = (mode_index + 1) % num_modes
        effect_frame = 0  # Reset effect animation

        if mode_index == 0:
            show_multi_color()
        elif mode_index == len(color_names) + 1:  # UCA mode
            show_uca()
        elif mode_index == len(color_names) + 2:  # Rainbow Chase
            pass  # Will update in main loop
        elif mode_index == len(color_names) + 3:  # Pulse Wave
            pass
        elif mode_index == len(color_names) + 4:  # Fire Effect
            pass
        elif mode_index == len(color_names) + 5:  # Scanner
            pass
        elif mode_index == len(color_names) + 6:  # Sparkle
            pass
        elif mode_index == len(color_names) + 7:  # Christmas Fire
            pass
        elif mode_index == len(color_names) + 8:  # Wave Effect
            pass
        elif mode_index == len(color_names) + 9:  # Color Fade
            pass
        elif mode_index == len(color_names) + 10:  # Strobe
            pass
        elif mode_index == len(color_names) + 11:  # Meteor Shower
            pass
        elif mode_index == len(color_names) + 12:  # Police Lights
            pass
        elif mode_index == len(color_names) + 13:  # Matrix Rain
            pass
        elif mode_index == len(color_names) + 14:  # Aurora
            pass
        elif mode_index == len(color_names) + 15:  # Lava Lamp
            pass
        elif mode_index == len(color_names) + 16:  # Waterfall
            pass
        elif mode_index == len(color_names) + 17:  # Fireworks
            pass
        elif mode_index <= len(color_names):
            apply_color_to_all_strips(color_names[mode_index - 1])

        time.sleep(0.2)
    last_color_state = current_color_state

    # --- Brightness control button (GP6) ---
    current_brightness_state = button_brightness.value()
    if current_brightness_state == 0 and last_brightness_state == 1:
        brightness += brightness_direction * 25
        if brightness <= 0:
            brightness = 0
            brightness_direction = 1
        elif brightness >= 255:
            brightness = 255
            brightness_direction = -1
        update_brightness_on_all_strips(brightness)

        # Refresh the current display mode (static modes only)
        if mode_index == 0:
            show_multi_color()
        elif mode_index == len(color_names) + 1:
            show_uca()
        elif mode_index <= len(color_names):
            apply_color_to_all_strips(color_names[mode_index - 1])

        time.sleep(0.2)
    last_brightness_state = current_brightness_state
    
    # --- Animated effects (continuous update) ---
    if mode_index == len(color_names) + 2:  # Rainbow Chase
        show_rainbow_chase()
        time.sleep(0.05)
    elif mode_index == len(color_names) + 3:  # Pulse Wave
        show_pulse_wave()
        time.sleep(0.02)
    elif mode_index == len(color_names) + 4:  # Fire Effect
        show_fire_effect()
        time.sleep(0.08)
    elif mode_index == len(color_names) + 5:  # Scanner
        show_scanner()
        time.sleep(0.1)
    elif mode_index == len(color_names) + 6:  # Sparkle
        show_sparkle()
        time.sleep(0.05)
    elif mode_index == len(color_names) + 7:  # Christmas Fire
        show_christmas_fire()
        time.sleep(0.08)
    elif mode_index == len(color_names) + 8:  # Wave Effect
        show_wave_effect()
        time.sleep(0.06)
    elif mode_index == len(color_names) + 9:  # Color Fade
        show_color_fade()
        time.sleep(0.03)
    elif mode_index == len(color_names) + 10:  # Strobe
        show_strobe()
        time.sleep(0.15)
    elif mode_index == len(color_names) + 11:  # Meteor Shower
        show_meteor_shower()
        time.sleep(0.06)
    elif mode_index == len(color_names) + 12:  # Police Lights
        show_police_lights()
        time.sleep(0.08)
    elif mode_index == len(color_names) + 13:  # Matrix Rain
        show_matrix_rain()
        time.sleep(0.08)
    elif mode_index == len(color_names) + 14:  # Aurora
        show_aurora()
        time.sleep(0.05)
    elif mode_index == len(color_names) + 15:  # Lava Lamp
        show_lava_lamp()
        time.sleep(0.07)
    elif mode_index == len(color_names) + 16:  # Waterfall
        show_waterfall()
        time.sleep(0.04)
    elif mode_index == len(color_names) + 17:  # Fireworks
        show_fireworks()
        time.sleep(0.06)






