import asyncio
import random
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
import threading
import time
import math
from tkinter import ttk, messagebox
from abc import ABC, abstractmethod
from wild_ai_bot_setup import wild_ai_make_bid,wild_ai_call_fake
class Die:
    def __init__(self):
        self.value = 1
        self.is_wild = False

    def roll(self):
        self.value = random.randint(1, 6)
        self.is_wild = False


class Player(ABC):
    def __init__(self, name):
        self.name = name
        self.dice = [Die() for _ in range(5)]

    def roll_dice(self):
        for die in self.dice:
            die.roll()

    @abstractmethod
    def make_bid(self, current_bid):
        pass

    @abstractmethod
    def call_fake_bid(self, current_bid):
        pass


class HumanPlayer(Player):
    def make_bid(self, current_bid):
        pass

    def call_fake_bid(self, current_bid):
        pass

    def use_ai_hint(self):
        game_flow = app.history
        dice = [die.value for die in self.dice]
        play_style = "optimal"
        wild_ones_mode = app.game.state.wild_ones
        is_fake = wild_ai_call_fake(game_flow, dice, self.name, play_style, wild_ones_mode, hint=True)
        if is_fake[0]:
            return ['call fake', is_fake[1]]
        else:
            new_bit = wild_ai_make_bid(game_flow, dice, self.name, play_style, wild_ones_mode, hint=True)
            return new_bit


class BotPlayer(Player):
    def __init__(self, name, difficulty):
        super().__init__(name)
        self.difficulty = difficulty

    def make_bid(self, current_bid, total_dice):
        if self.difficulty == "easy":
            return self.easy_bid(current_bid)
        elif self.difficulty == "medium":
            return self.medium_bid(current_bid, total_dice)
        else:
            return self.hard_bid(current_bid, total_dice)

    def easy_bid(self, current_bid):
        if random.random() < 0.5:
            return (current_bid[0] + 1, current_bid[1])
        else:
            return (current_bid[0], min(current_bid[1] + 1, 6))

    def medium_bid(self, current_bid, total_dice):
        dice_count = {i: 0 for i in range(1, 7)}
        wild_count = 0
        dice = len(self.dice)
        risk_persentage = 0.2 + (dice / 10)

        for die in self.dice:
            if die.is_wild:
                wild_count += 1
            else:
                dice_count[die.value] += 1

        most_used_value = max(dice_count, key=dice_count.get)
        most_used_count = dice_count[most_used_value]
        total_for_most_used = most_used_count + wild_count
        remaining_dice = total_dice - dice
        expected_other_players_count = (most_used_count / 6) * remaining_dice * risk_persentage
        estimated_total_count = total_for_most_used + expected_other_players_count
        quantity, value = current_bid

        if estimated_total_count > quantity and value >= most_used_value:
            return (int(estimated_total_count), value)
        elif estimated_total_count >= quantity and value < most_used_value:
            return (int(estimated_total_count), most_used_value)
        else:
            return (quantity + 1, value)

    def hard_bid(self, current_bid, total_dice):
        game_flow = app.history
        dice = [die.value for die in self.dice]
        play_style = "optimal"
        wild_ones_mode = app.game.state.wild_ones
        new_bit = wild_ai_make_bid(game_flow, dice, self.name, play_style, wild_ones_mode)
        return new_bit

    def call_fake_bid(self, current_bid, players, wild_ones):
        if self.difficulty == "easy":
            return random.random() < 0.3
        elif self.difficulty == "medium":
            total_players = len(players)
            own_count = sum(1 for die in self.dice if die.value == current_bid[1] or die.is_wild)
            total_dice = sum(len(p.dice) for p in players)
            remaining_dice = total_dice - len(self.dice)
            expected_others = (1 / 6) * remaining_dice

            if wild_ones:
                expected_others += (1 / 6) * remaining_dice

            expected_total = own_count + expected_others
            required_percentage = 0.2 + (0.05 if not wild_ones else 0.1) * (total_players - 2)
            threshold = current_bid[0] * required_percentage
            chance = 5
            if wild_ones:
                chance = 3.5

            if current_bid[0] == 0:
                return False
            if own_count == 0 and current_bid[0] < (remaining_dice / chance):
                return False
            elif own_count == 0 and current_bid[0] == (remaining_dice / chance):
                return random.random() < 0.25
            elif own_count == 0 and current_bid[0] == (remaining_dice / chance + 1):
                return random.random() < 0.10
            if expected_total < current_bid[0]:
                return True

            return False

        else:
            game_flow = app.history
            dice = [die.value for die in self.dice]
            play_style = "optimal"
            wild_ones_mode = app.game.state.wild_ones
            is_fake = wild_ai_call_fake(game_flow, dice, self.name, play_style, wild_ones_mode)
            return is_fake
class GameState:
    def __init__(self, players: list, wild_ones: bool):
        self.players = players
        self.wild_ones = wild_ones
        self.current_bid = (0, 1)
        self.current_player_index = 0
        self.hint_is_used = False

    def next_player(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def count_dice(self, value):
        count = 0
        for player in self.players:
            for die in player.dice:
                if die.value == value or (self.wild_ones and die.value == 1):
                    count += 1
        return count


class Game:
    def __init__(self, num_bots, bot_difficulties, wild_ones):
        self.history = ''
        self.rounds = 0
        self.players = [HumanPlayer("Human")]
        self.players += [BotPlayer(f"Bot {i + 1}", difficulty) for i, difficulty in enumerate(bot_difficulties)]
        self.state = GameState(self.players, wild_ones)

    def start_round(self):
        self.rounds += 1
        app.add_info_text(f'Round {self.rounds}\n______________________\n')
        for player in self.players:
            player.roll_dice()
        if self.state.wild_ones:
            for player in self.players:
                for die in player.dice:
                    if die.value == 1:
                        die.is_wild = True
        self.state.current_bid = (0, 1)

    def make_bid(self, quantity, value):
        self.state.current_bid = (quantity, value)
        if self.state.current_player_index == 0:
            self.state.next_player()
            app.add_info_text(f"Human made a new bid of {quantity} {value}s\n")
        result = self.handle_bot_turns()
        return result

    def call_fake(self):
        call_faked_value = self.state.current_bid[1]
        actual_count = self.state.count_dice(call_faked_value)
        if actual_count >= self.state.current_bid[0]:
            loser = self.players[self.state.current_player_index]
            winner = self.players[(self.state.current_player_index - 1) % len(self.players)]
        else:
            winner = self.players[self.state.current_player_index]
            loser = self.players[(self.state.current_player_index - 1) % len(self.players)]
        if (len(loser.dice) - 1) == 0:
            self.state.current_player_index = (self.players.index(loser) - 1) % len(self.players)
            self.players.remove(loser)
            app.add_info_text(f"{loser.name} has no more dice and lose the game!")
        else:
            self.state.current_player_index = self.players.index(loser)
        return winner, loser, actual_count

    def handle_bot_turns(self):
        while isinstance(self.players[self.state.current_player_index], BotPlayer):
            current_player = self.players[self.state.current_player_index]
            info_text = f"Current player: {current_player.name}\n{current_player.name} is thinking...\n"
            app.add_info_text(info_text)
            time.sleep(2)
            if current_player.call_fake_bid(self.state.current_bid, self.players, self.state.wild_ones):
                app.add_info_text(f"{current_player.name} call faked!\n")
                return "call_fake", current_player
            else:
                new_bid = current_player.make_bid(self.state.current_bid, sum(len(p.dice) for p in self.players))
                self.state.current_bid = new_bid
                app.add_info_text(f"{current_player.name} made a bid of {new_bid[0]} {new_bid[1]}s!\n")
                self.state.next_player()
        return "continue", None


class CustomSpinbox(tk.Frame):
    def __init__(self, master, from_, to, update_command, **kwargs):
        super().__init__(master, **kwargs)
        self.value = tk.IntVar(value=from_)
        self.update_command = update_command
        self.increment_button = ttk.Button(self, text="▲", command=self.increment)
        self.increment_button.pack(side=tk.TOP, padx=5)
        self.entry = ttk.Entry(self, textvariable=self.value, width=5, justify='center')
        self.entry.pack(side=tk.TOP, padx=5)
        self.decrement_button = ttk.Button(self, text="▼", command=self.decrement)
        self.decrement_button.pack(side=tk.TOP, padx=5)
        self.from_ = from_
        self.to = to

    def increment(self):
        if self.value.get() < self.to:
            self.value.set(self.value.get() + 1)
            self.update_command()

    def decrement(self):
        if self.value.get() > self.from_:
            self.value.set(self.value.get() - 1)
            self.update_command()

    def get(self):
        return self.value.get()


class LoadingSpinner:
    def __init__(self, master, size=50):
        self.master = master
        self.size = size
        self.canvas = tk.Canvas(master, width=size, height=size, bg='#f5f5f5', highlightthickness=0)
        self.angle = 0
        self.is_running = False

    def start(self):
        self.is_running = True
        self.draw_frame()

    def stop(self):
        self.is_running = False
        self.canvas.delete("all")

    def draw_frame(self):
        if not self.is_running:
            return
        self.canvas.delete("all")
        start_angle = self.angle
        extent = 100
        x0 = y0 = 5
        x1 = y1 = self.size - 5
        self.canvas.create_arc(x0, y0, x1, y1, start=start_angle, extent=extent, width=3, style="arc", outline="#4a90e2")
        self.angle = (self.angle + 10) % 360
        self.master.after(50, self.draw_frame)

    def pack(self, **kwargs):
        self.canvas.pack(**kwargs)

    def grid(self, **kwargs):
        self.canvas.grid(**kwargs)


class LoadingModal:
    def __init__(self, master):
        self.loading_window = tk.Toplevel(master)
        window_x = master.winfo_x()
        window_y = master.winfo_y()
        window_width = master.winfo_width()
        window_height = master.winfo_height()
        modal_width = 300
        modal_height = 200

        x_position = window_x + (window_width - modal_width) // 2
        y_position = window_y + (window_height - modal_height) // 2
        self.loading_window.geometry(f"{modal_width}x{modal_height}+{x_position}+{y_position}")
        self.loading_window.configure(bg='#f5f5f5')
        self.loading_window.transient(master)
        self.loading_window.grab_set()
        self.loading_window.overrideredirect(True)

        content_frame = ttk.Frame(self.loading_window, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)

        self.spinner = LoadingSpinner(content_frame)
        self.spinner.pack(pady=(0, 15))

        self.loading_text = ttk.Label(content_frame, text="AI is analyzing the game state...", font=('Arial', 12), wraplength=250)
        self.loading_text.pack()

        self.spinner.start()

    def destroy(self):
        self.spinner.stop()
        self.loading_window.destroy()


class HintModal:
    def __init__(self, master, hint_text):
        self.hint_window = tk.Toplevel(master)
        self.hint_window.title("AI Hint")

        window_x = master.winfo_x()
        window_y = master.winfo_y()
        window_width = master.winfo_width()
        window_height = master.winfo_height()

        modal_width = 400
        modal_height = 300
        x_position = window_x + (window_width - modal_width) // 2
        y_position = window_y + (window_height - modal_height) // 2

        self.hint_window.geometry(f"{modal_width}x{modal_height}+{x_position}+{y_position}")
        self.hint_window.configure(bg='#f5f5f5')
        self.hint_window.transient(master)
        self.hint_window.grab_set()

        content_frame = ttk.Frame(self.hint_window, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(
            content_frame,
            text="Strategic Advice",
            font=('Arial', 16, 'bold'),
            wraplength=350
        )
        title_label.pack(pady=(0, 15))

        desc_label = ttk.Label(
            content_frame,
            text=hint_text['description'],
            wraplength=350,
            font=('Arial', 11),
            justify=tk.LEFT
        )
        desc_label.pack(pady=(0, 15))

        conclusion_label = ttk.Label(
            content_frame,
            text=hint_text['conclusion'],
            wraplength=350,
            font=('Arial', 11, 'italic'),
            justify=tk.LEFT
        )
        conclusion_label.pack(pady=(0, 20))

        close_button = ttk.Button(
            content_frame,
            text="Got it!",
            command=self.hint_window.destroy
        )
        close_button.pack()

class HintButton:
    def __init__(self, master, hint_is_used):
        style = ttk.Style()
        style.configure(
            'Hint.TButton',
            background='#4a90e2',
            foreground='white',
            padding=(10, 5),
            font=('Arial', 10)
        )

        self.hint_button = ttk.Button(
            master,
            text="🔍 AI Hint",
            style='Hint.TButton',
            command=self.show_hint
        )

        self.master = master
        self.hint_is_used = hint_is_used
        self.loading_modal = None
        self.update_button_state()

        self.loop = asyncio.new_event_loop()
        self.executor = ThreadPoolExecutor(max_workers=1)

    def update_button_state(self):
        if self.hint_is_used:
            self.hint_button.configure(state='disabled')
            self.hint_button.configure(text="❌ Hint Used")
        else:
            self.hint_button.configure(state='normal')
            self.hint_button.configure(text="🔍 AI Hint")

    def fetch_hint_data(self):
        response = app.game.players[0].use_ai_hint()
        if response:
            self.hint_is_used = True
        return {
            'description': response[1],
            'conclusion': response[0]
        }

    def run_async_fetch(self):
        asyncio.set_event_loop(self.loop)
        hint_text = self.fetch_hint_data()
        self.master.after(0, self.show_hint_modal, hint_text)

    def show_hint(self):
        if not self.hint_is_used:
            self.loading_modal = LoadingModal(self.master)
            thread = threading.Thread(target=self.run_async_fetch)
            thread.daemon = True
            thread.start()

    def show_hint_modal(self, hint_text):
        if self.loading_modal:
            self.loading_modal.destroy()
            self.loading_modal = None

        HintModal(self.master, hint_text)
        self.hint_is_used = True
        self.update_button_state()

    def pack(self, **kwargs):
        self.hint_button.pack(**kwargs)

    def grid(self, **kwargs):
        self.hint_button.grid(**kwargs)

    def __del__(self):
        if hasattr(self, 'loop') and self.loop is not None:
            self.loop.close()
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

class LiarsDiceGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Liar's Dice")
        self.master.geometry("900x750")
        self.master.configure(bg='#f0f0f0')
        self.history = ''

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TButton', background='#4CAF50', foreground='white', font=('Arial', 12))
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 12))
        style.configure('TCheckbutton', background='#f0f0f0', font=('Arial', 12))

        self.setup_frame = ttk.Frame(self.master, padding="20")
        self.setup_frame.pack(fill=tk.BOTH, expand=True, pady=(10))

        ttk.Label(self.setup_frame, text="Liar's Dice", font=('Arial', 24, 'bold')).pack(pady=15)

        ttk.Label(self.setup_frame, text="Number of Bots:").pack(pady=5)
        self.bot_count = CustomSpinbox(self.setup_frame, from_=1, to=10, update_command=self.update_bot_difficulties)
        self.bot_count.pack(pady=5)
        self.bot_count.get()
        self.bot_count.value.set(1)

        self.difficulties_frame = ttk.Frame(self.setup_frame)
        self.difficulties_frame.pack(pady=(10, 30))

        self.bot_difficulties = []
        self.update_bot_difficulties()

        self.wild_ones_var = tk.BooleanVar()
        ttk.Checkbutton(self.setup_frame, text="Wild Ones Mode", variable=self.wild_ones_var).pack(pady=5)

        self.hide_all_dice_var = tk.BooleanVar()
        ttk.Checkbutton(self.setup_frame, text="Hide all dice", variable=self.hide_all_dice_var).pack(pady=5)

        ttk.Button(self.setup_frame, text="Start Game", command=self.start_game).pack(pady=(20))

        self.game_frame = ttk.Frame(self.master, padding="20")
        self.left_frame = ttk.Frame(self.game_frame)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.right_frame = ttk.Frame(self.game_frame)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.dice_frames = ttk.Frame(self.left_frame)
        self.dice_frames.grid(row=0, column=0, padx=10, pady=10)

        self.bid_frame = ttk.Frame(self.left_frame)
        self.bid_frame.grid(row=1, column=0, padx=10, pady=10)

        self.action_frame = ttk.Frame(self.left_frame)
        self.action_frame.grid(row=2, column=0, padx=10, pady=10)

        self.info_frame = ttk.Frame(self.right_frame)
        self.info_frame.grid_remove()

        self.game_frame.columnconfigure(0, weight=1)
        self.game_frame.columnconfigure(1, weight=1)
        self.game = None

    def start_game(self):
        num_bots = int(self.bot_count.get())
        difficulties = [diff.get() for diff in self.bot_difficulties[:num_bots]]
        wild_ones = self.wild_ones_var.get()
        self.game = Game(num_bots, difficulties, wild_ones)

        self.setup_frame.pack_forget()
        self.game_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.right_frame, height=700)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(self.right_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.info_frame = ttk.Frame(self.canvas)

        self.canvas_window = self.canvas.create_window((0, 0), window=self.info_frame, anchor="nw")

        self.info_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        self.start_round()

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def add_info_text(self, text):
        self.history += text
        label = ttk.Label(self.info_frame, text=text, justify=tk.LEFT, wraplength=self.canvas.winfo_width() - 20)
        label.pack(fill=tk.X, expand=True, padx=5, pady=5)

        self.info_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        self.canvas.yview_moveto(1)

    def update_bot_difficulties(self):
        for widget in self.difficulties_frame.winfo_children():
            widget.destroy()

        self.bot_difficulties = []
        difficulties = ["easy", "medium", "hard"]
        for i in range(int(self.bot_count.get())):
            ttk.Label(self.difficulties_frame, text=f"Bot {i + 1} Difficulty:").grid(row=i, column=0, padx=5, pady=2)
            diff = ttk.Combobox(self.difficulties_frame, values=difficulties, width=10)
            diff.grid(row=i, column=1, padx=5, pady=2)
            diff.set(difficulties[1])
            self.bot_difficulties.append(diff)

    def start_round(self):
        self.game.start_round()
        self.update_display()

    def update_display(self):
        hide_all_dice = self.hide_all_dice_var.get()

        for widget in self.dice_frames.winfo_children():
            widget.destroy()
        for widget in self.bid_frame.winfo_children():
            widget.destroy()
        for widget in self.action_frame.winfo_children():
            widget.destroy()

        style = ttk.Style()
        style.configure("Yellow.TLabel", background="yellow")

        for i, player in enumerate(self.game.players):
            player_frame = ttk.Frame(self.dice_frames)
            player_frame.pack(fill=tk.X, pady=5)
            if isinstance(player, HumanPlayer):
                ttk.Label(player_frame, text=f"{player.name}'s dice:", font=('Arial', 12, 'bold'),
                          style="Yellow.TLabel").pack(side=tk.LEFT, padx=5)
            else:
                ttk.Label(player_frame, text=f"{player.name}'s dice:", font=('Arial', 12, 'bold')).pack(side=tk.LEFT,
                                                                                                        padx=5)

            for die in player.dice:
                if isinstance(player, HumanPlayer) or not hide_all_dice:
                    if self.game.state.wild_ones and die.value == 1:
                        text = "WILD"
                        color = "yellow"
                    else:
                        text = str(die.value)
                        color = "white"
                else:
                    text = "?"
                    color = "white"
                ttk.Label(player_frame, text=text, width=4, background=color, borderwidth=1, relief="solid").pack(
                    side=tk.LEFT, padx=2)

        ttk.Label(self.bid_frame, text="Quantity:").pack(anchor=tk.CENTER, padx=5)
        self.quantity_entry = ttk.Spinbox(self.bid_frame, from_=1, to=30, width=5)
        self.quantity_entry.pack(anchor=tk.CENTER, padx=5)
        self.quantity_entry.set(self.game.state.current_bid[0] + 1)

        ttk.Label(self.bid_frame, text="Value:").pack(anchor=tk.CENTER, padx=5)
        self.value_entry = ttk.Spinbox(self.bid_frame, from_=1, to=6, width=5)
        self.value_entry.pack(anchor=tk.CENTER, padx=5)
        self.value_entry.set(self.game.state.current_bid[1])
        self.hint_button = HintButton(self.bid_frame, self.game.state.hint_is_used)
        self.hint_button.pack(side=tk.RIGHT, pady=15)

        ttk.Button(self.action_frame, text="Make Bid", command=self.make_bid).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.action_frame, text="Call Fake", command=self.call_fake).pack(side=tk.RIGHT, padx=5)
        curent_player = self.game.players[self.game.state.current_player_index]
        info_text = f"Current bid: {self.game.state.current_bid[0]} dice with value {self.game.state.current_bid[1]}\n"
        info_text += f"Current player: {curent_player.name}\n"
        info_text += "Players:\n"
        for player in self.game.players:
            info_text += f"{player.name}: {len(player.dice)} dice\n"
        info_text += f"{curent_player.name} is thinking...\n"
        self.add_info_text(info_text)

    def make_bid(self):
        quantity = int(self.quantity_entry.get())
        value = int(self.value_entry.get())

        if quantity < self.game.state.current_bid[0] or (
                quantity == self.game.state.current_bid[0] and value <= self.game.state.current_bid[1]):
            messagebox.showerror("Invalid Bid", "Humans bid must be higher than the current bid.")
            return

        result, challenging_bot = self.game.make_bid(quantity, value)
        if result == "call_fake":
            self.handle_call_fake(challenging_bot)
        else:
            self.update_display()

    def call_fake(self):
        winner, loser, actual_count = self.game.call_fake()
        self.show_round_result(winner, loser, actual_count)
        loser.dice.pop()

    def handle_call_fake(self, challenging_bot):
        winner, loser, actual_count = self.game.call_fake()
        self.show_round_result(winner, loser, actual_count, challenging_bot)
        loser.dice.pop()

    def show_round_result(self, winner, loser, actual_count, challenging_bot=None):
        result_window = tk.Toplevel(self.master)
        result_window.title("Round Result")
        result_window.geometry("400x600")
        result_window.configure(bg='#f0f0f0')
        info_text = ''

        if challenging_bot:
            ttk.Label(result_window, text=f"{challenging_bot.name} call faked the bid!",
                      font=('Arial', 14, 'bold')).pack(pady=10)
            info_text += f"{challenging_bot.name} call faked the bid!\n"
        else:
            info_text += f"Human call faked the bid!\n"

        ttk.Label(result_window, text=f"{winner.name} wins the call fake!", font=('Arial', 14, 'bold')).pack(pady=10)
        info_text += f"{winner.name} wins the call fake!\n"

        ttk.Label(result_window,
                  text=f"There were actually {actual_count} dice with value {self.game.state.current_bid[1]}.",
                  font=('Arial', 12)).pack(pady=5)
        info_text += f"There were actually {actual_count} dice with value {self.game.state.current_bid[1]}.\n"

        ttk.Label(result_window, text=f"{loser.name} loses a die.", font=('Arial', 12)).pack(pady=5)
        info_text += f"{loser.name} loses a die..\n"

        for player in self.game.players:
            player_frame = ttk.Frame(result_window)
            player_frame.pack(fill=tk.X, pady=5)
            ttk.Label(player_frame, text=f"{player.name}'s dice:", font=('Arial', 12, 'bold')).pack(side=tk.LEFT,
                                                                                                    padx=5)
            for die in player.dice:
                if self.game.state.wild_ones and die.value == 1:
                    text = "WILD"
                    color = "yellow"
                else:
                    text = str(die.value)
                    color = "white"
                ttk.Label(player_frame, text=text, width=4, background=color, borderwidth=1, relief="solid").pack(
                    side=tk.LEFT, padx=2)

        self.add_info_text(info_text)

        def close_and_continue():
            result_window.destroy()
            if len(self.game.players) == 1:
                messagebox.showinfo("Game Over", f"{self.game.players[0].name} wins the game!")
                self.master.quit()
            elif not isinstance(self.game.players[0], HumanPlayer):
                messagebox.showinfo("Game Over", f"Human have lost!")
                self.master.quit()
            else:
                self.start_round()
                if self.game.state.current_player_index != 0:
                    self.make_bid()

        ttk.Button(result_window, text="Continue", command=close_and_continue).pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = LiarsDiceGUI(root)
    root.mainloop()
