import random
import config
from card import Card
import pygame

class SolitaireGame:
    def __init__(self):
        self.all_cards = []
        suits = [Card.SUIT_HEARTS, Card.SUIT_DIAMONDS, Card.SUIT_CLUBS, Card.SUIT_SPADES]
        for suit in suits:
            for val in range(1, 14):
                self.all_cards.append(Card(suit, val))

        self.stock = []
        self.waste = []
        self.foundations = [[] for _ in range(4)]
        self.tableaus = [[] for _ in range(7)]

        self.dragged_cards = []
        self.drag_source_pile = None

        self.score = 0
        self.moves = 0
        self.draw_count = config.DRAW_COUNT

        self.undo_stack = []

        self.start_new_game()

    def start_new_game(self):
        for card in self.all_cards:
            card.face_up = False
            card.dragging = False
            card.is_flipping = False
            card.flip_progress = 1.0
            card.set_position(config.START_X, config.TOP_PILE_Y, immediate=True)

        shuffled = list(self.all_cards)
        random.shuffle(shuffled)

        self.stock = []
        self.waste = []
        self.foundations = [[] for _ in range(4)]
        self.tableaus = [[] for _ in range(7)]
        self.undo_stack = []
        self.score = 0
        self.moves = 0

        idx = 0
        for i in range(7):
            for j in range(i + 1):
                card = shuffled[idx]
                idx += 1
                if j == i:
                    card.face_up = True
                self.tableaus[i].append(card)

        while idx < len(shuffled):
            self.stock.append(shuffled[idx])
            idx += 1

        self.update_card_targets()

    def update_card_targets(self):
        for card in self.stock:
            card.set_position(config.START_X, config.TOP_PILE_Y)

        waste_start_x = config.START_X + config.CARD_WIDTH + config.GAP_X
        for i, card in enumerate(self.waste):
            fan_idx = max(0, i - (len(self.waste) - 3)) if len(self.waste) > 3 else i
            offset_x = fan_idx * 16
            card.set_position(waste_start_x + offset_x, config.TOP_PILE_Y)

        foundation_start_x = config.START_X + 3 * (config.CARD_WIDTH + config.GAP_X)
        for f_idx, pile in enumerate(self.foundations):
            f_x = foundation_start_x + f_idx * (config.CARD_WIDTH + config.GAP_X)
            for card in pile:
                card.set_position(f_x, config.TOP_PILE_Y)

        for c_idx, column in enumerate(self.tableaus):
            col_x = config.START_X + c_idx * (config.CARD_WIDTH + config.GAP_X)
            current_y = config.START_Y
            for card in column:
                card.set_position(col_x, current_y)
                gap = config.TABLEAU_CARD_GAP_REVEALED if card.face_up else config.TABLEAU_CARD_GAP_HIDDEN
                current_y += gap

    def save_state(self):
        snapshot = {
            "stock": [card for card in self.stock],
            "waste": [card for card in self.waste],
            "foundations": [[card for card in pile] for pile in self.foundations],
            "tableaus": [[card for card in col] for col in self.tableaus],
            "face_up_states": {card: card.face_up for card in self.all_cards},
            "score": self.score,
            "moves": self.moves
        }
        self.undo_stack.append(snapshot)
        if len(self.undo_stack) > 100:
            self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack:
            return False

        snapshot = self.undo_stack.pop()
        
        self.stock = list(snapshot["stock"])
        self.waste = list(snapshot["waste"])
        
        self.foundations = []
        for pile in snapshot["foundations"]:
            self.foundations.append(list(pile))

        self.tableaus = []
        for col in snapshot["tableaus"]:
            self.tableaus.append(list(col))

        for card, face_up in snapshot["face_up_states"].items():
            if card.face_up != face_up:
                card.start_flip(face_up)
            else:
                card.face_up = face_up

        self.score = snapshot["score"]
        self.moves = snapshot["moves"]

        self.update_card_targets()
        return True

    def draw_from_stock(self):
        self.save_state()
        self.moves += 1

        if not self.stock:
            if not self.waste:
                return
            self.stock = list(self.waste)
            self.stock.reverse()
            self.waste = []
            
            for card in self.stock:
                card.start_flip(False)
            
            self.score = max(0, self.score - 15)
        else:
            draws = min(self.draw_count, len(self.stock))
            drawn_cards = []
            for _ in range(draws):
                card = self.stock.pop()
                drawn_cards.append(card)

            for card in drawn_cards:
                self.waste.append(card)
                card.start_flip(True)

            self.score += 5

        self.update_card_targets()

    def get_card_at_pos(self, mx, my):
        if self.waste:
            card = self.waste[-1]
            w_rect = pygame.Rect(card.x, card.y, config.CARD_WIDTH, config.CARD_HEIGHT)
            if w_rect.collidepoint(mx, my):
                return card, self.waste

        for pile in self.foundations:
            if pile:
                card = pile[-1]
                f_rect = pygame.Rect(card.x, card.y, config.CARD_WIDTH, config.CARD_HEIGHT)
                if f_rect.collidepoint(mx, my):
                    return card, pile

        for col in self.tableaus:
            if col:
                for idx in range(len(col) - 1, -1, -1):
                    card = col[idx]
                    
                    is_last = (idx == len(col) - 1)
                    gap = config.TABLEAU_CARD_GAP_REVEALED if card.face_up else config.TABLEAU_CARD_GAP_HIDDEN
                    h = config.CARD_HEIGHT if is_last else gap
                    
                    c_rect = pygame.Rect(card.x, card.y, config.CARD_WIDTH, h)
                    if c_rect.collidepoint(mx, my):
                        return card, col
        return None, None

    def start_dragging(self, card, source_pile, mx, my):
        if not card.face_up:
            if source_pile in self.tableaus and card == source_pile[-1]:
                self.save_state()
                card.start_flip(True)
                self.score += 5
                self.moves += 1
                return True
            return False

        if source_pile == self.waste or source_pile in self.foundations:
            self.dragged_cards = [card]
        elif source_pile in self.tableaus:
            idx = source_pile.index(card)
            self.dragged_cards = source_pile[idx:]
        
        self.drag_source_pile = source_pile

        for c in self.dragged_cards:
            c.dragging = True
            
        return True

    def stop_dragging(self, mx, my):
        if not self.dragged_cards:
            return

        target_pile, target_pile_type = self.get_drop_pile(mx, my)

        valid_move = False
        
        if target_pile is not None and target_pile != self.drag_source_pile:
            lead_card = self.dragged_cards[0]
            
            if target_pile_type == "tableau":
                if not target_pile:
                    if lead_card.value == 13:
                        valid_move = True
                else:
                    top_target = target_pile[-1]
                    if top_target.face_up:
                        color_match = (lead_card.is_red != top_target.is_red)
                        val_match = (lead_card.value == top_target.value - 1)
                        if color_match and val_match:
                            valid_move = True

            elif target_pile_type == "foundation":
                if len(self.dragged_cards) == 1:
                    idx = self.foundations.index(target_pile)
                    assigned_suit = [Card.SUIT_HEARTS, Card.SUIT_DIAMONDS, Card.SUIT_CLUBS, Card.SUIT_SPADES][idx]
                    
                    if not target_pile:
                        if lead_card.value == 1 and lead_card.suit == assigned_suit:
                            valid_move = True
                    else:
                        top_target = target_pile[-1]
                        suit_match = (lead_card.suit == top_target.suit)
                        val_match = (lead_card.value == top_target.value + 1)
                        if suit_match and val_match and lead_card.suit == assigned_suit:
                            valid_move = True

        if valid_move:
            self.save_state()
            self.moves += 1

            for c in self.dragged_cards:
                self.drag_source_pile.remove(c)

            for c in self.dragged_cards:
                target_pile.append(c)

            if target_pile_type == "foundation":
                self.score += 10
            elif target_pile_type == "tableau":
                if self.drag_source_pile == self.waste:
                    self.score += 5
                elif self.drag_source_pile in self.foundations:
                    self.score = max(0, self.score - 15)

            if self.drag_source_pile in self.tableaus and self.drag_source_pile:
                top_card = self.drag_source_pile[-1]
                if not top_card.face_up:
                    top_card.start_flip(True)
                    self.score += 5

        for c in self.dragged_cards:
            c.dragging = False

        self.dragged_cards = []
        self.drag_source_pile = None

        self.update_card_targets()

    def get_drop_pile(self, mx, my):
        points_to_test = [(mx, my)]
        if self.dragged_cards:
            lead = self.dragged_cards[0]
            cx = lead.x + config.CARD_WIDTH // 2
            cy = lead.y + config.CARD_HEIGHT // 2
            points_to_test.append((cx, cy))

        for idx, col in enumerate(self.tableaus):
            remaining = [c for c in col if c not in self.dragged_cards]
            
            col_x = config.START_X + idx * (config.CARD_WIDTH + config.GAP_X)
            col_rect = pygame.Rect(col_x, config.START_Y, config.CARD_WIDTH, config.SCREEN_HEIGHT - config.START_Y)
            empty_rect = pygame.Rect(col_x, config.START_Y, config.CARD_WIDTH, config.CARD_HEIGHT)
            
            for tx, ty in points_to_test:
                if remaining:
                    last_card = remaining[-1]
                    card_rect = pygame.Rect(last_card.x, last_card.y, config.CARD_WIDTH, config.CARD_HEIGHT)
                    if card_rect.collidepoint(tx, ty) or col_rect.collidepoint(tx, ty):
                        return col, "tableau"
                else:
                    if empty_rect.collidepoint(tx, ty):
                        return col, "tableau"

        foundation_start_x = config.START_X + 3 * (config.CARD_WIDTH + config.GAP_X)
        for idx, pile in enumerate(self.foundations):
            f_x = foundation_start_x + idx * (config.CARD_WIDTH + config.GAP_X)
            f_rect = pygame.Rect(f_x, config.TOP_PILE_Y, config.CARD_WIDTH, config.CARD_HEIGHT)
            for tx, ty in points_to_test:
                if f_rect.collidepoint(tx, ty):
                    return pile, "foundation"

        return None, None

    def auto_move_to_foundation(self, card, source_pile):
        if not card.face_up:
            return False

        if source_pile in self.tableaus and card != source_pile[-1]:
            return False

        suits = [Card.SUIT_HEARTS, Card.SUIT_DIAMONDS, Card.SUIT_CLUBS, Card.SUIT_SPADES]
        if card.suit not in suits:
            return False
        
        target_idx = suits.index(card.suit)
        pile = self.foundations[target_idx]

        valid = False
        if not pile:
            if card.value == 1:
                valid = True
        else:
            top_card = pile[-1]
            if card.value == top_card.value + 1:
                valid = True

        if valid:
            self.save_state()
            self.moves += 1

            source_pile.remove(card)
            pile.append(card)

            self.score += 10

            if source_pile in self.tableaus and source_pile:
                top_card = source_pile[-1]
                if not top_card.face_up:
                    top_card.start_flip(True)
                    self.score += 5

            self.update_card_targets()
            return True

        return False

    def check_auto_complete(self):
        if self.stock or self.waste:
            return False

        for col in self.tableaus:
            for card in col:
                if not card.face_up:
                    return False

        return True

    def check_win_condition(self):
        for pile in self.foundations:
            if len(pile) != 13:
                return False
        return True

    def auto_solve_step(self):
        candidates = []
        for col in self.tableaus:
            if col:
                candidates.append((col[-1], col))

        suits = [Card.SUIT_HEARTS, Card.SUIT_DIAMONDS, Card.SUIT_CLUBS, Card.SUIT_SPADES]

        for card, pile in candidates:
            if card.suit not in suits:
                continue
            target_idx = suits.index(card.suit)
            f_pile = self.foundations[target_idx]

            valid = False
            if not f_pile:
                if card.value == 1:
                    valid = True
            else:
                top_f = f_pile[-1]
                if card.value == top_f.value + 1:
                    valid = True

            if valid:
                pile.remove(card)
                f_pile.append(card)
                self.score += 10
                self.moves += 1
                self.update_card_targets()
                return True
        return False
