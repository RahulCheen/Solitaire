import pygame
import math
import config

class Card:
    SUIT_HEARTS = "Hearts"
    SUIT_DIAMONDS = "Diamonds"
    SUIT_CLUBS = "Clubs"
    SUIT_SPADES = "Spades"

    def __init__(self, suit, value):
        self.suit = suit
        self.value = value
        
        self.face_up = False
        self.dragging = False
        
        self.x = 0
        self.y = 0
        self.target_x = 0
        self.target_y = 0
        
        self.is_flipping = False
        self.flip_progress = 1.0
        self.flip_target_state = False
        self.flip_direction = -1
        
        self.font = None
        self.small_font = None

        self.shadow_surface = None

        self.front_surf = None
        self.back_surf = None

    def __repr__(self):
        val_str = {1: "A", 11: "J", 12: "Q", 13: "K"}.get(self.value, str(self.value))
        suit_sym = {"Hearts": "♥", "Diamonds": "♦", "Clubs": "♣", "Spades": "♠"}.get(self.suit, "?")
        return f"{val_str}{suit_sym}"

    @property
    def is_red(self):
        return self.suit in (Card.SUIT_HEARTS, Card.SUIT_DIAMONDS)

    @property
    def value_str(self):
        return {1: "A", 11: "J", 12: "Q", 13: "K"}.get(self.value, str(self.value))

    def set_position(self, x, y, immediate=False):
        self.target_x = x
        self.target_y = y
        if immediate:
            self.x = x
            self.y = y

    def start_flip(self, target_face_up):
        if self.face_up == target_face_up:
            return
        self.is_flipping = True
        self.flip_target_state = target_face_up
        self.flip_progress = 1.0
        self.flip_direction = -1

    def update(self):
        if not self.dragging:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            if abs(dx) > 0.1:
                self.x += dx * config.LERP_SPEED
            else:
                self.x = self.target_x

            if abs(dy) > 0.1:
                self.y += dy * config.LERP_SPEED
            else:
                self.y = self.target_y

        if self.is_flipping:
            self.flip_progress += self.flip_direction * config.FLIP_SPEED
            
            if self.flip_direction == -1 and self.flip_progress <= 0:
                self.flip_progress = 0.0
                self.flip_direction = 1
                self.face_up = self.flip_target_state
            
            elif self.flip_direction == 1 and self.flip_progress >= 1.0:
                self.flip_progress = 1.0
                self.is_flipping = False
                self.flip_direction = -1

    def draw_suit_shape(self, surface, color, center, size, suit=None):
        cx, cy = center
        w, h = size, size
        suit = suit or self.suit

        if suit == Card.SUIT_DIAMONDS:
            pts = [
                (cx, cy - h // 2),
                (cx + w // 2, cy),
                (cx, cy + h // 2),
                (cx - w // 2, cy)
            ]
            pygame.draw.polygon(surface, color, pts)

        elif suit == Card.SUIT_HEARTS:
            r = w // 4
            top_y = cy - h // 6
            pygame.draw.circle(surface, color, (cx - r, top_y), r)
            pygame.draw.circle(surface, color, (cx + r, top_y), r)
            tri_pts = [
                (cx - w // 2 + 1, top_y),
                (cx + w // 2 - 1, top_y),
                (cx, cy + h // 2)
            ]
            pygame.draw.polygon(surface, color, tri_pts)

        elif suit == Card.SUIT_SPADES:
            r = w // 5
            bottom_y = cy + h // 6
            tri_pts = [
                (cx - w // 2 + 1, bottom_y),
                (cx + w // 2 - 1, bottom_y),
                (cx, cy - h // 2)
            ]
            pygame.draw.polygon(surface, color, tri_pts)
            pygame.draw.circle(surface, color, (cx - r - 1, bottom_y), r)
            pygame.draw.circle(surface, color, (cx + r + 1, bottom_y), r)
            stem_pts = [
                (cx, cy + h // 12),
                (cx - w // 6, cy + h // 2),
                (cx + w // 6, cy + h // 2)
            ]
            pygame.draw.polygon(surface, color, stem_pts)

        elif suit == Card.SUIT_CLUBS:
            r = int(w * 0.27)
            
            pygame.draw.circle(surface, color, (cx, cy - h // 8), r)
            pygame.draw.circle(surface, color, (cx - int(w * 0.2), cy + h // 12), r)
            pygame.draw.circle(surface, color, (cx + int(w * 0.2), cy + h // 12), r)
            
            center_pts = [
                (cx, cy - h // 8),
                (cx - int(w * 0.2), cy + h // 12),
                (cx + int(w * 0.2), cy + h // 12)
            ]
            pygame.draw.polygon(surface, color, center_pts)
            
            pygame.draw.rect(surface, color, (cx - 2, cy + h // 12, 4, int(h * 0.38)))
            stem_pts = [
                (cx - 2, cy + h // 4),
                (cx - w // 5, cy + h // 2),
                (cx + w // 5, cy + h // 2)
            ]
            pygame.draw.polygon(surface, color, stem_pts)

    def draw_card_front(self, surface, rect, scale=1):
        pygame.draw.rect(surface, config.CARD_BG, rect, border_radius=int(config.CARD_BORDER_RADIUS * scale))
        pygame.draw.rect(surface, config.CARD_BORDER, rect, width=int(1 * scale) or 1, border_radius=int(config.CARD_BORDER_RADIUS * scale))

        scaled_font = pygame.font.SysFont("Segoe UI", int(24 * scale), bold=True)

        suit_color = config.SUIT_RED if self.is_red else config.SUIT_BLACK

        idx_text = self.value_str
        idx_surf = scaled_font.render(idx_text, True, suit_color)
        
        surface.blit(idx_surf, (rect.x + int(8 * scale), rect.y + int(6 * scale)))
        self.draw_suit_shape(surface, suit_color, (rect.x + int(16 * scale), rect.y + int(45 * scale)), int(18 * scale), suit=self.suit)

        corner_surf = pygame.Surface((int(30 * scale), int(55 * scale)), pygame.SRCALPHA)
        c_idx_surf = scaled_font.render(idx_text, True, suit_color)
        corner_surf.blit(c_idx_surf, (int(15 * scale) - c_idx_surf.get_width() // 2, int(2 * scale)))
        
        self.draw_suit_shape(corner_surf, suit_color, (int(15 * scale), int(42 * scale)), int(18 * scale), suit=self.suit)
        
        rotated_corner = pygame.transform.rotate(corner_surf, 180)
        surface.blit(rotated_corner, (rect.right - int(38 * scale), rect.bottom - int(61 * scale)))

        cx = rect.centerx
        cy = rect.centery

        if self.value == 1:
            self.draw_suit_shape(surface, suit_color, (cx, cy), int(48 * scale))
        elif self.value in (11, 12, 13):
            inner_rect = pygame.Rect(rect.x + int(28 * scale), rect.y + int(24 * scale), rect.width - int(56 * scale), rect.height - int(48 * scale))
            pygame.draw.rect(surface, suit_color, inner_rect, width=int(1 * scale) or 1, border_radius=int(4 * scale))
            
            crest_color = (212, 175, 55) if not self.is_red else (190, 24, 74)
            if self.value == 13:
                crown_pts = [
                    (cx - int(15 * scale), cy + int(10 * scale)),
                    (cx - int(18 * scale), cy - int(10 * scale)),
                    (cx - int(7 * scale), cy - int(2 * scale)),
                    (cx, cy - int(15 * scale)),
                    (cx + int(7 * scale), cy - int(2 * scale)),
                    (cx + int(18 * scale), cy - int(10 * scale)),
                    (cx + int(15 * scale), cy + int(10 * scale))
                ]
                pygame.draw.polygon(surface, crest_color, crown_pts)
                pygame.draw.rect(surface, suit_color, (cx - int(15 * scale), cy + int(10 * scale), int(30 * scale), int(4 * scale)), border_radius=int(1 * scale) or 1)
            elif self.value == 12:
                shield_pts = [
                    (cx, cy - int(15 * scale)),
                    (cx + int(14 * scale), cy - int(8 * scale)),
                    (cx + int(10 * scale), cy + int(12 * scale)),
                    (cx, cy + int(18 * scale)),
                    (cx - int(10 * scale), cy + int(12 * scale)),
                    (cx - int(14 * scale), cy - int(8 * scale))
                ]
                pygame.draw.polygon(surface, crest_color, shield_pts)
                pygame.draw.circle(surface, suit_color, (cx, cy), int(4 * scale))
            else:
                sword_pts = [
                    (cx - int(2 * scale), cy - int(18 * scale)), (cx + int(2 * scale), cy - int(18 * scale)),
                    (cx + int(2 * scale), cy + int(10 * scale)), (cx - int(2 * scale), cy + int(10 * scale))
                ]
                pygame.draw.polygon(surface, crest_color, sword_pts)
                pygame.draw.rect(surface, suit_color, (cx - int(8 * scale), cy - int(10 * scale), int(16 * scale), int(3 * scale)))
                self.draw_suit_shape(surface, suit_color, (cx, cy + int(12 * scale)), int(12 * scale))

            self.draw_suit_shape(surface, suit_color, (rect.x + int(36 * scale), rect.y + int(32 * scale)), int(10 * scale))
            self.draw_suit_shape(surface, suit_color, (rect.right - int(36 * scale), rect.bottom - int(32 * scale)), int(10 * scale))
        else:
            layout_coords = self.get_suit_layout(self.value, rect)
            for suit_x, suit_y, suit_sz in layout_coords:
                self.draw_suit_shape(surface, suit_color, (suit_x, suit_y), suit_sz)

    def get_suit_layout(self, val, rect):
        cx = rect.centerx
        cy = rect.centery
        w = rect.width
        h = rect.height
        
        left_x = rect.x + int(w * 0.33)
        right_x = rect.x + int(w * 0.67)
        top_y = rect.y + int(h * 0.23)
        upper_mid_y = rect.y + int(h * 0.36)
        mid_y = cy
        lower_mid_y = rect.y + int(h * 0.64)
        bot_y = rect.y + int(h * 0.77)

        scale = rect.width / config.CARD_WIDTH
        sz = int(18 * scale)

        if val == 2:
            return [(cx, top_y, sz), (cx, bot_y, sz)]
        elif val == 3:
            return [(cx, top_y, sz), (cx, mid_y, sz), (cx, bot_y, sz)]
        elif val == 4:
            return [(left_x, top_y, sz), (right_x, top_y, sz),
                    (left_x, bot_y, sz), (right_x, bot_y, sz)]
        elif val == 5:
            return [(left_x, top_y, sz), (right_x, top_y, sz),
                    (cx, mid_y, sz),
                    (left_x, bot_y, sz), (right_x, bot_y, sz)]
        elif val == 6:
            return [(left_x, top_y, sz), (right_x, top_y, sz),
                    (left_x, mid_y, sz), (right_x, mid_y, sz),
                    (left_x, bot_y, sz), (right_x, bot_y, sz)]
        elif val == 7:
            return [(left_x, top_y, sz), (right_x, top_y, sz),
                    (left_x, mid_y, sz), (right_x, mid_y, sz),
                    (cx, upper_mid_y, sz),
                    (left_x, bot_y, sz), (right_x, bot_y, sz)]
        elif val == 8:
            return [(left_x, top_y, sz), (right_x, top_y, sz),
                    (left_x, mid_y, sz), (right_x, mid_y, sz),
                    (cx, upper_mid_y, sz), (cx, lower_mid_y, sz),
                    (left_x, bot_y, sz), (right_x, bot_y, sz)]
        elif val == 9:
            return [(left_x, top_y, sz), (right_x, top_y, sz),
                    (left_x, upper_mid_y, sz), (right_x, upper_mid_y, sz),
                    (left_x, lower_mid_y, sz), (right_x, lower_mid_y, sz),
                    (left_x, bot_y, sz), (right_x, bot_y, sz),
                    (cx, mid_y, sz)]
        elif val == 10:
            return [(left_x, top_y, sz), (right_x, top_y, sz),
                    (left_x, upper_mid_y, sz), (right_x, upper_mid_y, sz),
                    (left_x, lower_mid_y, sz), (right_x, lower_mid_y, sz),
                    (left_x, bot_y, sz), (right_x, bot_y, sz),
                    (cx, rect.y + int(h * 0.3), sz), (cx, rect.y + int(h * 0.7), sz)]
        return []

    def draw_card_back(self, surface, rect, scale=1):
        pygame.draw.rect(surface, config.CARD_BACK_PRIMARY, rect, border_radius=int(config.CARD_BORDER_RADIUS * scale))
        
        outer_margin = int(5 * scale)
        outer_rect = pygame.Rect(
            rect.x + outer_margin,
            rect.y + outer_margin,
            rect.width - outer_margin * 2,
            rect.height - outer_margin * 2
        )
        pygame.draw.rect(surface, config.CARD_BACK_GOLD, outer_rect, width=int(2 * scale) or 1, border_radius=int((config.CARD_BORDER_RADIUS - 2) * scale))

        inner_margin = int(9 * scale)
        inner_rect = pygame.Rect(
            rect.x + inner_margin,
            rect.y + inner_margin,
            rect.width - inner_margin * 2,
            rect.height - inner_margin * 2
        )
        pygame.draw.rect(surface, config.CARD_BACK_GOLD, inner_rect, width=int(1 * scale) or 1, border_radius=int((config.CARD_BORDER_RADIUS - 4) * scale))

        cx = rect.centerx
        cy = rect.centery
        dw = rect.width - int(32 * scale)
        dh = rect.height - int(48 * scale)
        
        diamond_pts = [
            (cx, cy - dh // 2),
            (cx + dw // 2, cy),
            (cx, cy + dh // 2),
            (cx - dw // 2, cy)
        ]
        pygame.draw.polygon(surface, config.CARD_BACK_GOLD, diamond_pts, width=int(1 * scale) or 1)

        dw2 = dw - int(16 * scale)
        dh2 = dh - int(24 * scale)
        diamond_pts2 = [
            (cx, cy - dh2 // 2),
            (cx + dw2 // 2, cy),
            (cx, cy + dh2 // 2),
            (cx - dw2 // 2, cy)
        ]
        pygame.draw.polygon(surface, config.CARD_BACK_GOLD, diamond_pts2, width=int(1 * scale) or 1)

        pygame.draw.line(surface, config.CARD_BACK_GOLD, (cx - dw2 // 2, cy), (cx + dw2 // 2, cy), int(1 * scale) or 1)
        pygame.draw.line(surface, config.CARD_BACK_GOLD, (cx, cy - dh2 // 2), (cx, cy + dh2 // 2), int(1 * scale) or 1)

        q_dist_x = dw // 4
        q_dist_y = dh // 4
        pygame.draw.circle(surface, config.CARD_BACK_GOLD, (cx - q_dist_x, cy - q_dist_y), int(3 * scale), width=int(1 * scale) or 1)
        pygame.draw.circle(surface, config.CARD_BACK_GOLD, (cx + q_dist_x, cy - q_dist_y), int(3 * scale), width=int(1 * scale) or 1)
        pygame.draw.circle(surface, config.CARD_BACK_GOLD, (cx - q_dist_x, cy + q_dist_y), int(3 * scale), width=int(1 * scale) or 1)
        pygame.draw.circle(surface, config.CARD_BACK_GOLD, (cx + q_dist_x, cy + q_dist_y), int(3 * scale), width=int(1 * scale) or 1)

        pygame.draw.rect(surface, config.CARD_BORDER, rect, width=int(1 * scale) or 1, border_radius=int(config.CARD_BORDER_RADIUS * scale))

    def draw_shadow(self, surface):
        if self.shadow_surface is None:
            self.shadow_surface = pygame.Surface(
                (config.CARD_WIDTH + 14, config.CARD_HEIGHT + 14), 
                pygame.SRCALPHA
            )
            for i in range(7):
                alpha = 24 - i * 3
                shadow_rect = pygame.Rect(
                    7 - i,
                    7 - i,
                    config.CARD_WIDTH + i * 2,
                    config.CARD_HEIGHT + i * 2
                )
                pygame.draw.rect(
                    self.shadow_surface, 
                    (0, 0, 0, alpha), 
                    shadow_rect, 
                    border_radius=config.CARD_BORDER_RADIUS + i
                )

        offset_x = 4 if not self.dragging else 8
        offset_y = 6 if not self.dragging else 12
        shadow_x = int(self.x) - 7 + offset_x
        shadow_y = int(self.y) - 7 + offset_y
        surface.blit(self.shadow_surface, (shadow_x, shadow_y))

    def draw(self, surface):
        scale = 2
        
        if self.front_surf is None:
            self.front_surf = pygame.Surface((config.CARD_WIDTH * scale, config.CARD_HEIGHT * scale), pygame.SRCALPHA)
            temp_rect = pygame.Rect(0, 0, config.CARD_WIDTH * scale, config.CARD_HEIGHT * scale)
            self.draw_card_front(self.front_surf, temp_rect, scale=scale)
            
        if self.back_surf is None:
            self.back_surf = pygame.Surface((config.CARD_WIDTH * scale, config.CARD_HEIGHT * scale), pygame.SRCALPHA)
            temp_rect = pygame.Rect(0, 0, config.CARD_WIDTH * scale, config.CARD_HEIGHT * scale)
            self.draw_card_back(self.back_surf, temp_rect, scale=scale)
            
        scale_width = int(config.CARD_WIDTH * max(0.01, self.flip_progress))
        scale_height = config.CARD_HEIGHT
        
        offset_x = (config.CARD_WIDTH - scale_width) // 2
        card_rect = pygame.Rect(
            int(self.x) + offset_x, 
            int(self.y), 
            scale_width, 
            scale_height
        )

        source_surf = self.front_surf if self.face_up else self.back_surf
        
        scaled_card = pygame.transform.smoothscale(source_surf, (scale_width, scale_height))
        surface.blit(scaled_card, card_rect.topleft)
