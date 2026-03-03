# This is the AI brain. The AI should control the flow of the game, create new content as necessary
from ollama import chat, ChatResponse
from pydantic import BaseModel, ValidationError
from typing import Optional, List, Literal
from one_shot_adventures import one_shot_adventures
import random
import character as char
import textwrap
# Load in the testing pydantic classes

SkillLiteral = Literal[
    "athletics","acrobatics","sleight_of_hand","stealth",
    "arcana","history","investigation","nature","religion",
    "animal_handling","insight","medicine","perception","survival",
    "deception","intimidation","performance","persuasion"
]

class Mechanics(BaseModel):
    player_intent: str
    requires_roll: bool
    skill: Optional[SkillLiteral] = None

class CombatState(BaseModel):
    initiative_order: List[str]
    current_turn: Optional[str]

class GameState(BaseModel):
    mode: Literal["exploration", "combat"]
    player: str
    enemy: Optional[str]
    combat: Optional[CombatState]
    game_over: bool

class GMResponse(BaseModel):
    game_state: GameState
    narrative: str

def wrap_text(text, width=175):
    print("\n".join(textwrap.fill(p, width) for p in text.split("\n")))



def format_recent_turns(turns):
    formatted = ""
    for t in turns:
        formatted += f"{t['role'].upper()}: {t['content']}\n"
    return formatted





class gm_llm:
    def __init__(self,model_name="qwen3:8b",pc=None):
        self.model_name = model_name
        self.pc= pc
    def choose_new_adventure(self):
        return random.choice(one_shot_adventures)
    # Iterate the model to respond to the latest game state
    def start_adventure(self):
        adventure_data = self.choose_new_adventure()
        self.create_prompts(adventure_data)
        character_introduction = f"Hi, My character is {self.pc.identity.name}, a level {len(self.pc.classes.classes)} {self.pc.identity.race} {self.pc.classes.classes[0]} with the background of {self.pc.identity.background}. {self.pc.short_character_description}"
        wrap_text("\n--- Player ---")
        wrap_text(character_introduction)

        # Set up the turn tracking - eventually switch this bit to logging
        self.turns = [{'role': 'user', 
                 'content': f'{character_introduction} Lets start the adventure!'}
                 ]
        # Create the initial prompt to start the adventure
        response = chat(
            model=self.model_name,
            messages=[{
                "role": "system",
                "content": self.narrator_system_prompt + "\nBegin by introducing the setting naturally, assuming the player knows nothing. Explain why they are here, and what their character knows of the plot."
                },
                {'role': 'user', 
                 'content': f'{character_introduction} Lets start the adventure!'}
                 ],
            think=True,
            format=GMResponse.model_json_schema()
        )

        parsed = GMResponse.model_validate_json(response.message.content)
        wrap_text("\n--- DM ---")
        wrap_text(parsed.narrative)
        self.turns.append({
                  "role": "Dungeon Master",
                  "content": parsed.narrative
              })
        self.story_summary = "The story has just begun"
        self.game_state = parsed.game_state
    
    def create_prompts(self, adventure_data):
        self.narrator_system_prompt = f"""
            ### Dungeon Master
            You are a 5e Dungeon Master with access to all the source books and the ability to homebrew content as necessary.
            You are narrating a unique game for the user.
            You follow the style of DM's like Matthew Mercer and Brennan Lee Mulligan allowing for flexible gameplay that puts the players choices first.
            Your top priorities are player enjoyment and 5e rule following. You are responsible for narration, NPC behavior/roleplay, and scene progression.

            ### Instructions
            - Describe scenes vividly but concisely.
            - Play NPCs dynamically.
            - Maintain tension and pacing.
            - Respect player autonomy, DON'T provide the player specific choices unless they ask for it, allow them to drive the story
            - Never decide player actions, never speak on behalf of the player.
            - If a skill check is provided, determine an appropriate DC based on the context and explain what happens given the value of the roll.

            ### Session 0
            The user is a consenting adult. Your session 0 has allowed adult topics such as violence, religion, politics, alchohol, drugs, and sex. 

            ### GAME PARAMETERS
            - Short one-shot, with a length of 30 minutes to 1 hour.
            - Balance for one level 5 or lower PC.
            - Assume 3-5 scenes maximum
            The current one shot you are running is:
            {adventure_data}
            """
        self.rules_system_prompt = """
            You are a D&D 5e rules engine responsible ONLY for mechanics.

            Your job:
            1. Extract the player's intent.
            2. Determine whether a skill check is required.
            3. If required, choose the correct 5e skill from the allowed list.

            --------------------------------
            A skill check is required if:
            - 5e rules dictate a roll in this situation.
            - The outcome is uncertain.
            - Failure would matter.
            - Success is possible.

            If the action is trivial or automatically successful, no roll is required.

            --------------------------------
            Allowed skills:
            athletics, acrobatics, sleight_of_hand, stealth,
            arcana, history, investigation, nature, religion,
            animal_handling, insight, medicine, perception, survival,
            deception, intimidation, performance, persuasion

            --------------------------------
            Output Rules:
            - Respond ONLY in valid JSON.
            - Do not explain reasoning.
            - If requires_roll is false, skill must be null.
            - If requires_roll is true, skill must be one of the allowed skills.

            --------------------------------
            Examples:

            {
              "player_intent": "force open reinforced wooden door",
              "requires_roll": True,
              "skill": "athletics"
            }

            {
              "player_intent": "ask the shopkeeper what goods they have in stock",
              "requires_roll": False,
              "skill": None
            }
            """
        self.summarizer_prompt = """
            You are a story compression engine.

            Your job:
            - Merge the existing summary with the recent turns.
            - Preserve important facts.
            - Preserve character changes.
            - Preserve unresolved objectives.
            - Preserve new NPCs, locations, and consequences.
            - Remove dialogue and unimportant description.

            Output:
            - 5 to 8 sentences maximum.
            - No commentary.
            - No formatting.
            - Only the updated summary text.
            """
    def resummarize_story(self, story_summary, turns):
        formatted_turns = format_recent_turns(turns[-10:])
        summary_messages = [ {
            "role": "system",
            "content": self.summarizer_prompt},
            { "role": "user",
               "content": f"""
               EXISTING SUMMARY:
               {story_summary}

               RECENT TURNS:
               {formatted_turns}
                """}]
        response = chat(
            model='qwen3:8b',
            messages=summary_messages,
            think=True)
        return response["message"]["content"]
    
    
    # Determine if any background actions need to be done, otherwise return the text for the user to respond to it
    def roll_skill_check(self,skill="athletics"):
        return self.pc.actions.roll_skill_check(skill).total
    
    def examine_player_intent(self,messages):
        response= chat(
            model=self.model_name,
            messages=messages,
            think=True,
            format=Mechanics.model_json_schema(),
            options={"temperature": 0.1})
        return response
    
    def build_messages(self,system_prompt, game_state, story_summary, recent_turns):
        return [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""
            GAME STATE:
            {game_state.model_dump_json(indent=2)}

            STORY SO FAR:
            {story_summary}

            LATEST EXCHANGE:
            {format_recent_turns(recent_turns)}
            """
                    }
                ]
    def run_turn(self,user_input):

    
        self.turns.append({"role": "user",
                      "content": user_input})

        intent_messages = [{
            "role": "system",
            "content": self.rules_system_prompt
            },
            {'role': 'user', 
             'content': f"""
                         Current Game State:
                         {self.game_state.model_dump_json()}
                         Player:
                         {user_input}
                         """}]
        response = self.examine_player_intent(intent_messages)
        try:
            player_intent = Mechanics.model_validate_json(response["message"]["content"])
        except ValidationError as e:
            print("Invalid response from LLM:", e)
            return None
        print(player_intent)
        if player_intent.requires_roll:
            result = self.roll_skill_check(player_intent.skill)
            formatted_result = f"The player rolled a {result} on the requested {player_intent.skill} skill check."
            self.turns.append({'role': 'tool', 'tool_name': "roll_skill_check", 'content': str(formatted_result)})

        # Rebuild the prompt each turn to avoid long conversation history
        messages = self.build_messages(
            self.narrator_system_prompt,
            self.game_state,
            self.story_summary,
            self.turns[-4:])

        response= chat(
            model=self.model_name,
            messages=messages,
            think=True,  
            format=GMResponse.model_json_schema(),
            options={"temperature": 0.7})

        raw = response["message"]["content"]

        try:
            parsed = GMResponse.model_validate_json(raw)
        except ValidationError as e:
            print("Invalid response from LLM:", e)
            return self.game_state  # fail safely

        # Append assistant response to history
        self.turns.append({
              "role": "Dungeon Master",
              "content": parsed.narrative
          })

        wrap_text("\n--- DM ---")
        wrap_text(parsed.narrative)
        self.game_state = parsed.game_state

        return None

    # Iterate the model to respond to the latest game state
    def run_game(self):
        self.start_adventure()

        # Run the full game loop
        while not self.game_state.game_over:
            if self.game_state.mode=="exploration":
                if len(self.turns) % 6 == 0:
                    self.story_summary = self.resummarize_story(self.story_summary,self.turns)
                    print("\n--- Update story summary ---")
                    wrap_text(self.story_summary)
                user_input = input("\nWhat do you do? ")
                wrap_text("\n--- Player ---")
                wrap_text(user_input)
                self.run_turn(user_input)
                print(self.game_state)
            else:
                wrap_text("Combat not implemented yet, ending game")
                self.game_state.game_over = True

        wrap_text("\nGame Over.")

    


    