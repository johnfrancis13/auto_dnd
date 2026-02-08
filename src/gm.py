# This is the AI brain. The AI should control the flow of the game, create new content as necessary


class gm_llm:
    def __init__(self,model_name):
        self.model_name = model_name
        self.model = self.create_model(self.model_name)

    # Iterate the model to respond to the latest game state
    def create_model(self, model_name):
        model = None
        return(model)
    
    # Iterate the model to respond to the latest game state
    def run(self, game_state):
        output = model.chat(self.model_name)
        return(output)
    
    # Determine if any background actions need to be done, otherwise return the text for the user to respond to it
    def parse_output(self, output):
        pass
        

    