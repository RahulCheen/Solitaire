# Solitaire in Pygame

An implementation of **Klondike Solitaire** in Python using Pygame. This project features drag-and-drop mechanics, an undo system, and a recreation of the classic Windows Solitaire bouncing-card victory cascade animation.

Additionally, the game incorporates **2x Supersample Anti-Aliasing (2x SSAA)** rendering, custom math-driven vector card suit shapes, and a fully resizable layout.

---

## Key Features

### 1. Anti-Aliased Graphics
* **2x Supersample Anti-Aliasing (2x SSAA)**: All card elements (fronts, backs, text, vectors, rounded corners) are pre-rendered onto a 2x resolution canvas and cached. During draw loops, Pygame's `smoothscale` downsamples them, resulting in smooth, anti-aliased cards at any window scale.
* **Optimized Suit Geometry**: Rendered mathematically using vector formulas:
  * **Spades**: Pointed arrowhead with circular bottom lobes.
  * **Clubs**: Three-leaf clover with a flared stem base.
  * **Hearts & Diamonds**: Proportioned geometric shapes.

* **Depth Shadows**: Cards feature drop shadows rendered dynamically using nested transparent rounded rectangles to represent depth.
* **Card Back**: A crimson background framed with gold double borders and quadrant circles.

### 2. Mechanics & Animations
* **3D Card Flip Animations**: Toggling card states scales them horizontally down to a single pixel before shifting their face-up state and expanding back out.
* **Physics Glides (LERP)**: Cards glide back to their stacks or to their targets using Linear Interpolation (LERP).
* **Bouncing Victory Cascade**: When a game is won (or via debug key), card decks peel off the foundations and bounce across the screen, leaving trails on a persistent canvas background while keeping the top HUD bar active.

### 3. Gameplay Features
* **Draw-3 Mode by Default**: Solitaire initiates in Draw-3 mode (toggletable to Draw-1 in real-time).
* **Double-Click Auto-Move**: Double-clicking an eligible card moves it to its designated foundation suit stack (Hearts, Diamonds, Clubs, Spades).
* **Infinite Undo**: Undo moves sequentially. Piles glide back to their former coordinates on the board.
* **Auto-Solve Solver**: Once all cards are revealed and the stock pile is empty, the game automatically moves remaining cards to foundations.
* **Expanded Stacking Overlaps**: Tableau cascades feature expanded spacing (`36px` revealed gaps, `16px` hidden gaps) making rank numbers and suits on lower cards readable.

---

## Responsive Layout Spacing
The game window opens at a 1020 x 860 resolution and is fully resizable:
* The window can be dragged, resized, or maximized at any point during play.
* The vertical felt gradient, top UI banners, buttons, and victory cascades scale in real-time to fit the window aspect ratio.
* Card piles are positioned at `TOP_PILE_Y = 110` and `START_Y = 280` to ensure visual clearance below the top stats bar.

---

## File Architecture

* **requirements.txt**: Specifies project library dependencies (`pygame>=2.5.0`).
* **config.py**: Spacing constants, gaps, vertical offsets, game settings, animation physics, and the HSL-tailored color scheme.
* **card.py**: The `Card` model managing coordinate properties, LERP updates, flip vectors, and the 2x supersampled high-res render cache.
* **solitaire_game.py**: Core rules verification, pile arrays (stock, waste, tableaus, foundations), double-click solvers, and snapshot-based infinite undos.
* **main.py**: The game display execution thread, capturing resize events, mouse dragging stack hitboxes, and the bouncing cascade canvas loop.

---

## How to Run the Game

### 1. Install Dependencies
Ensure Python is installed, then run the terminal command:
```bash
pip install -r requirements.txt
```

### 2. Launch the Game
Start Solitaire by running the main entrypoint script:
```bash
python main.py
```

### 3. Interactive Shortcuts
* **`U`** (or **`UNDO` button**): Reverse the last move. Piles glide backwards to their former stacks.
* **`R`** (or **`NEW GAME` button**): Shuffle the deck and deal a new game.
* **`W`**: Debug key to trigger the bouncing card victory cascade.
* **`ESC`**: Exit the application.
