import random
import time
import tkinter as tk
from operator import index
from tkinter import ttk, messagebox
from abc import ABC, abstractmethod
from wild_ai_bot_setup import wild_ai_make_bid,wild_ai_call_fake

# Die class represents a single die used in the game
class Die:
    def __init__(self):
        self.value = 1  # Initial value of the die is 1
        self.is_wild = False  # Indicates if the die is considered 'wild' in certain game modes

    # Method to simulate rolling the die
    def roll(self):
        self.value = random.randint(1, 6)  # Randomly assigns a value between 1 and 6
        self.is_wild = False  # Resets the 'wild' status after every roll


# Abstract base class for a player, can be either a human or a bot
class Player(ABC):
    def __init__(self, name):
        self.name = name  # Stores the player's name
        # Creates a set of 5 dice for the player
        self.dice = [Die() for _ in range(5)]

    # Rolls all dice of the player
    def roll_dice(self):
        for die in self.dice:
            die.roll()

    # Abstract method to make a bid, implemented in derived classes
    @abstractmethod
    def make_bid(self, current_bid):
        pass

    # Abstract method to call out a fake bid, implemented in derived classes
    @abstractmethod
    def call_fake_bid(self, current_bid):
        pass


# Represents a human player, controlled through the GUI
class HumanPlayer(Player):
    def make_bid(self, current_bid):
        # Human bid logic will be handled by the GUI interface
        pass

    def call_fake_bid(self, current_bid):
        # Human call logic will be handled by the GUI interface
        pass

    def use_ai_hint(self):
        game_flow = app.history
        dice = [die.value for die in self.dice]
        play_style = "optimal"
        wild_ones_mode = app.game.state.wild_ones
        is_fake = wild_ai_call_fake(game_flow, dice, self.name, play_style, wild_ones_mode,hint=True)
        if is_fake[0]:
            return ['call fake',is_fake[1]]
        else:
            new_bit = wild_ai_make_bid(game_flow, dice, self.name, play_style, wild_ones_mode,hint=True)
            return new_bit
        


# BotPlayer class simulates a computer-controlled player with varying difficulty
class BotPlayer(Player):
    def __init__(self, name, difficulty):
        super().__init__(name)
        self.difficulty = difficulty  # Sets the bot's difficulty (easy, medium, hard)

    # Bot's bid-making logic based on difficulty and the current bid

    def make_bid(self, current_bid, total_dice):
        # time.sleep(2)

        if self.difficulty == "easy":
            return self.easy_bid(current_bid)  # Simple bidding strategy
        elif self.difficulty == "medium":
            return self.medium_bid(current_bid, total_dice)  # Moderate complexity
        else:
            return self.hard_bid(current_bid, total_dice)  # Complex decision-making

    # Simple bid strategy for easy bots: always increase the quantity

    def easy_bid(self, current_bid):
        if random.random() < 0.5:
            return (current_bid[0] + 1, current_bid[1])  # Increase quantity
        else:
            return (current_bid[0], min(current_bid[1] + 1, 6))  # Increases the quantity but keeps the face value same

    # Medium bid strategy: has a 50% chance to increase the quantity or the face value

    def medium_bid(self, current_bid, total_dice):
        # Step 1: Count the occurrences of each dice value the player has
        dice_count = {i: 0 for i in range(1, 7)}  # For dice values 1 to 6
        wild_count = 0
        dice = len(self.dice)
        risk_persentage = 0.2 + (dice / 10)

        # Count dice and handle wild ones
        for die in self.dice:
            if die.is_wild:  # Assuming 1 is wild in this game
                wild_count += 1
            else:
                dice_count[die.value] += 1

        # Step 2: Identify the highest occurring dice face
        most_used_value = max(dice_count, key=dice_count.get)
        most_used_count = dice_count[most_used_value]

        # Include wild dice in the total count for the most frequent value
        total_for_most_used = most_used_count + wild_count

        # Step 3: Estimate expected count for most used dice face on the table
        remaining_dice = total_dice - dice

        # Estimate how many dice of the most frequent face might be held by others
        expected_other_players_count = (most_used_count / 6) * remaining_dice * risk_persentage

        # Total estimated count for the most used dice value (including wilds)
        estimated_total_count = total_for_most_used + expected_other_players_count

        # Step 4: Compare with the current bid
        quantity, value = current_bid
        #     own_count=
        if estimated_total_count > quantity and value >= most_used_value:
            return (int(estimated_total_count), value)

        elif estimated_total_count >= quantity and value < most_used_value:
            return (int(estimated_total_count), most_used_value)
        else:
            return (quantity + 1, value)  # Increase face value if bid cannot be raised

    # Advanced bid strategy: estimates based on the number of dice the bot has and the total dice in the game
    def hard_bid(self, current_bid, total_dice):
        game_flow = app.history
        dice = [die.value for die in  self.dice]
        play_style="optimal"
        wild_ones_mode= app.game.state.wild_ones
        new_bit = wild_ai_make_bid(game_flow,dice,self.name,play_style,wild_ones_mode)
        return new_bit

    # Bot decision to call out a fake bid (Liar!) based on difficulty
    def call_fake_bid(self, current_bid, players, wild_ones):
        # Easy bots call out a lie 20% of the time

        if self.difficulty == "easy":
            # time.sleep(2)
            return random.random() < 0.3  # Medium bots call out a lie 30% of the time
        elif self.difficulty == "medium":
            # time.sleep(2)
            total_players = len(players)
            # Number of dice the bot has matching the current bid or are wild
            own_count = sum(1 for die in self.dice if die.value == current_bid[1] or die.is_wild)

            # Total dice in the game
            total_dice = sum(len(p.dice) for p in players)
            # Calculate remaining dice held by other players
            remaining_dice = total_dice - len(self.dice)

            # Estimate how many matching dice other players might have
            expected_others = (1 / 6) * remaining_dice

            # Include wild dice if the wild_ones rule is on
            if wild_ones:
                expected_others += (1 / 6) * remaining_dice  # Wild dice can match any value

            # Calculate the expected total matching dice (bot's dice + expected others)
            expected_total = own_count + expected_others

            # Dynamic threshold based on the number of players
            required_percentage = 0.2 + (0.05 if not wild_ones else 0.1) * (total_players - 2)
            threshold = current_bid[0] * required_percentage
            chance = 5
            if wild_ones:
                chance = 3.5
            # If the bot has fewer than the threshold of dice, it calls a fake bid
            if current_bid[0] == 0:
                return False
            if own_count == 0 and current_bid[0] < (remaining_dice / chance):
                # If the bot has 0 matching dice, introduce some logic for calling a fake bid
                # It will call a fake bid based on a weighted chance that expected_total won't reach the current bid
                return False  # Higher chance of calling if own count is 0
            elif own_count == 0 and current_bid[0] == (remaining_dice / chance):
                # If the bot has 0 matching dice, introduce some logic for calling a fake bid
                # It will call a fake bid based on a weighted chance that expected_total won't reach the current bid
                return random.random() < 0.25
            elif own_count == 0 and current_bid[0] == (remaining_dice / chance + 1):
                # If the bot has 0 matching dice, introduce some logic for calling a fake bid
                # It will call a fake bid based on a weighted chance that expected_total won't reach the current bid
                return random.random() < 0.10
            # Compare the expected total to the current bid
            if expected_total < current_bid[0]:
                return True  # Call a fake bid if expected total doesn't meet the current bid

            return False  # Do not call if expected total seems reasonable

        else:
            game_flow = app.history
            dice = [die.value for die in self.dice]
            play_style = "optimal"
            wild_ones_mode = app.game.state.wild_ones
            is_fake = wild_ai_call_fake(game_flow, dice, self.name, play_style, wild_ones_mode)
            return is_fake


class GameState:
    def __init__(self, players: list, wild_ones: bool):
        # Initializes the game state, storing the players, wild ones rule, current bid, and current player.
        self.players = players  # List of all players in the game (human and bots)
        self.wild_ones = wild_ones  # Boolean flag indicating if 'wild ones' rule is active (1s count as wild)
        self.current_bid = (0, 1)  # Current bid in the form (quantity, face value)
        self.current_player_index = 0  # Index of the current player in the players list

    def next_player(self):
        # Advances to the next player by incrementing the player index in a circular fashion.
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def count_dice(self, value):
        # Counts the total number of dice across all players that match the given value (or 1 if wild ones are active).
        count = 0
        for player in self.players:
            for die in player.dice:
                # If wild ones is active and the die is 1, it counts as wild (matches any face value).
                if die.value == value or (self.wild_ones and die.value == 1):
                    count += 1
        return count  # Return the total count of matching dice in the game


class Game:

    def __init__(self, num_bots, bot_difficulties, wild_ones):
        self.history = ''
        self.rounds = 0
        # Initializes the game with a human player and the specified number of bots.
        self.players = [HumanPlayer("Human")]  # Start with one human player
        # Add the specified number of bot players with their respective difficulties
        self.players += [BotPlayer(f"Bot {i + 1}", difficulty) for i, difficulty in enumerate(bot_difficulties)]
        # Create the game state, passing in the players and the wild ones rule
        self.state = GameState(self.players, wild_ones)

    def start_round(self):
        self.rounds += 1
        app.add_info_text(f'Round {self.rounds}\n______________________\n')
        # Starts a new round by rolling dice for each player and resetting the bid and player turn.
        for player in self.players:
            player.roll_dice()  # Roll all dice for each player
        # If the wild ones rule is active, set dice with value 1 to wild
        if self.state.wild_ones:
            for player in self.players:
                for die in player.dice:
                    if die.value == 1:
                        die.is_wild = True
        # Reset the current bid and player index to start the round
        self.state.current_bid = (0, 1)
        # self.state.current_player_index = 0

    def make_bid(self, quantity, value):
        # Handles when a player makes a bid by setting the current bid and advancing the turn.
        self.state.current_bid = (quantity, value)
        if self.state.current_player_index == 0:  # Update the current bid with the new bid
            self.state.next_player()
            app.add_info_text(f"Human made a new bid of {quantity} {value}s\n")

        result = self.handle_bot_turns()

        # If it's a bot's turn, handle the bot's actions and return the result
        return result

    def call_fake(self):
        # Handles the case when a player calls the previous bid as fake, checking the actual count of matching dice.
        call_faked_value = self.state.current_bid[1]  # Get the face value of the current bid
        actual_count = self.state.count_dice(call_faked_value)  # Count how many dice match the bid face value

        # Determine the winner and loser based on the actual count versus the bid
        if actual_count >= self.state.current_bid[0]:
            # If the actual count is equal to or exceeds the bid, the current player loses (called wrongly)
            loser = self.players[self.state.current_player_index]
            winner = self.players[(self.state.current_player_index - 1) % len(self.players)]
        else:
            # Otherwise, the previous player (who made the bid) loses
            winner = self.players[self.state.current_player_index]
            loser = self.players[(self.state.current_player_index - 1) % len(self.players)]

        # loser.dice.pop()  # The loser loses a die

        if (len(loser.dice) - 1) == 0:
            # If the loser has no dice left, remove them from the game
            self.state.current_player_index = (self.players.index(loser) - 1) % len(self.players)
            self.players.remove(loser)
            app.add_info_text(f"{loser.name} has no more dice and lose the game!")

        else:
            self.state.current_player_index = self.players.index(loser)

        return winner, loser, actual_count  # Return the winner, loser, and actual count of matching dice

    def handle_bot_turns(self):
        # Handles bot turns, making the bots either call a fake bid or make a new bid.
        while isinstance(self.players[self.state.current_player_index], BotPlayer):
            current_player = self.players[self.state.current_player_index]
            info_text = ''
            # info_text += f"Current bid: {self.state.current_bid[0]} dice with value {self.state.current_bid[1]}\n"
            info_text += f"Current player: {current_player.name}\n"
            info_text += f"{current_player.name} is thinking...\n"

            # Get the current bot player
            app.add_info_text(info_text)
            time.sleep(2)  # Check if the bot wants to call the current bid as fake
            if current_player.call_fake_bid(self.state.current_bid, self.players, self.state.wild_ones):
                app.add_info_text(f"{current_player.name} call faked!\n")
                return "call_fake", current_player  # Return that the bot called the bid as fake
            else:
                # Otherwise, the bot makes a new bid
                new_bid = current_player.make_bid(self.state.current_bid, sum(len(p.dice) for p in self.players))
                self.state.current_bid = new_bid
                app.add_info_text(f"{current_player.name} made a bid of {new_bid[0]} {new_bid[1]}s!\n")
                # Update the game state with the bot's new bid
                self.state.next_player()  # Move to the next player
        return "continue", None  # Continue the game if no bots call a fake bid


class CustomSpinbox(tk.Frame):
    def __init__(self, master, from_, to, update_command, **kwargs):
        super().__init__(master, **kwargs)

        self.value = tk.IntVar(value=from_)
        self.update_command = update_command  # Store the update command

        # Create increment button
        self.increment_button = ttk.Button(self, text="▲", command=self.increment)
        self.increment_button.pack(side=tk.TOP, padx=5)

        # Create Entry for the value display
        self.entry = ttk.Entry(self, textvariable=self.value, width=5, justify='center')
        self.entry.pack(side=tk.TOP, padx=5)

        # Create decrement button
        self.decrement_button = ttk.Button(self, text="▼", command=self.decrement)
        self.decrement_button.pack(side=tk.TOP, padx=5)

        # Set from_ and to limits
        self.from_ = from_
        self.to = to

    def increment(self):
        if self.value.get() < self.to:
            self.value.set(self.value.get() + 1)
            self.update_command()  # Call the update command

    def decrement(self):
        if self.value.get() > self.from_:
            self.value.set(self.value.get() - 1)
            self.update_command()  # Call the update command

    def get(self):
        """Return the current value of the spinbox."""
        return self.value.get()


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

        # Bot count and other setup elements here...
        ttk.Label(self.setup_frame, text="Number of Bots:").pack(pady=5)
        self.bot_count = CustomSpinbox(self.setup_frame, from_=1, to=10, update_command=self.update_bot_difficulties)
        self.bot_count.pack(pady=5)
        self.bot_count.get()  # Set default bot count initially to 3
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

        # Game frame layout
        self.game_frame = ttk.Frame(self.master, padding="20")

        # Create the main frame layout
        self.left_frame = ttk.Frame(self.game_frame)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.right_frame = ttk.Frame(self.game_frame)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Left side frames (dice, bid, and action)
        self.dice_frames = ttk.Frame(self.left_frame)
        self.dice_frames.grid(row=0, column=0, padx=10, pady=10)

        self.bid_frame = ttk.Frame(self.left_frame)
        self.bid_frame.grid(row=1, column=0, padx=10, pady=10)

        self.action_frame = ttk.Frame(self.left_frame)
        self.action_frame.grid(row=2, column=0, padx=10, pady=10)

        # Right side frame (info_frame in a scrollable frame)
        self.info_frame = ttk.Frame(self.right_frame)

        # Initially hide the info frame
        self.info_frame.grid_remove()

        self.game_frame.columnconfigure(0, weight=1)
        self.game_frame.columnconfigure(1, weight=1)
        self.game = None

    def start_game(self):
        # Retrieves the number of bots and selected difficulties
        num_bots = int(self.bot_count.get())
        difficulties = [diff.get() for diff in self.bot_difficulties[:num_bots]]
        wild_ones = self.wild_ones_var.get()
        # Initializes the Game object with the selected options
        self.game = Game(num_bots, difficulties, wild_ones)
        # history=self.game.history

        # Hides the setup frame and shows the game frame
        self.setup_frame.pack_forget()
        self.game_frame.pack(fill=tk.BOTH, expand=True)

        # Create a canvas widget
        self.canvas = tk.Canvas(self.right_frame, height=700)
        self.canvas.pack(side="left", fill="both", expand=True)

        # Add a scrollbar to the canvas
        self.scrollbar = ttk.Scrollbar(self.right_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")

        # Configure the canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Create another frame inside the canvas
        self.info_frame = ttk.Frame(self.canvas)

        # Add that frame to a window in the canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.info_frame, anchor="nw")

        # Make sure the frame takes up the full width of the canvas
        self.info_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        # Starts a new round
        self.start_round()

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def add_info_text(self, text):
        """Add text to the scrollable info frame."""
        self.history += text
        label = ttk.Label(self.info_frame, text=text, justify=tk.LEFT, wraplength=self.canvas.winfo_width() - 20)
        label.pack(fill=tk.X, expand=True, padx=5, pady=5)

        # Update the scroll region to encompass the new content
        self.info_frame.update_idletasks()  # Update the sizes of the widgets
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))  # Update scroll region

        # Scroll to the bottom
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
            diff.set(difficulties[1])  # Set default difficulty to medium
            self.bot_difficulties.append(diff)

    # def start_game(self):
    #     # Retrieves the number of bots and selected difficulties
    #     num_bots = int(self.bot_count.get())
    #     difficulties = [diff.get() for diff in self.bot_difficulties[:num_bots]]
    #     wild_ones = self.wild_ones_var.get()
    #     # Gets the wild ones mode status
    #
    #     # Initializes the Game object with the selected options
    #     self.game = Game(num_bots, difficulties, wild_ones)
    #
    #     # Hides the setup frame and shows the game frame
    #     self.setup_frame.pack_forget()
    #     self.game_frame.pack(fill=tk.BOTH, expand=True)
    #
    #
    #     # Starts a new round
    #     self.start_round()

    def start_round(self):

        # Calls the start_round method in the game logic to begin a new round
        self.game.start_round()
        self.update_display()  # Updates the UI with the new round information

    def update_display(self):
        hide_all_dice = self.hide_all_dice_var.get()

        # Clears the current game display (dice, bids, actions, info)
        for widget in self.dice_frames.winfo_children():
            widget.destroy()
        for widget in self.bid_frame.winfo_children():
            widget.destroy()
        for widget in self.action_frame.winfo_children():
            widget.destroy()
        # for widget in self.info_frame.winfo_children():
        #     widget.destroy()

        # Loops through all players and displays their dice
        style = ttk.Style()
        style.configure("Yellow.TLabel", background="yellow")  # Create a new style with yellow background

        for i, player in enumerate(self.game.players):
            player_frame = ttk.Frame(self.dice_frames)  # Creates a frame for each player's dice
            player_frame.pack(fill=tk.X, pady=5)
            if isinstance(player, HumanPlayer):
                ttk.Label(player_frame, text=f"{player.name}'s dice:", font=('Arial', 12, 'bold'),
                          style="Yellow.TLabel").pack(side=tk.LEFT, padx=5)
            else:
                ttk.Label(player_frame, text=f"{player.name}'s dice:", font=('Arial', 12, 'bold')).pack(side=tk.LEFT,
                                                                                                        padx=5)

            # Displays each die for the player (showing "WILD" for wild dice if applicable)
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
                # Each die is displayed with its value (or "WILD") and styled as a solid bordered label
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

        # Check if the bid is invalid
        if quantity < self.game.state.current_bid[0] or (
                quantity == self.game.state.current_bid[0] and value <= self.game.state.current_bid[1]):
            messagebox.showerror("Invalid Bid", "Humans bid must be higher than the current bid.")
            return

            # if self.game.state.current_player_index!=0:
        #     quantity,value=self.game.state.current_bid
        # quantity+=1
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

        ttk.Button(result_window, text="Continue", command=close_and_continue).pack(pady=20)


if __name__ == "__main__":
    root = tk.Tk()
    app = LiarsDiceGUI(root)
    root.mainloop()