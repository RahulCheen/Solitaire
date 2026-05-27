import pygame
import sys
import random
import config
from card import Card
from solitaire_game import SolitaireGame

class SolitaireApp:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Modern Classic Solitaire")
        self.clock = pygame.time.Clock()

        self.game = SolitaireGame()

        self.font_logo = pygame.font.SysFont("Segoe UI", 26, bold=True)
        self.font_ui = pygame.font.SysFont("Segoe UI", 16, bold=True)
        self.font_big = pygame.font.SysFont("Segoe UI", 36, bold=True)
        
        self.last_click_time = 0
        self.last_clicked_card = None
        self.last_clicked_pile = None

        self.drag_offset_x = 0
        self.drag_offset_y = 0

        self.start_ticks = pygame.time.get_ticks()
        self.elapsed_seconds = 0
        self.timer_active = True

        self.win_cascade_active = False
        self.trail_surface = None
        self.bounce_queue = []
        self.active_bouncers = []
        self.release_timer = 0
        self.release_interval = 10
        
        self.btn_undo = pygame.Rect(600, 24, 80, 36)
        self.btn_draw = pygame.Rect(696, 24, 110, 36)
        self.btn_restart = pygame.Rect(822, 24, 120, 36)

    def reset_timer(self):
        self.start_ticks = pygame.time.get_ticks()
        self.elapsed_seconds = 0
        self.timer_active = True

    def toggle_rules(self):
        if self.game.draw_count == 1:
            self.game.draw_count = 3
        else:
            self.game.draw_count = 1
        
        config.DRAW_COUNT = self.game.draw_count
        self.game.start_new_game()
        self.reset_timer()
        self.win_cascade_active = False

    def check_hover(self, rect, mx, my):
        return rect.collidepoint(mx, my)

    def draw_felt_gradient(self, surface):
        h = config.SCREEN_HEIGHT
        w = config.SCREEN_WIDTH
        for y in range(0, h, 2):
            t = y / h
            r = int(config.BG_GRADIENT_TOP[0] * (1 - t) + config.BG_GRADIENT_BOTTOM[0] * t)
            g = int(config.BG_GRADIENT_TOP[1] * (1 - t) + config.BG_GRADIENT_BOTTOM[1] * t)
            b = int(config.BG_GRADIENT_TOP[2] * (1 - t) + config.BG_GRADIENT_BOTTOM[2] * t)
            pygame.draw.rect(surface, (r, g, b), (0, y, w, 2))

    def trigger_victory_cascade(self):
        self.win_cascade_active = True
        self.timer_active = False

        self.trail_surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.draw_felt_gradient(self.trail_surface)
        self.draw_ui_bar(self.trail_surface, (0, 0))
        
        self.draw_empty_piles(self.trail_surface)
        
        self.bounce_queue = list(self.game.all_cards)
        self.bounce_queue.sort(key=lambda c: c.value, reverse=True)
        
        self.active_bouncers = []
        self.release_timer = 0

    def update_victory_cascade(self):
        if self.bounce_queue:
            self.release_timer += 1
            if self.release_timer >= self.release_interval:
                self.release_timer = 0
                card = self.bounce_queue.pop(0)
                
                direction = -1 if card.x > config.SCREEN_WIDTH / 2 else 1
                
                bouncer = {
                    "card": card,
                    "x": float(card.x),
                    "y": float(card.y),
                    "vx": direction * random.uniform(2.5, 5.0),
                    "vy": random.uniform(-6.0, -2.5),
                    "gravity": 0.35,
                    "bounce": -0.85
                }
                card.face_up = True
                self.active_bouncers.append(bouncer)

        for b in list(self.active_bouncers):
            b["x"] += b["vx"]
            b["y"] += b["vy"]
            b["vy"] += b["gravity"]

            card_h = config.CARD_HEIGHT
            if b["y"] + card_h >= config.SCREEN_HEIGHT:
                b["y"] = float(config.SCREEN_HEIGHT - card_h)
                b["vy"] = b["vy"] * b["bounce"]
                
                if abs(b["vy"]) < 1.0:
                    b["vy"] = 0

            b["card"].x = b["x"]
            b["card"].y = b["y"]
            b["card"].draw(self.trail_surface)

            card_w = config.CARD_WIDTH
            if b["x"] < -card_w or b["x"] > config.SCREEN_WIDTH:
                self.active_bouncers.remove(b)

    def draw_empty_piles(self, surface):
        stock_rect = pygame.Rect(config.START_X, config.TOP_PILE_Y, config.CARD_WIDTH, config.CARD_HEIGHT)
        if not self.game.stock:
            pygame.draw.rect(surface, (255, 255, 255, 20), stock_rect, width=2, border_radius=config.CARD_BORDER_RADIUS)
            cx, cy = stock_rect.center
            pygame.draw.circle(surface, (255, 255, 255, 50), (cx, cy), 20, width=2)
            pygame.draw.polygon(surface, (255, 255, 255, 100), [(cx + 20, cy - 5), (cx + 25, cy + 2), (cx + 15, cy + 2)])
        
        waste_rect = pygame.Rect(config.START_X + config.CARD_WIDTH + config.GAP_X, config.TOP_PILE_Y, config.CARD_WIDTH, config.CARD_HEIGHT)
        if not self.game.waste:
            pygame.draw.rect(surface, (255, 255, 255, 15), waste_rect, width=1, border_radius=config.CARD_BORDER_RADIUS)

        foundation_start_x = config.START_X + 3 * (config.CARD_WIDTH + config.GAP_X)
        suits = [Card.SUIT_HEARTS, Card.SUIT_DIAMONDS, Card.SUIT_CLUBS, Card.SUIT_SPADES]
        for idx, suit in enumerate(suits):
            f_x = foundation_start_x + idx * (config.CARD_WIDTH + config.GAP_X)
            f_rect = pygame.Rect(f_x, config.TOP_PILE_Y, config.CARD_WIDTH, config.CARD_HEIGHT)
            
            if not self.game.foundations[idx]:
                pygame.draw.rect(surface, (255, 255, 255, 25), f_rect, width=1, border_radius=config.CARD_BORDER_RADIUS)
                
                color = (255, 255, 255, 30) if suit not in (Card.SUIT_HEARTS, Card.SUIT_DIAMONDS) else (config.SUIT_RED[0], config.SUIT_RED[1], config.SUIT_RED[2], 25)
                temp_card = self.game.all_cards[0]
                temp_card.draw_suit_shape(surface, color, f_rect.center, 36, suit=suit)

        for idx, col in enumerate(self.game.tableaus):
            col_x = config.START_X + idx * (config.CARD_WIDTH + config.GAP_X)
            col_rect = pygame.Rect(col_x, config.START_Y, config.CARD_WIDTH, config.CARD_HEIGHT)
            if not col:
                pygame.draw.rect(surface, (255, 255, 255, 20), col_rect, width=1, border_radius=config.CARD_BORDER_RADIUS)

    def draw_ui_bar(self, surface, mouse_pos):
        pygame.draw.rect(surface, config.COLOR_UI_BAR, (0, 0, config.SCREEN_WIDTH, 84))
        pygame.draw.line(surface, (16, 50, 42), (0, 84), (config.SCREEN_WIDTH, 84), 1)

        logo_surf = self.font_logo.render("SOLITAIRE", True, (212, 175, 55))
        surface.blit(logo_surf, (60, 24))

        score_text = self.font_ui.render(f"SCORE: {self.game.score}", True, config.COLOR_TEXT_LIGHT)
        moves_text = self.font_ui.render(f"MOVES: {self.game.moves}", True, config.COLOR_TEXT_LIGHT)
        
        minutes = self.elapsed_seconds // 60
        seconds = self.elapsed_seconds % 60
        time_text = self.font_ui.render(f"TIME: {minutes:02d}:{seconds:02d}", True, config.COLOR_TEXT_LIGHT)

        surface.blit(score_text, (260, 31))
        surface.blit(moves_text, (380, 31))
        surface.blit(time_text, (490, 31))

        self.draw_button(surface, self.btn_undo, "UNDO", mouse_pos)
        
        draw_text = f"DRAW {self.game.draw_count}"
        self.draw_button(surface, self.btn_draw, draw_text, mouse_pos)
        
        self.draw_button(surface, self.btn_restart, "NEW GAME", mouse_pos)

    def draw_button(self, surface, rect, label, mouse_pos):
        is_hovered = rect.collidepoint(mouse_pos)
        color = config.COLOR_BUTTON_HOVER if is_hovered else config.COLOR_BUTTON
        
        pygame.draw.rect(surface, color, rect, border_radius=6)
        pygame.draw.rect(surface, (45, 55, 72), rect, width=1, border_radius=6)

        label_surf = self.font_ui.render(label, True, config.COLOR_BUTTON_TEXT)
        lx = rect.x + (rect.width - label_surf.get_width()) // 2
        ly = rect.y + (rect.height - label_surf.get_height()) // 2
        surface.blit(label_surf, (lx, ly))

    def handle_mouse_down(self, pos):
        mx, my = pos

        if self.btn_undo.collidepoint(mx, my):
            self.game.undo()
            return
        elif self.btn_draw.collidepoint(mx, my):
            self.toggle_rules()
            return
        elif self.btn_restart.collidepoint(mx, my):
            self.game.start_new_game()
            self.reset_timer()
            self.win_cascade_active = False
            return

        if self.win_cascade_active:
            return

        stock_rect = pygame.Rect(config.START_X, config.TOP_PILE_Y, config.CARD_WIDTH, config.CARD_HEIGHT)
        if stock_rect.collidepoint(mx, my):
            self.game.draw_from_stock()
            return

        card, source_pile = self.game.get_card_at_pos(mx, my)
        if card and source_pile:
            click_time = pygame.time.get_ticks()
            
            if (click_time - self.last_click_time < 250 and 
                card == self.last_clicked_card and 
                source_pile == self.last_clicked_pile):
                
                self.game.auto_move_to_foundation(card, source_pile)
                
                self.last_clicked_card = None
                self.last_clicked_pile = None
            else:
                self.last_click_time = click_time
                self.last_clicked_card = card
                self.last_clicked_pile = source_pile
                
                success = self.game.start_dragging(card, source_pile, mx, my)
                if success:
                    self.drag_offset_x = mx - card.x
                    self.drag_offset_y = my - card.y

    def handle_mouse_move(self, pos):
        if not self.game.dragged_cards or self.win_cascade_active:
            return

        mx, my = pos
        lead_card = self.game.dragged_cards[0]
        lead_card.x = mx - self.drag_offset_x
        lead_card.y = my - self.drag_offset_y

        for i in range(1, len(self.game.dragged_cards)):
            stacked_card = self.game.dragged_cards[i]
            stacked_card.x = lead_card.x
            stacked_card.y = lead_card.y + i * config.TABLEAU_CARD_GAP_REVEALED

    def handle_mouse_up(self, pos):
        if self.game.dragged_cards:
            mx, my = pos
            self.game.stop_dragging(mx, my)

    def update(self):
        if self.timer_active:
            now = pygame.time.get_ticks()
            self.elapsed_seconds = (now - self.start_ticks) // 1000

        if not self.win_cascade_active:
            for card in self.game.all_cards:
                card.update()

            if self.game.check_win_condition():
                self.trigger_victory_cascade()
            
            elif self.game.check_auto_complete():
                ticks = pygame.time.get_ticks()
                if ticks % 20 == 0:
                    self.game.auto_solve_step()

        else:
            self.update_victory_cascade()

    def run(self):
        running = True
        while running:
            self.clock.tick(config.FPS)
            mx, my = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    config.SCREEN_WIDTH, config.SCREEN_HEIGHT = event.size
                    self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.RESIZABLE)
                    if self.win_cascade_active and self.trail_surface:
                        new_trail = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
                        new_trail.blit(self.trail_surface, (0, 0))
                        self.trail_surface = new_trail
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.handle_mouse_down(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_move(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.handle_mouse_up(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w:
                        self.trigger_victory_cascade()
                    elif event.key == pygame.K_u:
                        self.game.undo()
                    elif event.key == pygame.K_r:
                        self.game.start_new_game()
                        self.reset_timer()
                        self.win_cascade_active = False
                    elif event.key == pygame.K_ESCAPE:
                        running = False

            self.update()

            if self.win_cascade_active:
                self.screen.blit(self.trail_surface, (0, 0))
                self.draw_ui_bar(self.screen, (mx, my))

                if not self.bounce_queue and not self.active_bouncers:
                    overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 150))
                    self.screen.blit(overlay, (0, 0))
                    
                    txt_win = self.font_big.render("VICTORY ACHIEVED!", True, (212, 175, 55))
                    txt_restart = self.font_ui.render("Press 'R' or click 'NEW GAME' to start over", True, config.COLOR_TEXT_LIGHT)
                    
                    self.screen.blit(txt_win, (config.SCREEN_WIDTH // 2 - txt_win.get_width() // 2, config.SCREEN_HEIGHT // 2 - 40))
                    self.screen.blit(txt_restart, (config.SCREEN_WIDTH // 2 - txt_restart.get_width() // 2, config.SCREEN_HEIGHT // 2 + 15))
                    
                    self.draw_ui_bar(self.screen, (mx, my))
            else:
                self.draw_felt_gradient(self.screen)
                self.draw_empty_piles(self.screen)

                for card in self.game.stock:
                    if not card.dragging:
                        card.draw_shadow(self.screen)
                        card.draw(self.screen)

                for card in self.game.waste:
                    if not card.dragging:
                        card.draw_shadow(self.screen)
                        card.draw(self.screen)

                for pile in self.game.foundations:
                    for card in pile:
                        if not card.dragging:
                            card.draw_shadow(self.screen)
                            card.draw(self.screen)

                for col in self.game.tableaus:
                    for card in col:
                        if not card.dragging:
                            card.draw_shadow(self.screen)
                            card.draw(self.screen)

                for card in self.game.dragged_cards:
                    card.draw_shadow(self.screen)
                    card.draw(self.screen)

                self.draw_ui_bar(self.screen, (mx, my))

            pygame.display.flip()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = SolitaireApp()
    app.run()
