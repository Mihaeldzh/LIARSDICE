from wild_ai import OpenAIFormatter


api_key = "sk-W4m-iZw3xAdCrJAtbgdtIeQAsTs1r2S0svTO1n6yJHT3BlbkFJ1tH8kF4Kj0ax16JiJcEnaWuMpuU0QWIwS8zWxgszEA"
formatter = OpenAIFormatter(api_key=api_key)

class MakeBidInstructions:
    def __init__(self):
        self.instructions = """
"You are playing a dice game with multiple players. The game is played as follows:

Each player rolls five dice and keeps the result hidden from others.
Players take turns making bids about how many dice of a particular face value are present among all players.
On your turn, you can either:
Raise the bid by increasing the quantity or the face value.
Call the previous player a liar by challenging their bid.
If you challenge a bid and the bid is false, the challenger wins. If the bid is valid, the bidder wins.
Each time a player loses, they lose one of their dice. The game continues until only one player has dice left.

Your Goals:
Your objective is to outlast all other players by strategically bidding or calling bluffs.
 Keep track of the current bids and the history of the game to make the best decisions based on the dice you and others may have rolled.
Use your strategy to:

Make bids that seem plausible, or bluff to mislead opponents.
Challenge bids that seem too unlikely to be true.
        """
        self.data = ""
        self.additional_info = ""
        self.format_info = ""

    def add_wild_ones_rule(self):
        self.instructions+="Advanced rule: In this game, the face 'ones' are wild, and can represent any face value."

    def set_data(self, data):
        self.data = data


    def set_additional_info(self, info):
        self.additional_info = info

    def set_format_info(self, format_info):
        self.format_info = format_info

    def get_prompt(self):
        return self.instructions + self.data + self.additional_info + self.format_info


class CallFakeInstructions:
    def __init__(self):
        self.instructions = """
You are about to decide whether to challenge the previous player's bid in a dice game. Your goal is to determine if the bid is likely false based on your own dice and the game context. Here's how you should approach the decision:

Analyze the Bid:

Consider the face value and the number of dice claimed in the current bid.
Compare the bid to the dice in your hand. If you hold a significant portion of the dice with that face value, the bid may be fake.
Estimate Total Dice in Play:

Estimate how many dice of the bid face value could reasonably be on the table, based on the number of players and remaining dice.
If the bid seems too high compared to the estimated number of dice in play, it's more likely a bluff.
Consider Game History:

Review the bidding history. Has the current player been bluffing or making safe bids so far? This can help you gauge whether their current bid is trustworthy or suspicious.
Weigh the Risk:

If you successfully challenge a fake bid, you gain a strategic advantage. However, if the bid is valid and you call incorrectly, you lose a die.
Evaluate whether the risk of losing a die is worth the potential reward of exposing a fake bid.
        """
        self.data = ""
        self.additional_info = ""
        self.format_info = ""
    def add_wild_ones_rule(self):
        self.instructions+="""Wild Ones Rule is Active:
In this game, the face 'ones' are wild. This means that 'ones' can count as any face value in bids.
When making your decision, consider that the number of 'ones' on the table can significantly increase the likelihood of a bid being valid.
This rule makes it more difficult to determine whether a bid is false, so take extra care when calling a bluff.
Factor this into your final decision before challenging a bid."""

    def set_data(self, data):
        self.data = data

    def set_additional_info(self, info):
        self.additional_info = info

    def set_format_info(self, format_info):
        self.format_info = format_info

    def get_prompt(self):
        return self.instructions + self.data + self.additional_info + self.format_info


# Function for AI to make a bid
def wild_ai_make_bid(data,dice,name,play_style='optimal',wild_ones_mode=False):
    make_bid_instructions = MakeBidInstructions()
    if wild_ones_mode:
        make_bid_instructions.add_wild_ones_rule()
    make_bid_instructions.set_data(f"\nThe history of the game flow is: {data}.\n Now it is your turn you are {name} and you have dice: {dice}\n")
    if play_style == "safe":
        make_bid_instructions.set_additional_info("""Use Safe Playstyle:
Focus on conservative bidding. Only raise the bid when you are confident the total number of dice will meet or exceed your bid.
Call a bluff only when you have strong evidence that the bid is false based on your dice and the game history.
Prioritize survival and avoid unnecessary risks.""")
    elif play_style == "aggressive":
        make_bid_instructions.set_additional_info("""Use Aggressive Playstyle:
Take risks by raising the bid even when you don't have full confidence in the dice pool.
Challenge bids more frequently, even when the evidence isn't clear.
Try to intimidate opponents with high bids and frequent challenges.""")
    elif play_style == "bluff":
        make_bid_instructions.set_additional_info("""Use Bluff Playstyle:
Bluff often by bidding higher than the dice you actually have.
Try to deceive opponents and keep them guessing.
Challenge bids aggressively, even if you don't have strong evidence.""")
    else:
        make_bid_instructions.set_additional_info("""Shift between safe, aggressive, and bluff tactics as needed.
If your opponents are conservative, bluff more often. If they are aggressive, play it safe and call bluffs strategically.
Always analyze the risks and rewards of each decision.""")
    make_bid_instructions.set_format_info("ALWAYS REMEMBER: Raise the bid by increasing the quantity or the face value.\nThe format of the response should be ONLY a in a python tuple and nothing more."
                                          " Example tuple :(the bid quantity,and the bid value)")

    make_bid_prompt = make_bid_instructions.get_prompt()
    print(make_bid_prompt)
    result_make_bid = formatter.process_prompt(make_bid_prompt, code_output=True)

    return result_make_bid


def wild_ai_call_fake(data,dice,name,play_style='optimal',wild_ones_mode=False):
    call_fake_instructions = CallFakeInstructions()
    if wild_ones_mode:
        call_fake_instructions.add_wild_ones_rule()
    call_fake_instructions.set_data(f"\nThe history of the game flow is: {data}.\n Now it is your turn you are {name} and you have dice: {dice}\n")
    if play_style == "safe":
        call_fake_instructions.set_additional_info("""Use Safe Playstyle:
    Focus on cautious decisions. Only call a bluff if the bid seems highly improbable.
    Base your decision on strong evidence from your dice and the game history.
    Avoid calling a bluff unless you are confident the bid is false.
    Prioritize minimizing risks to keep your dice count high.""")
    elif play_style == "aggressive":
        call_fake_instructions.set_additional_info("""Use Aggressive Playstyle:
    Challenge bids frequently, even if the evidence isn't conclusive.
    Take more risks and assume that your opponents are bluffing.
    Trust your instincts and aim to gain an advantage by calling fake bids regularly.
    Intimidate your opponents by not hesitating to challenge their bids.""")
    elif play_style == "bluff":
        call_fake_instructions.set_additional_info("""Use Bluff Playstyle:
    Call bluffs aggressively, often without solid evidence.
    Keep your opponents on edge by frequently challenging their bids.
    Leverage your unpredictability to make your opponents doubt their own bids.
    Use challenges as part of your strategy to manipulate game flow.""")
    else:
        call_fake_instructions.set_additional_info("""Use Optimal Playstyle:
    Adapt your strategy based on the current game context. 
    Shift between cautious, aggressive, and bluff tactics as needed.
    Call a bluff if the bid seems unlikely, but balance risk with reward.
    Monitor game history and adjust your playstyle accordingly to maintain an advantage.""")
    call_fake_instructions.set_format_info("ALWAYS REMEMBER: be sure in your choice\nThe format of the response should be ONLY a in a python list and nothing more."
                                          " Example of that list - containing only True or False :(True(if fake bid)/False(if not fake bid))")

    call_fake_prompt = call_fake_instructions.get_prompt()
    print(call_fake_prompt)
    result_call_fake = formatter.process_prompt(call_fake_prompt, code_output=True)

    return  result_call_fake[0]

if __name__ == "__main__":
    data = ''''
    Round 1
______________________
Current bid: 0 dice with value 1
Current player: Human
Players:
Human: 5 dice
Bot 1: 5 dice
Bot 2: 5 dice
Human is thinking...
Human made a new bid of 1 1s
Current player: Bot 1
Bot 1 is thinking...
    '''
    dice = '[4, 1, 6, 5, 3]'
    name = "Bot 1"
    # print( wild_ai_make_bid(data,dice,name,play_style='aggressive'))
    print( wild_ai_call_fake(data,dice,name,play_style='optimal'))
